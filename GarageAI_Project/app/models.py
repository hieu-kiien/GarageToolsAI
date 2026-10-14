# -*- coding: utf-8 -*-
"""Lớp dữ liệu và quy tắc kiểm tra đầu vào (Pydantic v2).

Vì sao dùng Pydantic cho cả biểu mẫu HTML:
Form gửi lại toàn bộ giá trị dưới dạng chuỗi. Nếu ép kiểu thủ công, chỗ này
dễ quên kiểm tra, và chỗ quên là chỗ thừa dữ liệu rác lọt vào CSDL. Pydantic gom
mọi quy tắc vào một chỗ, trả về lỗi theo tên trường để giao diện tô đúng chỗ.

Nguyên tắc áp dụng:
* `extra='forbid'` — chặn gán thừa (mass assignment): form gửi lên `role=MANAGER`
  thì bị từ chối thay vì âm thầm ghi vào CSDL.
* Mọi chuỗi có `max_length`, mọi số có khoảng giới hạn.
* Tiền nhập dạng chuỗi cũng chấp nhận (`1.500.000`), nhưng chỉ nhận số nguyên.
"""
from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .core.money import parse_tien

BIEN_SO = re.compile(r'^[0-9A-ZĐÁÀẢÃẠĂẰẮẲẴẶÂẤẦẨẪẬÉÈẺẼẸÊẾỀỂỄỆÍÌỈĨỊÓÒỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÚÙỦŨỤƯỨỪỬỮỰÝỲỶỸỴĐ -]{3,12}$')
SDT = re.compile(r'^(0|\+84)\d{8,11}$')
EMAIL = re.compile(r'^[^@\s]+@[^@\s]+\.[a-zA-Z]{2,}$')
NGAY_GIO = re.compile(r'^\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(:\d{2})?$')

CoBan = ConfigDict(str_strip_whitespace=True, extra='forbid', validate_assignment=True)


# ---------------------------------------------------------------------------
# Khoá ngoại tham chiếu
# ---------------------------------------------------------------------------
class FKCoBan(BaseModel):
    """Giá trị khóa ngoại tùy chọn: rỗng nghĩa là NULL."""

    model_config = CoBan

    @classmethod
    def tu_form(cls, raw) -> int | None:
        if raw is None or str(raw).strip() == '':
            return None
        return int(str(raw).strip())


# ---------------------------------------------------------------------------
# Tài khoản
# ---------------------------------------------------------------------------
class DangNhapInput(BaseModel):
    model_config = CoBan
    username: str = Field(min_length=3, max_length=40)
    password: str = Field(min_length=6, max_length=128)
    next: str = Field(default='/', max_length=300)

    @field_validator('username')
    @classmethod
    def _chuan_hoa(cls, v: str) -> str:
        v = v.strip()
        if not re.fullmatch(r'[a-z0-9._-]+', v):
            raise ValueError('Tên đăng nhập chỉ gồm chữ thường, số và các ký tự . _ -')
        return v

    @field_validator('next')
    @classmethod
    def _chan_open_redirect(cls, v: str) -> str:
        """Chặn chuyển hướng ra ngoài: chỉ nhận đường dẫn nội bộ bắt đầu bằng /."""
        if not v.startswith('/') or v.startswith('//') or '\\' in v:
            return '/'
        return v


class DoiMatKhauInput(BaseModel):
    model_config = CoBan
    mat_khau_cu: str = Field(min_length=1, max_length=128)
    mat_khau_moi: str = Field(min_length=8, max_length=128)

    @model_validator(mode='after')
    def _khac_nhau(self):
        if self.mat_khau_cu == self.mat_khau_moi:
            raise ValueError('Mật khẩu mới phải khác mật khẩu cũ')
        return self

    @field_validator('mat_khau_moi')
    @classmethod
    def _do_khoe(cls, v: str) -> str:
        if len(set(v)) < 6:
            raise ValueError('Mật khẩu mới cần đủ độ phức tạp')
        return v


class TaiKhoanInput(BaseModel):
    model_config = CoBan
    id: int | None = None
    username: str = Field(min_length=3, max_length=40)
    full_name: str = Field(min_length=2, max_length=80)
    email: str | None = Field(default=None, max_length=120)
    role: Literal['MANAGER', 'RECEPTIONIST', 'TECHNICIAN', 'CASHIER'] = 'RECEPTIONIST'
    is_active: bool = True

    @field_validator('username')
    @classmethod
    def _ten(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.fullmatch(r'[a-z0-9._-]{3,40}', v):
            raise ValueError('Tên đăng nhập chỉ gồm chữ thường, số và các ký tự . _ -')
        return v

    @field_validator('email')
    @classmethod
    def _email(cls, v):
        if v and not EMAIL.match(v):
            raise ValueError('Email không đúng định dạng')
        return v


class LuuTaiKhoanInput(TaiKhoanInput):
    """Tạo/cập nhật tài khoản từ API. `password` chỉ bắt buộc khi tạo mới."""
    password: str | None = Field(default=None, min_length=8, max_length=128)


# ---------------------------------------------------------------------------
# Danh mục
# ---------------------------------------------------------------------------
class DichVuInput(BaseModel):
    model_config = CoBan
    id: int | None = None
    name: str = Field(min_length=2, max_length=120)
    price: Any                      # chuỗi hoặc số, chuẩn hoá thành int
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool = True

    @field_validator('price')
    @classmethod
    def _gia(cls, v) -> int:
        return _chuan_hoa_tien(v, 'Đơn giá')


class PhuTungInput(BaseModel):
    model_config = CoBan
    id: int | None = None
    name: str = Field(min_length=2, max_length=120)
    sku: str | None = Field(default=None, max_length=60)
    price: Any
    stock: Any
    min_stock: Any = 0
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool = True

    @field_validator('price')
    @classmethod
    def _gia(cls, v) -> int:
        return _chuan_hoa_tien(v, 'Đơn giá')

    @field_validator('stock')
    @classmethod
    def _ton(cls, v) -> int:
        n = _chuan_hoa_so(v, 'Tồn kho')
        if n < 0:
            raise ValueError('Tồn kho không được âm')
        return n

    @field_validator('min_stock')
    @classmethod
    def _ton_toi_thieu(cls, v) -> int:
        n = _chuan_hoa_so(v, 'Tồn kho cảnh báo')
        if n < 0:
            raise ValueError('Tồn kho cảnh báo không được âm')
        return n


class NhapKhoInput(BaseModel):
    """Nhập thêm phụ tùng vào kho (RECEIPT)."""
    model_config = CoBan
    part_id: int = Field(gt=0)
    qty: int = Field(gt=0)
    note: str | None = Field(default=None, max_length=500)


class DieuChinhTonKhoInput(BaseModel):
    """Điều chỉnh tồn kho về một giá trị cụ thể (kiểm kê)."""
    model_config = CoBan
    part_id: int = Field(gt=0)
    moi: int = Field(ge=0)
    note: str | None = Field(default=None, max_length=500)


def _chuan_hoa_tien(v, nhan: str) -> int:
    n = parse_tien(v)
    if n is None:
        raise ValueError('%s phải là số' % nhan)
    if n < 0:
        raise ValueError('%s không được âm' % nhan)
    return n


def _chuan_hoa_so(v, nhan: str) -> int:
    if isinstance(v, bool):
        raise ValueError('%s không hợp lệ' % nhan)
    if isinstance(v, int):
        return v
    s = str(v or '').strip()
    if not s:
        raise ValueError('%s không được để trống' % nhan)
    try:
        return int(s)
    except ValueError:
        raise ValueError('%s phải là số nguyên' % nhan)


# ---------------------------------------------------------------------------
# Khách hàng và phương tiện
# ---------------------------------------------------------------------------
class KhachHangInput(BaseModel):
    model_config = CoBan
    id: int | None = None
    name: str = Field(min_length=2, max_length=80)
    phone: str = Field(min_length=8, max_length=20)
    email: str | None = Field(default=None, max_length=120)
    address: str | None = Field(default=None, max_length=200)

    @field_validator('phone')
    @classmethod
    def _sdt(cls, v: str) -> str:
        v = re.sub(r'[\s.\-()]', '', v.strip())
        if not SDT.match(v):
            raise ValueError('Số điện thoại không hợp lệ, cần dạng 09xx xxx xxx')
        return v

    @field_validator('email')
    @classmethod
    def _email(cls, v):
        if v and not EMAIL.match(v):
            raise ValueError('Email không đúng định dạng')
        return v


class PhuongTienInput(BaseModel):
    model_config = CoBan
    id: int | None = None
    plate: str = Field(min_length=3, max_length=12)
    brand: str = Field(min_length=1, max_length=60)
    model: str = Field(min_length=1, max_length=60)
    year: Any = None
    vin: str | None = Field(default=None, max_length=17)
    color: str | None = Field(default=None, max_length=40)
    odometer: Any = None
    customer_id: int = Field(ge=1)
    is_active: bool = True

    @field_validator('plate')
    @classmethod
    def _bien(cls, v: str) -> str:
        v = re.sub(r'\s+', ' ', v.strip().upper())
        if not BIEN_SO.match(v):
            raise ValueError('Biển số không hợp lệ, ví dụ hợp lệ: 30A-1234')
        if not any(c.isdigit() for c in v):
            raise ValueError('Biển số phải có ít nhất một chữ số, ví dụ 30A-1234')
        if not any(c.isalpha() for c in v):
            raise ValueError('Biển số phải có ít nhất một chữ cái, ví dụ 30A-1234')
        return v

    @field_validator('year')
    @classmethod
    def _nam(cls, v):
        if v is None or str(v).strip() == '':
            return None
        try:
            y = int(str(v).strip())
        except ValueError:
            raise ValueError('Năm sản xuất phải là số')
        if not 1900 <= y <= 2100:
            raise ValueError('Năm sản xuất phải nằm trong khoảng 1900 - 2100')
        return y

    @field_validator('vin')
    @classmethod
    def _vin(cls, v):
        if v is None:
            return None
        v = v.strip().upper()
        if not v:
            return None
        if len(v) < 8 or len(v) > 17:
            raise ValueError('VIN phải dài 8–17 ký tự')
        if not re.fullmatch(r'[A-HJ-NPR-Z0-9]+', v):
            raise ValueError('VIN chỉ gồm chữ hoa A–Z (trừ I, O, Q) và số 0–9')
        return v

    @field_validator('odometer')
    @classmethod
    def _odo(cls, v):
        if v is None or str(v).strip() == '':
            return None
        try:
            n = int(str(v).strip())
        except ValueError:
            raise ValueError('Số km phải là số nguyên')
        if n < 0:
            raise ValueError('Số km không được âm')
        if n > 2_000_000:
            raise ValueError('Số km vượt giá trị hợp lý')
        return n


# ---------------------------------------------------------------------------
# Lịch hẹn
# ---------------------------------------------------------------------------
class LichHenInput(BaseModel):
    model_config = CoBan
    id: int | None = None
    customer_id: int = Field(ge=1)
    vehicle_id: int = Field(ge=1)
    scheduled_at: str = Field(min_length=16, max_length=19)
    notes: str | None = Field(default=None, max_length=500)
    status: Literal['SCHEDULED', 'CONFIRMED', 'CANCELLED', 'DONE'] = 'SCHEDULED'

    @field_validator('scheduled_at')
    @classmethod
    def _ngay(cls, v: str) -> str:
        v = v.strip().replace('T', ' ')
        if not NGAY_GIO.match(v):
            raise ValueError('Thời gian phải có dạng YYYY-MM-DD HH:MM')
        import datetime as dt
        try:
            dt.datetime.strptime(v[:16], '%Y-%m-%d %H:%M')
        except ValueError:
            raise ValueError('Thời gian không tồn tại, ví dụ 2026-12-01 08:00')
        return v[:16]

    @field_validator('notes')
    @classmethod
    def _note(cls, v):
        return v.strip() if v else None


# ---------------------------------------------------------------------------
# Phiếu sửa chữa
# ---------------------------------------------------------------------------
class TaoPhieuInput(BaseModel):
    model_config = CoBan
    vehicle_id: int = Field(ge=1)
    technician_id: int | None = None
    technical_notes: str | None = Field(default=None, max_length=1000)

    @field_validator('technician_id', mode='before')
    @classmethod
    def _ktv(cls, v):
        return None if v is None or str(v).strip() == '' else int(str(v).strip())


class TiepNhanInput(BaseModel):
    """Biên bản tiếp nhận xe tại thời điểm khách giao xe."""
    model_config = CoBan
    odometer_at_intake: Any = None
    fuel_level: Literal['EMPTY', 'QUARTER', 'HALF', 'THREE_QUARTER', 'FULL', 'UNKNOWN'] = 'UNKNOWN'
    exterior_condition: str | None = Field(default=None, max_length=1000)
    accessories: str | None = Field(default=None, max_length=500)
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator('odometer_at_intake')
    @classmethod
    def _odo(cls, v):
        if v is None or str(v).strip() == '':
            return None
        try:
            n = int(str(v).strip())
        except ValueError:
            raise ValueError('Số km phải là số nguyên')
        if n < 0:
            raise ValueError('Số km không được âm')
        if n > 2_000_000:
            raise ValueError('Số km vượt giá trị hợp lý')
        return n


class NghiemThuInput(BaseModel):
    """Nghiệm thu: khách ký nhận xe sau khi sửa xong."""
    model_config = CoBan
    acceptance_note: str | None = Field(default=None, max_length=1000)


# ---------------------------------------------------------------------------
# Báo giá chính thức
# ---------------------------------------------------------------------------
class TaoBaoGiaInput(BaseModel):
    model_config = CoBan
    repair_order_id: int = Field(ge=1)
    note: str | None = Field(default=None, max_length=1000)
    valid_until: str | None = Field(default=None, max_length=10)

    @field_validator('valid_until')
    @classmethod
    def _ngay(cls, v):
        if v is None or str(v).strip() == '':
            return None
        import datetime as dt
        s = str(v).strip()
        try:
            dt.datetime.strptime(s, '%Y-%m-%d')
        except ValueError:
            raise ValueError('Ngày hiệu lực phải có dạng YYYY-MM-DD')
        return s


class HangMucBaoGiaInput(BaseModel):
    model_config = CoBan
    loai: Literal['dich_vu', 'phu_tung']
    ma: int = Field(ge=1)
    qty: Any = 1

    @field_validator('qty')
    @classmethod
    def _so(cls, v) -> int:
        n = _chuan_hoa_so(v, 'Số lượng')
        if n < 1:
            raise ValueError('Số lượng phải lớn hơn 0')
        if n > 9999:
            raise ValueError('Số lượng quá lớn')
        return n


class DuyetBaoGiaInput(BaseModel):
    model_config = CoBan
    quyet_dinh: Literal['APPROVED', 'REJECTED']


class ThemHangMucInput(BaseModel):
    model_config = CoBan
    loai: Literal['dich_vu', 'phu_tung']
    ma: int = Field(ge=1)
    qty: Any = 1

    @field_validator('qty')
    @classmethod
    def _so(cls, v) -> int:
        n = _chuan_hoa_so(v, 'Số lượng')
        if n < 1:
            raise ValueError('Số lượng phải lớn hơn 0')
        if n > 9999:
            raise ValueError('Số lượng quá lớn')
        return n


class DoiTrangThaiInput(BaseModel):
    """Trạng thái phiếu sửa chữa — chỉ nhận mã hợp lệ của máy trạng thái."""
    model_config = CoBan
    status: Literal['RECEIVED', 'INSPECTING', 'ESTIMATING', 'REPAIRING',
                    'COMPLETED', 'CANCELLED']


class PhanCongInput(BaseModel):
    model_config = CoBan
    technician_id: int | None = None

    @field_validator('technician_id', mode='before')
    @classmethod
    def _ktv(cls, v):
        return None if v is None or str(v).strip() == '' else int(str(v).strip())


class NhatKyInput(BaseModel):
    model_config = CoBan
    note: str = Field(min_length=1, max_length=1000)

    @field_validator('note')
    @classmethod
    def _noi_dung(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('Nội dung nhật ký không được để trống')
        return v


# ---------------------------------------------------------------------------
# Hóa đơn và thanh toán
# ---------------------------------------------------------------------------
class ThanhToanInput(BaseModel):
    model_config = CoBan
    amount: Any
    method: Literal['CASH', 'CARD', 'TRANSFER', 'ZALO'] = 'CASH'

    @field_validator('amount')
    @classmethod
    def _tien(cls, v) -> int:
        n = parse_tien(v)
        if n is None:
            raise ValueError('Số tiền không hợp lệ')
        if n <= 0:
            raise ValueError('Số tiền thanh toán phải lớn hơn 0')
        if n > 10_000_000_000:
            raise ValueError('Số tiền vượt giới hạn cho phép')
        return n


class LapHoaDonInput(BaseModel):
    """Yêu cầu lập hoá đơn từ giao diện JSON (POST /api/invoices)."""
    model_config = CoBan
    repair_order_id: int = Field(ge=1)


# ---------------------------------------------------------------------------
# AI
# ---------------------------------------------------------------------------
class AIHistoryInput(BaseModel):
    model_config = CoBan
    vehicle_id: int = Field(ge=1)


class AIExplainInput(BaseModel):
    model_config = CoBan
    service_id: int = Field(ge=1)


class AIQuoteInput(BaseModel):
    model_config = CoBan
    repair_order_id: int = Field(ge=1)


class ChayAiInput(BaseModel):
    """Thân POST /api/ai/run: trường `kind` + đúng tham số của chức năng đó.

    Khác CoBan ở chỗ `extra='allow'`: các trường riêng (vehicle_id,
    service_id, repair_order_id) do model tương ứng kiểm tra sau khi đã
    biết `kind`.
    """
    model_config = ConfigDict(str_strip_whitespace=True, extra='allow')
    kind: str = Field(max_length=30)


class DuyetKetQuaInput(BaseModel):
    model_config = CoBan
    quyet_dinh: Literal['APPROVED', 'REJECTED']


# ---------------------------------------------------------------------------
# Bảo hành
# ---------------------------------------------------------------------------
class TaoBaoHanhInput(BaseModel):
    """Tạo bảo hành cho MỘT hạng mục của phiếu COMPLETED.

    XOR: đúng một trong `service_id` / `part_id` phải khác None.
    """
    model_config = CoBan
    repair_order_id: int = Field(ge=1)
    months: int = Field(ge=1, le=60)
    service_id: int | None = None
    part_id: int | None = None
    note: str | None = Field(default=None, max_length=500)
    start_date: str = Field(min_length=10, max_length=10)

    @model_validator(mode='after')
    def _xor_service_part(self):
        if (self.service_id is None) == (self.part_id is None):
            raise ValueError('phải chọn đúng một trong: dịch vụ hoặc phụ tùng')
        return self


class HuyBaoHanhInput(BaseModel):
    model_config = CoBan
    note: str | None = Field(default=None, max_length=500)


# ---------------------------------------------------------------------------
# Cửa hàng (mở rộng, ngoài phạm vi đề tài)
# ---------------------------------------------------------------------------
class SanPhamInput(BaseModel):
    model_config = CoBan
    id: int | None = None
    name: str = Field(min_length=2, max_length=120)
    sku: str | None = Field(default=None, max_length=60)
    category_id: int = Field(ge=1)
    price: Any
    stock: Any
    description: str | None = Field(default=None, max_length=1000)
    is_active: bool = True

    @field_validator('price')
    @classmethod
    def _gia(cls, v) -> int:
        return _chuan_hoa_tien(v, 'Giá bán')

    @field_validator('stock')
    @classmethod
    def _ton(cls, v) -> int:
        n = _chuan_hoa_so(v, 'Tồn kho')
        if n < 0:
            raise ValueError('Tồn kho không được âm')
        return n