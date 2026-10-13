import { createContext, useContext, useEffect, useMemo, type ReactNode } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api, q, SU_KIEN_HET_PHIEN } from "@/services/api";
import type { Meta, Phien, ThanhVien } from "@/types";

export type Area = "dashboard" | "board" | "orders" | "inspection" | "ai" | "inventory" | "finance";

/**
 * Mỗi màn hình ánh xạ tới quyền backend — không tự suy đoán theo vai trò.
 * `can(area)` đúng = người này được mở màn hình (server vẫn kiểm lại lần nữa).
 * Lưu ý: xem và thao tác tách quyền riêng (vd: thấy bảng `order.view`,
 * kéo trạng thái `order.progress`) nên nút thao tác check quyền lẻ phía trong.
 */
const AREA_QUYEN: Record<Area, string[]> = {
  dashboard: ["dashboard.view"],
  board: ["order.view"],
  orders: ["order.view"],
  inspection: ["order.create"],
  ai: ["ai.history", "ai.explain", "ai.quote", "ai.review"],
  inventory: ["stock.manage"],
  finance: ["report.view"],
};

type Ctx = {
  trangThaiPhien: "dang_tai" | "da_dang_nhap" | "chua_dang_nhap";
  user: ThanhVien | null;
  quyen: Record<string, boolean>;
  meta: Meta | undefined;
  can: (tenQuyen: string) => boolean;
  area: (a: Area) => boolean;
  dangNhap: (username: string, password: string) => Promise<string>;
  dangXuat: () => Promise<void>;
};

const RoleCtx = createContext<Ctx | null>(null);

export function RoleProvider({ children }: { children: ReactNode }) {
  const qc = useQueryClient();
  const phien = useQuery(q.session());
  const user = phien.data?.user ?? null;
  const meta = useQuery({ ...q.meta(), enabled: !!user });

  // Backend trả 401 khi phiên hết hạn → tải lại session để quay về màn đăng nhập.
  useEffect(() => {
    const het = () => qc.invalidateQueries({ queryKey: ["session"] });
    window.addEventListener(SU_KIEN_HET_PHIEN, het);
    return () => window.removeEventListener(SU_KIEN_HET_PHIEN, het);
  }, [qc]);

  const value = useMemo<Ctx>(() => {
    const quyen = phien.data?.quyen ?? {};
    return {
      trangThaiPhien: phien.isPending ? "dang_tai" : user ? "da_dang_nhap" : "chua_dang_nhap",
      user,
      quyen,
      meta: meta.data,
      can: (tenQuyen) => quyen[tenQuyen] === true,
      area: (a) => AREA_QUYEN[a].some((k) => quyen[k] === true),
      dangNhap: async (username, password) => {
        const kq = await api.dangNhap({ username, password });
        await qc.invalidateQueries();
        return kq.thong_bao ?? "Đăng nhập thành công.";
      },
      dangXuat: async () => {
        try {
          await api.dangXuat();
        } finally {
          await qc.invalidateQueries();
        }
      },
    };
  }, [phien.data, phien.isPending, user, meta.data, qc]);

  return <RoleCtx.Provider value={value}>{children}</RoleCtx.Provider>;
}

export function useRole() {
  const c = useContext(RoleCtx);
  if (!c) throw new Error("useRole phải nằm trong RoleProvider");
  return c;
}

/**
 * Nhãn tiếng Việt lấy từ `GET /api/meta` — backend là nguồn duy nhất,
 * giao diện không giữ bản sao cứng (sửa một chỗ là cả hai phía đổi theo).
 */
export function useNhan() {
  const { meta } = useRole();
  return useMemo(
    () => ({
      trangThai: (k: string) => meta?.trang_thai?.[k] ?? k,
      vaiTro: (r: string) => meta?.vai_tro?.[r as keyof typeof meta.vai_tro] ?? r,
      hinhThuc: (m: string) =>
        meta?.hinh_thuc_thanh_toan?.[m as keyof typeof meta.hinh_thuc_thanh_toan] ?? m,
      nhienLieu: (f: string) => meta?.muc_nhien_lieu?.[f as keyof typeof meta.muc_nhien_lieu] ?? f,
      lyDoKho: (r: string) => meta?.ly_do_kho?.[r] ?? r,
      kinhAi: (k: string) => meta?.kinh_ai?.[k as keyof typeof meta.kinh_ai] ?? k,
      trangThaiPhieu: meta?.trang_thai_phieu ?? [],
      chuyenTrangThai: (s: string) =>
        meta?.chuyen_trang_thai?.[s as keyof typeof meta.chuyen_trang_thai] ?? [],
    }),
    [meta],
  );
}

export const vnd = (n: number) => new Intl.NumberFormat("vi-VN").format(n) + " ₫";
export const vndShort = (n: number) =>
  n >= 1e9
    ? (n / 1e9).toFixed(2) + " tỷ"
    : n >= 1e6
      ? (n / 1e6).toFixed(1).replace(".0", "") + " tr"
      : vnd(n);

/** Chuỗi ngày giờ của backend dạng `YYYY-MM-DD HH:MM:SS` (UTC) → hiển thị VN. */
export const fmtTime = (iso: string) => {
  const d = new Date(iso.includes("T") || iso.includes(" ") ? iso.replace(" ", "T") : iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("vi-VN", {
    hour: "2-digit",
    minute: "2-digit",
    day: "2-digit",
    month: "2-digit",
    timeZone: "Asia/Ho_Chi_Minh",
  });
};

export const fmtNgay = (iso: string) => {
  const d = new Date(iso.includes("T") || iso.includes(" ") ? iso.replace(" ", "T") : iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("vi-VN", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    timeZone: "Asia/Ho_Chi_Minh",
  });
};
