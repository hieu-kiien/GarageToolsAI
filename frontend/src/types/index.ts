// Kiểu dữ liệu khớp chính xác JSON mà backend FastAPI trả về (app/routes/api/*).
// Tiền là số nguyên VND; ngày giờ là chuỗi ISO 8601 / SQLite UTC.

export type Role = "MANAGER" | "RECEPTIONIST" | "TECHNICIAN" | "CASHIER";

/** Trạng thái phiếu sửa chữa — enum thật của backend (`security_matrix`). */
export type RepairStatus =
  "RECEIVED" | "INSPECTING" | "ESTIMATING" | "REPAIRING" | "COMPLETED" | "CANCELLED";

export type InvoiceStatus = "UNPAID" | "PARTIAL" | "PAID";
export type ReviewStatus = "PENDING" | "APPROVED" | "REJECTED";
export type PayMethod = "CASH" | "CARD" | "TRANSFER" | "ZALO";
export type FuelLevel = "EMPTY" | "QUARTER" | "HALF" | "THREE_QUARTER" | "FULL" | "UNKNOWN";
export type AiKind = "history" | "explain" | "quote";
export type StockReason = "RECEIPT" | "USAGE" | "RETURN" | "ADJUSTMENT";

/** Người dùng đã đăng nhập — `GET /api/auth/session`. */
export interface ThanhVien {
  id: number;
  username: string;
  full_name: string;
  email: string | null;
  role: Role;
  ten_vai_tro: string;
  is_active: boolean;
}

/** `GET /api/auth/session` — user=null khi chưa đăng nhập. */
export interface Phien {
  user: ThanhVien | null;
  quyen: Record<string, boolean>;
}

/** Bao phân trang thống nhất của mọi danh sách backend. */
export interface PhanTrang<T> {
  dong: T[];
  tong: number;
  trang: number;
  moi_trang: number;
  tong_trang: number;
}

// --- Tổng quan ------------------------------------------------------------
export interface Kpi {
  tong_phieu: number;
  dang_xu_ly: number;
  lich_hen: number;
  da_thu: number;
  chua_thu: number;
  khach_hang: number;
  xe: number;
  cho_duyet_ai: number;
}

export interface PhieuGanNhat {
  id: number;
  status: RepairStatus;
  created_at: string;
  technical_notes: string | null;
  plate: string;
}

export interface DoanhThuTheoThang {
  thang: string;
  so_hoa_don: number;
  tong: number;
  da_thu: number;
}

export interface Dashboard {
  kpi: Kpi;
  trang_thai: { status: RepairStatus; n: number }[];
  gan_nhat: PhieuGanNhat[];
  doanh_thu: DoanhThuTheoThang[];
}

// --- Phiếu sửa chữa --------------------------------------------------------
/** Dòng danh sách `GET /api/orders`. */
export interface PhieuDong {
  id: number;
  plate: string;
  brand: string;
  model: string;
  status: RepairStatus;
  created_at: string;
  technical_notes: string | null;
  ky_thuat_vien: string | null;
}

/** `phieu` trong `GET /api/orders/{id}` — `r.*` cộng các cột JOIN. */
export interface Phieu {
  id: number;
  vehicle_id: number;
  technician_id: number | null;
  status: RepairStatus;
  technical_notes: string | null;
  created_at: string;
  plate: string;
  brand: string;
  model: string;
  year: number | null;
  customer_id: number;
  khach: string;
  khach_phone: string | null;
  ky_thuat_vien: string | null;
  tong: number;
  ten_trang_thai: string;
}

export interface HangMuc {
  id: number;
  service_id: number | null;
  part_id: number | null;
  qty: number;
  unit_price: number;
  ten: string;
  thanh_tien: number;
}

export interface NhatKy {
  id: number;
  note: string;
  created_at: string;
  full_name: string | null;
}

export interface HoaDon {
  id: number;
  repair_order_id: number;
  total: number;
  paid: number;
  status: InvoiceStatus;
  created_at: string;
}

export interface TienIchTiepNhan {
  id: number;
  repair_order_id: number;
  odometer_at_intake: number | null;
  fuel_level: FuelLevel;
  exterior_condition: string | null;
  accessories: string | null;
  notes: string | null;
  created_at: string;
  nguoi_tiep_nhan: string | null;
}

/** Trả về đủ năm khoá trong `orders.chi_tiet`. */
export interface ChiTietPhieu {
  phieu: Phieu;
  hang_muc: HangMuc[];
  nhat_ky: NhatKy[];
  hoa_don: HoaDon | null;
  tiep_nhan: TienIchTiepNhan | null;
}

// --- Hoá đơn ---------------------------------------------------------------
/** Dòng danh sách `GET /api/invoices`. */
export interface HoaDonDong {
  id: number;
  repair_order_id: number;
  plate: string;
  khach: string;
  total: number;
  paid: number;
  status: InvoiceStatus;
  created_at: string;
}

/** `hoa_don` trong `GET /api/invoices/{id}` — `i.*` cộng các cột JOIN. */
export interface HoaDonChiTiet extends HoaDon {
  vehicle_id: number;
  plate: string;
  khach: string;
  ten_trang_thai: string;
  da_thu: number;
  con_phai_thu: number;
}

export interface KhoanThu {
  id: number;
  amount: number;
  method: PayMethod;
  paid_at: string;
}

export interface HoaDonChiTietPhan {
  hoa_don: HoaDonChiTiet;
  khoan_thu: KhoanThu[];
}

// --- Kho -------------------------------------------------------------------
export interface GiaoDichKho {
  id: number;
  part_id: number;
  ten_phu_tung: string;
  qty: number;
  reason: StockReason;
  repair_order_id: number | null;
  note: string | null;
  nguoi_tao: string | null;
  created_at: string;
}

export interface CanhBaoKho {
  id: number;
  name: string;
  sku: string;
  stock: number;
  min_stock: number;
}

export interface LechSoKho {
  part_id: number;
  name: string;
  stock: number;
  tong_sach: number;
  lech: number;
}

export interface KhoPhanTrang extends PhanTrang<GiaoDichKho> {
  lech: LechSoKho[];
  canh_bao: CanhBaoKho[];
  ly_do: Record<string, string>;
}

// --- AI --------------------------------------------------------------------
/** Dòng `GET /api/ai/results` (hàng chờ duyệt). */
export interface KetQuaAI {
  id: number;
  kind: AiKind;
  repair_order_id: number | null;
  output_text: string;
  is_valid: number;
  review_status: ReviewStatus;
  reviewed_by: number | null;
  reviewed_at: string | null;
  created_at: string;
  plate: string | null;
  nguoi_duyet: string | null;
}

/** Dòng `GET /api/ai/recent`. */
export interface KetQuaGanNhat {
  id: number;
  kind: AiKind;
  output_text: string;
  review_status: ReviewStatus;
  is_valid: number;
  created_at: string;
  plate: string | null;
}

// --- Tra cứu & từ điển ------------------------------------------------------
export interface Lookups {
  khach_hang: { id: number; name: string }[];
  xe: { id: number; plate: string; brand: string; model: string }[];
  dich_vu: { id: number; name: string; price: number }[];
  phu_tung: { id: number; name: string; price: number; stock: number }[];
  ky_thuat_vien: { id: number; full_name: string }[];
  phieu: { id: number; plate: string }[];
  vai_tro: Record<Role, string>;
  trang_thai: Record<string, string>;
  chuyen_trang_thai: Record<RepairStatus, RepairStatus[]>;
  hinh_thuc: Record<PayMethod, string>;
  ly_do_kho: Record<string, string>;
}

/** `GET /api/meta` — nhãn + luật chuyển trạng thái, không hard-code bản sao. */
export interface Meta {
  user: { id: number; role: Role };
  vai_tro: Record<Role, string>;
  quyen: Record<string, Role[]>;
  trang_thai: Record<string, string>;
  trang_thai_phieu: RepairStatus[];
  chuyen_trang_thai: Record<RepairStatus, RepairStatus[]>;
  hinh_thuc_thanh_toan: Record<PayMethod, string>;
  trang_thai_bao_gia: string[];
  trang_thai_bao_hanh: Record<string, string>;
  muc_nhien_lieu: Record<FuelLevel, string>;
  ly_do_kho: Record<string, string>;
  kinh_ai: Record<AiKind, string>;
  ai_provider: string;
}
