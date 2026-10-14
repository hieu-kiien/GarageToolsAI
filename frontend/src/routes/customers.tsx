import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Car, Pencil, Plus, Trash2, Users } from "lucide-react";
import { api, q, ApiError } from "@/services/api";
import { useRole, fmtNgay } from "@/lib/rbac";
import { DangTai, Empty, NoAccess, PageHeader, Panel, Pill, Plate } from "@/components/app/ui-kit";
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
import type { KhachHangDong, PhuongTienDong } from "@/types";

export const Route = createFileRoute("/customers")({
  head: () => ({
    meta: [
      { title: "Khách hàng & Xe — GarageTools AI" },
      {
        name: "description",
        content: "Danh mục khách hàng và phương tiện của xưởng dịch vụ.",
      },
      { property: "og:title", content: "Khách hàng & Xe — GarageTools AI" },
      { property: "og:description", content: "Quản lý khách hàng và phương tiện." },
    ],
  }),
  component: KhachVaXe,
});

function KhachVaXe() {
  const { area } = useRole();
  const [tab, setTab] = useState<"khach" | "xe">("khach");

  if (!area("customers")) return <NoAccess />;

  return (
    <>
      <PageHeader
        eyebrow="Danh mục"
        title="Khách hàng & Xe"
        desc="Thông tin liên hệ của khách và các phương tiện họ đang sở hữu — thao tác ghi đều phải quyền `customer.edit` / `vehicle.edit`."
        actions={
          <div className="flex gap-1 rounded-md border bg-muted/40 p-1">
            {(["khach", "xe"] as const).map((k) => (
              <button
                key={k}
                onClick={() => setTab(k)}
                className={cn(
                  "rounded-md px-3 py-1.5 text-xs font-medium",
                  tab === k
                    ? "bg-background text-foreground shadow-sm"
                    : "text-muted-foreground hover:text-foreground",
                )}
              >
                {k === "khach" ? "Khách hàng" : "Phương tiện"}
              </button>
            ))}
          </div>
        }
      />
      <div className="p-6 lg:p-8">{tab === "khach" ? <BangKhach /> : <BangXe />}</div>
    </>
  );
}

function BangKhach() {
  const { can } = useRole();
  const qc = useQueryClient();

  const [tim, setTim] = useState("");
  const [tuKhoa, setTuKhoa] = useState("");
  const [trang, setTrang] = useState(1);

  const [moForm, setMoForm] = useState(false);
  const [dangSua, setDangSua] = useState<KhachHangDong | null>(null);
  const [ten, setTen] = useState("");
  const [sdt, setSdt] = useState("");
  const [email, setEmail] = useState("");
  const [diaChi, setDiaChi] = useState("");
  const [xoaId, setXoaId] = useState<number | null>(null);

  // Gõ xong 300ms mới gọi backend — tránh một request cho mỗi phím bấm.
  useEffect(() => {
    const h = setTimeout(() => {
      setTuKhoa(tim.trim());
      setTrang(1);
    }, 300);
    return () => clearTimeout(h);
  }, [tim]);

  const ds = useQuery(q.customers({ moi_trang: 20, trang, q: tuKhoa || undefined }));

  const loi = (e: unknown) => toast.error(e instanceof ApiError ? e.message : "Thao tác thất bại.");

  const luu = useMutation({
    mutationFn: () => {
      const body = {
        name: ten.trim(),
        phone: sdt.trim(),
        email: email.trim() || null,
        address: diaChi.trim() || null,
      };
      return dangSua ? api.suaKhach(dangSua.id, body) : api.taoKhach(body);
    },
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      setMoForm(false);
      await qc.invalidateQueries({ queryKey: ["customers"] });
      await qc.invalidateQueries({ queryKey: ["vehicles"] });
      await qc.invalidateQueries({ queryKey: ["lookups"] });
    },
    onError: loi,
  });

  const xoa = useMutation({
    mutationFn: (id: number) => api.xoaKhach(id),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      setXoaId(null);
      await qc.invalidateQueries({ queryKey: ["customers"] });
      await qc.invalidateQueries({ queryKey: ["vehicles"] });
      await qc.invalidateQueries({ queryKey: ["lookups"] });
    },
    onError: (e) => {
      loi(e);
      setXoaId(null);
    },
  });

  const coSua = can("customer.edit");

  const moTao = () => {
    setDangSua(null);
    setTen("");
    setSdt("");
    setEmail("");
    setDiaChi("");
    setMoForm(true);
  };

  const moSua = (k: KhachHangDong) => {
    setDangSua(k);
    setTen(k.name);
    setSdt(k.phone);
    setEmail(k.email ?? "");
    setDiaChi(k.address ?? "");
    setMoForm(true);
  };

  if (ds.isPending) return <DangTai mat="Đang tải danh sách khách hàng…" />;
  if (!ds.data)
    return (
      <div className="p-8 text-sm text-destructive">
        Không tải được danh sách khách hàng.{" "}
        {ds.error instanceof ApiError ? ds.error.message : "Lỗi kết nối."}
      </div>
    );

  const { dong, tong, trang: trangHienTai, tong_trang } = ds.data;

  return (
    <>
      <Panel
        title="Khách hàng"
        bodyClass="p-0"
        action={
          coSua && (
            <Button size="sm" onClick={moTao}>
              <Plus className="size-4" />
              Thêm khách hàng
            </Button>
          )
        }
      >
        <div className="flex items-center border-b p-3">
          <Input
            value={tim}
            onChange={(e) => setTim(e.target.value)}
            placeholder="Lọc theo tên, số điện thoại, email…"
            className="h-8 md:ml-auto md:w-72"
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
            <Empty title="Chưa có khách hàng" desc="Thêm khách hàng đầu tiên từ nút Thêm mới." />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 text-left text-[11px] uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="px-4 py-2 font-medium">Mã</th>
                  <th className="px-4 py-2 font-medium">Họ tên</th>
                  <th className="px-4 py-2 font-medium">Số điện thoại</th>
                  <th className="px-4 py-2 font-medium">Email</th>
                  <th className="px-4 py-2 font-medium">Địa chỉ</th>
                  <th className="px-4 py-2 font-medium">Ngày tạo</th>
                  {coSua && <th className="px-4 py-2 text-right font-medium">Thao tác</th>}
                </tr>
              </thead>
              <tbody className="divide-y">
                {dong.map((k) => (
                  <tr key={k.id} className="hover:bg-muted/40">
                    <td className="tabular px-4 py-2.5 text-xs text-muted-foreground">#{k.id}</td>
                    <td className="px-4 py-2.5 font-medium">{k.name}</td>
                    <td className="tabular px-4 py-2.5">{k.phone}</td>
                    <td className="px-4 py-2.5 text-muted-foreground">{k.email ?? "—"}</td>
                    <td className="max-w-[220px] truncate px-4 py-2.5 text-xs text-muted-foreground">
                      {k.address ?? "—"}
                    </td>
                    <td className="tabular px-4 py-2.5 text-xs">{fmtNgay(k.created_at)}</td>
                    {coSua && (
                      <td className="px-4 py-2.5 text-right">
                        <div className="flex justify-end gap-1">
                          <Button size="sm" variant="ghost" onClick={() => moSua(k)}>
                            <Pencil className="size-3.5" />
                            Sửa
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-destructive hover:text-destructive"
                            onClick={() => setXoaId(k.id)}
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
            Trang {trangHienTai}/{tong_trang} · {tong} khách hàng
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

      <Dialog
        open={moForm}
        onOpenChange={(o) => {
          if (!o) setMoForm(false);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Users className="size-4" />
              {dangSua ? `Sửa khách hàng #${dangSua.id}` : "Thêm khách hàng"}
            </DialogTitle>
            <DialogDescription>
              Số điện thoại phải duy nhất trong hệ thống — backend kiểm tra khi lưu.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 text-sm">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Họ và tên</label>
              <Input
                value={ten}
                onChange={(e) => setTen(e.target.value)}
                placeholder="Nguyễn Văn A"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Số điện thoại</label>
              <Input
                value={sdt}
                onChange={(e) => setSdt(e.target.value)}
                placeholder="0909123456"
                inputMode="tel"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Email</label>
              <Input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="khachhang@email.com"
              />
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Địa chỉ</label>
              <Input
                value={diaChi}
                onChange={(e) => setDiaChi(e.target.value)}
                placeholder="Quận 7, TP. Hồ Chí Minh"
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setMoForm(false)}>
              Huỷ
            </Button>
            <Button
              disabled={!ten.trim() || !sdt.trim() || luu.isPending}
              onClick={() => luu.mutate()}
            >
              {dangSua ? "Lưu thay đổi" : "Thêm khách hàng"}
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
            <AlertDialogTitle>Xoá khách hàng #{xoaId}?</AlertDialogTitle>
            <AlertDialogDescription>
              Khách đã phát sinh xe hoặc phiếu thì backend từ chối xoá — chỉ hiển thị thông báo lỗi.
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
              Xoá khách hàng
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

function BangXe() {
  const { can } = useRole();
  const qc = useQueryClient();

  const [tim, setTim] = useState("");
  const [tuKhoa, setTuKhoa] = useState("");
  const [trang, setTrang] = useState(1);

  const [moForm, setMoForm] = useState(false);
  const [dangSua, setDangSua] = useState<PhuongTienDong | null>(null);
  const [bien, setBien] = useState("");
  const [hang, setHang] = useState("");
  const [dongXe, setDongXe] = useState("");
  const [nam, setNam] = useState("");
  const [vin, setVin] = useState("");
  const [mau, setMau] = useState("");
  const [soKm, setSoKm] = useState("");
  const [khachId, setKhachId] = useState("");
  const [hoatDong, setHoatDong] = useState(true);
  const [xoaId, setXoaId] = useState<number | null>(null);

  // Gõ xong 300ms mới gọi backend — tránh một request cho mỗi phím bấm.
  useEffect(() => {
    const h = setTimeout(() => {
      setTuKhoa(tim.trim());
      setTrang(1);
    }, 300);
    return () => clearTimeout(h);
  }, [tim]);

  const ds = useQuery(q.vehicles({ moi_trang: 20, trang, q: tuKhoa || undefined }));
  const dsKhach = useQuery({ ...q.customers({ moi_trang: 500 }), enabled: moForm });

  const loi = (e: unknown) => toast.error(e instanceof ApiError ? e.message : "Thao tác thất bại.");

  const luu = useMutation({
    mutationFn: () => {
      const body = {
        plate: bien.trim(),
        brand: hang.trim(),
        model: dongXe.trim(),
        customer_id: Number(khachId),
        year: nam.trim() ? Number(nam.trim()) : null,
        vin: vin.trim() || null,
        color: mau.trim() || null,
        odometer: soKm.trim() ? Number(soKm.trim()) : null,
        is_active: hoatDong,
      };
      return dangSua ? api.suaXe(dangSua.id, body) : api.taoXe(body);
    },
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      setMoForm(false);
      await qc.invalidateQueries({ queryKey: ["vehicles"] });
      await qc.invalidateQueries({ queryKey: ["lookups"] });
      await qc.invalidateQueries({ queryKey: ["appointments"] });
    },
    onError: loi,
  });

  const xoa = useMutation({
    mutationFn: (id: number) => api.xoaXe(id),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      setXoaId(null);
      await qc.invalidateQueries({ queryKey: ["vehicles"] });
      await qc.invalidateQueries({ queryKey: ["lookups"] });
    },
    onError: (e) => {
      loi(e);
      setXoaId(null);
    },
  });

  const coSua = can("vehicle.edit");

  const moTao = () => {
    setDangSua(null);
    setBien("");
    setHang("");
    setDongXe("");
    setNam("");
    setVin("");
    setMau("");
    setSoKm("");
    setKhachId("");
    setHoatDong(true);
    setMoForm(true);
  };

  const moSua = (x: PhuongTienDong) => {
    setDangSua(x);
    setBien(x.plate);
    setHang(x.brand);
    setDongXe(x.model);
    setNam(x.year === null ? "" : String(x.year));
    setVin(x.vin ?? "");
    setMau(x.color ?? "");
    setSoKm(x.odometer === null ? "" : String(x.odometer));
    setKhachId(String(x.customer_id));
    setHoatDong(!!x.is_active);
    setMoForm(true);
  };

  const namSo = Number(nam);
  const namHopLe = !nam.trim() || (Number.isInteger(namSo) && namSo >= 1900 && namSo <= 2100);
  const soKmSo = Number(soKm);
  const soKmHopLe =
    !soKm.trim() || (Number.isInteger(soKmSo) && soKmSo >= 0 && soKmSo <= 2_000_000);

  if (ds.isPending) return <DangTai mat="Đang tải danh sách phương tiện…" />;
  if (!ds.data)
    return (
      <div className="p-8 text-sm text-destructive">
        Không tải được danh sách phương tiện.{" "}
        {ds.error instanceof ApiError ? ds.error.message : "Lỗi kết nối."}
      </div>
    );

  const { dong, tong, trang: trangHienTai, tong_trang } = ds.data;

  return (
    <>
      <Panel
        title="Phương tiện"
        bodyClass="p-0"
        action={
          coSua && (
            <Button size="sm" onClick={moTao}>
              <Plus className="size-4" />
              Thêm xe
            </Button>
          )
        }
      >
        <div className="flex items-center border-b p-3">
          <Input
            value={tim}
            onChange={(e) => setTim(e.target.value)}
            placeholder="Lọc theo biển số, hãng hoặc dòng xe…"
            className="h-8 md:ml-auto md:w-72"
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
            <Empty title="Chưa có phương tiện" desc="Thêm xe đầu tiên từ nút Thêm mới." />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 text-left text-[11px] uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="px-4 py-2 font-medium">Biển số</th>
                  <th className="px-4 py-2 font-medium">Hãng · Dòng xe</th>
                  <th className="px-4 py-2 font-medium">Năm · Màu</th>
                  <th className="px-4 py-2 font-medium">VIN · ODO</th>
                  <th className="px-4 py-2 font-medium">Chủ xe</th>
                  <th className="px-4 py-2 font-medium">Trạng thái</th>
                  {coSua && <th className="px-4 py-2 text-right font-medium">Thao tác</th>}
                </tr>
              </thead>
              <tbody className="divide-y">
                {dong.map((x) => (
                  <tr key={x.id} className="hover:bg-muted/40">
                    <td className="px-4 py-2.5">
                      <Plate>{x.plate}</Plate>
                    </td>
                    <td className="px-4 py-2.5">
                      <span className="font-medium">{x.brand}</span> {x.model}
                    </td>
                    <td className="tabular px-4 py-2.5 text-xs">
                      {x.year ?? "—"}
                      {x.color ? ` · ${x.color}` : ""}
                    </td>
                    <td className="px-4 py-2.5 text-xs text-muted-foreground">
                      <div className="font-mono">{x.vin ?? "—"}</div>
                      {x.odometer !== null && (
                        <div className="tabular">{x.odometer.toLocaleString("vi-VN")} km</div>
                      )}
                    </td>
                    <td className="px-4 py-2.5 text-muted-foreground">{x.khach}</td>
                    <td className="px-4 py-2.5">
                      <Pill t={x.is_active ? "success" : "neutral"} dot>
                        {x.is_active ? "Đang hoạt động" : "Ngừng hoạt động"}
                      </Pill>
                    </td>
                    {coSua && (
                      <td className="px-4 py-2.5 text-right">
                        <div className="flex justify-end gap-1">
                          <Button size="sm" variant="ghost" onClick={() => moSua(x)}>
                            <Pencil className="size-3.5" />
                            Sửa
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-destructive hover:text-destructive"
                            onClick={() => setXoaId(x.id)}
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
            Trang {trangHienTai}/{tong_trang} · {tong} phương tiện
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

      <Dialog
        open={moForm}
        onOpenChange={(o) => {
          if (!o) setMoForm(false);
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Car className="size-4" />
              {dangSua ? `Sửa xe #${dangSua.id}` : "Thêm phương tiện"}
            </DialogTitle>
            <DialogDescription>
              Biển số và VIN phải duy nhất — backend kiểm tra khi lưu.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 text-sm">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Biển số</label>
                <Input
                  value={bien}
                  onChange={(e) => setBien(e.target.value)}
                  placeholder="30A-12345"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Năm sản xuất</label>
                <Input
                  type="number"
                  min={1900}
                  max={2100}
                  value={nam}
                  onChange={(e) => setNam(e.target.value)}
                  placeholder="2020"
                />
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Hãng</label>
                <Input
                  value={hang}
                  onChange={(e) => setHang(e.target.value)}
                  placeholder="Toyota"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Dòng xe</label>
                <Input
                  value={dongXe}
                  onChange={(e) => setDongXe(e.target.value)}
                  placeholder="Vios"
                />
              </div>
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Số khung (VIN)</label>
                <Input
                  value={vin}
                  onChange={(e) => setVin(e.target.value)}
                  placeholder="RL4BT9F3..."
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Màu sơn</label>
                <Input
                  value={mau}
                  onChange={(e) => setMau(e.target.value)}
                  placeholder="Trắng / Đen..."
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">ODO (km)</label>
                <Input
                  type="number"
                  min={0}
                  max={2000000}
                  value={soKm}
                  onChange={(e) => setSoKm(e.target.value)}
                  placeholder="45000"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Chủ xe</label>
              <Select value={khachId} onValueChange={setKhachId}>
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
              <label className="text-xs font-medium text-muted-foreground">Trạng thái xe</label>
              <Select value={hoatDong ? "1" : "0"} onValueChange={(v) => setHoatDong(v === "1")}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">Đang hoạt động</SelectItem>
                  <SelectItem value="0">Ngừng hoạt động</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setMoForm(false)}>
              Huỷ
            </Button>
            <Button
              disabled={
                !bien.trim() ||
                !hang.trim() ||
                !dongXe.trim() ||
                !khachId ||
                !namHopLe ||
                !soKmHopLe ||
                luu.isPending
              }
              onClick={() => luu.mutate()}
            >
              {dangSua ? "Lưu thay đổi" : "Thêm xe"}
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
            <AlertDialogTitle>Xoá phương tiện #{xoaId}?</AlertDialogTitle>
            <AlertDialogDescription>
              Xe đã có lịch hẹn hoặc phiếu sửa chữa thì backend từ chối xoá — chỉ hiển thị thông báo
              lỗi.
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
              Xoá xe
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
