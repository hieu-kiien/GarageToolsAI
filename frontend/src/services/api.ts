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
  ChiTietPhieu,
  Dashboard,
  HoaDonChiTietPhan,
  HoaDonDong,
  KhoPhanTrang,
  KetQuaAI,
  KetQuaGanNhat,
  Lookups,
  Meta,
  PhanTrang,
  Phien,
  PhieuDong,
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
      dayDu(path) + hangSo(method === "GET" ? (body as Record<string, unknown>) : undefined),
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
  orders: (p: ThamSoDanhSach & { trang_thai?: string | undefined } = {}) =>
    goi<PhanTrang<PhieuDong>>("GET", "/orders", p),
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

  // --- hoá đơn & thu tiền ---
  invoices: (p: ThamSoDanhSach & { trang_thai?: string | undefined } = {}) =>
    goi<PhanTrang<HoaDonDong>>("GET", "/invoices", p),
  invoice: (id: number) => goi<HoaDonChiTietPhan>("GET", `/invoices/${id}`),
  thuTien: (id: number, body: { amount: number; method: string }) =>
    goi<{ thong_bao: string }>("POST", `/invoices/${id}/payments`, body),

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
};
