import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { q, ApiError } from "@/services/api";
import { useLookups } from "@/services/lookups";
import { useNhan, useRole, fmtNgay, vnd } from "@/lib/rbac";
import {
  PageHeader,
  Panel,
  Plate,
  StatusPill,
  NoAccess,
  Empty,
  DangTai,
} from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/repair-orders/")({
  head: () => ({
    meta: [
      { title: "Phiếu sửa chữa — GarageTools AI" },
      {
        name: "description",
        content: "Danh sách phiếu sửa chữa, lọc theo trạng thái, biển số và ghi chú.",
      },
      { property: "og:title", content: "Phiếu sửa chữa — GarageTools AI" },
      { property: "og:description", content: "Tra cứu nhanh phiếu sửa chữa trong xưởng." },
    ],
  }),
  component: List,
});

function List() {
  const { area } = useRole();
  const N = useNhan();
  const L = useLookups();
  const [loc, setLoc] = useState<string>("all");
  const [locKtv, setLocKtv] = useState<string>("all");
  const [locNgay, setLocNgay] = useState<string>("all");
  const [tim, setTim] = useState("");
  const [tuKhoa, setTuKhoa] = useState("");
  const [trang, setTrang] = useState(1);

  // Gõ xong 300ms mới gọi backend — tránh một request cho mỗi phím bấm.
  useEffect(() => {
    const h = setTimeout(() => {
      setTuKhoa(tim.trim());
      setTrang(1);
    }, 300);
    return () => clearTimeout(h);
  }, [tim]);

  const ds = useQuery(
    q.orders({
      moi_trang: 20,
      trang,
      q: tuKhoa || undefined,
      trang_thai: loc === "all" ? undefined : loc,
      ktv: locKtv === "all" ? undefined : locKtv,
      ngay: locNgay === "all" ? undefined : locNgay,
    }),
  );

  if (!area("orders")) return <NoAccess />;
  if (ds.isPending) return <DangTai mat="Đang tải phiếu sửa chữa…" />;
  if (!ds.data)
    return (
      <div className="p-8 text-sm text-destructive">
        Không tải được danh sách phiếu.{" "}
        {ds.error instanceof ApiError ? ds.error.message : "Lỗi kết nối."}
      </div>
    );

  const { dong, tong, trang: trangHienTai, tong_trang } = ds.data;

  return (
    <>
      <PageHeader
        eyebrow="Vận hành"
        title="Phiếu sửa chữa"
        desc={`${tong} phiếu khớp bộ lọc — dữ liệu lấy từ backend, tìm kiếm theo biển số, ghi chú hoặc mã phiếu.`}
      />
      <div className="p-6 lg:p-8">
        <Panel bodyClass="p-0">
          <div className="flex flex-col gap-3 border-b p-3 xl:flex-row xl:items-center">
            <div className="flex flex-wrap gap-1">
              {["all", "DANG_XU_LY", ...N.trangThaiPhieu].map((k) => (
                <button
                  key={k}
                  onClick={() => {
                    setLoc(k);
                    setTrang(1);
                  }}
                  className={cn(
                    "rounded-md px-2.5 py-1 text-xs font-medium",
                    loc === k
                      ? "bg-foreground text-background"
                      : "text-muted-foreground hover:bg-muted",
                  )}
                >
                  {k === "all" ? "Tất cả" : k === "DANG_XU_LY" ? "Đang xử lý" : N.trangThai(k)}
                </button>
              ))}
            </div>
            <div className="flex flex-wrap items-center gap-2 xl:ml-auto">
              <Select
                value={locKtv}
                onValueChange={(v) => {
                  setLocKtv(v);
                  setTrang(1);
                }}
              >
                <SelectTrigger className="h-8 w-40 text-xs">
                  <SelectValue placeholder="Mọi KTV" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Mọi KTV</SelectItem>
                  <SelectItem value="none">Chưa phân công</SelectItem>
                  {L.ky_thuat_vien.map((t) => (
                    <SelectItem key={t.id} value={String(t.id)}>
                      {t.full_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select
                value={locNgay}
                onValueChange={(v) => {
                  setLocNgay(v);
                  setTrang(1);
                }}
              >
                <SelectTrigger className="h-8 w-36 text-xs">
                  <SelectValue placeholder="Mọi thời gian" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Mọi thời gian</SelectItem>
                  <SelectItem value="hom_nay">Hôm nay</SelectItem>
                  <SelectItem value="7_ngay">7 ngày qua</SelectItem>
                  <SelectItem value="30_ngay">30 ngày qua</SelectItem>
                </SelectContent>
              </Select>
              <input
                value={tim}
                onChange={(e) => setTim(e.target.value)}
                placeholder="Lọc mã, biển số, khách, SĐT, ghi chú…"
                className="h-8 rounded-md border bg-background px-2.5 text-sm md:w-64"
              />
            </div>
          </div>

          {ds.isError && (
            <div className="p-6 text-sm text-destructive">
              Không tải được danh sách.{" "}
              {ds.error instanceof ApiError ? ds.error.message : "Lỗi kết nối."}
            </div>
          )}

          {dong.length === 0 && !ds.isError ? (
            <div className="p-6">
              <Empty title="Không có phiếu phù hợp" desc="Thử bỏ bộ lọc hoặc đổi từ khoá." />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 text-left text-[11px] uppercase tracking-wider text-muted-foreground">
                  <tr>
                    {[
                      "Mã phiếu",
                      "Biển số",
                      "Xe",
                      "Khách hàng",
                      "Trạng thái",
                      "KTV",
                      "Tổng tiền",
                      "Ngày tạo",
                      "Ghi chú",
                    ].map((h) => (
                      <th key={h} className="px-4 py-2 font-medium">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {dong.map((o) => (
                    <tr key={o.id} className="hover:bg-muted/40">
                      <td className="px-4 py-2.5">
                        <Link
                          to="/repair-orders/$id"
                          params={{ id: String(o.id) }}
                          className="font-mono text-xs font-medium text-primary"
                        >
                          #{o.id}
                        </Link>
                      </td>
                      <td className="px-4 py-2.5">
                        <Plate>{o.plate}</Plate>
                      </td>
                      <td className="px-4 py-2.5">
                        {o.brand} {o.model}
                      </td>
                      <td className="px-4 py-2.5">
                        <div>{o.khach ?? "—"}</div>
                        {o.khach_phone && (
                          <div className="font-mono text-[11px] text-muted-foreground">
                            {o.khach_phone}
                          </div>
                        )}
                      </td>
                      <td className="px-4 py-2.5">
                        <StatusPill s={o.status} />
                      </td>
                      <td className="px-4 py-2.5 text-muted-foreground">
                        {o.ky_thuat_vien ?? "—"}
                      </td>
                      <td className="tabular px-4 py-2.5 font-medium">{vnd(o.tong ?? 0)}</td>
                      <td className="tabular px-4 py-2.5 text-xs">{fmtNgay(o.created_at)}</td>
                      <td className="max-w-[240px] truncate px-4 py-2.5 text-xs text-muted-foreground">
                        {o.technical_notes ?? "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="flex items-center justify-between border-t px-4 py-3 text-xs text-muted-foreground">
            <span className="tabular">
              Trang {trangHienTai}/{tong_trang} · {tong} phiếu
            </span>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                disabled={trangHienTai <= 1}
                onClick={() => setTrang(trangHienTai - 1)}
              >
                Trước
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={trangHienTai >= tong_trang}
                onClick={() => setTrang(trangHienTai + 1)}
              >
                Sau
              </Button>
            </div>
          </div>
        </Panel>
      </div>
    </>
  );
}
