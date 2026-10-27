import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Ban, Plus, ShieldCheck } from "lucide-react";
import { api, q, ApiError } from "@/services/api";
import { useNhan, useRole, fmtNgay } from "@/lib/rbac";
import {
  DangTai,
  Empty,
  NoAccess,
  PageHeader,
  Panel,
  Pill,
  Plate,
  StatusPill,
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
import type { ChiTietPhieu } from "@/types";

export const Route = createFileRoute("/warranties")({
  head: () => ({
    meta: [
      { title: "Bảo hành — GarageTools AI" },
      {
        name: "description",
        content: "Danh sách bảo hành dịch vụ và phụ tùng, lọc theo trạng thái.",
      },
      { property: "og:title", content: "Bảo hành — GarageTools AI" },
      { property: "og:description", content: "Lập và theo dõi bảo hành của xưởng dịch vụ." },
    ],
  }),
  component: List,
});

/** Tông nhãn theo `warranties.status` — tên tiếng Việt lấy từ `GET /api/meta`. */
const toneBaoHanh: Record<string, Tone> = {
  ACTIVE: "success",
  EXPIRED: "neutral",
  CLAIMED: "warning",
  CANCELLED: "danger",
};

const homNay = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(
    d.getDate(),
  ).padStart(2, "0")}`;
};

function List() {
  const { area, can, meta } = useRole();
  const N = useNhan();
  const qc = useQueryClient();

  const [loc, setLoc] = useState("all");
  const [tim, setTim] = useState("");
  const [tuKhoa, setTuKhoa] = useState("");
  const [trang, setTrang] = useState(1);

  // Biểu mẫu lập bảo hành.
  const [moForm, setMoForm] = useState(false);
  const [phieuId, setPhieuId] = useState("");
  const [phieuKq, setPhieuKq] = useState<ChiTietPhieu | null>(null);
  const [maHangMuc, setMaHangMuc] = useState("");
  const [thang, setThang] = useState("12");
  const [ngayBd, setNgayBd] = useState(homNay());
  const [ghiChu, setGhiChu] = useState("");
  // Xác nhận huỷ.
  const [huyId, setHuyId] = useState<number | null>(null);
  const [lyDoHuy, setLyDoHuy] = useState("");

  // Gõ xong 300ms mới gọi backend — tránh một request cho mỗi phím bấm.
  useEffect(() => {
    const h = setTimeout(() => {
      setTuKhoa(tim.trim());
      setTrang(1);
    }, 300);
    return () => clearTimeout(h);
  }, [tim]);

  const ds = useQuery(
    q.warranties({
      moi_trang: 20,
      trang,
      q: tuKhoa || undefined,
      trang_thai: loc === "all" ? undefined : loc,
    }),
  );

  // Chỉ phiếu COMPLETED mới có hạng mục cần bảo hành.
  const dsPhieuHoanThanh = useQuery({
    ...q.orders({ moi_trang: 100, trang_thai: "COMPLETED" }),
    enabled: moForm,
  });
  const oidKtra = phieuKq?.phieu.status === "COMPLETED" ? phieuKq.phieu.id : 0;
  const hangMuc = useQuery({
    queryKey: ["warranty-eligible", oidKtra],
    enabled: oidKtra > 0,
    queryFn: () => api.hangMucBaoHanh(oidKtra),
  });

  const loi = (e: unknown) => toast.error(e instanceof ApiError ? e.message : "Thao tác thất bại.");

  const ktra = useMutation({
    mutationFn: (id: number) => api.order(id),
    onSuccess: (kq) => {
      setPhieuKq(kq);
      setMaHangMuc("");
      if (kq.phieu.status !== "COMPLETED")
        toast.error(`Phiếu #${kq.phieu.id} đang ở trạng thái "${N.trangThai(kq.phieu.status)}".`);
    },
    onError: loi,
  });

  const tao = useMutation({
    mutationFn: () => {
      const hm = (hangMuc.data?.dong ?? []).find((x) => String(x.item_id) === maHangMuc);
      return api.taoBaoHanh({
        repair_order_id: Number(phieuId),
        months: Number(thang),
        start_date: ngayBd,
        service_id: hm?.service_id ?? null,
        part_id: hm?.part_id ?? null,
        note: ghiChu.trim() || null,
      });
    },
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      dongForm();
      await qc.invalidateQueries({ queryKey: ["warranties"] });
    },
    onError: loi,
  });

  const huy = useMutation({
    mutationFn: (id: number) => api.huyBaoHanh(id, { note: lyDoHuy.trim() || undefined }),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      dongHuy();
      await qc.invalidateQueries({ queryKey: ["warranties"] });
    },
    onError: (e) => {
      loi(e);
      dongHuy();
    },
  });

  const coQuanLy = can("warranty.manage");

  const datLaiForm = () => {
    setPhieuId("");
    setPhieuKq(null);
    setMaHangMuc("");
    setThang("12");
    setNgayBd(homNay());
    setGhiChu("");
  };
  const moTao = () => {
    datLaiForm();
    setMoForm(true);
  };
  const dongForm = () => {
    setMoForm(false);
    datLaiForm();
  };
  const dongHuy = () => {
    setHuyId(null);
    setLyDoHuy("");
  };

  const soThang = Number(thang);
  const coTheTao =
    phieuKq !== null &&
    phieuKq.phieu.status === "COMPLETED" &&
    maHangMuc !== "" &&
    ngayBd !== "" &&
    Number.isInteger(soThang) &&
    soThang >= 1 &&
    soThang <= 60;

  if (!area("warranty")) return <NoAccess />;
  if (ds.isPending) return <DangTai mat="Đang tải danh sách bảo hành…" />;
  if (!ds.data)
    return (
      <div className="p-8 text-sm text-destructive">
        Không tải được danh sách bảo hành.{" "}
        {ds.error instanceof ApiError ? ds.error.message : "Lỗi kết nối."}
      </div>
    );

  const { dong, tong, trang: trangHienTai, tong_trang } = ds.data;
  // Bộ lọc lấy đúng danh sách trạng thái backend công bố — không tự suy đoán.
  const dsTrangThai = Object.keys(meta?.trang_thai_bao_hanh ?? {});

  return (
    <>
      <PageHeader
        eyebrow="Danh mục"
        title="Bảo hành"
        desc={`${tong} bảo hành khớp bộ lọc — ngày hết hạn do backend tính từ ngày bắt đầu + số tháng.`}
        actions={
          coQuanLy && (
            <Button size="sm" onClick={moTao}>
              <Plus className="size-4" />
              Lập bảo hành
            </Button>
          )
        }
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
              placeholder="Lọc theo biển số, hạng mục hoặc mã bảo hành…"
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
              <Empty
                title="Không có bảo hành phù hợp"
                desc="Thử bỏ bộ lọc, đổi từ khoá hoặc lập bảo hành mới."
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 text-left text-[11px] uppercase tracking-wider text-muted-foreground">
                  <tr>
                    {[
                      "Mã BH",
                      "Phiếu",
                      "Biển số",
                      "Hạng mục",
                      "Phạm vi",
                      "Thời hạn",
                      "Từ ngày",
                      "Đến ngày",
                      "Trạng thái",
                      "Người lập",
                      "Ghi chú",
                      "Thao tác",
                    ].map((h) => (
                      <th key={h} className="px-4 py-2 font-medium">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {dong.map((w) => (
                    <tr key={w.id} className="hover:bg-muted/40">
                      <td className="px-4 py-2.5 font-mono text-xs font-medium">#{w.id}</td>
                      <td className="px-4 py-2.5">
                        <Link
                          to="/repair-orders/$id"
                          params={{ id: String(w.repair_order_id) }}
                          className="font-mono text-xs text-muted-foreground hover:text-primary"
                        >
                          #{w.repair_order_id}
                        </Link>
                      </td>
                      <td className="px-4 py-2.5">
                        <Plate>{w.plate}</Plate>
                      </td>
                      <td className="max-w-[220px] truncate px-4 py-2.5">{w.ten_hang_muc}</td>
                      <td className="px-4 py-2.5 text-xs text-muted-foreground">
                        {w.scope === "SERVICE" ? "Dịch vụ" : "Phụ tùng"}
                      </td>
                      <td className="tabular px-4 py-2.5">{w.months} tháng</td>
                      <td className="tabular px-4 py-2.5 text-xs">{fmtNgay(w.start_date)}</td>
                      <td className="tabular px-4 py-2.5 text-xs">{fmtNgay(w.end_date)}</td>
                      <td className="px-4 py-2.5">
                        <Pill t={toneBaoHanh[w.status] ?? "neutral"} dot>
                          {N.trangThai(w.status)}
                        </Pill>
                      </td>
                      <td className="px-4 py-2.5 text-muted-foreground">{w.nguoi_lap ?? "—"}</td>
                      <td className="max-w-[220px] truncate px-4 py-2.5 text-xs text-muted-foreground">
                        {w.note ?? "—"}
                      </td>
                      <td className="px-4 py-2.5">
                        {coQuanLy && w.status === "ACTIVE" && (
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-destructive hover:text-destructive"
                            onClick={() => setHuyId(w.id)}
                          >
                            <Ban className="size-3.5" />
                            Huỷ
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
              Trang {trangHienTai}/{tong_trang} · {tong} bảo hành
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
          if (!o) dongForm();
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ShieldCheck className="size-4" />
              Lập bảo hành
            </DialogTitle>
            <DialogDescription>
              Chỉ lập được cho phiếu đã hoàn thành và hạng mục chưa có bảo hành — ngày hết hạn do
              backend tính.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 text-sm">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">
                Phiếu sửa chữa (đã hoàn thành)
              </label>
              <Select
                value={phieuId}
                onValueChange={(v) => {
                  setPhieuId(v);
                  setPhieuKq(null);
                  setMaHangMuc("");
                  if (Number(v)) ktra.mutate(Number(v));
                }}
              >
                <SelectTrigger>
                  <SelectValue
                    placeholder={
                      dsPhieuHoanThanh.isPending
                        ? "Đang tải phiếu hoàn thành…"
                        : "Chọn phiếu đã hoàn thành…"
                    }
                  />
                </SelectTrigger>
                <SelectContent>
                  {(dsPhieuHoanThanh.data?.dong ?? []).map((p) => (
                    <SelectItem key={p.id} value={String(p.id)}>
                      #{p.id} — {p.plate} ({p.brand} {p.model})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {phieuKq && (
              <div className="flex items-center justify-between gap-2 rounded-md border bg-muted/40 px-3 py-2">
                <span className="flex min-w-0 items-center gap-2">
                  <Plate>{phieuKq.phieu.plate}</Plate>
                  <span className="truncate text-xs text-muted-foreground">
                    {phieuKq.phieu.brand} {phieuKq.phieu.model}
                  </span>
                </span>
                <StatusPill s={phieuKq.phieu.status} />
              </div>
            )}

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Hạng mục bảo hành</label>
              {phieuKq?.phieu.status !== "COMPLETED" ? (
                <p className="text-xs text-muted-foreground">
                  Chọn một phiếu đã hoàn thành ở trên để hiển thị danh sách hạng mục.
                </p>
              ) : hangMuc.isPending ? (
                <p className="text-xs text-muted-foreground">Đang tải hạng mục của phiếu…</p>
              ) : (hangMuc.data?.dong.length ?? 0) === 0 ? (
                <p className="text-xs text-destructive">
                  Phiếu không còn hạng mục nào chưa có bảo hành.
                </p>
              ) : (
                <Select value={maHangMuc} onValueChange={setMaHangMuc}>
                  <SelectTrigger>
                    <SelectValue placeholder="Chọn dịch vụ hoặc phụ tùng…" />
                  </SelectTrigger>
                  <SelectContent>
                    {(hangMuc.data?.dong ?? []).map((h) => (
                      <SelectItem key={h.item_id} value={String(h.item_id)}>
                        {h.ten_hang_muc} · {h.service_id ? "dịch vụ" : "phụ tùng"} #
                        {h.service_id ?? h.part_id}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              )}
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">
                  Thời hạn (tháng)
                </label>
                <Input
                  type="number"
                  min={1}
                  max={60}
                  value={thang}
                  onChange={(e) => setThang(e.target.value)}
                  placeholder="12"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Ngày bắt đầu</label>
                <Input type="date" value={ngayBd} onChange={(e) => setNgayBd(e.target.value)} />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Ghi chú</label>
              <Textarea
                value={ghiChu}
                onChange={(e) => setGhiChu(e.target.value)}
                placeholder="Việc đã làm, khuyến nghị của kỹ thuật viên…"
                className="min-h-[60px]"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={dongForm}>
              Đóng
            </Button>
            <Button disabled={!coTheTao || tao.isPending} onClick={() => tao.mutate()}>
              Tạo bảo hành
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog
        open={huyId !== null}
        onOpenChange={(o) => {
          if (!o) dongHuy();
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Huỷ bảo hành #{huyId}?</AlertDialogTitle>
            <AlertDialogDescription>
              Chỉ huỷ được bảo hành đang còn hiệu lực. Thao tác được ghi thẳng vào CSDL và không
              hoàn tác được.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <Textarea
            value={lyDoHuy}
            onChange={(e) => setLyDoHuy(e.target.value)}
            placeholder="Lý do huỷ (tuỳ chọn)…"
            className="min-h-[60px]"
          />
          <AlertDialogFooter>
            <AlertDialogCancel>Đóng</AlertDialogCancel>
            <AlertDialogAction
              disabled={huy.isPending}
              onClick={(e) => {
                e.preventDefault();
                if (huyId !== null) huy.mutate(huyId);
              }}
            >
              Xác nhận huỷ
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
