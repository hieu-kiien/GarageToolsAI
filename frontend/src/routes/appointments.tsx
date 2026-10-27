import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { CalendarDays, ClipboardList, Pencil, Plus, Trash2 } from "lucide-react";
import { api, q, ApiError } from "@/services/api";
import { useNhan, useRole, fmtNgay, fmtTime } from "@/lib/rbac";
import {
  DangTai,
  Empty,
  NoAccess,
  PageHeader,
  Panel,
  Pill,
  Plate,
  type Tone,
} from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { cn } from "@/lib/utils";
import type { AppointmentStatus, LichHenDong } from "@/types";

export const Route = createFileRoute("/appointments")({
  head: () => ({
    meta: [
      { title: "Lịch hẹn — GarageTools AI" },
      {
        name: "description",
        content: "Danh sách lịch hẹn, lọc theo trạng thái và tra cứu theo biển số, tên khách.",
      },
      { property: "og:title", content: "Lịch hẹn — GarageTools AI" },
      { property: "og:description", content: "Quản lý lịch hẹn của khách hàng." },
    ],
  }),
  component: LichHen,
});

/** Trạng thái thật của bảng `appointments` (backend `LichHenInput.status`). */
const TRANG_THAI_LICH = ["SCHEDULED", "CONFIRMED", "DONE", "CANCELLED"] as const;

const toneLich: Record<AppointmentStatus, Tone> = {
  SCHEDULED: "success",
  CONFIRMED: "info",
  DONE: "neutral",
  CANCELLED: "danger",
};

const hai = (n: number) => String(n).padStart(2, "0");

/** Chuỗi UTC của backend `YYYY-MM-DD HH:MM` → giá trị `datetime-local` theo giờ máy. */
const denInput = (iso: string) => {
  const t = iso.trim().replace(" ", "T");
  const d = new Date(/(Z|[+-]\d{2}:?\d{2})$/.test(t) ? t : `${t}Z`);
  if (Number.isNaN(d.getTime())) return "";
  return `${d.getFullYear()}-${hai(d.getMonth() + 1)}-${hai(d.getDate())}T${hai(
    d.getHours(),
  )}:${hai(d.getMinutes())}`;
};

/** Giá trị `datetime-local` → chuỗi `YYYY-MM-DD HH:MM` (UTC) mà backend yêu cầu. */
const tuInput = (v: string) => {
  const d = new Date(v);
  if (Number.isNaN(d.getTime())) return "";
  return `${d.getUTCFullYear()}-${hai(d.getUTCMonth() + 1)}-${hai(d.getUTCDate())} ${hai(
    d.getUTCHours(),
  )}:${hai(d.getUTCMinutes())}`;
};

function LichHen() {
  const { area, can } = useRole();
  const N = useNhan();
  const qc = useQueryClient();

  const [loc, setLoc] = useState<string>("all");
  const [tim, setTim] = useState("");
  const [tuKhoa, setTuKhoa] = useState("");
  const [trang, setTrang] = useState(1);

  const [moForm, setMoForm] = useState(false);
  const [dangSua, setDangSua] = useState<LichHenDong | null>(null);
  const [khachId, setKhachId] = useState("");
  const [xeId, setXeId] = useState("");
  const [gio, setGio] = useState("");
  const [ghiChu, setGhiChu] = useState("");
  const [trangThai, setTrangThai] = useState<string>("SCHEDULED");
  const [xoaId, setXoaId] = useState<number | null>(null);

  // Gõ xong 300ms mới gọi backend — tránh một request cho mỗi phím bấm.
  useEffect(() => {
    const h = setTimeout(() => {
      setTuKhoa(tim.trim());
      setTrang(1);
    }, 300);
    return () => clearTimeout(h);
  }, [tim]);

  const ds = useQuery(
    q.appointments({
      moi_trang: 20,
      trang,
      q: tuKhoa || undefined,
      trang_thai: loc === "all" ? undefined : loc,
    }),
  );
  const dsKhach = useQuery({ ...q.customers({ moi_trang: 500 }), enabled: moForm });
  const dsXe = useQuery({
    ...q.vehicles({ moi_trang: 500, khach: khachId ? Number(khachId) : undefined }),
    enabled: moForm && !!khachId,
  });

  const loi = (e: unknown) => toast.error(e instanceof ApiError ? e.message : "Thao tác thất bại.");

  const luu = useMutation({
    mutationFn: () => {
      const body = {
        customer_id: Number(khachId),
        vehicle_id: Number(xeId),
        scheduled_at: tuInput(gio),
        notes: ghiChu.trim() || null,
        status: trangThai,
      };
      return dangSua ? api.suaLich(dangSua.id, body) : api.taoLich(body);
    },
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      setMoForm(false);
      await qc.invalidateQueries({ queryKey: ["appointments"] });
    },
    onError: loi,
  });

  const xoa = useMutation({
    mutationFn: (id: number) => api.xoaLich(id),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      setXoaId(null);
      await qc.invalidateQueries({ queryKey: ["appointments"] });
    },
    onError: (e) => {
      loi(e);
      setXoaId(null);
    },
  });

  const moTao = () => {
    setDangSua(null);
    setKhachId("");
    setXeId("");
    setGio(denInput(new Date().toISOString()));
    setGhiChu("");
    setTrangThai("SCHEDULED");
    setMoForm(true);
  };

  const moSua = (l: LichHenDong) => {
    setDangSua(l);
    setKhachId(String(l.customer_id));
    setXeId(String(l.vehicle_id));
    setGio(denInput(l.scheduled_at));
    setGhiChu(l.notes ?? "");
    setTrangThai(l.status);
    setMoForm(true);
  };

  if (!area("appointments")) return <NoAccess />;
  if (ds.isPending) return <DangTai mat="Đang tải lịch hẹn…" />;
  if (!ds.data)
    return (
      <div className="p-8 text-sm text-destructive">
        Không tải được danh sách lịch hẹn.{" "}
        {ds.error instanceof ApiError ? ds.error.message : "Lỗi kết nối."}
      </div>
    );

  const { dong, tong, trang: trangHienTai, tong_trang } = ds.data;
  const coSua = can("appointment.edit");

  return (
    <>
      <PageHeader
        eyebrow="Vận hành"
        title="Lịch hẹn"
        desc={`${tong} lịch hẹn khớp bộ lọc — backend sắp xếp theo thời gian hẹn, tìm kiếm theo biển số hoặc tên khách hàng.`}
        actions={
          coSua && (
            <Button size="sm" onClick={moTao}>
              <Plus className="size-4" />
              Đặt lịch hẹn
            </Button>
          )
        }
      />

      <div className="p-6 lg:p-8">
        <Panel bodyClass="p-0">
          <div className="flex flex-col gap-3 border-b p-3 md:flex-row md:items-center">
            <div className="flex flex-wrap gap-1">
              {["all", ...TRANG_THAI_LICH].map((k) => (
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
            <Input
              value={tim}
              onChange={(e) => setTim(e.target.value)}
              placeholder="Lọc theo biển số, tên khách…"
              className="h-8 md:ml-auto md:w-64"
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
              <Empty title="Không có lịch hẹn phù hợp" desc="Thử bỏ bộ lọc hoặc đổi từ khoá." />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 text-left text-[11px] uppercase tracking-wider text-muted-foreground">
                  <tr>
                    <th className="px-4 py-2 font-medium">Thời gian hẹn</th>
                    <th className="px-4 py-2 font-medium">Khách hàng</th>
                    <th className="px-4 py-2 font-medium">Biển số</th>
                    <th className="px-4 py-2 font-medium">Trạng thái</th>
                    <th className="px-4 py-2 font-medium">Ghi chú</th>
                    <th className="px-4 py-2 font-medium">Ngày tạo</th>
                    {coSua && <th className="px-4 py-2 text-right font-medium">Thao tác</th>}
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {dong.map((l) => (
                    <tr key={l.id} className="hover:bg-muted/40">
                      <td className="tabular px-4 py-2.5 text-xs">{fmtTime(l.scheduled_at)}</td>
                      <td className="px-4 py-2.5">{l.khach}</td>
                      <td className="px-4 py-2.5">
                        <Plate>{l.plate}</Plate>
                      </td>
                      <td className="px-4 py-2.5">
                        <Pill t={toneLich[l.status] ?? "neutral"} dot>
                          {N.trangThai(l.status)}
                        </Pill>
                      </td>
                      <td className="max-w-[240px] truncate px-4 py-2.5 text-xs text-muted-foreground">
                        {l.notes ?? "—"}
                      </td>
                      <td className="tabular px-4 py-2.5 text-xs">{fmtNgay(l.created_at)}</td>
                      {coSua && (
                        <td className="px-4 py-2.5 text-right">
                          <div className="flex justify-end gap-1">
                            {can("order.create") &&
                              (l.status === "SCHEDULED" || l.status === "CONFIRMED") && (
                                <Button size="sm" variant="outline" asChild>
                                  <Link
                                    to="/inspection"
                                    onClick={() => {
                                      try {
                                        sessionStorage.setItem(
                                          "garagetools_intake_prefill",
                                          JSON.stringify({
                                            xeId: String(l.vehicle_id),
                                            ghiChuPhieu: l.notes ?? "",
                                          }),
                                        );
                                      } catch {
                                        /* ignore */
                                      }
                                    }}
                                  >
                                    <ClipboardList className="size-3.5" />
                                    Tiếp nhận
                                  </Link>
                                </Button>
                              )}
                            <Button size="sm" variant="ghost" onClick={() => moSua(l)}>
                              <Pencil className="size-3.5" />
                              Sửa
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              className="text-destructive hover:text-destructive"
                              onClick={() => setXoaId(l.id)}
                            >
                              <Trash2 className="size-3.5" />
                              Xoá
                            </Button>
                          </div>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="flex items-center justify-between border-t px-4 py-3 text-xs text-muted-foreground">
            <span className="tabular">
              Trang {trangHienTai}/{tong_trang} · {tong} lịch hẹn
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

      <Dialog
        open={moForm}
        onOpenChange={(o) => {
          if (!o) setMoForm(false);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CalendarDays className="size-4" />
              {dangSua ? `Sửa lịch hẹn #${dangSua.id}` : "Đặt lịch hẹn mới"}
            </DialogTitle>
            <DialogDescription>
              Xe phải thuộc đúng khách hàng đã chọn — backend kiểm tra lại khi lưu.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 text-sm">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Khách hàng</label>
              <Select
                value={khachId}
                onValueChange={(v) => {
                  setKhachId(v);
                  setXeId("");
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Chọn khách hàng…" />
                </SelectTrigger>
                <SelectContent>
                  {(dsKhach.data?.dong ?? []).map((k) => (
                    <SelectItem key={k.id} value={String(k.id)}>
                      {k.name} · {k.phone}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Phương tiện</label>
              <Select value={xeId} onValueChange={setXeId} disabled={!khachId}>
                <SelectTrigger>
                  <SelectValue placeholder={khachId ? "Chọn xe của khách…" : "Chọn khách trước…"} />
                </SelectTrigger>
                <SelectContent>
                  {(dsXe.data?.dong ?? []).map((x) => (
                    <SelectItem key={x.id} value={String(x.id)}>
                      {x.plate} — {x.brand} {x.model}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Thời gian hẹn</label>
              <Input type="datetime-local" value={gio} onChange={(e) => setGio(e.target.value)} />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Trạng thái</label>
              <Select value={trangThai} onValueChange={setTrangThai}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {TRANG_THAI_LICH.map((tt) => (
                    <SelectItem key={tt} value={tt}>
                      {N.trangThai(tt)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Ghi chú</label>
              <Textarea
                value={ghiChu}
                onChange={(e) => setGhiChu(e.target.value)}
                placeholder="Yêu cầu của khách, khung giờ ưu tiên…"
                className="min-h-[70px]"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setMoForm(false)}>
              Huỷ
            </Button>
            <Button
              disabled={!khachId || !xeId || !gio || luu.isPending}
              onClick={() => luu.mutate()}
            >
              {dangSua ? "Lưu thay đổi" : "Đặt lịch"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog
        open={xoaId !== null}
        onOpenChange={(o) => {
          if (!o) setXoaId(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Xoá lịch hẹn #{xoaId}?</AlertDialogTitle>
            <AlertDialogDescription>
              Lịch hẹn sẽ bị xoá vĩnh viễn khỏi hệ thống.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Đóng</AlertDialogCancel>
            <AlertDialogAction
              disabled={xoa.isPending}
              onClick={(e) => {
                e.preventDefault();
                if (xoaId !== null) xoa.mutate(xoaId);
              }}
            >
              Xoá lịch hẹn
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
