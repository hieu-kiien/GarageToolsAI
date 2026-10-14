import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { ChevronRight, User } from "lucide-react";
import { api, q, ApiError } from "@/services/api";
import { useLookups } from "@/services/lookups";
import { useNhan, useRole, fmtTime } from "@/lib/rbac";
import { PageHeader, Plate, StatusPill, NoAccess, DangTai, Empty } from "@/components/app/ui-kit";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import type { PhieuDong, RepairStatus } from "@/types";

export const Route = createFileRoute("/workflow")({
  head: () => ({
    meta: [
      { title: "Bảng điều phối sửa chữa — GarageTools AI" },
      {
        name: "description",
        content:
          "Kanban luồng phiếu sửa chữa từ tiếp nhận đến hoàn thành, phân công kỹ thuật viên.",
      },
      { property: "og:title", content: "Bảng điều phối sửa chữa — GarageTools AI" },
      { property: "og:description", content: "Bảng điều phối xưởng dịch vụ ô tô." },
    ],
  }),
  component: Board,
});

function Board() {
  const { area, can, user } = useRole();
  const N = useNhan();
  const qc = useQueryClient();
  const L = useLookups();
  const danhSach = useQuery(q.orders({ moi_trang: 100 }));
  const [sel, setSel] = useState<PhieuDong | null>(null);
  const [keo, setKeo] = useState<number | null>(null);
  // Chi tiết đang mở để lấy technician_id (danh sách chỉ trả tên KTV).
  const chiTiet = useQuery({ ...q.order(sel?.id ?? 0), enabled: sel !== null });
  const phieu = chiTiet.data?.phieu;

  const chuyen = useMutation({
    mutationFn: ({ id, status }: { id: number; status: RepairStatus }) =>
      api.doiTrangThai(id, status),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      await qc.invalidateQueries({ queryKey: ["orders"] });
      await qc.invalidateQueries({ queryKey: ["dashboard"] });
      await qc.invalidateQueries({ queryKey: ["stock"] });
      await qc.invalidateQueries({ queryKey: ["parts"] });
      await qc.invalidateQueries({ queryKey: ["lookups"] });
      setSel((s) => (s ? { ...s, status: (kq.phieu as PhieuDong).status } : s));
    },
    onError: (e) => toast.error(e instanceof ApiError ? e.message : "Chuyển trạng thái thất bại."),
  });

  const phanCong = useMutation({
    mutationFn: ({ id, technician_id }: { id: number; technician_id: number | null }) =>
      api.phanCong(id, technician_id),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      await qc.invalidateQueries({ queryKey: ["orders"] });
    },
    onError: (e) => toast.error(e instanceof ApiError ? e.message : "Phân công thất bại."),
  });

  if (!area("board")) return <NoAccess />;
  if (!N.trangThaiPhieu.length || danhSach.isPending)
    return <DangTai mat="Đang tải bảng điều phối…" />;
  if (danhSach.isError)
    return (
      <div className="p-8 text-sm text-destructive">
        Không tải được danh sách phiếu.{" "}
        {danhSach.error instanceof ApiError ? danhSach.error.message : ""}
      </div>
    );

  const dong = danhSach.data.dong;
  const tong = danhSach.data.tong;
  const canChuyen = can("order.progress");
  const canPhanCong = can("order.assign");
  const ketThucSel = sel ? sel.status === "COMPLETED" || sel.status === "CANCELLED" : false;
  const ktvDuocPhepSel =
    user?.role !== "TECHNICIAN" || (phieu ? phieu.technician_id === user.id : true);

  const thuChuyen = (id: number, status: RepairStatus) => {
    if (!canChuyen) return toast.error("Bạn không có quyền chuyển trạng thái phiếu.");
    chuyen.mutate({ id, status });
    return undefined;
  };

  return (
    <>
      <PageHeader
        eyebrow="Vận hành"
        title="Bảng điều phối sửa chữa"
        desc="Kéo thả thẻ giữa các cột hoặc bấm nút chuyển trạng thái. Luật chuyển do backend quy định — kéo sai luật hệ thống sẽ báo lỗi."
        actions={
          <span className="text-xs text-muted-foreground">
            {canChuyen
              ? "Bạn có quyền chuyển trạng thái"
              : "Chỉ xem — tài khoản của bạn không có quyền chuyển trạng thái"}
          </span>
        }
      />
      {tong > dong.length && (
        <div className="mx-4 mt-4 rounded-md border border-warning/40 bg-warning-soft px-4 py-2.5 text-xs lg:mx-6">
          Đang hiển thị {dong.length}/{tong} phiếu — xem danh sách đầy đủ tại{" "}
          <Link to="/repair-orders" className="font-medium text-primary">
            Phiếu sửa chữa
          </Link>
        </div>
      )}
      <div className="overflow-x-auto p-4 lg:p-6">
        <div className="flex min-w-max gap-3">
          {N.trangThaiPhieu.map((st) => {
            const col = dong.filter((o) => o.status === st);
            return (
              <div
                key={st}
                onDragOver={(e) => e.preventDefault()}
                onDrop={() => {
                  if (keo !== null) thuChuyen(keo, st);
                  setKeo(null);
                }}
                className="flex w-72 flex-col rounded-lg border bg-muted/50"
              >
                <div className="flex items-center justify-between px-3 py-2.5">
                  <span className="text-[13px] font-semibold">{N.trangThai(st)}</span>
                  <span className="tabular rounded bg-card px-1.5 text-xs text-muted-foreground">
                    {col.length}
                  </span>
                </div>
                <div className="flex min-h-[50vh] flex-col gap-2 px-2 pb-2">
                  {col.map((o) => (
                    <button
                      key={o.id}
                      draggable={canChuyen}
                      onDragStart={() => setKeo(o.id)}
                      onClick={() => setSel(o)}
                      className="cursor-grab rounded-md border bg-card p-3 text-left shadow-card transition hover:border-primary/40 active:cursor-grabbing"
                    >
                      <div className="flex items-center justify-between">
                        <Plate>{o.plate}</Plate>
                        <span className="font-mono text-[11px] text-muted-foreground">#{o.id}</span>
                      </div>
                      <div className="mt-2 text-[13px] font-medium">
                        {o.brand} {o.model}
                      </div>
                      <div className="mt-0.5 line-clamp-2 min-h-[2rem] text-xs text-muted-foreground">
                        {o.technical_notes ?? "Không có ghi chú"}
                      </div>
                      <div className="mt-2.5 flex items-center justify-between text-[11px] text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <User className="size-3" />
                          {o.ky_thuat_vien ?? "Chưa phân công"}
                        </span>
                        <span className="tabular">{fmtTime(o.created_at)}</span>
                      </div>
                    </button>
                  ))}
                  {col.length === 0 && (
                    <div className="rounded-md border border-dashed p-3 text-center text-xs text-muted-foreground">
                      Trống
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <Sheet open={!!sel} onOpenChange={(o) => !o && setSel(null)}>
        <SheetContent className="w-full sm:max-w-md">
          {sel && (
            <>
              <SheetHeader>
                <SheetTitle className="flex items-center gap-2">
                  <Plate>{sel.plate}</Plate>
                  <span className="font-mono text-sm text-muted-foreground">#{sel.id}</span>
                </SheetTitle>
                <SheetDescription>
                  {sel.brand} {sel.model} · {sel.ky_thuat_vien ?? "Chưa phân công KTV"}
                </SheetDescription>
              </SheetHeader>
              <div className="space-y-5 px-4">
                <div className="flex items-center justify-between">
                  <StatusPill s={sel.status} />
                  <span className="text-xs text-muted-foreground">
                    Tạo {fmtTime(sel.created_at)}
                  </span>
                </div>
                <p className="rounded-md bg-muted p-3 text-sm">
                  {sel.technical_notes ?? "Không có ghi chú kỹ thuật."}
                </p>

                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">
                    Kỹ thuật viên phụ trách
                  </label>
                  <Select
                    disabled={!canPhanCong || ketThucSel}
                    value={phieu?.technician_id ? String(phieu.technician_id) : "none"}
                    onValueChange={(v) =>
                      phanCong.mutate({
                        id: sel.id,
                        technician_id: v === "none" ? null : Number(v),
                      })
                    }
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Chưa phân công" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none">Chưa phân công</SelectItem>
                      {L.ky_thuat_vien.map((t) => (
                        <SelectItem key={t.id} value={String(t.id)}>
                          {t.full_name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {(!canPhanCong || ketThucSel) && (
                    <p className="text-[11px] text-muted-foreground">
                      {ketThucSel
                        ? "Phiếu đã kết thúc — không thể đổi phân công."
                        : "Chỉ Quản lý hoặc Lễ tân được phân công."}
                    </p>
                  )}
                </div>

                <div className="space-y-2">
                  <div className="text-xs font-medium text-muted-foreground">
                    Chuyển trạng thái (luật do backend quy định)
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {canChuyen &&
                      ktvDuocPhepSel &&
                      N.chuyenTrangThai(sel.status).map((tt) => (
                        <Button
                          key={tt}
                          size="sm"
                          variant={tt === "CANCELLED" ? "destructive" : "default"}
                          onClick={() => {
                            thuChuyen(sel.id, tt);
                            setSel(null);
                          }}
                        >
                          {N.trangThai(tt)}
                        </Button>
                      ))}
                    {N.chuyenTrangThai(sel.status).length === 0 && (
                      <p className="text-xs text-muted-foreground">
                        Phiếu đã kết thúc — không còn trạng thái chuyển tiếp.
                      </p>
                    )}
                  </div>
                  {(!canChuyen || !ktvDuocPhepSel) && (
                    <p className="text-[11px] text-muted-foreground">
                      {!canChuyen
                        ? "Tài khoản của bạn không có quyền chuyển trạng thái."
                        : "Chỉ kỹ thuật viên được phân công phụ trách phiếu mới được chuyển trạng thái."}
                    </p>
                  )}
                </div>

                <div className="flex gap-2">
                  <Button variant="outline" asChild className="flex-1">
                    <Link to="/repair-orders/$id" params={{ id: String(sel.id) }}>
                      Chi tiết <ChevronRight className="size-4" />
                    </Link>
                  </Button>
                </div>
              </div>
            </>
          )}
          {sel === null && (
            <div className="p-4">
              <Empty title="Không có phiếu được chọn" />
            </div>
          )}
        </SheetContent>
      </Sheet>
    </>
  );
}
