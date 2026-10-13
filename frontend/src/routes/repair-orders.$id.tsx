import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { ArrowLeft, Plus, Phone, User, Receipt, Trash2, FileText } from "lucide-react";
import { api, q, ApiError } from "@/services/api";
import { useLookups } from "@/services/lookups";
import { useNhan, useRole, fmtTime, vnd } from "@/lib/rbac";
import {
  PageHeader,
  Panel,
  Plate,
  StatusPill,
  NoAccess,
  Empty,
  DangTai,
  InvoicePill,
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
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import type { PayMethod } from "@/types";

export const Route = createFileRoute("/repair-orders/$id")({
  head: () => ({
    meta: [
      { title: "Chi tiết phiếu sửa chữa — GarageTools AI" },
      {
        name: "description",
        content: "Không gian làm việc phiếu: hạng mục, nhật ký, biên bản tiếp nhận, hoá đơn.",
      },
      { property: "og:title", content: "Chi tiết phiếu sửa chữa — GarageTools AI" },
      { property: "og:description", content: "Chi tiết phiếu sửa chữa xưởng dịch vụ." },
    ],
  }),
  component: Detail,
});

function Detail() {
  const { id } = Route.useParams();
  const oid = Number(id);
  const { area, can, meta } = useRole();
  const N = useNhan();
  const L = useLookups();
  const qc = useQueryClient();

  const ds = useQuery(q.order(oid));
  const [ghiChu, setGhiChu] = useState("");
  const [loai, setLoai] = useState<"dich_vu" | "phu_tung">("dich_vu");
  const [ma, setMa] = useState<string>("");
  const [sl, setSl] = useState(1);
  const [soTien, setSoTien] = useState(0);
  const [hinhThuc, setHinhThuc] = useState<PayMethod>("CASH");
  const [dangThu, setDangThu] = useState(false);

  const loi = (e: unknown) => toast.error(e instanceof ApiError ? e.message : "Thao tác thất bại.");

  const hopQuyen = (ten: string) => {
    if (!can(ten)) {
      toast.error("Bạn không có quyền thực hiện thao tác này.");
      return false;
    }
    return true;
  };

  const themMuc = useMutation({
    mutationFn: () => api.themHangMuc(oid, { loai, ma: Number(ma), qty: sl }),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      setMa("");
      setSl(1);
      await qc.invalidateQueries({ queryKey: ["orders"] });
    },
    onError: loi,
  });
  const goMuc = useMutation({
    mutationFn: (iid: number) => api.goHangMuc(oid, iid),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      await qc.invalidateQueries({ queryKey: ["orders"] });
    },
    onError: loi,
  });
  const themLog = useMutation({
    mutationFn: () => api.themNhatKy(oid, ghiChu.trim()),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      setGhiChu("");
      await qc.invalidateQueries({ queryKey: ["orders"] });
    },
    onError: loi,
  });
  const chuyenTT = useMutation({
    mutationFn: (status: string) => api.doiTrangThai(oid, status),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      await qc.invalidateQueries({ queryKey: ["orders"] });
    },
    onError: loi,
  });
  const phanCong = useMutation({
    mutationFn: (technician_id: number | null) => api.phanCong(oid, technician_id),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      await qc.invalidateQueries({ queryKey: ["orders"] });
    },
    onError: loi,
  });
  const lapHD = useMutation({
    mutationFn: () => api.lapHoaDon(oid),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      await qc.invalidateQueries({ queryKey: ["orders"] });
    },
    onError: loi,
  });
  const thuTien = useMutation({
    mutationFn: () => api.thuTien(ds.data!.hoa_don!.id, { amount: soTien, method: hinhThuc }),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      setDangThu(false);
      await qc.invalidateQueries({ queryKey: ["orders"] });
    },
    onError: loi,
  });

  if (!area("orders")) return <NoAccess />;
  if (ds.isPending) return <DangTai mat="Đang tải phiếu…" />;
  if (ds.isError)
    return (
      <div className="p-8 text-sm text-destructive">
        Không tải được phiếu. {ds.error instanceof ApiError ? ds.error.message : ""}
      </div>
    );

  const { phieu, hang_muc, nhat_ky, hoa_don, tiep_nhan } = ds.data;
  const buoc = N.trangThaiPhieu;
  const viTri = buoc.indexOf(phieu.status);
  const dichVu = L.dich_vu;
  const phuTung = L.phu_tung;
  const conPhaiThu = hoa_don ? hoa_don.total - hoa_don.paid : 0;

  return (
    <>
      <PageHeader
        eyebrow={
          <Link
            to="/repair-orders"
            className="inline-flex items-center gap-1 hover:text-foreground"
          >
            <ArrowLeft className="size-3" />
            Phiếu sửa chữa
          </Link>
        }
        title={`Phiếu #${phieu.id} · ${phieu.brand} ${phieu.model}`}
        desc={phieu.technical_notes ?? "Không có ghi chú kỹ thuật."}
        actions={
          <>
            <StatusPill s={phieu.status} />
            {N.chuyenTrangThai(phieu.status).map((tt) => (
              <Button
                key={tt}
                size="sm"
                variant={tt === "CANCELLED" ? "destructive" : "outline"}
                onClick={() => hopQuyen("order.progress") && chuyenTT.mutate(tt)}
              >
                → {N.trangThai(tt)}
              </Button>
            ))}
          </>
        }
      />

      <div className="border-b bg-card px-6 py-4 lg:px-8">
        <ol className="flex gap-1 overflow-x-auto">
          {buoc.map((s, i) => (
            <li key={s} className="flex min-w-[120px] flex-1 flex-col gap-1.5">
              <div
                className={cn(
                  "h-1 rounded-full",
                  viTri >= 0 && i <= viTri ? "bg-primary" : "bg-muted",
                )}
              />
              <span
                className={cn(
                  "text-[11px]",
                  i === viTri ? "font-semibold text-foreground" : "text-muted-foreground",
                )}
              >
                {N.trangThai(s)}
              </span>
            </li>
          ))}
        </ol>
      </div>

      <div className="grid gap-6 p-6 lg:p-8 xl:grid-cols-3">
        <div className="space-y-6 xl:col-span-2">
          <Panel
            title="Hạng mục sửa chữa"
            bodyClass="p-0"
            action={
              <span className="tabular text-xs text-muted-foreground">{hang_muc.length} mục</span>
            }
          >
            {hang_muc.length === 0 ? (
              <div className="p-4">
                <Empty title="Chưa có hạng mục" desc="Thêm dịch vụ hoặc phụ tùng vào phiếu." />
              </div>
            ) : (
              <table className="w-full text-sm">
                <thead className="text-left text-[11px] uppercase tracking-wider text-muted-foreground">
                  <tr className="border-b">
                    <th className="px-4 py-2 font-medium">Hạng mục</th>
                    <th className="px-4 py-2 text-right font-medium">SL</th>
                    <th className="px-4 py-2 text-right font-medium">Đơn giá</th>
                    <th className="px-4 py-2 text-right font-medium">Thành tiền</th>
                    <th className="w-10" />
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {hang_muc.map((m) => (
                    <tr key={m.id}>
                      <td className="px-4 py-2.5">
                        <div>{m.ten}</div>
                        <div className="text-[11px] text-muted-foreground">
                          {m.service_id ? "Dịch vụ" : "Phụ tùng"} · mã {m.service_id ?? m.part_id}
                        </div>
                      </td>
                      <td className="tabular px-4 text-right">{m.qty}</td>
                      <td className="tabular px-4 text-right">{vnd(m.unit_price)}</td>
                      <td className="tabular px-4 text-right font-medium">{vnd(m.thanh_tien)}</td>
                      <td className="px-2 text-right">
                        {can("order.item") && (
                          <button
                            onClick={() => hopQuyen("order.item") && goMuc.mutate(m.id)}
                            className="rounded p-1 text-muted-foreground hover:text-destructive"
                            aria-label="Bỏ hạng mục"
                          >
                            <Trash2 className="size-4" />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}

            {can("order.item") && (
              <div className="flex flex-wrap items-end gap-2 border-t bg-muted/30 px-4 py-3">
                <div className="space-y-1">
                  <label className="text-[11px] text-muted-foreground">Loại</label>
                  <Select
                    value={loai}
                    onValueChange={(v) => {
                      setLoai(v as "dich_vu" | "phu_tung");
                      setMa("");
                    }}
                  >
                    <SelectTrigger className="h-9 w-36">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="dich_vu">Dịch vụ</SelectItem>
                      <SelectItem value="phu_tung">Phụ tùng</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1">
                  <label className="text-[11px] text-muted-foreground">Mục</label>
                  <Select value={ma} onValueChange={setMa}>
                    <SelectTrigger className="h-9 w-64">
                      <SelectValue placeholder="Chọn…" />
                    </SelectTrigger>
                    <SelectContent>
                      {(loai === "dich_vu" ? dichVu : phuTung).map((x) => (
                        <SelectItem key={x.id} value={String(x.id)}>
                          {x.name} — {vnd(x.price)}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-1">
                  <label className="text-[11px] text-muted-foreground">SL</label>
                  <Input
                    type="number"
                    min={1}
                    max={9999}
                    value={sl}
                    onChange={(e) => setSl(Number(e.target.value))}
                    className="h-9 w-20"
                  />
                </div>
                <Button
                  size="sm"
                  className="h-9"
                  disabled={!ma || sl < 1 || themMuc.isPending}
                  onClick={() => hopQuyen("order.item") && themMuc.mutate()}
                >
                  <Plus className="size-4" />
                  Thêm
                </Button>
              </div>
            )}
            <dl className="space-y-1.5 border-t bg-muted/40 px-4 py-3 text-sm">
              <div className="flex justify-between border-t pt-1.5 font-semibold">
                <dt>Tổng phiếu (backend tính)</dt>
                <dd className="tabular">{vnd(phieu.tong)}</dd>
              </div>
              <p className="pt-1 text-[11px] text-muted-foreground">
                Thành tiền từng dòng và tổng phiếu đều do backend tính từ dữ liệu đã lưu — giao diện
                chỉ hiển thị.
              </p>
            </dl>
          </Panel>

          <Panel title="Nhật ký sửa chữa">
            <div className="flex gap-2">
              <Textarea
                value={ghiChu}
                onChange={(e) => setGhiChu(e.target.value)}
                placeholder="Ghi nhận phát hiện, đo đạc, khuyến nghị…"
                className="min-h-[60px]"
                disabled={!can("order.progress")}
              />
              <Button
                disabled={!ghiChu.trim() || themLog.isPending}
                onClick={() => hopQuyen("order.progress") && themLog.mutate()}
              >
                Lưu
              </Button>
            </div>
            {!can("order.progress") && (
              <p className="mt-2 text-[11px] text-muted-foreground">
                Chỉ Quản lý hoặc Kỹ thuật viên được ghi nhật ký.
              </p>
            )}
            <ol className="mt-4 space-y-4 border-l pl-4">
              {nhat_ky.length === 0 && (
                <li className="text-sm text-muted-foreground">Chưa có nhật ký.</li>
              )}
              {nhat_ky.map((n) => (
                <li key={n.id} className="relative">
                  <span className="absolute -left-[21px] top-1.5 size-2 rounded-full bg-primary" />
                  <div className="text-xs text-muted-foreground">
                    <span className="font-medium text-foreground">{n.full_name ?? "Hệ thống"}</span>{" "}
                    · {fmtTime(n.created_at)}
                  </div>
                  <p className="mt-0.5 text-sm">{n.note}</p>
                </li>
              ))}
            </ol>
          </Panel>
        </div>

        <div className="space-y-6">
          <Panel title="Xe & phân công">
            <div className="flex items-center justify-between">
              <Plate className="text-sm">{phieu.plate}</Plate>
              <span className="text-xs text-muted-foreground">{phieu.year ?? ""}</span>
            </div>
            <div className="mt-1 text-sm text-muted-foreground">
              {phieu.brand} {phieu.model}
            </div>
            <div className="mt-4 space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Kỹ thuật viên</label>
              <Select
                value={phieu.technician_id ? String(phieu.technician_id) : "none"}
                onValueChange={(v) =>
                  hopQuyen("order.assign") && phanCong.mutate(v === "none" ? null : Number(v))
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
              {!can("order.assign") && (
                <p className="text-[11px] text-muted-foreground">Chỉ xem — cần quyền phân công.</p>
              )}
            </div>
          </Panel>

          <Panel title="Khách hàng">
            <div className="flex items-center gap-2 font-medium">
              <User className="size-4 text-muted-foreground" />
              {phieu.khach}
            </div>
            {phieu.khach_phone && (
              <div className="mt-2 flex items-center gap-1.5 text-sm text-muted-foreground">
                <Phone className="size-3.5" />
                {phieu.khach_phone}
              </div>
            )}
          </Panel>

          <Panel
            title={
              <span className="flex items-center gap-2">
                <FileText className="size-4" />
                Biên bản tiếp nhận
              </span>
            }
          >
            {!tiep_nhan ? (
              <div>
                <Empty title="Chưa ghi biên bản" desc="Ghi biên bản khi tiếp nhận xe." />
                {can("order.create") && (
                  <div className="mt-3">
                    <Button variant="outline" size="sm" asChild>
                      <Link to="/inspection">Đi tới màn tiếp nhận</Link>
                    </Button>
                  </div>
                )}
              </div>
            ) : (
              <dl className="space-y-2 text-sm">
                <Row
                  k="ODO tiếp nhận"
                  v={
                    tiep_nhan.odometer_at_intake !== null
                      ? `${tiep_nhan.odometer_at_intake.toLocaleString("vi-VN")} km`
                      : "—"
                  }
                />
                <Row k="Nhiên liệu" v={N.nhienLieu(tiep_nhan.fuel_level)} />
                <Row k="Tình trạng ngoại thất" v={tiep_nhan.exterior_condition || "—"} />
                <Row k="Đồ đạc" v={tiep_nhan.accessories || "—"} />
                <Row k="Ghi chú" v={tiep_nhan.notes || "—"} />
                <Row
                  k="Người tiếp nhận"
                  v={`${tiep_nhan.nguoi_tiep_nhan ?? "—"} · ${fmtTime(tiep_nhan.created_at)}`}
                />
              </dl>
            )}
          </Panel>

          <Panel
            title={
              <span className="flex items-center gap-2">
                <Receipt className="size-4" />
                Hoá đơn
              </span>
            }
          >
            {!hoa_don ? (
              <div>
                <Empty
                  title="Chưa lập hoá đơn"
                  desc="Hoá đơn do backend tính tổng từ hạng mục phiếu."
                />
                {can("invoice.manage") && (
                  <Button
                    className="mt-3 w-full"
                    size="sm"
                    disabled={lapHD.isPending}
                    onClick={() => hopQuyen("invoice.manage") && lapHD.mutate()}
                  >
                    Lập hoá đơn cho phiếu này
                  </Button>
                )}
              </div>
            ) : (
              <div className="space-y-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="font-mono text-xs font-medium">HĐ #{hoa_don.id}</span>
                  <InvoicePill s={hoa_don.status} />
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Tổng tiền</span>
                  <span className="tabular font-semibold">{vnd(hoa_don.total)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Đã thu</span>
                  <span className="tabular">{vnd(hoa_don.paid)}</span>
                </div>
                <div className="flex justify-between border-t pt-1.5">
                  <span className="text-muted-foreground">Còn phải thu</span>
                  <span className="tabular font-semibold text-destructive">{vnd(conPhaiThu)}</span>
                </div>
                {can("payment.record") && hoa_don.status !== "PAID" && (
                  <Button
                    className="w-full"
                    size="sm"
                    onClick={() => {
                      setSoTien(conPhaiThu);
                      setDangThu(true);
                    }}
                  >
                    Ghi nhận thanh toán
                  </Button>
                )}
              </div>
            )}
          </Panel>
        </div>
      </div>

      <Dialog open={dangThu} onOpenChange={(o) => !o && setDangThu(false)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Ghi nhận thanh toán · HĐ #{hoa_don?.id}</DialogTitle>
          </DialogHeader>
          {hoa_don && (
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Còn phải thu</span>
                <span className="tabular font-semibold">{vnd(conPhaiThu)}</span>
              </div>
              <Input
                type="number"
                min={1}
                max={conPhaiThu}
                value={soTien}
                onChange={(e) => setSoTien(Number(e.target.value))}
              />
              <Select value={hinhThuc} onValueChange={(v) => setHinhThuc(v as PayMethod)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(meta?.hinh_thuc_thanh_toan ?? { CASH: "Tiền mặt" }).map(
                    ([k, v]) => (
                      <SelectItem key={k} value={k}>
                        {v}
                      </SelectItem>
                    ),
                  )}
                </SelectContent>
              </Select>
            </div>
          )}
          <DialogFooter>
            <Button
              disabled={soTien <= 0 || thuTien.isPending}
              onClick={() => hopQuyen("payment.record") && thuTien.mutate()}
            >
              Xác nhận thu tiền
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}

function Row({ k, v }: { k: string; v: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-3">
      <dt className="text-muted-foreground">{k}</dt>
      <dd className="text-right">{v}</dd>
    </div>
  );
}
