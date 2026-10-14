import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import {
  ArrowLeft,
  Plus,
  Phone,
  User,
  Receipt,
  Trash2,
  FileText,
  ClipboardCheck,
} from "lucide-react";
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
  Pill,
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
  const navigate = useNavigate();
  const { area, can, meta, user } = useRole();
  const N = useNhan();
  const L = useLookups();
  const qc = useQueryClient();

  const ds = useQuery(q.order(oid));
  const bg = useQuery({
    ...q.quotations({ q: String(oid), moi_trang: 100 }),
    enabled: can("quote.manage"),
  });
  const [ghiChu, setGhiChu] = useState("");
  const [loai, setLoai] = useState<"dich_vu" | "phu_tung">("dich_vu");
  const [ma, setMa] = useState<string>("");
  const [sl, setSl] = useState(1);
  const [soTien, setSoTien] = useState(0);
  const [hinhThuc, setHinhThuc] = useState<PayMethod>("CASH");
  const [dangThu, setDangThu] = useState(false);
  const [dangNghiemThu, setDangNghiemThu] = useState(false);
  const [ghiChuNghiemThu, setGhiChuNghiemThu] = useState("");
  const [dangXoa, setDangXoa] = useState(false);
  const [maXoa, setMaXoa] = useState("");

  const loi = (e: unknown) => toast.error(e instanceof ApiError ? e.message : "Thao tác thất bại.");

  const hopQuyen = (ten: string) => {
    if (!can(ten)) {
      toast.error("Bạn không có quyền thực hiện thao tác này.");
      return false;
    }
    return true;
  };

  const taiLaiKhoVaPhieu = async () => {
    await qc.invalidateQueries({ queryKey: ["orders"] });
    await qc.invalidateQueries({ queryKey: ["stock"] });
    await qc.invalidateQueries({ queryKey: ["parts"] });
    await qc.invalidateQueries({ queryKey: ["lookups"] });
    await qc.invalidateQueries({ queryKey: ["dashboard"] });
  };

  const themMuc = useMutation({
    mutationFn: () => api.themHangMuc(oid, { loai, ma: Number(ma), qty: sl }),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      setMa("");
      setSl(1);
      await taiLaiKhoVaPhieu();
    },
    onError: loi,
  });
  const goMuc = useMutation({
    mutationFn: (iid: number) => api.goHangMuc(oid, iid),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      await taiLaiKhoVaPhieu();
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
      await taiLaiKhoVaPhieu();
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
      await qc.invalidateQueries({ queryKey: ["invoices"] });
      await qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: loi,
  });
  const thuTien = useMutation({
    mutationFn: () => api.thuTien(ds.data!.hoa_don!.id, { amount: soTien, method: hinhThuc }),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      setDangThu(false);
      await qc.invalidateQueries({ queryKey: ["orders"] });
      await qc.invalidateQueries({ queryKey: ["invoices"] });
      await qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: loi,
  });
  const nghiemThu = useMutation({
    mutationFn: () => api.nghiemThu(oid, ghiChuNghiemThu.trim() || undefined),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      setDangNghiemThu(false);
      setGhiChuNghiemThu("");
      await qc.invalidateQueries({ queryKey: ["orders"] });
    },
    onError: loi,
  });
  const xoa = useMutation({
    mutationFn: () => api.xoaPhieu(oid),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      await qc.invalidateQueries({ queryKey: ["orders"] });
      await qc.invalidateQueries({ queryKey: ["dashboard"] });
      await qc.invalidateQueries({ queryKey: ["lookups"] });
      navigate({ to: "/repair-orders" });
    },
    onError: loi,
  });
  const taoBG = useMutation({
    mutationFn: () => api.taoBaoGia({ repair_order_id: oid }),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      await qc.invalidateQueries({ queryKey: ["quotations"] });
      navigate({ to: "/quotations/$id", params: { id: String(kq.id) } });
    },
    onError: loi,
  });
  const apDung = useMutation({
    mutationFn: (bgId: number) => api.apDungBaoGia(bgId),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      await taiLaiKhoVaPhieu();
      await qc.invalidateQueries({ queryKey: ["quotations"] });
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
  const dsBaoGia = bg.data?.dong.filter((b) => b.repair_order_id === oid) ?? [];
  const daApDungBaoGia = dsBaoGia.some((b) => b.applied_at !== null);

  const ketThuc = phieu.status === "COMPLETED" || phieu.status === "CANCELLED";
  const ktvDuocPhep = user?.role !== "TECHNICIAN" || phieu.technician_id === user.id;
  const coSuaHangMuc = can("order.item") && ktvDuocPhep && !ketThuc && !hoa_don;
  const coChuyenTT = can("order.progress") && ktvDuocPhep;
  const coPhanCong = can("order.assign") && !ketThuc;

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
            {can("quote.manage") && dsBaoGia.length > 0 && (
              <Pill t={daApDungBaoGia ? "success" : "info"}>
                {daApDungBaoGia ? "Đã áp dụng báo giá" : `${dsBaoGia.length} báo giá`}
              </Pill>
            )}
            {phieu.acceptance_at && <Pill t="success">Đã nghiệm thu</Pill>}
            <StatusPill s={phieu.status} />
            {coChuyenTT &&
              N.chuyenTrangThai(phieu.status).map((tt) => (
                <Button
                  key={tt}
                  size="sm"
                  variant={tt === "CANCELLED" ? "destructive" : "outline"}
                  onClick={() => hopQuyen("order.progress") && chuyenTT.mutate(tt)}
                >
                  → {N.trangThai(tt)}
                </Button>
              ))}
            {phieu.status === "COMPLETED" && !phieu.acceptance_at && can("order.accept") && (
              <Button size="sm" onClick={() => setDangNghiemThu(true)}>
                <ClipboardCheck className="size-4" />
                Nghiệm thu (khách ký nhận)
              </Button>
            )}
            {can("order.create") && (
              <Button
                size="sm"
                variant="destructive"
                onClick={() => {
                  setMaXoa("");
                  setDangXoa(true);
                }}
              >
                <Trash2 className="size-4" />
                Xoá phiếu
              </Button>
            )}
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
                        {coSuaHangMuc && (
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

            {coSuaHangMuc ? (
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
            ) : (
              can("order.item") && (
                <p className="border-t bg-muted/20 px-4 py-2 text-[11px] text-muted-foreground">
                  {hoa_don
                    ? "Không thể sửa hạng mục khi phiếu đã lập hoá đơn."
                    : ketThuc
                      ? "Phiếu đã hoàn thành hoặc đã huỷ — không thể thêm/gỡ hạng mục."
                      : "Chỉ kỹ thuật viên được phân công phụ trách phiếu mới được sửa hạng mục."}
                </p>
              )
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

          <Panel
            title={
              <span className="flex items-center gap-2">
                <FileText className="size-4" />
                Báo giá
              </span>
            }
            action={
              can("quote.manage") &&
              !ketThuc && (
                <Button
                  size="sm"
                  variant="outline"
                  disabled={taoBG.isPending}
                  onClick={() => hopQuyen("quote.manage") && taoBG.mutate()}
                >
                  <Plus className="size-4" />
                  Tạo báo giá nháp
                </Button>
              )
            }
          >
            {!can("quote.manage") ? (
              <p className="text-sm text-muted-foreground">
                Cần quyền quản lý báo giá để xem danh sách báo giá của phiếu.
              </p>
            ) : bg.isError ? (
              <p className="text-sm text-destructive">Không tải được báo giá của phiếu.</p>
            ) : bg.isPending ? (
              <p className="text-sm text-muted-foreground">Đang tải báo giá…</p>
            ) : dsBaoGia.length === 0 ? (
              <Empty
                title="Chưa có báo giá"
                desc="Tạo báo giá nháp từ phiếu này, thêm hạng mục rồi gửi khách duyệt."
              />
            ) : (
              <ul className="space-y-2">
                {dsBaoGia.map((b) => (
                  <li
                    key={b.id}
                    className="flex flex-wrap items-center gap-2 rounded-md border px-3 py-2"
                  >
                    <Link
                      to="/quotations/$id"
                      params={{ id: String(b.id) }}
                      className="font-mono text-xs font-semibold hover:underline"
                    >
                      BG #{b.id}
                    </Link>
                    <StatusPill s={b.status} />
                    {b.applied_at && <Pill t="success">Đã áp dụng</Pill>}
                    <span className="tabular ml-auto text-sm font-medium">{vnd(b.total)}</span>
                    {b.status === "APPROVED" &&
                      !b.applied_at &&
                      can("quote.manage") &&
                      !ketThuc &&
                      !hoa_don && (
                        <Button
                          size="sm"
                          variant="outline"
                          disabled={apDung.isPending}
                          onClick={() => hopQuyen("quote.manage") && apDung.mutate(b.id)}
                        >
                          Áp dụng
                        </Button>
                      )}
                  </li>
                ))}
              </ul>
            )}
          </Panel>

          <Panel title="Nhật ký sửa chữa">
            <div className="flex gap-2">
              <Textarea
                value={ghiChu}
                onChange={(e) => setGhiChu(e.target.value)}
                placeholder="Ghi nhận phát hiện, đo đạc, khuyến nghị…"
                className="min-h-[60px]"
                disabled={!coChuyenTT}
              />
              <Button
                disabled={!coChuyenTT || !ghiChu.trim() || themLog.isPending}
                onClick={() => hopQuyen("order.progress") && themLog.mutate()}
              >
                Lưu
              </Button>
            </div>
            {!coChuyenTT && (
              <p className="mt-2 text-[11px] text-muted-foreground">
                Chỉ Quản lý hoặc Kỹ thuật viên được phân công phụ trách phiếu mới được ghi nhật ký.
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
                disabled={!coPhanCong}
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
              {!coPhanCong && (
                <p className="text-[11px] text-muted-foreground">
                  {ketThuc
                    ? "Phiếu đã hoàn thành hoặc đã huỷ — không thể đổi phân công."
                    : "Chỉ xem — cần quyền phân công."}
                </p>
              )}
            </div>
            {phieu.acceptance_at && (
              <div className="mt-4 rounded-md border bg-muted/40 p-2.5 text-xs">
                <div className="font-medium text-foreground">
                  Đã nghiệm thu lúc {fmtTime(phieu.acceptance_at)}
                </div>
                {phieu.acceptance_note && (
                  <p className="mt-1 text-muted-foreground">{phieu.acceptance_note}</p>
                )}
              </div>
            )}
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
                {can("order.create") && !ketThuc && (
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
                {can("invoice.manage") && phieu.status !== "CANCELLED" && phieu.tong > 0 && (
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

      <Dialog open={dangNghiemThu} onOpenChange={(o) => !o && setDangNghiemThu(false)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Nghiệm thu · Phiếu #{phieu.id}</DialogTitle>
          </DialogHeader>
          <div className="space-y-2 text-sm">
            <p className="text-muted-foreground">
              Khách hàng ký nhận xe sau khi sửa xong. Ghi chú nghiệm thu là tuỳ chọn.
            </p>
            <Textarea
              value={ghiChuNghiemThu}
              onChange={(e) => setGhiChuNghiemThu(e.target.value)}
              placeholder="Ghi chú nghiệm thu (tình trạng giao xe, đồ đạc còn lại…)"
              className="min-h-[80px]"
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDangNghiemThu(false)}>
              Huỷ
            </Button>
            <Button
              disabled={nghiemThu.isPending}
              onClick={() => hopQuyen("order.accept") && nghiemThu.mutate()}
            >
              Xác nhận nghiệm thu
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={dangXoa} onOpenChange={(o) => !o && setDangXoa(false)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Xoá phiếu #{phieu.id}</DialogTitle>
          </DialogHeader>
          <div className="space-y-2 text-sm">
            <p className="text-muted-foreground">
              Chỉ xoá được phiếu trống (chưa phát sinh hạng mục, hoá đơn, biên bản, báo giá). Hành
              động này không thể hoàn tác — nhập <b>#{phieu.id}</b> để xác nhận.
            </p>
            <Input
              value={maXoa}
              onChange={(e) => setMaXoa(e.target.value)}
              placeholder={`#${phieu.id}`}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDangXoa(false)}>
              Huỷ
            </Button>
            <Button
              variant="destructive"
              disabled={maXoa.trim() !== `#${phieu.id}` || xoa.isPending}
              onClick={() => hopQuyen("order.create") && xoa.mutate()}
            >
              Xoá vĩnh viễn
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
