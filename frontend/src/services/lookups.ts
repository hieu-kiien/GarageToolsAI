import { useQuery, type QueryClient } from "@tanstack/react-query";
import { q } from "./api";
import type { Lookups } from "@/types";

/** Gọi trước khi vào form cần tra cứu (không dùng loader — dữ liệu tải bên máy khách). */
export const ensureLookups = (qc: QueryClient) => qc.ensureQueryData(q.lookups());

/** Toàn bộ bảng tra cứu id+tên của backend (`GET /api/lookups`). */
export function useLookups() {
  const { data } = useQuery(q.lookups());
  const d: Lookups | undefined = data;
  return {
    ready: !!d,
    khach_hang: d?.khach_hang ?? [],
    xe: d?.xe ?? [],
    dich_vu: d?.dich_vu ?? [],
    phu_tung: d?.phu_tung ?? [],
    ky_thuat_vien: d?.ky_thuat_vien ?? [],
    phieu: d?.phieu ?? [],
    khach: (id: number | null | undefined) => d?.khach_hang.find((k) => k.id === id),
    xeTheoId: (id: number | null | undefined) => d?.xe.find((x) => x.id === id),
    ktv: (id: number | null | undefined) => d?.ky_thuat_vien.find((t) => t.id === id),
    dichVu: (id: number | null | undefined) => d?.dich_vu.find((s) => s.id === id),
    phuTung: (id: number | null | undefined) => d?.phu_tung.find((p) => p.id === id),
  };
}
