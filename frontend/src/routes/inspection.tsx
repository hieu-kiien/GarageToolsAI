import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { Plus, UserPlus, Car } from "lucide-react";
import { api, q, ApiError } from "@/services/api";
import { useLookups } from "@/services/lookups";
import { useNhan, useRole } from "@/lib/rbac";
import { PageHeader, Panel, NoAccess, DangTai, Empty, Pill } from "@/components/app/ui-kit";
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

export const Route = createFileRoute("/inspection")({
  head: () => ({
    meta: [
      { title: "Tiếp nhận xe — GarageTools AI" },
      { name: "description", content: "Tạo phiếu sửa chữa và ghi biên bản tiếp nhận xe tại quầy." },
      { property: "og:title", content: "Tiếp nhận xe — GarageTools AI" },
      { property: "og:description", content: "Màn hình tiếp nhận xe của lễ tân." },
    ],
  }),
  component: Inspection,
});

function Inspection() {
  const { area, can, meta } = useRole();
  const N = useNhan();
  const L = useLookups();
  const qc = useQueryClient();

  // Bước 1 — tạo phiếu mới.
  const [xeId, setXeId] = useState("");
  const [ktvId, setKtvId] = useState("none");
  const [ghiChuPhieu, setGhiChuPhieu] = useState("");

  // Bước 2 — biên bản tiếp nhận cho một phiếu.
  const [phieuId, setPhieuId] = useState("");
  const [odo, setOdo] = useState("");
  const [nhienLieu, setNhienLieu] = useState("UNKNOWN");
  const [ngoaiThat, setNgoaiThat] = useState("");
  const [doDac, setDoDac] = useState("");
  const [ghiChu, setGhiChu] = useState("");

  // Thêm nhanh khách hàng & xe tại quầy (ADR-9).
  const [moThemKhach, setMoThemKhach] = useState(false);
  const [tenKhach, setTenKhach] = useState("");
  const [sdtKhach, setSdtKhach] = useState("");
  const [diaChiKhach, setDiaChiKhach] = useState("");

  const [moThemXe, setMoThemXe] = useState(false);
  const [khachXeId, setKhachXeId] = useState("");
  const [bienXe, setBienXe] = useState("");
  const [hangXe, setHangXe] = useState("");
  const [dongXe, setDongXe] = useState("");
  const [namXe, setNamXe] = useState("");

  const phieuMoi = useQuery(q.orders({ moi_trang: 10, trang_thai: "RECEIVED" }));
  const dsKhach = useQuery({ ...q.customers({ moi_trang: 500 }), enabled: moThemXe });
  const loi = (e: unknown) => toast.error(e instanceof ApiError ? e.message : "Thao tác thất bại.");

  const taoPhieu = useMutation({
    mutationFn: () =>
      api.taoPhieu({
        vehicle_id: Number(xeId),
        technician_id: ktvId === "none" ? null : Number(ktvId),
        technical_notes: ghiChuPhieu.trim() || undefined,
      }),
    onSuccess: async (kq) => {
      toast.success(`${kq.thong_bao} (mã #${kq.id})`);
      setPhieuId(String(kq.id));
      setGhiChuPhieu("");
      await qc.invalidateQueries({ queryKey: ["orders"] });
      await qc.invalidateQueries({ queryKey: ["dashboard"] });
      await qc.invalidateQueries({ queryKey: ["lookups"] });
    },
    onError: loi,
  });

  const ghiBan = useMutation({
    mutationFn: () =>
      api.ghiTiepNhan(Number(phieuId), {
        odometer_at_intake: odo.trim() ? Number(odo) : null,
        fuel_level: nhienLieu,
        exterior_condition: ngoaiThat.trim() || undefined,
        accessories: doDac.trim() || undefined,
        notes: ghiChu.trim() || undefined,
      }),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      await qc.invalidateQueries({ queryKey: ["orders"] });
      await qc.invalidateQueries({ queryKey: ["vehicles"] });
      await qc.invalidateQueries({ queryKey: ["lookups"] });
    },
    onError: loi,
  });

  const taoKhachNhanh = useMutation({
    mutationFn: () =>
      api.taoKhach({
        name: tenKhach.trim(),
        phone: sdtKhach.trim(),
        address: diaChiKhach.trim() || null,
      }),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      setMoThemKhach(false);
      setTenKhach("");
      setSdtKhach("");
      setDiaChiKhach("");
      await qc.invalidateQueries({ queryKey: ["customers"] });
      await qc.invalidateQueries({ queryKey: ["lookups"] });
      if (can("vehicle.edit")) {
        setKhachXeId(String(kq.id));
        setMoThemXe(true);
      }
    },
    onError: loi,
  });

  const taoXeNhanh = useMutation({
    mutationFn: () =>
      api.taoXe({
        plate: bienXe.trim(),
        brand: hangXe.trim(),
        model: dongXe.trim(),
        customer_id: Number(khachXeId),
        year: namXe.trim() ? Number(namXe.trim()) : null,
        is_active: true,
      }),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      setMoThemXe(false);
      setBienXe("");
      setHangXe("");
      setDongXe("");
      setNamXe("");
      await qc.invalidateQueries({ queryKey: ["vehicles"] });
      await qc.invalidateQueries({ queryKey: ["lookups"] });
      setXeId(String(kq.id));
    },
    onError: loi,
  });

  if (!area("inspection")) return <NoAccess />;

  const danhSachPhieu = phieuMoi.data?.dong ?? [];
  const coTaoPhieu = can("order.create");

  return (
    <>
      <PageHeader
        eyebrow="Vận hành"
        title="Tiếp nhận xe"
        desc="Bước 1: tạo phiếu sửa chữa cho xe. Bước 2: ghi biên bản tiếp nhận (ODO, nhiên liệu, tình trạng, đồ đạc)."
        actions={
          <>
            {can("customer.edit") && (
              <Button variant="outline" size="sm" onClick={() => setMoThemKhach(true)}>
                <UserPlus className="size-4" />
                Thêm khách mới
              </Button>
            )}
            {can("vehicle.edit") && (
              <Button variant="outline" size="sm" onClick={() => setMoThemXe(true)}>
                <Plus className="size-4" />
                Thêm xe mới
              </Button>
            )}
            {phieuId && <Pill t="success">Phiếu #{phieuId} đã tạo — ghi biên bản ở bước 2</Pill>}
          </>
        }
      />
      <div className="grid gap-6 p-6 lg:p-8 xl:grid-cols-2">
        <Panel title="Bước 1 · Tạo phiếu sửa chữa">
          <div className="space-y-4">
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-muted-foreground">Xe *</label>
                {can("vehicle.edit") && (
                  <button
                    type="button"
                    onClick={() => setMoThemXe(true)}
                    className="text-xs font-medium text-primary hover:underline"
                  >
                    + Thêm xe mới
                  </button>
                )}
              </div>
              <Select value={xeId} onValueChange={setXeId} disabled={!coTaoPhieu}>
                <SelectTrigger>
                  <SelectValue placeholder="Chọn biển số…" />
                </SelectTrigger>
                <SelectContent>
                  {L.xe.map((x) => (
                    <SelectItem key={x.id} value={String(x.id)}>
                      {x.plate} — {x.brand} {x.model}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">
                Kỹ thuật viên (tuỳ chọn)
              </label>
              <Select value={ktvId} onValueChange={setKtvId} disabled={!coTaoPhieu}>
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
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Ghi chú tiếp nhận</label>
              <Textarea
                value={ghiChuPhieu}
                onChange={(e) => setGhiChuPhieu(e.target.value)}
                placeholder="Khách báo hư hỏng gì? Yêu cầu gì?"
                className="min-h-[70px]"
                disabled={!coTaoPhieu}
              />
            </div>
            <Button
              className="w-full"
              disabled={!coTaoPhieu || !xeId || taoPhieu.isPending}
              onClick={() => taoPhieu.mutate()}
            >
              Tạo phiếu sửa chữa
            </Button>
          </div>
        </Panel>

        <Panel title="Bước 2 · Biên bản tiếp nhận xe">
          {phieuMoi.isPending ? (
            <DangTai mat="Đang tải danh sách phiếu…" />
          ) : danhSachPhieu.length === 0 && !phieuId ? (
            <Empty title="Chưa có phiếu chờ tiếp nhận" desc="Hãy tạo phiếu ở bước 1." />
          ) : (
            <div className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">
                  Phiếu sửa chữa *
                </label>
                <Select value={phieuId} onValueChange={setPhieuId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Chọn phiếu…" />
                  </SelectTrigger>
                  <SelectContent>
                    {phieuId && !danhSachPhieu.some((p) => String(p.id) === phieuId) && (
                      <SelectItem value={phieuId}>Phiếu #{phieuId} (vừa tạo)</SelectItem>
                    )}
                    {danhSachPhieu.map((p) => (
                      <SelectItem key={p.id} value={String(p.id)}>
                        #{p.id} — {p.plate}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">ODO (km)</label>
                  <Input
                    type="number"
                    min={0}
                    max={2000000}
                    value={odo}
                    onChange={(e) => setOdo(e.target.value)}
                    placeholder="VD: 52300"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">
                    Mức nhiên liệu
                  </label>
                  <Select value={nhienLieu} onValueChange={setNhienLieu}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(meta?.muc_nhien_lieu ?? {}).map(([k, v]) => (
                        <SelectItem key={k} value={k}>
                          {v}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">
                  Tình trạng ngoại thất
                </label>
                <Textarea
                  value={ngoaiThat}
                  onChange={(e) => setNgoaiThat(e.target.value)}
                  placeholder="VD: trầy cản trước, móp gương phải…"
                  className="min-h-[60px]"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">
                  Đồ đạc khách để lại
                </label>
                <Input
                  value={doDac}
                  onChange={(e) => setDoDac(e.target.value)}
                  placeholder="VD: ô, giấy tờ xe, ghế trẻ em…"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Ghi chú khác</label>
                <Textarea
                  value={ghiChu}
                  onChange={(e) => setGhiChu(e.target.value)}
                  className="min-h-[50px]"
                />
              </div>
              <div className="flex items-center gap-2">
                <Button
                  className="flex-1"
                  disabled={!phieuId || ghiBan.isPending}
                  onClick={() => ghiBan.mutate()}
                >
                  Ghi biên bản tiếp nhận
                </Button>
                {phieuId && (
                  <Button variant="outline" asChild>
                    <Link to="/repair-orders/$id" params={{ id: String(phieuId) }}>
                      Xem phiếu
                    </Link>
                  </Button>
                )}
              </div>
              <p className="text-[11px] text-muted-foreground">
                Biên bản ghi một lần cho mỗi phiếu — backend chặn ghi trùng.
              </p>
            </div>
          )}
        </Panel>
      </div>
      <div className="px-6 pb-2 text-[11px] text-muted-foreground lg:px-8">
        Nhãn mức nhiên liệu lấy từ <code className="font-mono">GET /api/meta</code> — cùng nguồn với
        mọi màn hình.
      </div>

      <Dialog open={moThemKhach} onOpenChange={(o) => !o && setMoThemKhach(false)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <UserPlus className="size-4" />
              Thêm nhanh khách hàng
            </DialogTitle>
            <DialogDescription>
              Tạo khách hàng mới ngay tại quầy tiếp nhận — lưu xong sẽ chuyển sang thêm xe cho khách
              này.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 text-sm">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Họ và tên *</label>
              <Input
                value={tenKhach}
                onChange={(e) => setTenKhach(e.target.value)}
                placeholder="Nguyễn Văn A"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Số điện thoại *</label>
              <Input
                value={sdtKhach}
                onChange={(e) => setSdtKhach(e.target.value)}
                placeholder="0909123456"
                inputMode="tel"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Địa chỉ</label>
              <Input
                value={diaChiKhach}
                onChange={(e) => setDiaChiKhach(e.target.value)}
                placeholder="Quận 7, TP. Hồ Chí Minh"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setMoThemKhach(false)}>
              Huỷ
            </Button>
            <Button
              disabled={!tenKhach.trim() || !sdtKhach.trim() || taoKhachNhanh.isPending}
              onClick={() => taoKhachNhanh.mutate()}
            >
              Lưu khách hàng
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={moThemXe} onOpenChange={(o) => !o && setMoThemXe(false)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Car className="size-4" />
              Thêm nhanh phương tiện
            </DialogTitle>
            <DialogDescription>
              Lưu xong xe mới sẽ được tự động chọn ở Bước 1 để lập phiếu ngay.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 text-sm">
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-muted-foreground">Chủ xe *</label>
                {can("customer.edit") && (
                  <button
                    type="button"
                    onClick={() => {
                      setMoThemXe(false);
                      setMoThemKhach(true);
                    }}
                    className="text-xs font-medium text-primary hover:underline"
                  >
                    + Tạo khách mới
                  </button>
                )}
              </div>
              <Select value={khachXeId} onValueChange={setKhachXeId}>
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
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Biển số *</label>
                <Input
                  value={bienXe}
                  onChange={(e) => setBienXe(e.target.value)}
                  placeholder="30A-12345"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Năm sản xuất</label>
                <Input
                  type="number"
                  min={1900}
                  max={2100}
                  value={namXe}
                  onChange={(e) => setNamXe(e.target.value)}
                  placeholder="2022"
                />
              </div>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Hãng *</label>
                <Input
                  value={hangXe}
                  onChange={(e) => setHangXe(e.target.value)}
                  placeholder="Toyota"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Dòng xe *</label>
                <Input
                  value={dongXe}
                  onChange={(e) => setDongXe(e.target.value)}
                  placeholder="Vios"
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setMoThemXe(false)}>
              Huỷ
            </Button>
            <Button
              disabled={
                !bienXe.trim() ||
                !hangXe.trim() ||
                !dongXe.trim() ||
                !khachXeId ||
                taoXeNhanh.isPending
              }
              onClick={() => taoXeNhanh.mutate()}
            >
              Lưu & chọn xe
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
