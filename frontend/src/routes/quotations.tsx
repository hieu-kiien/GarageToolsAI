import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { q, ApiError } from "@/services/api";
import { useNhan, useRole, fmtNgay, vnd } from "@/lib/rbac";
import {
  PageHeader,
  Panel,
  Plate,
  Pill,
  NoAccess,
  Empty,
  DangTai,
  type Tone,
} from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/quotations")({
  head: () => ({
    meta: [
      { title: "Báo giá — GarageTools AI" },
      {
        name: "description",
        content: "Danh sách báo giá: lọc theo trạng thái, tìm theo biển số hoặc mã báo giá.",
      },
      { property: "og:title", content: "Báo giá — GarageTools AI" },
      { property: "og:description", content: "Theo dõi báo giá gửi khách và áp dụng vào phiếu." },
    ],
  }),
  component: List,
});

/** Tông nhãn theo `quotations.status` — tên tiếng Việt lấy từ `GET /api/meta`. */
const toneBaoGia: Record<string, Tone> = {
  DRAFT: "neutral",
  SENT: "info",
  APPROVED: "success",
  REJECTED: "danger",
  CANCELLED: "danger",
  EXPIRED: "warning",
};

function List() {
  const { area, meta } = useRole();
  const N = useNhan();
  const [loc, setLoc] = useState("all");
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
    q.quotations({
      moi_trang: 20,
      trang,
      q: tuKhoa || undefined,
      trang_thai: loc === "all" ? undefined : loc,
    }),
  );

  if (!area("quotes")) return <NoAccess />;
  if (ds.isPending) return <DangTai mat="Đang tải danh sách báo giá…" />;
  if (!ds.data)
    return (
      <div className="p-8 text-sm text-destructive">
        Không tải được danh sách báo giá.{" "}
        {ds.error instanceof ApiError ? ds.error.message : "Lỗi kết nối."}
      </div>
    );

  const { dong, tong, trang: trangHienTai, tong_trang } = ds.data;
  // Bộ lọc lấy đúng danh sách trạng thái backend công bố — không tự suy đoán.
  const dsTrangThai = meta?.trang_thai_bao_gia ?? [];

  return (
    <>
      <PageHeader
        eyebrow="Vận hành"
        title="Báo giá"
        desc={`${tong} báo giá khớp bộ lọc — tổng tiền do backend tính từ từng hạng mục.`}
      />
      <div className="p-6 lg:p-8">
        <Panel bodyClass="p-0">
          <div className="flex flex-col gap-3 border-b p-3 md:flex-row md:items-center">
            <div className="flex flex-wrap gap-1">
              {["all", ...dsTrangThai].map((k) => (
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
                  {k === "all" ? "Tất cả" : N.trangThai(k)}
                </button>
              ))}
            </div>
            <input
              value={tim}
              onChange={(e) => setTim(e.target.value)}
              placeholder="Lọc theo mã báo giá, biển số, mã phiếu…"
              className="h-8 rounded-md border bg-background px-2.5 text-sm md:ml-auto md:w-72"
            />
          </div>

          {ds.isError && (
            <div className="p-6 text-sm text-destructive">
              Không tải được danh sách.{" "}
              {ds.error instanceof ApiError ? ds.error.message : "Lỗi kết nối."}
            </div>
          )}

          {dong.length === 0 && !ds.isError ? (
            <div className="p-6">
              <Empty title="Không có báo giá phù hợp" desc="Thử bỏ bộ lọc hoặc đổi từ khoá." />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 text-left text-[11px] uppercase tracking-wider text-muted-foreground">
                  <tr>
                    {[
                      "Mã báo giá",
                      "Phiếu",
                      "Biển số",
                      "Trạng thái",
                      "Tổng cộng",
                      "Ngày tạo",
                      "Áp dụng",
                    ].map((h) => (
                      <th key={h} className="px-4 py-2 font-medium">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {dong.map((bg) => (
                    <tr key={bg.id} className="hover:bg-muted/40">
                      <td className="px-4 py-2.5">
                        <Link
                          to="/quotations/$id"
                          params={{ id: String(bg.id) }}
                          className="font-mono text-xs font-medium text-primary"
                        >
                          #{bg.id}
                        </Link>
                      </td>
                      <td className="px-4 py-2.5">
                        <Link
                          to="/repair-orders/$id"
                          params={{ id: String(bg.repair_order_id) }}
                          className="font-mono text-xs text-muted-foreground hover:text-primary"
                        >
                          #{bg.repair_order_id}
                        </Link>
                      </td>
                      <td className="px-4 py-2.5">
                        <Plate>{bg.plate}</Plate>
                      </td>
                      <td className="px-4 py-2.5">
                        <Pill t={toneBaoGia[bg.status] ?? "neutral"} dot>
                          {N.trangThai(bg.status)}
                        </Pill>
                      </td>
                      <td className="tabular px-4 py-2.5 font-medium">{vnd(bg.total)}</td>
                      <td className="tabular px-4 py-2.5 text-xs">{fmtNgay(bg.created_at)}</td>
                      <td className="px-4 py-2.5">
                        {bg.applied_at ? (
                          <Pill t="success">Đã áp dụng</Pill>
                        ) : (
                          <span className="text-xs text-muted-foreground">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="flex items-center justify-between border-t px-4 py-3 text-xs text-muted-foreground">
            <span className="tabular">
              Trang {trangHienTai}/{tong_trang} · {tong} báo giá
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
