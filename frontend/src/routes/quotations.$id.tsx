import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { ArrowLeft, Ban, CheckCircle2, FileCheck, Plus, Send, Trash2, XCircle } from "lucide-react";
import { api, q, ApiError } from "@/services/api";
import { useLookups } from "@/services/lookups";
import { useNhan, useRole, fmtNgay, fmtTime, vnd } from "@/lib/rbac";
import {
  PageHeader,
  Panel,
  Plate,
  Pill,
  NoAccess,
  DangTai,
  Empty,
  type Tone,
} from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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

export const Route = createFileRoute("/quotations/$id")({
  head: () => ({
    meta: [
      { title: "Chi tiết báo giá — GarageTools AI" },
      {
        name: "description",
        content: "Hạng mục báo giá, gửi khách, duyệt và áp dụng vào phiếu sửa chữa.",
      },
      { property: "og:title", content: "Chi tiết báo giá — GarageTools AI" },
      { property: "og:description", content: "Chi tiết và điều phối một báo giá." },
    ],
  }),
  component: Detail,
});

const toneBaoGia: Record<string, Tone> = {
  DRAFT: "neutral",
  SENT: "info",
  APPROVED: "success",
  REJECTED: "danger",
  CANCELLED: "danger",
  EXPIRED: "warning",
};

function Detail() {
  const { id } = Route.useParams();
  const qid = Number(id);
  const { area, can } = useRole();
  const N = useNhan();
  const L = useLookups();
  const qc = useQueryClient();

  const ds = useQuery(q.quotation(qid));

  const [moThem, setMoThem] = useState(false);
  const [loai, setLoai] = useState<"dich_vu" | "phu_tung">("dich_vu");
  const [ma, setMa] = useState("");
  const [sl, setSl] = useState(1);

  const loi = (e: unknown) => toast.error(e instanceof ApiError ? e.message : "Thao tác thất bại.");

  const taiLai = async () => {
    await qc.invalidateQueries({ queryKey: ["quotations"] });
    await qc.invalidateQueries({ queryKey: ["orders"] });
    await qc.invalidateQueries({ queryKey: ["stock"] });
    await qc.invalidateQueries({ queryKey: ["parts"] });
    await qc.invalidateQueries({ queryKey: ["lookups"] });
    await qc.invalidateQueries({ queryKey: ["dashboard"] });
  };

  const themDong = useMutation({
    mutationFn: () => api.themDongBaoGia(qid, { loai, ma: Number(ma), qty: sl }),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      setMa("");
      setSl(1);
      setMoThem(false);
      await taiLai();
    },
    onError: loi,
  });

  const goDong = useMutation({
    mutationFn: (iid: number) => api.goDongBaoGia(qid, iid),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      await taiLai();
    },
    onError: loi,
  });

  const guiBaoGia = useMutation({
    mutationFn: () => api.guiBaoGia(qid),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      await taiLai();
    },
    onError: loi,
  });

  const huyBaoGia = useMutation({
    mutationFn: () => api.huyBaoGia(qid),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      await taiLai();
    },
    onError: loi,
  });

  const duyetBaoGia = useMutation({
    mutationFn: (quyet_dinh: "APPROVED" | "REJECTED") => api.duyetBaoGia(qid, quyet_dinh),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      await taiLai();
    },
    onError: loi,
  });

  const apDungBaoGia = useMutation({
    mutationFn: () => api.apDungBaoGia(qid),
    onSuccess: async (kq) => {
      // Lỗi 409 (đã áp dụng / thiếu tồn kho) cũng rơi vào `loi` → hiện message backend.
      toast.success(kq.thong_bao, {
        description: (
          <Link
            to="/repair-orders/$id"
            params={{ id: String(kq.phieu_id) }}
            className="font-medium text-primary underline-offset-2 hover:underline"
          >
            Mở phiếu #{kq.phieu_id}
          </Link>
        ),
      });
      await taiLai();
    },
    onError: loi,
  });

  if (!area("quotes")) return <NoAccess />;
  if (ds.isPending) return <DangTai mat="Đang tải báo giá…" />;
  if (ds.isError)
    return (
      <div className="p-8 text-sm text-destructive">
        Không tải được báo giá. {ds.error instanceof ApiError ? ds.error.message : "Lỗi kết nối."}
      </div>
    );

  const { bao_gia, hang_muc, co_sua, co_gui, co_duyet, co_huy, co_ap_dung } = ds.data;

  // Cờ co_* do backend tính theo trạng thái; quyền do giao diện lọc thêm.
  const sua = co_sua && can("quote.manage");
  const gui = co_gui && can("quote.manage");
  const huy = co_huy && can("quote.manage");
  const duyet = co_duyet && can("quote.approve");
  const apDung = co_ap_dung && can("quote.manage");
  const chiXem = !sua && !gui && !huy && !duyet && !apDung;

  return (
    <>
      <PageHeader
        eyebrow={
          <Link to="/quotations" className="inline-flex items-center gap-1 hover:text-foreground">
            <ArrowLeft className="size-3" />
            Báo giá
          </Link>
        }
        title={`Báo giá #${bao_gia.id} · ${bao_gia.plate}`}
        desc={`${bao_gia.brand} ${bao_gia.model} — khách ${bao_gia.khach}.`}
        actions={
          <>
            <Pill t={toneBaoGia[bao_gia.status] ?? "neutral"} dot>
              {N.trangThai(bao_gia.status)}
            </Pill>
            {bao_gia.applied_at && <Pill t="success">Đã áp dụng</Pill>}
            {sua && (
              <Button size="sm" variant="outline" onClick={() => setMoThem(true)}>
                <Plus className="size-4" />
                Sửa hạng mục
              </Button>
            )}
            {gui && (
              <Button
                size="sm"
                variant="outline"
                disabled={guiBaoGia.isPending}
                onClick={() => guiBaoGia.mutate()}
              >
                <Send className="size-4" />
                Gửi khách
              </Button>
            )}
            {duyet && (
              <>
                <Button
                  size="sm"
                  disabled={duyetBaoGia.isPending}
                  onClick={() => duyetBaoGia.mutate("APPROVED")}
                >
                  <CheckCircle2 className="size-4" />
                  Duyệt
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={duyetBaoGia.isPending}
                  onClick={() => duyetBaoGia.mutate("REJECTED")}
                >
                  <XCircle className="size-4" />
                  Từ chối
                </Button>
              </>
            )}
            {apDung && (
              <Button
                size="sm"
                disabled={apDungBaoGia.isPending}
                onClick={() => apDungBaoGia.mutate()}
              >
                <FileCheck className="size-4" />
                Áp dụng vào phiếu
              </Button>
            )}
            {huy && (
              <Button
                size="sm"
                variant="destructive"
                disabled={huyBaoGia.isPending}
                onClick={() => huyBaoGia.mutate()}
              >
                <Ban className="size-4" />
                Huỷ
              </Button>
            )}
          </>
        }
      />

      <div className="grid gap-6 p-6 lg:p-8 xl:grid-cols-3">
        <div className="space-y-6 xl:col-span-2">
          <Panel
            title="Hạng mục báo giá"
            bodyClass="p-0"
            action={
              <span className="tabular text-xs text-muted-foreground">{hang_muc.length} dòng</span>
            }
          >
            {hang_muc.length === 0 ? (
              <div className="p-4">
                <Empty
                  title="Chưa có hạng mục"
                  desc="Báo giá cần ít nhất một dòng thì mới gửi được cho khách."
                />
                {sua && (
                  <div className="mt-3 text-center">
                    <Button size="sm" variant="outline" onClick={() => setMoThem(true)}>
                      <Plus className="size-4" />
                      Thêm hạng mục
                    </Button>
                  </div>
                )}
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="text-left text-[11px] uppercase tracking-wider text-muted-foreground">
                    <tr className="border-b">
                      <th className="px-4 py-2 font-medium">Tên hạng mục</th>
                      <th className="px-4 py-2 font-medium">Loại</th>
                      <th className="px-4 py-2 text-right font-medium">Đơn giá</th>
                      <th className="px-4 py-2 text-right font-medium">Số lượng</th>
                      <th className="px-4 py-2 text-right font-medium">Thành tiền</th>
                      <th className="w-10" />
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {hang_muc.map((m) => (
                      <tr key={m.id} className="hover:bg-muted/40">
                        <td className="px-4 py-2.5">
                          <div>{m.ten || `Mã ${m.service_id ?? m.part_id}`}</div>
                          <div className="font-mono text-[11px] text-muted-foreground">
                            mã {m.service_id ?? m.part_id}
                          </div>
                        </td>
                        <td className="px-4 py-2.5 text-muted-foreground">
                          <Pill t={m.service_id ? "info" : "neutral"}>
                            {m.service_id ? "Dịch vụ" : "Phụ tùng"}
                          </Pill>
                        </td>
                        <td className="tabular px-4 py-2.5 text-right">{vnd(m.unit_price)}</td>
                        <td className="tabular px-4 py-2.5 text-right">{m.qty}</td>
                        <td className="tabular px-4 py-2.5 text-right font-medium">
                          {vnd(m.thanh_tien)}
                        </td>
                        <td className="px-2 py-2.5 text-right">
                          {sua && (
                            <button
                              disabled={goDong.isPending}
                              onClick={() => goDong.mutate(m.id)}
                              className="rounded p-1 text-muted-foreground hover:text-destructive disabled:opacity-50"
                              aria-label="Gỡ hạng mục khỏi báo giá"
                            >
                              <Trash2 className="size-4" />
                            </button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot>
                    <tr className="border-t bg-muted/40 text-sm">
                      <td className="px-4 py-2.5 font-semibold" colSpan={5}>
                        Tổng cộng (backend tính từ các dòng)
                      </td>
                      <td className="tabular px-4 py-2.5 text-right font-semibold">
                        {vnd(bao_gia.tong)}
                      </td>
                    </tr>
                  </tfoot>
                </table>
              </div>
            )}

            {chiXem && (
              <p className="border-t bg-muted/30 px-4 py-3 text-[11px] text-muted-foreground">
                Chế độ chỉ xem — bạn không có quyền thao tác trên báo giá này.
              </p>
            )}
          </Panel>
        </div>

        <div className="space-y-6">
          <Panel title="Thông tin báo giá">
            <dl className="space-y-2 text-sm">
              <Row k="Ngày tạo" v={fmtTime(bao_gia.created_at)} />
              <Row k="Hiệu lực đến" v={bao_gia.valid_until ? fmtNgay(bao_gia.valid_until) : "—"} />
              <Row
                k="Áp dụng lúc"
                v={bao_gia.applied_at ? fmtTime(bao_gia.applied_at) : "Chưa áp dụng"}
              />
              <Row k="Ghi chú" v={bao_gia.note ?? "—"} />
            </dl>
          </Panel>

          <Panel title="Phiếu sửa chữa">
            <div className="flex items-center justify-between gap-2">
              <Link
                to="/repair-orders/$id"
                params={{ id: String(bao_gia.repair_order_id) }}
                className="font-mono text-sm font-medium text-primary"
              >
                Phiếu #{bao_gia.repair_order_id}
              </Link>
              <Pill t={bao_gia.phieu_status === "CANCELLED" ? "danger" : "neutral"} dot>
                {N.trangThai(bao_gia.phieu_status)}
              </Pill>
            </div>
            <div className="mt-3 flex items-center justify-between gap-2">
              <Plate>{bao_gia.plate}</Plate>
              <span className="text-xs text-muted-foreground">
                {bao_gia.brand} {bao_gia.model}
              </span>
            </div>
            <div className="mt-3 text-sm text-muted-foreground">
              Khách: <span className="text-foreground">{bao_gia.khach}</span>
            </div>
          </Panel>
        </div>
      </div>

      <Dialog open={moThem} onOpenChange={(o) => !o && setMoThem(false)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Thêm hạng mục · báo giá #{bao_gia.id}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3 text-sm">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Loại</label>
              <Select
                value={loai}
                onValueChange={(v) => {
                  setLoai(v as "dich_vu" | "phu_tung");
                  setMa("");
                }}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="dich_vu">Dịch vụ</SelectItem>
                  <SelectItem value="phu_tung">Phụ tùng</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">
                {loai === "dich_vu" ? "Dịch vụ" : "Phụ tùng"}
              </label>
              <Select value={ma} onValueChange={setMa}>
                <SelectTrigger>
                  <SelectValue placeholder="Chọn theo mã…" />
                </SelectTrigger>
                <SelectContent>
                  {(loai === "dich_vu" ? L.dich_vu : L.phu_tung).map((x) => (
                    <SelectItem key={x.id} value={String(x.id)}>
                      {x.name} — {vnd(x.price)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <p className="text-[11px] text-muted-foreground">
                Giá chốt lấy từ danh mục tại thời điểm thêm — backend tự tính tổng.
              </p>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Số lượng</label>
              <Input
                type="number"
                min={1}
                max={9999}
                value={sl}
                onChange={(e) => setSl(Number(e.target.value))}
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              disabled={!ma || sl < 1 || themDong.isPending}
              onClick={() => themDong.mutate()}
            >
              <Plus className="size-4" />
              Thêm dòng
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
