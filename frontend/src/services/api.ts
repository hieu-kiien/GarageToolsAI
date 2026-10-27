/**
 * Khách API duy nhất — gọi thẳng FastAPI backend cùng gốc `/api/...`.
 *
 * - Lỗi luôn về dạng `{ loi, thong_diep, truong? }` → gói thành {@link ApiError}.
 * - CSRF: đọc cookie không-HttpOnly `garage_csrf` (backend gắn sẵn cho mọi
 *   phản hồi `/api/*`) rồi gửi kèm header `X-CSRF-Token` cho mọi POST/PUT/DELETE.
 * - Danh sách luôn có bao `{ dong, tong, trang, moi_trang, tong_trang }`.
 * - Không tính tổng tiền nào ở đây — tổng do backend tính.
 */
import { queryOptions } from "@tanstack/react-query";
import type {
  BaoCao,
  BaoGiaDong,
  BaoHanhDong,
  ChiTietBaoGia,
  ChiTietPhieu,
  Dashboard,
  DichVuDong,
  HoaDonChiTietPhan,
  HoaDonDong,
  KhoPhanTrang,
  KetQuaAI,
  KetQuaGanNhat,
  KhachHangDong,
  LichHenDong,
  LichSuDong,
  Lookups,
  Meta,
  NguoiDungDong,
  PhanTrang,
  PhieuDong,
  Phien,
  PhuTungDong,
  PhuongTienDong,
} from "@/types";

/** Mã sự kiện báo "phiên hết hạn" để `RoleProvider` tải lại session. */
export const SU_KIEN_HET_PHIEN = "gt:het-phien";

export class ApiError extends Error {
  readonly status: number;
  readonly ma: string;
  readonly truong: Record<string, string[]> | string | undefined;
  constructor(
    status: number,
    ma: string,
    message: string,
    truong?: Record<string, string[]> | string,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.ma = ma;
    this.truong = truong;
  }
}

function layCsrf(): string {
  if (typeof document === "undefined") return "";
  const m = document.cookie.match(/(?:^|;\s*)garage_csrf=([^;]*)/);
  return m ? decodeURIComponent(m[1] ?? "") : "";
}

function dayDu(path: string): string {
  return path.startsWith("/api") ? path : `/api${path}`;
}

function hangSo(params: Record<string, unknown> | undefined): string {
  if (!params) return "";
  const sp = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") sp.set(k, String(v));
  });
  const s = sp.toString();
  return s ? `?${s}` : "";
}

/** Gọi một endpoint JSON backend. Ném {@link ApiError} cho mọi phản hồi lỗi. */
export async function goi<T>(method: string, path: string, body?: unknown): Promise<T> {
  const doCung = method.toUpperCase();
  let res: Response;
  try {
    res = await fetch(
      dayDu(path) + hangSo(doCung === "GET" ? (body as Record<string, unknown>) : undefined),
      {
        method: doCung,
        credentials: "same-origin",
        headers: {
          Accept: "application/json",
          ...(body !== undefined && doCung !== "GET" ? { "Content-Type": "application/json" } : {}),
          ...(doCung === "GET" || doCung === "HEAD" ? {} : { "X-CSRF-Token": layCsrf() }),
        },
        body: body !== undefined && doCung !== "GET" ? JSON.stringify(body) : null,
      },
    );
  } catch {
    throw new ApiError(
      0,
      "khong_ket_noi",
      "Không kết nối được máy chủ. Kiểm tra backend đã chạy chưa.",
    );
  }

  let data: unknown = null;
  const text = await res.text();
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = null;
    }
  }

  if (!res.ok) {
    const e = data as {
      loi?: string;
      thong_diep?: string;
      truong?: Record<string, string[]> | string;
    } | null;
    if (res.status === 401) window.dispatchEvent(new CustomEvent(SU_KIEN_HET_PHIEN));
    throw new ApiError(
      res.status,
      e?.loi ?? `loi_${res.status}`,
      e?.thong_diep ?? `Máy chủ trả về lỗi ${res.status}.`,
      e?.truong,
    );
  }
  return data as T;
}

type ThamSoDanhSach = {
  trang?: number | undefined;
  moi_trang?: number | undefined;
  q?: string | undefined;
};

export const api = {
  // --- phiên & từ điển ---
  session: () => goi<Phien>("GET", "/auth/session"),
  dangNhap: (body: { username: string; password: string }) =>
    goi<Phien & { thong_bao: string }>("POST", "/auth/login", body),
  dangXuat: () => goi<{ thong_bao: string }>("POST", "/auth/logout"),
  meta: () => goi<Meta>("GET", "/meta"),
  lookups: () => goi<Lookups>("GET", "/lookups"),

  // --- tổng quan ---
  dashboard: () => goi<Dashboard>("GET", "/dashboard"),

  // --- phiếu sửa chữa ---
  orders: (
    p: ThamSoDanhSach & {
      trang_thai?: string | undefined;
      ktv?: string | undefined;
      ngay?: string | undefined;
    } = {},
  ) => goi<PhanTrang<PhieuDong>>("GET", "/orders", p),
  order: (id: number) => goi<ChiTietPhieu>("GET", `/orders/${id}`),
  taoPhieu: (body: {
    vehicle_id: number;
    technician_id?: number | null | undefined;
    technical_notes?: string | undefined;
  }) => goi<{ thong_bao: string; id: number }>("POST", "/orders", body),
  doiTrangThai: (id: number, status: string) =>
    goi<{ thong_bao: string; phieu: unknown }>("POST", `/orders/${id}/status`, { status }),
  phanCong: (id: number, technician_id: number | null) =>
    goi<{ thong_bao: string }>("POST", `/orders/${id}/assign`, { technician_id }),
  capNhatGhiChuPhieu: (id: number, technical_notes: string | null) =>
    goi<{ thong_bao: string; phieu: unknown }>("POST", `/orders/${id}/notes`, {
      technical_notes,
    }),
  themHangMuc: (id: number, body: { loai: "dich_vu" | "phu_tung"; ma: number; qty: number }) =>
    goi<{ thong_bao: string }>("POST", `/orders/${id}/items`, body),
  goHangMuc: (id: number, iid: number) =>
    goi<{ thong_bao: string }>("POST", `/orders/${id}/items/${iid}/remove`),
  themNhatKy: (id: number, note: string) =>
    goi<{ thong_bao: string }>("POST", `/orders/${id}/logs`, { note }),
  ghiTiepNhan: (
    id: number,
    body: {
      odometer_at_intake?: number | null | undefined;
      fuel_level?: string | undefined;
      exterior_condition?: string | undefined;
      accessories?: string | undefined;
      notes?: string | undefined;
    },
  ) => goi<{ thong_bao: string }>("POST", `/orders/${id}/intake`, body),
  lapHoaDon: (id: number) =>
    goi<{ thong_bao: string; id: number }>("POST", `/orders/${id}/invoice`),
  nghiemThu: (id: number, acceptance_note?: string) =>
    goi<{ thong_bao: string; phieu: unknown }>("POST", `/orders/${id}/accept`, {
      acceptance_note,
    }),
  xoaPhieu: (id: number) => goi<{ thong_bao: string; id: number }>("DELETE", `/orders/${id}`),

  // --- khách hàng / xe / lịch hẹn ---
  customers: (p: ThamSoDanhSach = {}) => goi<PhanTrang<KhachHangDong>>("GET", "/customers", p),
  taoKhach: (body: {
    name: string;
    phone: string;
    email?: string | null | undefined;
    address?: string | null | undefined;
  }) => goi<{ thong_bao: string; id: number }>("POST", "/customers", body),
  suaKhach: (
    id: number,
    body: {
      name: string;
      phone: string;
      email?: string | null | undefined;
      address?: string | null | undefined;
    },
  ) => goi<{ thong_bao: string; id: number }>("PUT", `/customers/${id}`, body),
  xoaKhach: (id: number) => goi<{ thong_bao: string; id: number }>("DELETE", `/customers/${id}`),

  vehicles: (p: ThamSoDanhSach & { khach?: number | undefined } = {}) =>
    goi<PhanTrang<PhuongTienDong>>("GET", "/vehicles", p),
  taoXe: (body: {
    plate: string;
    brand: string;
    model: string;
    customer_id: number;
    year?: number | null | undefined;
    vin?: string | null | undefined;
    color?: string | null | undefined;
    odometer?: number | null | undefined;
    is_active?: boolean | undefined;
  }) => goi<{ thong_bao: string; id: number }>("POST", "/vehicles", body),
  suaXe: (
    id: number,
    body: {
      plate: string;
      brand: string;
      model: string;
      customer_id: number;
      year?: number | null | undefined;
      vin?: string | null | undefined;
      color?: string | null | undefined;
      odometer?: number | null | undefined;
      is_active?: boolean | undefined;
    },
  ) => goi<{ thong_bao: string; id: number }>("PUT", `/vehicles/${id}`, body),
  xoaXe: (id: number) => goi<{ thong_bao: string; id: number }>("DELETE", `/vehicles/${id}`),

  appointments: (p: ThamSoDanhSach & { trang_thai?: string | undefined } = {}) =>
    goi<PhanTrang<LichHenDong>>("GET", "/appointments", p),
  taoLich: (body: {
    customer_id: number;
    vehicle_id: number;
    scheduled_at: string;
    notes?: string | null | undefined;
    status?: string | undefined;
  }) => goi<{ thong_bao: string; id: number }>("POST", "/appointments", body),
  suaLich: (
    id: number,
    body: {
      customer_id: number;
      vehicle_id: number;
      scheduled_at: string;
      notes?: string | null | undefined;
      status?: string | undefined;
    },
  ) => goi<{ thong_bao: string; id: number }>("PUT", `/appointments/${id}`, body),
  xoaLich: (id: number) => goi<{ thong_bao: string; id: number }>("DELETE", `/appointments/${id}`),

  // --- báo giá ---
  quotations: (p: ThamSoDanhSach & { trang_thai?: string | undefined } = {}) =>
    goi<PhanTrang<BaoGiaDong>>("GET", "/quotations", p),
  quotation: (id: number) => goi<ChiTietBaoGia>("GET", `/quotations/${id}`),
  taoBaoGia: (body: {
    repair_order_id: number;
    note?: string | null | undefined;
    valid_until?: string | null | undefined;
  }) => goi<{ thong_bao: string; id: number }>("POST", "/quotations", body),
  themDongBaoGia: (id: number, body: { loai: "dich_vu" | "phu_tung"; ma: number; qty: number }) =>
    goi<{ thong_bao: string }>("POST", `/quotations/${id}/items`, body),
  goDongBaoGia: (id: number, iid: number) =>
    goi<{ thong_bao: string }>("POST", `/quotations/${id}/items/${iid}/remove`),
  guiBaoGia: (id: number) => goi<{ thong_bao: string }>("POST", `/quotations/${id}/send`),
  duyetBaoGia: (id: number, quyet_dinh: "APPROVED" | "REJECTED") =>
    goi<{ thong_bao: string }>("POST", `/quotations/${id}/review`, { quyet_dinh }),
  huyBaoGia: (id: number) => goi<{ thong_bao: string }>("POST", `/quotations/${id}/cancel`),
  apDungBaoGia: (id: number) =>
    goi<{ thong_bao: string; phieu_id: number }>("POST", `/quotations/${id}/apply`),

  // --- bảo hành ---
  warranties: (p: ThamSoDanhSach & { trang_thai?: string | undefined } = {}) =>
    goi<PhanTrang<BaoHanhDong>>("GET", "/warranties", p),
  taoBaoHanh: (body: {
    repair_order_id: number;
    months: number;
    service_id?: number | null | undefined;
    part_id?: number | null | undefined;
    note?: string | null | undefined;
    start_date: string;
  }) => goi<{ thong_bao: string; id: number }>("POST", "/warranties", body),
  hangMucBaoHanh: (repairOrderId: number) =>
    goi<{
      dong: {
        item_id: number;
        service_id: number | null;
        part_id: number | null;
        ten_hang_muc: string;
      }[];
    }>("GET", `/warranties/eligible`, { repair_order_id: repairOrderId }),
  huyBaoHanh: (id: number, body: { note?: string | undefined } = {}) =>
    goi<{ thong_bao: string }>("POST", `/warranties/${id}/cancel`, body),

  // --- danh mục dịch vụ / phụ tùng ---
  services: (p: ThamSoDanhSach & { dang_dung?: string | undefined } = {}) =>
    goi<PhanTrang<DichVuDong>>("GET", "/services", p),
  luuDichVu: (body: {
    id?: number | null | undefined;
    name: string;
    price: number | string;
    description?: string | null | undefined;
    is_active?: boolean | undefined;
  }) =>
    body.id
      ? goi<{ thong_bao: string; id: number }>("PUT", `/services/${body.id}`, body)
      : goi<{ thong_bao: string; id: number }>("POST", "/services", body),
  xoaDichVu: (id: number) => goi<{ thong_bao: string; id: number }>("DELETE", `/services/${id}`),
  parts: (
    p: ThamSoDanhSach & {
      dang_dung?: string | undefined;
      het_kho?: string | undefined;
    } = {},
  ) => goi<PhanTrang<PhuTungDong>>("GET", "/parts", p),
  luuPhuTung: (body: {
    id?: number | null | undefined;
    name: string;
    sku?: string | null | undefined;
    price: number | string;
    stock: number | string;
    min_stock?: number | string | undefined;
    description?: string | null | undefined;
    is_active?: boolean | undefined;
  }) =>
    body.id
      ? goi<{ thong_bao: string; id: number }>("PUT", `/parts/${body.id}`, body)
      : goi<{ thong_bao: string; id: number }>("POST", "/parts", body),
  xoaPhuTung: (id: number) => goi<{ thong_bao: string; id: number }>("DELETE", `/parts/${id}`),

  // --- tài khoản ---
  users: (
    p: ThamSoDanhSach & {
      vai_tro?: string | undefined;
      dang_hoat_dong?: string | undefined;
    } = {},
  ) => goi<PhanTrang<NguoiDungDong> & { vai_tro: Record<string, string> }>("GET", "/users", p),
  luuNguoiDung: (body: {
    id?: number | null | undefined;
    username: string;
    full_name: string;
    email?: string | null | undefined;
    role: string;
    is_active?: boolean | undefined;
    password?: string | undefined;
  }) => goi<{ thong_bao: string; id: number }>("POST", "/users", body),
  batTatNguoiDung: (id: number) =>
    goi<{ thong_bao: string; id: number; is_active: boolean }>("POST", `/users/${id}/toggle`),
  doiMatKhau: (body: { mat_khau_cu: string; mat_khau_moi: string }) =>
    goi<{ thong_bao: string }>("POST", "/auth/password", body),

  // --- báo cáo / lịch sử ---
  baoCao: (kind: string) => goi<BaoCao>("GET", `/reports/${kind}`),
  lichSu: (p: ThamSoDanhSach = {}) => goi<PhanTrang<LichSuDong>>("GET", "/history", p),

  // --- hoá đơn: huỷ khoản thu (thu ngân ghi nhầm) ---
  huyKhoanThu: (iid: number, khoanId: number) =>
    goi<HoaDonChiTietPhan & { thong_bao: string }>(
      "POST",
      `/invoices/${iid}/payments/${khoanId}/cancel`,
    ),

  // --- hoá đơn & thu tiền ---
  invoices: (p: ThamSoDanhSach & { trang_thai?: string | undefined } = {}) =>
    goi<PhanTrang<HoaDonDong>>("GET", "/invoices", p),
  invoice: (id: number) => goi<HoaDonChiTietPhan>("GET", `/invoices/${id}`),
  thuTien: (id: number, body: { amount: number; method: string }) =>
    goi<HoaDonChiTietPhan & { thong_bao: string }>("POST", `/invoices/${id}/payments`, body),

  // --- kho ---
  stock: (p: ThamSoDanhSach & { part_id?: number | undefined; reason?: string | undefined } = {}) =>
    goi<KhoPhanTrang>("GET", "/stock", p),
  stockWarnings: () => goi<{ canh_bao: KhoPhanTrang["canh_bao"] }>("GET", "/stock/warnings"),
  nhapKho: (body: { part_id: number; qty: number; note?: string | undefined }) =>
    goi<{ thong_bao: string; ton_kho: number }>("POST", "/stock/receipt", body),
  dieuChinhKho: (body: { part_id: number; moi: number; note?: string | undefined }) =>
    goi<{ thong_bao: string; ton_kho: number }>("POST", "/stock/adjust", body),

  // --- AI ---
  aiRun: (body: {
    kind: "history" | "explain" | "quote";
    vehicle_id?: number | undefined;
    service_id?: number | undefined;
    repair_order_id?: number | undefined;
  }) => goi<{ thong_bao: string; id: number }>("POST", "/ai/run", body),
  aiResults: (p: ThamSoDanhSach & { trang_thai?: string | undefined } = {}) =>
    goi<PhanTrang<KetQuaAI> & { ten_kinh: Record<string, string> }>("GET", "/ai/results", p),
  aiRecent: () =>
    goi<{ dong: KetQuaGanNhat[]; ten_kinh: Record<string, string>; provider: string }>(
      "GET",
      "/ai/recent",
    ),
  aiReview: (id: number, quyet_dinh: "APPROVED" | "REJECTED") =>
    goi<{ thong_bao: string }>("POST", `/ai/results/${id}/review`, { quyet_dinh }),
};

export const q = {
  session: () => queryOptions({ queryKey: ["session"], queryFn: api.session, retry: false }),
  meta: () =>
    queryOptions({ queryKey: ["meta"], queryFn: api.meta, staleTime: 5 * 60_000, retry: false }),
  lookups: () =>
    queryOptions({ queryKey: ["lookups"], queryFn: api.lookups, staleTime: 5 * 60_000 }),
  dashboard: () => queryOptions({ queryKey: ["dashboard"], queryFn: api.dashboard }),
  orders: (p: Parameters<typeof api.orders>[0] = {}) =>
    queryOptions({ queryKey: ["orders", p], queryFn: () => api.orders(p) }),
  order: (id: number) => queryOptions({ queryKey: ["orders", id], queryFn: () => api.order(id) }),
  invoices: (p: Parameters<typeof api.invoices>[0] = {}) =>
    queryOptions({ queryKey: ["invoices", p], queryFn: () => api.invoices(p) }),
  invoice: (id: number) =>
    queryOptions({ queryKey: ["invoices", id], queryFn: () => api.invoice(id) }),
  stock: (p: Parameters<typeof api.stock>[0] = {}) =>
    queryOptions({ queryKey: ["stock", p], queryFn: () => api.stock(p) }),
  stockWarnings: () =>
    queryOptions({ queryKey: ["stock", "warnings"], queryFn: api.stockWarnings }),
  aiResults: (p: Parameters<typeof api.aiResults>[0] = {}) =>
    queryOptions({ queryKey: ["ai-results", p], queryFn: () => api.aiResults(p) }),
  aiRecent: () => queryOptions({ queryKey: ["ai-recent"], queryFn: api.aiRecent }),
  customers: (p: Parameters<typeof api.customers>[0] = {}) =>
    queryOptions({ queryKey: ["customers", p], queryFn: () => api.customers(p) }),
  vehicles: (p: Parameters<typeof api.vehicles>[0] = {}) =>
    queryOptions({ queryKey: ["vehicles", p], queryFn: () => api.vehicles(p) }),
  appointments: (p: Parameters<typeof api.appointments>[0] = {}) =>
    queryOptions({ queryKey: ["appointments", p], queryFn: () => api.appointments(p) }),
  quotations: (p: Parameters<typeof api.quotations>[0] = {}) =>
    queryOptions({ queryKey: ["quotations", p], queryFn: () => api.quotations(p) }),
  quotation: (id: number) =>
    queryOptions({ queryKey: ["quotations", id], queryFn: () => api.quotation(id) }),
  warranties: (p: Parameters<typeof api.warranties>[0] = {}) =>
    queryOptions({ queryKey: ["warranties", p], queryFn: () => api.warranties(p) }),
  services: (p: Parameters<typeof api.services>[0] = {}) =>
    queryOptions({ queryKey: ["services", p], queryFn: () => api.services(p) }),
  parts: (p: Parameters<typeof api.parts>[0] = {}) =>
    queryOptions({ queryKey: ["parts", p], queryFn: () => api.parts(p) }),
  users: (p: Parameters<typeof api.users>[0] = {}) =>
    queryOptions({ queryKey: ["users", p], queryFn: () => api.users(p) }),
  lichSu: (p: Parameters<typeof api.lichSu>[0] = {}) =>
    queryOptions({ queryKey: ["history", p], queryFn: () => api.lichSu(p) }),
  baoCao: (kind: string) =>
    queryOptions({ queryKey: ["reports", kind], queryFn: () => api.baoCao(kind) }),
};
