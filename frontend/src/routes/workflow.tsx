import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { ChevronRight, LayoutGrid, ListFilter, Search, User } from "lucide-react";
import { api, q, ApiError } from "@/services/api";
import { useLookups } from "@/services/lookups";
import { useNhan, useRole, fmtTime, vnd } from "@/lib/rbac";
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
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
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
  const danhSach = useQuery(q.orders({ moi_trang: 300 }));
  const [sel, setSel] = useState<PhieuDong | null>(null);
  const [keo, setKeo] = useState<number | null>(null);
  const [tim, setTim] = useState("");
  const [locKtv, setLocKtv] = useState<string>("all");
  const [gioiHanKetThuc, setGioiHanKetThuc] = useState<string>("5");
  const [thuGon, setThuGon] = useState(false);
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

  const dongGoc = danhSach.data.dong;
  const tong = danhSach.data.tong;
  const canChuyen = can("order.progress");
  const canPhanCong = can("order.assign");
  const ketThucSel = sel ? sel.status === "COMPLETED" || sel.status === "CANCELLED" : false;
  const ktvDuocPhepSel =
    user?.role !== "TECHNICIAN" || (phieu ? phieu.technician_id === user.id : true);
  const phieuDangKeo = keo !== null ? dongGoc.find((o) => o.id === keo) : undefined;
  const cotHopLeKhiKeo = phieuDangKeo ? N.chuyenTrangThai(phieuDangKeo.status) : [];

  const qNorm = tim.trim().toLowerCase().replace(/^#/, "");
  const dong = dongGoc.filter((o) => {
    if (locKtv === "none" && o.ky_thuat_vien) return false;
    if (locKtv !== "all" && locKtv !== "none") {
      if (o.technician_id !== undefined) {
        if (String(o.technician_id ?? "") !== locKtv) return false;
      } else {
        const ktvObj = L.ky_thuat_vien.find((k) => String(k.id) === locKtv);
        if (ktvObj && o.ky_thuat_vien !== ktvObj.full_name) return false;
      }
    }
    if (!qNorm) return true;
    return (
      String(o.id) === qNorm ||
      o.plate.toLowerCase().includes(qNorm) ||
      `${o.brand} ${o.model}`.toLowerCase().includes(qNorm) ||
      (o.khach ?? "").toLowerCase().includes(qNorm) ||
      (o.khach_phone ?? "").toLowerCase().includes(qNorm) ||
      (o.technical_notes ?? "").toLowerCase().includes(qNorm) ||
      (o.ky_thuat_vien ?? "").toLowerCase().includes(qNorm)
    );
  });

  const homNayIso = new Date().toISOString().slice(0, 10);
  const dangXuLyCount = dong.filter(
    (o) => o.status !== "COMPLETED" && o.status !== "CANCELLED",
  ).length;

  const thuChuyen = (id: number, status: RepairStatus) => {
    if (!canChuyen) return toast.error("Bạn không có quyền chuyển trạng thái phiếu.");
    const hienTai = dongGoc.find((o) => o.id === id);
    if (hienTai && hienTai.status === status) return undefined;
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
          <div className="flex flex-wrap items-center gap-2">
            <span className="rounded-md border bg-muted/60 px-2.5 py-1 text-xs font-medium">
              Đang xử lý in-bay: <b className="tabular text-primary">{dangXuLyCount}</b> xe
            </span>
            <Button
              size="sm"
              variant={thuGon ? "default" : "outline"}
              onClick={() => setThuGon((v) => !v)}
              title="Chuyển chế độ thẻ thu gọn để quan sát nhiều xe cùng lúc"
            >
              <LayoutGrid className="size-3.5" />
              {thuGon ? "Thẻ thu gọn" : "Thẻ chi tiết"}
            </Button>
          </div>
        }
      />

      {/* Thanh công cụ lọc nhanh cho xưởng lưu lượng lớn (30–50+ xe/ngày) */}
      <div className="mx-4 mt-4 flex flex-wrap items-center gap-2.5 rounded-lg border bg-card p-3 shadow-xs lg:mx-6">
        <div className="relative min-w-[220px] flex-1">
          <Search className="absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={tim}
            onChange={(e) => setTim(e.target.value)}
            placeholder="Tìm nhanh biển số, khách hàng, #mã phiếu, ghi chú…"
            className="h-8 pl-8 text-xs"
          />
        </div>
        <div className="flex items-center gap-1.5">
          <ListFilter className="size-3.5 text-muted-foreground" />
          <Select value={locKtv} onValueChange={setLocKtv}>
            <SelectTrigger className="h-8 w-44 text-xs">
              <SelectValue placeholder="Mọi kỹ thuật viên" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Mọi kỹ thuật viên</SelectItem>
              <SelectItem value="none">Chưa phân công KTV</SelectItem>
              {L.ky_thuat_vien.map((t) => (
                <SelectItem key={t.id} value={String(t.id)}>
                  KTV: {t.full_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-xs text-muted-foreground">Cột kết thúc:</span>
          <Select value={gioiHanKetThuc} onValueChange={setGioiHanKetThuc}>
            <SelectTrigger className="h-8 w-36 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="5">5 xe gần nhất</SelectItem>
              <SelectItem value="hom_nay">Trong hôm nay</SelectItem>
              <SelectItem value="20">20 xe gần nhất</SelectItem>
              <SelectItem value="all">Hiện tất cả</SelectItem>
            </SelectContent>
          </Select>
        </div>
        {(tim || locKtv !== "all") && (
          <Button
            size="sm"
            variant="ghost"
            className="h-8 px-2 text-xs"
            onClick={() => {
              setTim("");
              setLocKtv("all");
            }}
          >
            Xoá lọc
          </Button>
        )}
      </div>

      {tong > dongGoc.length && (
        <div className="mx-4 mt-3 rounded-md border border-warning/40 bg-warning-soft px-4 py-2 text-xs lg:mx-6">
          Đang tải {dongGoc.length}/{tong} phiếu gần nhất — tra cứu toàn bộ lịch sử tại{" "}
          <Link to="/repair-orders" className="font-medium text-primary underline">
            Phiếu sửa chữa
          </Link>
        </div>
      )}
      <div className="overflow-x-auto p-4 lg:p-6">
        <div className="grid min-w-[1080px] grid-cols-6 gap-2.5">
          {N.trangThaiPhieu.map((st) => {
            const colAll = dong.filter((o) => o.status === st);
            const laCotKetThuc = st === "COMPLETED" || st === "CANCELLED";
            let col = colAll;
            if (laCotKetThuc && !tim) {
              if (gioiHanKetThuc === "hom_nay") {
                col = colAll.filter((o) => o.created_at.slice(0, 10) === homNayIso);
              } else if (gioiHanKetThuc !== "all") {
                const cap = Number(gioiHanKetThuc) || 5;
                col = colAll.slice(0, cap);
              }
            }
            const soPhieuAn = colAll.length - col.length;
            const coTheTha = phieuDangKeo ? cotHopLeKhiKeo.includes(st) : false;
            const cungCot = phieuDangKeo ? phieuDangKeo.status === st : false;
            return (
              <div
                key={st}
                onDragOver={(e) => {
                  e.preventDefault();
                  e.dataTransfer.dropEffect = coTheTha || cungCot ? "move" : "none";
                }}
                onDrop={() => {
                  if (keo !== null) thuChuyen(keo, st);
                  setKeo(null);
                }}
                className={cn(
                  "flex min-w-0 flex-col rounded-lg border bg-muted/50 transition",
                  phieuDangKeo &&
                    coTheTha &&
                    "border-primary/60 bg-primary/5 ring-1 ring-primary/30",
                  phieuDangKeo && !coTheTha && !cungCot && "opacity-55",
                )}
              >
                <div className="flex items-center justify-between border-b bg-muted/70 px-3 py-2.5">
                  <span className="truncate text-[13px] font-semibold">{N.trangThai(st)}</span>
                  <span className="tabular rounded bg-card px-1.5 py-0.5 text-xs font-medium text-muted-foreground">
                    {col.length !== colAll.length
                      ? `${col.length}/${colAll.length}`
                      : colAll.length}
                  </span>
                </div>
                <div className="flex max-h-[calc(100vh-260px)] min-h-[45vh] flex-col gap-2 overflow-y-auto px-2 py-2">
                  {col.map((o) => (
                    <button
                      key={o.id}
                      draggable={canChuyen}
                      onDragStart={(e) => {
                        e.dataTransfer.effectAllowed = "move";
                        e.dataTransfer.setData("text/plain", String(o.id));
                        setKeo(o.id);
                      }}
                      onDragEnd={() => setKeo(null)}
                      onClick={() => setSel(o)}
                      className={cn(
                        "cursor-grab rounded-md border bg-card text-left shadow-card transition hover:border-primary/40 active:cursor-grabbing",
                        thuGon ? "p-2" : "p-3",
                      )}
                    >
                      <div className="flex items-center justify-between">
                        <Plate>{o.plate}</Plate>
                        <span className="font-mono text-[11px] text-muted-foreground">#{o.id}</span>
                      </div>
                      <div
                        className={cn("font-medium", thuGon ? "mt-1 text-xs" : "mt-2 text-[13px]")}
                      >
                        {o.brand} {o.model}
                      </div>
                      {!thuGon && (
                        <>
                          {o.khach && (
                            <div className="mt-0.5 truncate text-[11px] text-foreground/80">
                              KH: {o.khach}
                            </div>
                          )}
                          <div className="mt-0.5 line-clamp-2 min-h-[2rem] text-xs text-muted-foreground">
                            {o.technical_notes ?? "Không có ghi chú"}
                          </div>
                        </>
                      )}
                      <div
                        className={cn(
                          "flex items-center justify-between text-[11px] text-muted-foreground",
                          thuGon ? "mt-1.5" : "mt-2.5",
                        )}
                      >
                        <span className="flex items-center gap-1 truncate">
                          <User className="size-3 shrink-0" />
                          <span className="truncate">{o.ky_thuat_vien ?? "Chưa phân công"}</span>
                        </span>
                        {!thuGon && (
                          <span className="tabular shrink-0">{fmtTime(o.created_at)}</span>
                        )}
                      </div>
                    </button>
                  ))}
                  {soPhieuAn > 0 && (
                    <button
                      type="button"
                      onClick={() => setGioiHanKetThuc("all")}
                      className="rounded-md border border-dashed bg-card/60 py-2 text-center text-[11px] font-medium text-primary hover:bg-card"
                    >
                      + {soPhieuAn} phiếu cũ hơn (bấm để hiện tất cả)
                    </button>
                  )}
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
                {(phieu?.khach || sel.khach) && (
                  <div className="flex items-center justify-between rounded-md border bg-card px-3 py-2 text-xs">
                    <span className="text-muted-foreground">
                      Khách hàng: <b className="text-foreground">{phieu?.khach ?? sel.khach}</b>
                    </span>
                    <span className="tabular font-semibold text-primary">
                      {vnd(phieu?.tong ?? sel.tong ?? 0)}
                    </span>
                  </div>
                )}
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
