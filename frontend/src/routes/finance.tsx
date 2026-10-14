import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Wallet, Search, ReceiptText } from "lucide-react";
import { api, q, ApiError } from "@/services/api";
import { useNhan, useRole, fmtTime, vnd, vndShort } from "@/lib/rbac";
import {
  PageHeader,
  Panel,
  Plate,
  InvoicePill,
  Stat,
  NoAccess,
  DangTai,
  Empty,
} from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Sheet, SheetContent, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { PayMethod } from "@/types";

export const Route = createFileRoute("/finance")({
  head: () => ({
    meta: [
      { title: "Hoá đơn & Thanh toán — GarageTools AI" },
      {
        name: "description",
        content: "Theo dõi hoá đơn, công nợ và ghi nhận thanh toán của khách hàng.",
      },
      { property: "og:title", content: "Hoá đơn & Thanh toán — GarageTools AI" },
      { property: "og:description", content: "Quản lý tài chính xưởng dịch vụ." },
    ],
  }),
  component: Finance,
});

function Finance() {
  const { area, can, meta } = useRole();
  const N = useNhan();
  const qc = useQueryClient();

  const [trangThai, setTrangThai] = useState("");
  const [tim, setTim] = useState("");
  const [timDe, setTimDe] = useState("");
  const [trang, setTrang] = useState(1);
  const [chon, setChon] = useState<number | null>(null);
  const [thu, setThu] = useState<{ id: number; conLai: number } | null>(null);
  const [soTien, setSoTien] = useState(0);
  const [hinhThuc, setHinhThuc] = useState<PayMethod>("CASH");
  const [loiGhiThu, setLoiGhiThu] = useState<string | null>(null);

  // Tìm kiếm gộp sau 300ms để không gọi API từng ký tự.
  useEffect(() => {
    const t = setTimeout(() => {
      setTimDe(tim);
      setTrang(1);
    }, 300);
    return () => clearTimeout(t);
  }, [tim]);

  const dash = useQuery(q.dashboard());
  const ds = useQuery(
    q.invoices({ trang, moi_trang: 20, trang_thai: trangThai || undefined, q: timDe || undefined }),
  );
  const chiTiet = useQuery({ ...q.invoice(chon ?? 0), enabled: chon !== null });

  const ghiThu = useMutation({
    mutationFn: () => api.thuTien(thu!.id, { amount: soTien, method: hinhThuc }),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      setThu(null);
      setLoiGhiThu(null);
      await qc.invalidateQueries({ queryKey: ["invoices"] });
      await qc.invalidateQueries({ queryKey: ["dashboard"] });
      if (chon !== null) await qc.invalidateQueries({ queryKey: ["invoices", chon] });
    },
    onError: (e) => {
      const m = e instanceof ApiError ? e.message : "Ghi thu tiền thất bại.";
      setLoiGhiThu(m);
      toast.error(m);
    },
  });

  const huyThu = useMutation({
    mutationFn: ({ iid, khoanId }: { iid: number; khoanId: number }) =>
      api.huyKhoanThu(iid, khoanId),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      await qc.invalidateQueries({ queryKey: ["invoices"] });
      await qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (e) => toast.error(e instanceof ApiError ? e.message : "Huỷ khoản thu thất bại."),
  });

  if (!area("finance")) return <NoAccess />;

  const kpi = dash.data?.kpi;
  const dsData = ds.data;
  const ctData = chiTiet.data;
  const hd = ctData?.hoa_don;

  return (
    <>
      <PageHeader
        eyebrow="Kho & Tài chính"
        title="Hoá đơn & Thanh toán"
        desc="Tổng tiền và tổng đã thu do backend tính — màn hình này chỉ theo dõi công nợ và ghi nhận thu tiền."
        actions={
          <span className="text-xs text-muted-foreground">
            Số liệu từ <code className="font-mono">GET /api/dashboard</code>
          </span>
        }
      />

      <div className="space-y-6 p-6 lg:p-8">
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <Stat
            label="Đã thu (toàn hệ thống)"
            value={vndShort(kpi?.da_thu ?? 0)}
            icon={<Wallet className="size-4" />}
          />
          <Stat
            label="Còn phải thu"
            value={<span className="text-destructive">{vndShort(kpi?.chua_thu ?? 0)}</span>}
            sub="Từ hoá đơn chưa tất toán"
          />
          <Stat
            label="Hoá đơn (theo bộ lọc)"
            value={ds.data?.tong ?? 0}
            icon={<ReceiptText className="size-4" />}
          />
          <Stat
            label="Chờ duyệt AI"
            value={kpi?.cho_duyet_ai ?? 0}
            sub="Kết quả AI chưa có giá trị nghiệp vụ"
          />
        </div>

        <Panel
          title="Danh sách hoá đơn"
          bodyClass="p-0"
          action={
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-2 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={tim}
                  onChange={(e) => setTim(e.target.value)}
                  placeholder="Tìm biển số, khách…"
                  className="h-8 w-40 pl-7 text-xs"
                />
              </div>
              <Select
                value={trangThai}
                onValueChange={(v) => {
                  setTrangThai(v);
                  setTrang(1);
                }}
              >
                <SelectTrigger className="h-8 w-36 text-xs">
                  <SelectValue placeholder="Mọi trạng thái" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Mọi trạng thái</SelectItem>
                  {(["UNPAID", "PARTIAL", "PAID"] as const).map((k) => (
                    <SelectItem key={k} value={k}>
                      {N.trangThai(k)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          }
        >
          {ds.isPending ? (
            <DangTai mat="Đang tải hoá đơn…" />
          ) : !dsData || dsData.dong.length === 0 ? (
            <div className="p-4">
              <Empty
                title="Không có hoá đơn nào khớp bộ lọc"
                desc="Thử bỏ bớt bộ lọc hoặc đổi từ khoá."
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 text-left text-[11px] uppercase tracking-wider text-muted-foreground">
                  <tr>
                    {[
                      "Mã HĐ",
                      "Khách hàng",
                      "Biển số",
                      "Ngày lập",
                      "Tổng tiền",
                      "Đã thu",
                      "Trạng thái",
                      "",
                    ].map((h) => (
                      <th key={h} className="px-4 py-2 font-medium">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {dsData.dong.map((i) => (
                    <tr
                      key={i.id}
                      className="cursor-pointer hover:bg-muted/40"
                      onClick={() => setChon(i.id)}
                    >
                      <td className="px-4 py-2.5 font-mono text-xs font-medium">HD-{i.id}</td>
                      <td className="px-4 py-2.5">{i.khach}</td>
                      <td className="px-4 py-2.5">
                        <Plate>{i.plate}</Plate>
                      </td>
                      <td className="tabular px-4 py-2.5 text-xs">{fmtTime(i.created_at)}</td>
                      <td className="tabular px-4 py-2.5 font-medium">{vnd(i.total)}</td>
                      <td className="tabular px-4 py-2.5">{vnd(i.paid)}</td>
                      <td className="px-4 py-2.5">
                        <InvoicePill s={i.status} />
                      </td>
                      <td className="px-4 py-2.5 text-right" onClick={(e) => e.stopPropagation()}>
                        {i.status !== "PAID" && can("payment.record") && (
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setThu({ id: i.id, conLai: i.total - i.paid });
                              setSoTien(i.total - i.paid);
                              setHinhThuc("CASH");
                            }}
                          >
                            Thu tiền
                          </Button>
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
              Trang {ds.data?.trang ?? 1}/{ds.data?.tong_trang ?? 1} · {ds.data?.tong ?? 0} hoá đơn
            </span>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                disabled={(ds.data?.trang ?? 1) <= 1}
                onClick={() => setTrang((t) => t - 1)}
              >
                Trước
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={(ds.data?.trang ?? 1) >= (ds.data?.tong_trang ?? 1)}
                onClick={() => setTrang((t) => t + 1)}
              >
                Sau
              </Button>
            </div>
          </div>
        </Panel>

        <p className="text-center text-[11px] text-muted-foreground">
          Quyền: <code className="font-mono">report.view</code> để xem danh sách,{" "}
          <code className="font-mono">payment.record</code> để ghi nhận thu tiền — backend kiểm tra
          từng lần gọi.
        </p>
      </div>

      {/* Drawer chi tiết hoá đơn + lịch sử thu. */}
      <Sheet open={chon !== null} onOpenChange={(o) => !o && setChon(null)}>
        <SheetContent side="right" className="w-full sm:max-w-lg">
          <SheetHeader>
            <SheetTitle>Hoá đơn HD-{chon}</SheetTitle>
          </SheetHeader>
          {chiTiet.isPending ? (
            <DangTai mat="Đang tải chi tiết…" />
          ) : hd && ctData ? (
            <div className="space-y-4 px-4 pb-4 text-sm">
              <div className="rounded-lg border p-3">
                <div className="grid grid-cols-2 gap-2">
                  <span className="text-muted-foreground">Khách hàng</span>
                  <span className="text-right">{hd.khach}</span>
                  <span className="text-muted-foreground">Biển số</span>
                  <span className="flex justify-end">
                    <Plate>{hd.plate}</Plate>
                  </span>
                  <span className="text-muted-foreground">Phiếu sửa chữa</span>
                  <span className="text-right">
                    <Link
                      to="/repair-orders/$id"
                      params={{ id: String(hd.repair_order_id) }}
                      className="text-primary"
                    >
                      #{hd.repair_order_id}
                    </Link>
                  </span>
                  <span className="text-muted-foreground">Ngày lập</span>
                  <span className="tabular text-right">{fmtTime(hd.created_at)}</span>
                  <span className="text-muted-foreground">Tổng tiền</span>
                  <span className="tabular text-right font-semibold">{vnd(hd.total)}</span>
                  <span className="text-muted-foreground">Đã thu</span>
                  <span className="tabular text-right">{vnd(hd.da_thu)}</span>
                  <span className="text-muted-foreground">Còn phải thu</span>
                  <span className="tabular text-right font-medium text-destructive">
                    {vnd(hd.con_phai_thu)}
                  </span>
                </div>
                <div className="mt-2 flex justify-end">
                  <InvoicePill s={hd.status} />
                </div>
              </div>

              <div>
                <div className="mb-2 flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                    Lịch sử thu tiền
                  </span>
                  {hd.con_phai_thu > 0 && can("payment.record") && (
                    <Button
                      size="sm"
                      onClick={() => setThu({ id: hd.id, conLai: hd.con_phai_thu })}
                    >
                      Ghi thu
                    </Button>
                  )}
                </div>
                {ctData.khoan_thu.length === 0 ? (
                  <p className="text-xs text-muted-foreground">Chưa ghi nhận khoản thu nào.</p>
                ) : (
                  <table className="w-full text-xs">
                    <thead className="text-left text-muted-foreground">
                      <tr>
                        <th className="py-1 font-medium">Thời gian</th>
                        <th className="py-1 font-medium">Hình thức</th>
                        <th className="py-1 text-right font-medium">Số tiền</th>
                        {can("payment.record") && <th className="py-1" />}
                      </tr>
                    </thead>
                    <tbody className="divide-y">
                      {ctData.khoan_thu.map((k) => (
                        <tr key={k.id}>
                          <td className="tabular py-1.5">{fmtTime(k.paid_at)}</td>
                          <td className="py-1.5">{N.hinhThuc(k.method)}</td>
                          <td className="tabular py-1.5 text-right">{vnd(k.amount)}</td>
                          {can("payment.record") && (
                            <td className="py-1.5 text-right">
                              <Button
                                size="sm"
                                variant="ghost"
                                className="h-6 px-2 text-xs text-destructive hover:text-destructive"
                                disabled={huyThu.isPending}
                                onClick={() => {
                                  if (
                                    !window.confirm(
                                      `Huỷ khoản thu ${vnd(k.amount)} lúc ${fmtTime(k.paid_at)}?`,
                                    )
                                  )
                                    return;
                                  huyThu.mutate({ iid: hd.id, khoanId: k.id });
                                }}
                              >
                                Huỷ thu
                              </Button>
                            </td>
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </div>
          ) : null}
        </SheetContent>
      </Sheet>

      {/* Dialog ghi nhận thu tiền. */}
      <Dialog
        open={!!thu}
        onOpenChange={(o) => {
          if (!o) {
            setThu(null);
            setLoiGhiThu(null);
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Ghi nhận thanh toán · HD-{thu?.id}</DialogTitle>
          </DialogHeader>
          {loiGhiThu && (
            <div className="rounded-md border border-destructive/25 bg-danger-soft px-3 py-2 text-xs text-destructive">
              {loiGhiThu}
            </div>
          )}
          {thu && (
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Còn phải thu</span>
                <span className="tabular font-semibold">{vnd(thu.conLai)}</span>
              </div>
              <Input
                type="number"
                min={1}
                max={thu.conLai}
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
              disabled={!thu || soTien <= 0 || ghiThu.isPending}
              onClick={() => ghiThu.mutate()}
            >
              Xác nhận thu tiền
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
