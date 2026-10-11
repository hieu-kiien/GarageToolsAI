# -*- coding: utf-8 -*-
"""Lớp trung gian gọi AI.

Vì sao phải có lớp này: toàn bộ nghiệp vụ không được phụ thuộc vào một nhà
cung cấp AI cụ thể. Đổi provider, bật chế độ dự phòng hay kiểm thử đều chỉ
diễn ra trong tệp này, không đụng tới mã nghiệp vụ.

Ba nguyên tắc bắt buộc:
1. AI KHÔNG phải nguồn của dữ liệu nghiệp vụ. Giá và tổng tiền luôn do backend
   tính, AI chỉ trình bày.
2. Mọi phản hồi đều phải qua kiểm tra trước khi lưu.
3. Lỗi AI không được làm hỏng quy trình garage. Lỗi sẽ được bắt, ghi nhận và
   thông báo cho người dùng.
"""
import json
import logging
import re

from .core.config import get_settings

log = logging.getLogger('garage.ai')


class AiError(Exception):
    """Lỗi khi gọi AI. Ứng dụng bắt lỗi này và hiển thị thông báo."""


class AiResult(dict):
    """Kết quả một lần gọi AI, kèm cờ cho biết có dùng được hay không."""

    @property
    def hop_le(self):
        return bool(self.get('is_valid'))


# ---------------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------------
def _goi_openai(system_prompt, user_prompt):
    if not get_settings().OPENAI_API_KEY:
        raise AiError('Chưa cấu hình khóa API')
    try:
        import httpx
    except ImportError:
        raise AiError('Thiếu thư viện httpx')

    try:
        base = get_settings().OPENAI_BASE_URL.rstrip('/')
        r = httpx.post(
            base + '/chat/completions',
            headers={'Authorization': 'Bearer %s' % get_settings().OPENAI_API_KEY},
            json={
                'model': get_settings().OPENAI_MODEL,
                'temperature': 0,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt},
                ],
            },
            timeout=get_settings().AI_TIMEOUT,
        )
    except httpx.TimeoutException:
        # Không ghi lại khóa hay nội dung nhạy cảm vào log
        raise AiError('Nhà cung cấp AI không phản hồi trong %d giây' % get_settings().AI_TIMEOUT)
    except Exception:
        log.exception('Lỗi kết nối nhà cung cấp AI')
        raise AiError('Không kết nối được nhà cung cấp AI')

    if r.status_code == 429:
        raise AiError('Nhà cung cấp AI đang giới hạn số yêu cầu, vui lòng thử lại sau')
    if r.status_code >= 400:
        # Chỉ ghi mã lỗi, không ghi nội dung phản hồi vì có thể chứa dữ liệu
        log.warning('AI trả mã lỗi %d', r.status_code)
        raise AiError('Nhà cung cấp AI trả lỗi %d' % r.status_code)
    try:
        return r.json()['choices'][0]['message']['content']
    except Exception:
        raise AiError('Phản hồi AI không đúng định dạng mong đợi')


def _goi_mock(system_prompt, user_prompt):
    """Chế độ dự phòng.

    Không gọi mạng. Dùng để demo và kiểm thử khi không có khóa API, và làm
    chế độ dự phòng khi nhà cung cấp AI lỗi.
    """
    return None


def goi(system_prompt, user_prompt, cho_phep_mock=True):
    """Gọi AI theo cấu hình. Trả về chuỗi kết quả."""
    user_prompt = _cat_ngoi_dung(user_prompt)
    if get_settings().AI_PROVIDER == 'mock':
        return _goi_mock(system_prompt, user_prompt)
    try:
        return _goi_openai(system_prompt, user_prompt)
    except AiError:
        if cho_phep_mock:
            log.warning('AI lỗi, chuyển sang chế độ dự phòng')
            return _goi_mock(system_prompt, user_prompt)
        raise


def _cat_ngoi_dung(text):
    """Giới hạn độ dài ngữ cảnh để không vượt giới hạn và tăng chi phí."""
    if len(text) <= get_settings().AI_MAX_CONTEXT:
        return text
    return text[:get_settings().AI_MAX_CONTEXT] + '\n[dữ liệu bị cắt bớt do vượt giới hạn độ dài]'


def _lay_input(text):
    return {'provider': get_settings().AI_PROVIDER, 'model': get_settings().OPENAI_MODEL,
            'do_dai_input': len(text or '')}


# ---------------------------------------------------------------------------
# AI01 – Tóm tắt lịch sử sửa chữa
# ---------------------------------------------------------------------------
def tom_tat_lich_su(vehicle_id):
    from .core import db

    xe = db.fetch_one(
        'SELECT v.*, c.name AS customer_name FROM vehicles v'
        ' JOIN customers c ON c.id = v.customer_id WHERE v.id = ?', (vehicle_id,))
    if xe is None:
        raise AiError('Không tìm thấy xe')

    phieu = db.fetch_all(
        'SELECT r.id, r.status, r.technical_notes, r.created_at, v.plate'
        ' FROM repair_orders r JOIN vehicles v ON v.id = r.vehicle_id'
        ' WHERE r.vehicle_id = ? AND r.status <> %s'
        ' ORDER BY r.created_at DESC' % "'CANCELLED'", (vehicle_id,))

    dong = []
    for p in phieu:
        items = db.fetch_all(
            'SELECT COALESCE(s.name, pt.name) AS ten, i.qty, i.unit_price'
            ' FROM repair_order_items i'
            ' LEFT JOIN services s ON s.id = i.service_id'
            ' LEFT JOIN parts pt ON pt.id = i.part_id'
            ' WHERE i.repair_order_id = ?', (p['id'],))
        chitiet = '; '.join('%s x%d' % (i['ten'], i['qty']) for i in items) or 'chưa có hạng mục'
        dong.append('  - %s: %s (%s). Hạng mục: %s'
                    % (p['created_at'], p['id'], p['status'], chitiet))

    if phieu:
        lich_su = ('Xe: %s %s %s\nKhách hàng: %s\nSố lần sửa chữa: %d\nCác lần sửa chữa:\n%s'
                   % (xe['plate'], xe['brand'], xe['model'], xe['customer_name'],
                      len(phieu), '\n'.join(dong)))
    else:
        lich_su = ('Xe: %s %s %s\nKhách hàng: %s\nSố lần sửa chữa: 0\nCác lần sửa chữa: (không có)'
                   % (xe['plate'], xe['brand'], xe['model'], xe['customer_name']))

    user = get_settings().render_prompt(get_settings().load_prompt('history.txt'),
                                  repair_history=lich_su)
    out = goi(get_settings().load_prompt('system.txt'), user)

    if out is None:                       # chế độ mock
        out = _mock_history(xe, phieu, dong)

    return AiResult(kind='history', repair_order_id=None,
                    input_json=json.dumps(_lay_input(user), ensure_ascii=False),
                    output_text=out, is_valid=bool(out))


def _mock_history(xe, phieu, dong):
    if not phieu:
        return ('1. Thông tin xe: %s – %s %s\n'
                '2. Tổng quan: 0 lần sửa\n'
                '3. Các lần sửa chữa gần đây: (không có)\n'
                '4. Dữ liệu thiếu: Không có'
                % (xe['plate'], xe['brand'], xe['model']))
    return ('1. Thông tin xe: %s – %s %s\n'
            '2. Tổng quan: %d lần sửa, lần sửa gần nhất %s\n'
            '3. Các lần sửa chữa gần đây:\n%s\n'
            '4. Dữ liệu thiếu: Không có'
            % (xe['plate'], xe['brand'], xe['model'], len(phieu),
               phieu[0]['created_at'], '\n'.join(dong)))


# ---------------------------------------------------------------------------
# AI02 – Giải thích dịch vụ
# ---------------------------------------------------------------------------
def giai_thich_dich_vu(service_id):
    from .core import db

    dv = db.fetch_one('SELECT * FROM services WHERE id = ?', (service_id,))
    if dv is None:
        raise AiError('Không tìm thấy dịch vụ')

    user = get_settings().render_prompt(get_settings().load_prompt('explain.txt'),
                                  service='Tên dịch vụ: %s\nMô tả trong danh mục: %s'
                                          % (dv['name'], dv['description'] or '(danh mục chưa có mô tả)'))
    out = goi(get_settings().load_prompt('system.txt'), user)

    if out is None:                       # chế độ mock
        if not dv['description']:
            out = ('1. Dịch vụ là gì: Danh mục chưa có mô tả cho dịch vụ này\n'
                   '2. Hạng mục đang ghi nhận: %s\n'
                   '3. Khách cần lưu ý: Không có' % dv['name'])
        else:
            out = ('1. Dịch vụ là gì: %s\n'
                   '2. Hạng mục đang ghi nhận: %s\n'
                   '3. Khách cần lưu ý: Chi phí dự kiến %s đồng'
                   % (dv['description'], dv['name'], format(dv['price'], ',').replace(',', '.')))

    return AiResult(kind='explain', repair_order_id=None,
                    input_json=json.dumps(_lay_input(user), ensure_ascii=False),
                    output_text=out, is_valid=bool(out))


# ---------------------------------------------------------------------------
# AI03 – Báo giá nháp
# ---------------------------------------------------------------------------
def bao_gia_nhap(order_id):
    """Tạo bản nháp báo giá.

    Tổng tiền luôn do backend tính từ CSDL. Nếu AI trả về tổng khác, hệ thống bỏ
    qua giá trị của AI. Nếu AI thêm hạng mục không có trong phiếu, hạng mục đó
    bị loại.
    """
    from .core import db

    phieu = db.fetch_one('SELECT * FROM repair_orders WHERE id = ?', (order_id,))
    if phieu is None:
        raise AiError('Không tìm thấy phiếu sửa chữa')

    items = db.fetch_all(
        'SELECT i.id, COALESCE(s.name, pt.name) AS ten, i.qty, i.unit_price,'
        '       i.unit_price * i.qty AS subtotal'
        ' FROM repair_order_items i'
        ' LEFT JOIN services s ON s.id = i.service_id'
        ' LEFT JOIN parts pt ON pt.id = i.part_id'
        ' WHERE i.repair_order_id = ?', (order_id,))

    backend_total = db.tong_phieu(order_id)

    if not items:
        return AiResult(kind='quote', repair_order_id=order_id,
                        input_json=json.dumps({'items': [], 'backend_total': backend_total},
                                              ensure_ascii=False),
                        output_text='Phiếu sửa chữa số %d chưa có hạng mục nào được ghi nhận nên chưa thể lập báo giá nháp.'
                                    % order_id,
                        is_valid=True)

    danh_sach = '\n'.join('  - %s | số lượng: %d | đơn giá: %d | thành tiền: %d'
                          % (i['ten'], i['qty'], i['unit_price'], i['subtotal'])
                          for i in items)

    user = get_settings().render_prompt(get_settings().load_prompt('quote.txt'),
                                  items=danh_sach, backend_total=backend_total)
    raw = goi(get_settings().load_prompt('system.txt'), user)

    notes = ''
    if raw is None:                       # chế độ mock
        parsed, notes = None, ''
    else:
        parsed = _phan_tich_json(raw)

    if parsed is None:
        # Không đọc được JSON: dựng bản nháp từ dữ liệu CSDL, tuyệt đối không đoán
        body_lines = '\n'.join('- %s x%d: %s đồng' % (i['ten'], i['qty'],
                                                      format(i['subtotal'], ',').replace(',', '.'))
                               for i in items)
        out = ('Bảng báo giá nháp cho phiếu sửa chữa số %d\n%s\nTổng dự kiến: %s đồng\n'
               'Báo giá nháp, cần nhân viên kiểm tra trước khi sử dụng.'
               % (order_id, body_lines,
                  format(backend_total, ',').replace(',', '.')))
        return AiResult(kind='quote', repair_order_id=order_id,
                        input_json=json.dumps({'items': len(items),
                                               'backend_total': backend_total,
                                               'doc_ai_doc_duoc': False}, ensure_ascii=False),
                        output_text=out, is_valid=True)

    # Lọc lại: chỉ giữ hạng mục khớp với phiếu, tên, số lượng và đơn giá.
    # Dữ liệu trả về từ mô hình là dữ liệu KHÔNG TIN CẬY: có thể là danh sách
    # thay vì đối tượng, có thể thiếu khoá, có thể chứa chuỗi thay vì số. Mọi
    # phép chuyển kiểu phải bọc try, nếu không sẽ thành lỗi 500 cho người dùng.
    hop_le = []
    doc_ai = parsed.get('items')
    for p in (doc_ai if isinstance(doc_ai, list) else []):
        if not isinstance(p, dict):
            continue
        ten = str(p.get('name') or '').strip()
        so_luong = _so_nguyen(p.get('qty'))
        don_gia = _so_nguyen(p.get('unit_price'))
        if so_luong is None or don_gia is None:
            continue
        for i in items:
            if ten == i['ten'] and so_luong == i['qty'] and don_gia == i['unit_price']:
                hop_le.append({'name': i['ten'], 'qty': i['qty'],
                               'unit_price': i['unit_price'], 'subtotal': i['subtotal']})
                break

    thanh = '\n'.join('- %s x%d: %s đồng' % (i['name'], i['qty'],
                                              format(i['subtotal'], ',').replace(',', '.'))
                      for i in hop_le) or '(không có hạng mục nào khớp với phiếu)'
    tong_ai = _so_nguyen(parsed.get('total'))
    canh_bao = ('Tổng do AI trả về (%s) khác tổng của hệ thống, hệ thống dùng %s đồng.'
                % (tong_ai, format(backend_total, ',').replace(',', '.'))
                if tong_ai is not None and tong_ai != backend_total else '')

    ghi_chu = parsed.get('notes')
    ghi_chu = str(ghi_chu) if isinstance(ghi_chu, str) else ''
    out = ('Bảng báo giá nháp cho phiếu sửa chữa số %d\n%s\nTổng dự kiến: %s đồng\n%s\n%s\n'
           'Báo giá nháp, cần nhân viên kiểm tra trước khi sử dụng.'
           % (order_id, thanh, format(backend_total, ',').replace(',', '.'),
              canh_bao, ghi_chu))
    return AiResult(kind='quote', repair_order_id=order_id,
                    input_json=json.dumps({'items': len(items), 'backend_total': backend_total,
                                           'doc_ai_doc_duoc': True}, ensure_ascii=False),
                    output_text=out, is_valid=True)


def _so_nguyen(v):
    """Đổi giá trị do mô hình trả về thành số nguyên, sai thì trả None.

    Không dùng `int()` trực tiếp vì `int('abc')` ném ValueError và làm hỏng cả
    request — lỗi của dịch vụ ngoài không được biến thành lỗi 500.
    """
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return int(v) if v.is_integer() else None
    if isinstance(v, str):
        s = re.sub(r'[^\d-]', '', v)
        try:
            return int(s) if s not in ('', '-') else None
        except ValueError:
            return None
    return None


def _phan_tich_json(raw):
    """Đọc JSON trả về. Chịu được trường hợp model bọc trong khối văn bản."""
    raw = (raw or '').strip()
    if not raw:
        return None
    if raw.startswith('```'):
        raw = re.sub(r'^```[a-zA-Z]*\s*', '', raw)
        raw = re.sub(r'\s*```$', '', raw).strip()
    try:
        return json.loads(raw)
    except ValueError:
        pass
    m = re.search(r'\{.*\}', raw, re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except ValueError:
            return None
    return None