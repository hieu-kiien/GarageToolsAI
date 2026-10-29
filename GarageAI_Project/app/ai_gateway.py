# -*- coding: utf-8 -*-
"""Lớp trung gian gọi AI.

Vì sao phải có lớp này: toàn bộ nghiệp vụ không được phụ thuộc vào một nhà
cung cấp AI cụ thể. Đổi provider, bật chế độ dự phòng hay kiểm thử đều chỉ
diễn ra trong tệp này, không đụng tới mã nghiệp vụ.

Ba nguyên tắc bắt buộc:
1. AI KHÔNG phải nguồn của dữ liệu nghiệp vụ. Giá và tổng tiền luôn do backend
   tính, AI chỉ trình bày hoặc gợi ý đúng danh mục có sẵn trong CSDL.
2. Mọi phản hồi đều phải qua kiểm tra trước khi lưu.
3. Lỗi AI không được làm hỏng quy trình garage. Lỗi sẽ được bắt, ghi nhận và
   thông báo cho người dùng.
"""
import json
import logging
import re

from .core.config import get_settings
from .core.errors import KhongTimThay

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
def _chat_url(s) -> str:
    """Gộp base URL thành endpoint chat/completions (chấp nhận cả 2 dạng)."""
    base = (s.AI_BASE_URL or s.OPENAI_BASE_URL or '').rstrip('/')
    if not base:
        raise AiError('Chưa cấu hình AI_BASE_URL')
    if base.endswith('/chat/completions'):
        return base
    return base + '/chat/completions'


def _headers(s) -> dict:
    key = (s.AI_API_KEY or s.OPENAI_API_KEY or '').strip()
    # 9router local có thể chạy requireApiKey=false → không gửi Authorization.
    if not key and s.AI_PROVIDER == '9router':
        return {}
    h = {
        'Authorization': 'Bearer %s' % key,
        'User-Agent': 'GarageToolsAI/2.0 (Mozilla/5.0 compatible)',
    }
    # OpenRouter khuyến nghị gửi 2 header này để được ghi nhận traffic.
    if s.AI_PROVIDER == 'openrouter':
        h.setdefault('HTTP-Referer', 'https://localhost')
        h.setdefault('X-Title', s.APP_NAME)
    return h


def _goi_openai(system_prompt, user_prompt):
    s = get_settings()
    if s.AI_PROVIDER != '9router' and not (s.AI_API_KEY or s.OPENAI_API_KEY):
        raise AiError('Chưa cấu hình khóa API')
    try:
        import httpx
    except ImportError:
        raise AiError('Thiếu thư viện httpx')

    try:
        r = httpx.post(
            _chat_url(s),
            headers=_headers(s),
            json={
                'model': s.AI_MODEL or s.OPENAI_MODEL,
                'temperature': 0,
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt},
                ],
            },
            timeout=s.AI_TIMEOUT,
        )
    except httpx.TimeoutException:
        # Không ghi lại khóa hay nội dung nhạy cảm vào log
        raise AiError('Nhà cung cấp AI không phản hồi trong %d giây' % s.AI_TIMEOUT)
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


def _lay_input(text, *, du_phong: bool = False):
    s = get_settings()
    fallback = bool(du_phong and s.AI_PROVIDER != 'mock')
    return {
        'provider': s.AI_PROVIDER,
        'provider_thuc_te': 'mock' if du_phong else s.AI_PROVIDER,
        'fallback_used': fallback,
        'model': s.AI_MODEL or s.OPENAI_MODEL,
        'do_dai_input': len(text or ''),
    }


def _fmt_tien(so: int) -> str:
    return format(int(so or 0), ',').replace(',', '.')


# ---------------------------------------------------------------------------
# AI01 – Tóm tắt lịch sử sửa chữa
# ---------------------------------------------------------------------------
def tom_tat_lich_su(vehicle_id):
    from .core import db

    xe = db.fetch_one(
        'SELECT v.*, c.name AS customer_name FROM vehicles v'
        ' JOIN customers c ON c.id = v.customer_id WHERE v.id = ?', (vehicle_id,))
    if xe is None:
        # Thiếu bản ghi là lỗi nghiệp vụ 404, không phải lỗi dịch vụ ngoài 502.
        raise KhongTimThay('Không tìm thấy xe số %s.' % vehicle_id)

    phieu = db.fetch_all(
        'SELECT r.id, r.status, r.technical_notes, r.created_at, v.plate'
        ' FROM repair_orders r JOIN vehicles v ON v.id = r.vehicle_id'
        ' WHERE r.vehicle_id = ? AND r.status <> %s'
        ' ORDER BY r.created_at DESC' % "'CANCELLED'", (vehicle_id,))

    bao_hanh = db.fetch_all(
        'SELECT COALESCE(s.name, pt.name) AS ten, w.end_date'
        ' FROM warranties w'
        ' JOIN repair_orders r ON r.id = w.repair_order_id'
        ' LEFT JOIN services s ON s.id = w.service_id'
        ' LEFT JOIN parts pt ON pt.id = w.part_id'
        " WHERE r.vehicle_id = ? AND w.status = 'ACTIVE'"
        ' ORDER BY w.end_date DESC', (vehicle_id,))

    dong = []
    for p in phieu:
        items = db.fetch_all(
            'SELECT COALESCE(s.name, pt.name) AS ten, i.qty, i.unit_price'
            ' FROM repair_order_items i'
            ' LEFT JOIN services s ON s.id = i.service_id'
            ' LEFT JOIN parts pt ON pt.id = i.part_id'
            ' WHERE i.repair_order_id = ?', (p['id'],))
        chitiet = '; '.join('%s x%d' % (i['ten'], i['qty']) for i in items) or 'chưa có hạng mục'
        ghi_chu_kt = str(p.get('technical_notes') or '').strip()
        phan_ghi_chu = ('. Ghi chú kỹ thuật: %s' % ghi_chu_kt) if ghi_chu_kt else ''
        dong.append('  - %s: Phiếu #%s (%s). Hạng mục: %s%s'
                    % (p['created_at'], p['id'], p['status'], chitiet, phan_ghi_chu))

    thong_tin_phu = []
    if xe.get('year'):
        thong_tin_phu.append('Năm SX: %s' % xe['year'])
    if xe.get('odometer') is not None:
        thong_tin_phu.append('ODO: %s km' % _fmt_tien(xe['odometer']))
    chuoi_phu = (' (%s)' % ', '.join(thong_tin_phu)) if thong_tin_phu else ''

    dong_bh = ''
    if bao_hanh:
        dong_bh = '\nBảo hành đang còn hiệu lực: ' + '; '.join(
            '%s (đến %s)' % (b['ten'], b['end_date']) for b in bao_hanh if b.get('ten'))

    # Không gửi họ tên chủ xe (dữ liệu cá nhân nhạy cảm) sang nhà cung cấp AI ngoài.
    if phieu:
        lich_su = ('Xe: %s %s %s%s%s\nSố lần sửa chữa: %d\nCác lần sửa chữa:\n%s'
                   % (xe['plate'], xe['brand'], xe['model'], chuoi_phu, dong_bh,
                      len(phieu), '\n'.join(dong)))
    else:
        lich_su = ('Xe: %s %s %s%s%s\nSố lần sửa chữa: 0\nCác lần sửa chữa: (không có)'
                   % (xe['plate'], xe['brand'], xe['model'], chuoi_phu, dong_bh))

    user = get_settings().render_prompt(get_settings().load_prompt('history.txt'),
                                  repair_history=lich_su)
    out = goi(get_settings().load_prompt('system.txt'), user)
    du_phong = out is None

    if du_phong:                          # chế độ mock / dự phòng
        out = _mock_history(xe, phieu, dong, bao_hanh)

    meta = {
        **_lay_input(user, du_phong=du_phong),
        'vehicle_id': int(xe['id']),
        'plate': xe['plate'],
    }
    return AiResult(kind='history', repair_order_id=None,
                    input_json=json.dumps(meta, ensure_ascii=False),
                    output_text=out, is_valid=bool(out))


def _mock_history(xe, phieu, dong, bao_hanh=None):
    phu = []
    if xe.get('year'):
        phu.append('năm %s' % xe['year'])
    if xe.get('odometer') is not None:
        phu.append('ODO %s km' % _fmt_tien(xe['odometer']))
    them = (' (%s)' % ', '.join(phu)) if phu else ''

    thieu = []
    if not xe.get('year'):
        thieu.append('năm sản xuất')
    if xe.get('odometer') is None:
        thieu.append('số km ODO')
    chuoi_thieu = ', '.join(thieu) if thieu else 'Không có'

    if not phieu:
        return ('1. Thông tin xe: %s – %s %s%s\n'
                '2. Tổng quan: 0 lần sửa (xe chưa có lịch sử sửa chữa trong hệ thống)\n'
                '3. Các lần sửa chữa gần đây: (không có)\n'
                '4. Dữ liệu thiếu: %s'
                % (xe['plate'], xe['brand'], xe['model'], them, chuoi_thieu))

    bh_str = ''
    if bao_hanh:
        bh_str = '. Bảo hành còn hiệu lực: ' + ', '.join(
            '%s (đến %s)' % (b['ten'], b['end_date']) for b in bao_hanh if b.get('ten'))

    return ('1. Thông tin xe: %s – %s %s%s\n'
            '2. Tổng quan: %d lần sửa, lần sửa gần nhất %s%s\n'
            '3. Các lần sửa chữa gần đây:\n%s\n'
            '4. Dữ liệu thiếu: %s'
            % (xe['plate'], xe['brand'], xe['model'], them, len(phieu),
               phieu[0]['created_at'], bh_str, '\n'.join(dong), chuoi_thieu))


# ---------------------------------------------------------------------------
# AI02 – Giải thích dịch vụ
# ---------------------------------------------------------------------------
def giai_thich_dich_vu(service_id):
    from .core import db

    dv = db.fetch_one('SELECT * FROM services WHERE id = ?', (service_id,))
    if dv is None:
        raise KhongTimThay('Không tìm thấy dịch vụ số %s.' % service_id)

    gia_niemyet = _fmt_tien(dv['price'])
    mo_ta = (dv.get('description') or '').strip()
    user = get_settings().render_prompt(
        get_settings().load_prompt('explain.txt'),
        service='Tên dịch vụ: %s\nĐơn giá niêm yết: %s đồng\nMô tả trong danh mục: %s'
                % (dv['name'], gia_niemyet, mo_ta or '(danh mục chưa có mô tả)'))
    out = goi(get_settings().load_prompt('system.txt'), user)
    du_phong = out is None

    if not mo_ta:
        # Ca biên bắt buộc: dịch vụ trống mô tả phải trả thông báo chuẩn xác
        out = ('1. Dịch vụ là gì: Danh mục chưa có mô tả cho dịch vụ này\n'
               '2. Hạng mục đang ghi nhận: %s (đơn giá niêm yết: %s đồng)\n'
               '3. Khách cần lưu ý: Nhân viên cần bổ sung mô tả kỹ thuật trước khi tư vấn chi tiết.'
               % (dv['name'], gia_niemyet))
    elif du_phong:                        # chế độ mock / dự phòng
        out = ('1. Dịch vụ là gì: %s — giúp duy trì tình trạng vận hành ổn định và an toàn cho xe theo đúng tiêu chuẩn bảo dưỡng của xưởng.\n'
               '2. Hạng mục đang ghi nhận: %s — Đơn giá niêm yết: %s đồng.\n'
               '3. Khách cần lưu ý: Chi phí công dịch vụ dự kiến là %s đồng (chưa bao gồm phụ tùng thay thế phát sinh nếu có sau khi kỹ thuật viên kiểm tra thực tế).'
               % (mo_ta, dv['name'], gia_niemyet, gia_niemyet))

    meta = {
        **_lay_input(user, du_phong=du_phong),
        'service_id': int(dv['id']),
        'service_name': dv['name'],
    }
    return AiResult(kind='explain', repair_order_id=None,
                    input_json=json.dumps(meta, ensure_ascii=False),
                    output_text=out, is_valid=bool(out))


# ---------------------------------------------------------------------------
# AI03 – Báo giá nháp
# ---------------------------------------------------------------------------
def _goi_y_tu_danh_muc(ghi_chu: str, services: list[dict], parts: list[dict]) -> list[dict]:
    """Đối chiếu ghi chú tiếp nhận với danh mục dịch vụ & phụ tùng trong CSDL.

    Chỉ chọn các bản ghi có thật trong bảng `services` / `parts` với đúng đơn giá
    niêm yết của hệ thống, tuyệt đối không tự bịa hạng mục hay giá tiền.
    """
    text = (ghi_chu or '').lower()
    ket_qua: list[dict] = []
    da_chon_dv: set[int] = set()
    da_chon_pt: set[int] = set()

    tu_khoa_map = [
        (('dầu', 'nhớt', 'lọc gió', 'bảo dưỡng định kỳ'), ('dầu', 'lọc')),
        (('phanh', 'thắng', 'má phanh', 'kêu'), ('phanh', 'má phanh')),
        (('điều hòa', 'điều hoà', 'lạnh', 'mát', 'ga'), ('điều hòa', 'điều hoà', 'lọc gió')),
        (('điện', 'ắc quy', 'đề', 'máy phát', 'đèn', 'ánh sáng', 'pha'), ('điện', 'ắc quy', 'đèn', 'ánh sáng', 'máy phát')),
        (('lốp', 'vỏ', 'cân bằng', 'thước lái', 'gầm'), ('lốp', 'cân bằng', 'gầm')),
        (('động cơ', 'máy', 'rung', 'khói', 'bugi'), ('động cơ', 'bugi')),
    ]

    tu_tim: set[str] = set()
    for nhom_trieu_chung, nhom_danh_muc in tu_khoa_map:
        if any(tk in text for tk in nhom_trieu_chung):
            tu_tim.update(nhom_danh_muc)

    for s in services:
        ten_s = (s['name'] or '').lower()
        mota_s = (s.get('description') or '').lower()
        if (tu_tim and any(tk in ten_s or tk in mota_s for tk in tu_tim)) or (
            ten_s and ten_s in text
        ):
            if s['id'] not in da_chon_dv:
                da_chon_dv.add(s['id'])
                ket_qua.append({
                    'loai': 'dich_vu',
                    'ma': int(s['id']),
                    'name': s['name'],
                    'qty': 1,
                    'unit_price': int(s['price']),
                    'subtotal': int(s['price']),
                })

    for pt in parts:
        if int(pt.get('stock') or 0) <= 0:
            continue
        ten_p = (pt['name'] or '').lower()
        if (tu_tim and any(tk in ten_p for tk in tu_tim)) or (ten_p and ten_p in text):
            if pt['id'] not in da_chon_pt:
                da_chon_pt.add(pt['id'])
                ket_qua.append({
                    'loai': 'phu_tung',
                    'ma': int(pt['id']),
                    'name': pt['name'],
                    'qty': 1,
                    'unit_price': int(pt['price']),
                    'subtotal': int(pt['price']),
                })

    # Nếu ghi chú chung chung (vd: "Kiểm tra tổng quát lần đầu") chưa khớp từ khóa,
    # gợi ý dịch vụ bảo dưỡng/kiểm tra cơ bản đầu tiên trong danh mục đang hoạt động.
    if not ket_qua and services:
        s0 = services[0]
        ket_qua.append({
            'loai': 'dich_vu',
            'ma': int(s0['id']),
            'name': s0['name'],
            'qty': 1,
            'unit_price': int(s0['price']),
            'subtotal': int(s0['price']),
        })
    return ket_qua[:5]


def bao_gia_nhap(order_id):
    """Tạo bản nháp báo giá.

    Tổng tiền luôn do backend tính từ CSDL. Nếu AI trả về tổng khác, hệ thống bỏ
    qua giá trị của AI. Nếu AI thêm hạng mục không có trong phiếu/danh mục, hạng
    mục đó bị loại.
    """
    from .core import db

    phieu = db.fetch_one(
        'SELECT r.*, v.plate, v.brand, v.model'
        ' FROM repair_orders r JOIN vehicles v ON v.id = r.vehicle_id'
        ' WHERE r.id = ?', (order_id,))
    if phieu is None:
        raise KhongTimThay('Không tìm thấy phiếu sửa chữa số %s.' % order_id)

    items = db.fetch_all(
        'SELECT i.id, i.service_id, i.part_id, COALESCE(s.name, pt.name) AS ten,'
        '       i.qty, i.unit_price, i.unit_price * i.qty AS subtotal'
        ' FROM repair_order_items i'
        ' LEFT JOIN services s ON s.id = i.service_id'
        ' LEFT JOIN parts pt ON pt.id = i.part_id'
        ' WHERE i.repair_order_id = ?', (order_id,))

    backend_total = db.tong_phieu(order_id)

    # Nếu phiếu chưa có hạng mục trực tiếp nhưng đang có báo giá nháp/chờ duyệt
    # thì lấy danh sách hạng mục từ báo giá đó để tư vấn cho khách.
    if not items:
        bg = db.fetch_one(
            "SELECT id FROM quotations WHERE repair_order_id = ?"
            " AND status IN ('DRAFT', 'SENT', 'APPROVED') ORDER BY id DESC LIMIT 1",
            (order_id,))
        if bg:
            items = db.fetch_all(
                'SELECT i.id, i.service_id, i.part_id, COALESCE(s.name, pt.name) AS ten,'
                '       i.qty, i.unit_price, i.unit_price * i.qty AS subtotal'
                ' FROM quotation_items i'
                ' LEFT JOIN services s ON s.id = i.service_id'
                ' LEFT JOIN parts pt ON pt.id = i.part_id'
                ' WHERE i.quotation_id = ?', (bg['id'],))
            backend_total = sum(int(i['subtotal']) for i in items)

    ghi_chu_phieu = str(phieu.get('technical_notes') or '').strip()

    if not items:
        # Phiếu chưa được nhập hạng mục: tự động đối chiếu ghi chú tiếp nhận với
        # danh mục dịch vụ & phụ tùng trong CSDL để đề xuất báo giá nháp tham khảo.
        services = db.fetch_all(
            'SELECT id, name, price, description FROM services WHERE is_active = 1 ORDER BY id')
        parts = db.fetch_all(
            'SELECT id, name, price, stock, description FROM parts'
            ' WHERE is_active = 1 AND stock > 0 ORDER BY id')
        goi_y = _goi_y_tu_danh_muc(ghi_chu_phieu, services, parts)
        tong_goi_y = sum(int(g['subtotal']) for g in goi_y)

        dong_goi_y = '\n'.join(
            '- [%s] %s x%d: %s đồng'
            % ('Dịch vụ' if g['loai'] == 'dich_vu' else 'Phụ tùng',
               g['name'], g['qty'], _fmt_tien(g['subtotal']))
            for g in goi_y
        )
        ly_do = (
            'Ghi chú tiếp nhận trên phiếu: "%s".' % ghi_chu_phieu
            if ghi_chu_phieu
            else 'Phiếu chưa có ghi chú triệu chứng chi tiết, hệ thống đề xuất gói kiểm tra/bảo dưỡng cơ bản.'
        )

        # Nếu có kết nối LLM thật, nhờ LLM viết thêm câu tư vấn ngắn gọn dựa trên danh mục gợi ý
        user_ctx = (
            'Xe: %s %s %s\n%s\nHạng mục gợi ý từ danh mục xưởng:\n%s\nTổng dự kiến: %d'
            % (phieu['plate'], phieu['brand'], phieu['model'], ly_do, dong_goi_y, tong_goi_y)
        )
        user_prompt = get_settings().render_prompt(
            get_settings().load_prompt('quote.txt'),
            items=user_ctx,
            backend_total=tong_goi_y,
        )
        raw = goi(get_settings().load_prompt('system.txt'), user_prompt)
        du_phong = raw is None
        parsed = None if du_phong else _phan_tich_json(raw)
        ghi_chu_ai = ''
        if isinstance(parsed, dict) and isinstance(parsed.get('notes'), str):
            ghi_chu_ai = parsed['notes'].strip()[:300]

        out_lines = [
            'Phiếu sửa chữa số %d chưa có hạng mục nào được ghi nhận nên chưa thể lập báo giá nháp chính thức từ hạng mục đã chốt.' % order_id,
            '',
            'Đề xuất hạng mục tham khảo từ danh mục xưởng (Xe %s – %s %s):' % (
                phieu['plate'], phieu['brand'], phieu['model']),
            ly_do,
            dong_goi_y or '(Chưa có danh mục phù hợp)',
            'Tổng dự kiến theo đề xuất: %s đồng' % _fmt_tien(tong_goi_y),
        ]
        if ghi_chu_ai:
            out_lines.append('Ghi chú tham khảo (do AI sinh, cần nhân viên kiểm tra): %s' % ghi_chu_ai)
        out_lines.append('Báo giá nháp, cần nhân viên kiểm tra trước khi sử dụng.')

        return AiResult(
            kind='quote',
            repair_order_id=order_id,
            input_json=json.dumps({
                **_lay_input(user_prompt, du_phong=du_phong),
                'plate': phieu['plate'],
                'vehicle_id': int(phieu['vehicle_id']),
                'items': [],
                'backend_total': backend_total,
                'suggested_total': tong_goi_y,
                'suggested_items': goi_y,
            }, ensure_ascii=False),
            output_text='\n'.join(out_lines),
            is_valid=True,
        )

    suggested_from_items = [
        {
            'loai': 'dich_vu' if i.get('service_id') else 'phu_tung',
            'ma': int(i.get('service_id') or i.get('part_id')),
            'name': i['ten'],
            'qty': int(i['qty']),
            'unit_price': int(i['unit_price']),
            'subtotal': int(i['subtotal']),
        }
        for i in items
        if i.get('service_id') or i.get('part_id')
    ]

    danh_sach = '\n'.join('  - %s | số lượng: %d | đơn giá: %d | thành tiền: %d'
                          % (i['ten'], i['qty'], i['unit_price'], i['subtotal'])
                          for i in items)
    if ghi_chu_phieu:
        danh_sach = ('Thông tin xe: %s (%s %s) — Ghi chú kỹ thuật: %s\n'
                     % (phieu['plate'], phieu['brand'], phieu['model'], ghi_chu_phieu)) + danh_sach

    user = get_settings().render_prompt(get_settings().load_prompt('quote.txt'),
                                  items=danh_sach, backend_total=backend_total)
    raw = goi(get_settings().load_prompt('system.txt'), user)
    du_phong = raw is None

    if du_phong:                          # chế độ mock / dự phòng
        parsed = None
    else:
        parsed = _phan_tich_json(raw)

    if not isinstance(parsed, dict):
        # Không đọc được JSON dạng đối tượng: dựng bản nháp từ dữ liệu CSDL, tuyệt đối không đoán
        body_lines = '\n'.join('- %s x%d: %s đồng' % (i['ten'], i['qty'],
                                                      _fmt_tien(i['subtotal']))
                               for i in items)
        ghi_chu_mac_dinh = (
            'Ghi chú tham khảo: Các hạng mục trên được lập theo yêu cầu kiểm tra/sửa chữa của xe %s%s.'
            % (phieu['plate'], (' (%s)' % ghi_chu_phieu) if ghi_chu_phieu else '')
        )
        out = ('Bảng báo giá nháp cho phiếu sửa chữa số %d\n%s\nTổng dự kiến: %s đồng\n%s\n'
               'Báo giá nháp, cần nhân viên kiểm tra trước khi sử dụng.'
               % (order_id, body_lines, _fmt_tien(backend_total), ghi_chu_mac_dinh))
        return AiResult(kind='quote', repair_order_id=order_id,
                        input_json=json.dumps({**_lay_input(user, du_phong=du_phong),
                                               'plate': phieu['plate'],
                                               'vehicle_id': int(phieu['vehicle_id']),
                                               'items': len(items),
                                               'backend_total': backend_total,
                                               'suggested_items': suggested_from_items,
                                               'doc_ai_doc_duoc': False}, ensure_ascii=False),
                        output_text=out, is_valid=True)

    # Lọc lại: chỉ giữ hạng mục khớp với phiếu, tên, số lượng và đơn giá.
    # Mỗi dòng CSDL (theo i['id']) chỉ được khớp tối đa một lần để ngăn mô hình
    # lặp lại cùng một dòng hàng làm sai lệch bảng hiển thị so với backend_total.
    hop_le = []
    da_khop: set[int] = set()
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
            if (i['id'] not in da_khop and ten == i['ten']
                    and so_luong == i['qty'] and don_gia == i['unit_price']):
                da_khop.add(i['id'])
                hop_le.append({'name': i['ten'], 'qty': i['qty'],
                               'unit_price': i['unit_price'], 'subtotal': i['subtotal']})
                break

    # Nếu LLM viết tắt tên hạng mục làm bộ lọc khớp ít hơn thực tế, bổ sung các dòng
    # còn thiếu từ chính CSDL để bảng báo giá nháp luôn đầy đủ 100% hạng mục của phiếu.
    for i in items:
        if i['id'] not in da_khop:
            da_khop.add(i['id'])
            hop_le.append({'name': i['ten'], 'qty': i['qty'],
                           'unit_price': i['unit_price'], 'subtotal': i['subtotal']})

    thanh = '\n'.join('- %s x%d: %s đồng' % (i['name'], i['qty'],
                                              _fmt_tien(i['subtotal']))
                      for i in hop_le) or '(không có hạng mục nào khớp với phiếu)'
    tong_ai = _so_nguyen(parsed.get('total'))
    canh_bao = ('Tổng do AI trả về (%s) khác tổng của hệ thống, hệ thống dùng %s đồng.'
                % (tong_ai, _fmt_tien(backend_total))
                if tong_ai is not None and tong_ai != backend_total else '')

    ghi_chu = parsed.get('notes')
    ghi_chu = str(ghi_chu).strip()[:300] if isinstance(ghi_chu, str) else ''
    if ghi_chu:
        ghi_chu = 'Ghi chú tham khảo (do AI sinh, cần nhân viên kiểm tra): %s' % ghi_chu
    out = ('Bảng báo giá nháp cho phiếu sửa chữa số %d\n%s\nTổng dự kiến: %s đồng\n%s\n%s\n'
           'Báo giá nháp, cần nhân viên kiểm tra trước khi sử dụng.'
           % (order_id, thanh, _fmt_tien(backend_total),
              canh_bao, ghi_chu))
    return AiResult(kind='quote', repair_order_id=order_id,
                    input_json=json.dumps({**_lay_input(user, du_phong=False),
                                           'plate': phieu['plate'],
                                           'vehicle_id': int(phieu['vehicle_id']),
                                           'items': len(items),
                                           'backend_total': backend_total,
                                           'suggested_items': suggested_from_items,
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
