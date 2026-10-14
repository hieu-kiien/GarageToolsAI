# -*- coding: utf-8 -*-
"""Xác thực và phân quyền."""
from __future__ import annotations

import sqlite3

from .. import crud
from ..core import ratelimit
from ..core.errors import (AppError, KhongCoQuyen, KhongXacThuc, SaiQuyTac, XungDdot)
from ..core.security import (doc_phien, tao_phien, verify_dummy,
                             verify_password)
from ..models import DangNhapInput, DoiMatKhauInput, TaiKhoanInput
from .security_matrix import VAI_TRO, co_quyen


class NguoiDung(dict):
    """Bản ghi người dùng đã làm sạch, dùng cho template và kiểm tra quyền."""

    @property
    def ten_vai_tro(self) -> str:
        return VAI_TRO.get(self['role'], self['role'])


def _lam_sach(ban_ghi: dict) -> NguoiDung:
    return NguoiDung({
        'id': int(ban_ghi['id']),
        'username': ban_ghi['username'],
        'full_name': ban_ghi.get('full_name') or ban_ghi['username'],
        'email': ban_ghi.get('email'),
        'role': ban_ghi['role'],
        'is_active': bool(ban_ghi.get('is_active', 1)),
        'auth_version': int(ban_ghi.get('auth_version') or 1),
    })


# ---------------------------------------------------------------------------
# Phiên
# ---------------------------------------------------------------------------
def nguoi_dung_hien_tai(request) -> NguoiDung | None:
    """Đọc cookie phiên rồi đối chiếu với CSDL mỗi lần có yêu cầu.

    Đối chiếu mỗi lần giúp hai thứ: tài khoản bị khoá có hiệu lực ngay, và đổi
    mật khẩu làm mất hiệu lực mọi phiên cũ nhờ `auth_version`.
    """
    from ..core.config import get_settings
    phien = doc_phien(request.cookies.get(get_settings().SESSION_COOKIE))
    if phien is None:
        return None
    ban_ghi = crud.nguoi_dung_theo_id(phien.user_id)
    if not ban_ghi or not ban_ghi.get('is_active'):
        return None
    if int(ban_ghi.get('auth_version') or 1) != phien.auth_version:
        return None
    return _lam_sach(ban_ghi)


def yeu_cau_dang_nhap(request) -> NguoiDung | None:
    return nguoi_dung_hien_tai(request)


def yeu_cau_quyen(request, quyen: str) -> NguoiDung | None:
    """Trả về None nếu chưa đăng nhập, ném KhongCoQuyen nếu không đủ quyền."""
    u = nguoi_dung_hien_tai(request)
    if u is None:
        return None
    if not co_quyen(u['role'], quyen):
        raise KhongCoQuyen(
            'Vai trò %s không được phép thực hiện chức năng này.' % VAI_TRO.get(u['role']))
    return u


def co_the_quyen(u: dict | None, quyen: str) -> bool:
    return bool(u) and co_quyen(u['role'], quyen)


def gan_quyen_phan_cong(user) -> bool:
    """Vai trò được quyền sửa mọi phiếu, không phụ thuộc phân công."""
    from .security_matrix import PHAN_CONG_CHINH
    return user['role'] in PHAN_CONG_CHINH


# ---------------------------------------------------------------------------
# Đăng nhập
# ---------------------------------------------------------------------------
def dang_nhap(request, du_lieu: DangNhapInput) -> NguoiDung:
    ratelimit.kiem_tra_dang_nhap(request, du_lieu.username)
    ban_ghi = crud.nguoi_dung_theo_username(du_lieu.username)
    if ban_ghi is None:
        # Vẫn băm mật khẩu giả để thời gian phản hồi không tiết lộ tài khoản.
        verify_dummy(du_lieu.password)
        ratelimit.ghi_nhan_that_bai(du_lieu.username)
        raise KhongXacThuc('Sai tên đăng nhập hoặc mật khẩu.')
    if not verify_password(du_lieu.password, ban_ghi['password_hash']):
        ratelimit.ghi_nhan_that_bai(du_lieu.username)
        raise KhongXacThuc('Sai tên đăng nhập hoặc mật khẩu.')
    if not ban_ghi.get('is_active'):
        raise KhongXacThuc('Tài khoản đã bị khoá. Vui lòng liên hệ quản lý.')
    return _lam_sach(ban_ghi)


def tao_phien_cho(user: NguoiDung) -> str:
    return tao_phien(user['id'], user.get('auth_version', 1))


# ---------------------------------------------------------------------------
# Quản lý tài khoản
# ---------------------------------------------------------------------------
def _dong_mat_khau_ve(ten_nguoi_dung: str, cu: str, moi: str) -> None:
    if crud.co_ban_ghi('users', 'username = ?', (cu.lower(),)):
        raise XungDdot('Tên đăng nhập %s đã tồn tại.' % cu, truong='username')


def tao_tai_khoan(du_lieu: TaiKhoanInput, mat_khau: str) -> int:
    _dong_mat_khau_ve(du_lieu.full_name, du_lieu.username, du_lieu.username)
    try:
        khoa = crud.them('users', {
            'username': du_lieu.username,
            'password_hash': _bam(mat_khau),
            'full_name': du_lieu.full_name,
            'email': du_lieu.email,
            'role': du_lieu.role,
            'is_active': 1 if du_lieu.is_active else 0,
            'auth_version': 1,
        })
    except sqlite3.IntegrityError as e:
        raise _loi_integrity(e)
    return khoa


def sua_tai_khoan(du_lieu: TaiKhoanInput, mat_khau_moi: str | None = None) -> None:
    """Cập nhật tài khoản. `mat_khau_moi` khác None thì đổi mật khẩu luôn.

    Khi đổi mật khẩu, đổi vai trò hoặc khoá tài khoản thì tăng `auth_version`
    của tài khoản đó để vô hiệu hoá các phiên cũ của người dùng này.
    """
    cu = crud.yeu_cau_co('users', du_lieu.id, 'tài khoản')
    if crud.co_ban_ghi('users', 'username = ? AND id <> ?',
                       (du_lieu.username, du_lieu.id)):
        raise XungDdot('Tên đăng nhập %s đã tồn tại.' % du_lieu.username,
                       truong='username')
    du = {
        'username': du_lieu.username,
        'full_name': du_lieu.full_name,
        'email': du_lieu.email,
        'role': du_lieu.role,
        'is_active': 1 if du_lieu.is_active else 0,
    }
    if mat_khau_moi:
        du['password_hash'] = _bam(mat_khau_moi)
    crud.sua('users', du_lieu.id, du)
    if mat_khau_moi or cu.get('role') != du_lieu.role or not du_lieu.is_active:
        crud.tang_phien_ban(du_lieu.id)


def doi_mat_khau(user: NguoiDung, du_lieu: DoiMatKhauInput) -> None:
    ban_ghi = crud.nguoi_dung_theo_username(user['username'])
    if not ban_ghi or not verify_password(du_lieu.mat_khau_cu, ban_ghi['password_hash']):
        raise KhongXacThuc('Mật khẩu cũ không đúng.')
    crud.sua('users', user['id'], {'password_hash': _bam(du_lieu.mat_khau_moi)})
    crud.tang_phien_ban(user['id'])      # vô hiệu mọi phiên đang mở


def khoa_tai_khoan(user_id: int, vo_hieu_phien: bool = True) -> None:
    crud.yeu_cau_co('users', user_id, 'tài khoản')
    crud.sua('users', user_id, {'is_active': 0})
    if vo_hieu_phien:
        crud.tang_phien_ban(user_id)


def mo_tai_khoan(user_id: int) -> None:
    crud.yeu_cau_co('users', user_id, 'tài khoản')
    crud.sua('users', user_id, {'is_active': 1})


def _bam(mat_khau: str) -> str:
    from ..core.security import hash_password
    return hash_password(mat_khau)


def _loi_integrity(e: sqlite3.IntegrityError) -> AppError:
    """Dịch lỗi ràng buộc CSDL thành thông báo tiếng Việt cho người dùng."""
    n = str(e)
    if 'username' in n:
        return XungDdot('Tên đăng nhập đã tồn tại.', truong='username')
    if 'plate' in n:
        return XungDdot('Biển số đã tồn tại.', truong='plate')
    if 'FOREIGN KEY' in n:
        return SaiQuyTac('Dữ liệu tham chiếu không tồn tại hoặc không còn được phép dùng.')
    return SaiQuyTac('Dữ liệu không hợp lệ: %s' % n)


# Tên cũ (typo) được giữ lại để không vỡ import ở nơi khác.
XungDpot = XungDdot