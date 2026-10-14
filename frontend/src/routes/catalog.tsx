import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Package, Pencil, Plus, Trash2, Wrench } from "lucide-react";
import { api, q, ApiError } from "@/services/api";
import { useRole, vnd } from "@/lib/rbac";
import { DangTai, Empty, NoAccess, PageHeader, Panel, Pill } from "@/components/app/ui-kit";
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
import type { DichVuDong, PhuTungDong } from "@/types";

export const Route = createFileRoute("/catalog")({
  head: () => ({
    meta: [
      { title: "Danh mục — GarageTools AI" },
      {
        name: "description",
        content: "Bảng giá dịch vụ và danh mục phụ tùng kèm tồn kho, mức cảnh báo.",
      },
      { property: "og:title", content: "Danh mục Dịch vụ & Phụ tùng — GarageTools AI" },
      { property: "og:description", content: "Quản lý dịch vụ và phụ tùng của xưởng." },
    ],
  }),
  component: DanhMuc,
});

/** Số dương >= 0, chuỗi rỗng hoặc không phải số đều bị coi là chưa hợp lệ. */
const soHopLe = (s: string, bat_buoc: boolean) => {
  const v = s.trim();
  if (v === "") return !bat_buoc;
  const n = Number(v);
  return Number.isFinite(n) && n >= 0;
};

function DanhMuc() {
  const { area } = useRole();
  const [tab, setTab] = useState<"dich_vu" | "phu_tung">("dich_vu");

  if (!area("catalog")) return <NoAccess />;

  return (
    <>
      <PageHeader
        eyebrow="Danh mục"
        title="Dịch vụ & Phụ tùng"
        desc="Bảng giá dịch vụ và tồn kho phụ tùng — mọi thao tác ghi đều cần quyền catalog.edit."
        actions={
          <div className="flex gap-1 rounded-md border bg-muted/40 p-1">
            {(["dich_vu", "phu_tung"] as const).map((k) => (
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
                {k === "dich_vu" ? "Dịch vụ" : "Phụ tùng"}
              </button>
            ))}
          </div>
        }
      />
      <div className="p-6 lg:p-8">{tab === "dich_vu" ? <BangDichVu /> : <BangPhuTung />}</div>
    </>
  );
}

function BangDichVu() {
  const { can } = useRole();
  const qc = useQueryClient();

  const [tim, setTim] = useState("");
  const [tuKhoa, setTuKhoa] = useState("");
  const [trang, setTrang] = useState(1);

  const [moForm, setMoForm] = useState(false);
  const [dangSua, setDangSua] = useState<DichVuDong | null>(null);
  const [ten, setTen] = useState("");
  const [gia, setGia] = useState("");
  const [dienGiai, setDienGiai] = useState("");
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

  const ds = useQuery(q.services({ moi_trang: 20, trang, q: tuKhoa || undefined }));

  const loi = (e: unknown) => toast.error(e instanceof ApiError ? e.message : "Thao tác thất bại.");

  const luu = useMutation({
    mutationFn: () =>
      api.luuDichVu({
        id: dangSua?.id ?? null,
        name: ten.trim(),
        price: gia.trim(),
        description: dienGiai.trim() || null,
        is_active: hoatDong,
      }),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      setMoForm(false);
      await qc.invalidateQueries({ queryKey: ["services"] });
      await qc.invalidateQueries({ queryKey: ["lookups"] });
    },
    onError: loi,
  });

  const xoa = useMutation({
    mutationFn: (id: number) => api.xoaDichVu(id),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      setXoaId(null);
      await qc.invalidateQueries({ queryKey: ["services"] });
      await qc.invalidateQueries({ queryKey: ["lookups"] });
    },
    onError: (e) => {
      loi(e);
      setXoaId(null);
    },
  });

  const coSua = can("catalog.edit");
  const hopLe = ten.trim().length >= 2 && soHopLe(gia, true);

  const moTao = () => {
    setDangSua(null);
    setTen("");
    setGia("");
    setDienGiai("");
    setHoatDong(true);
    setMoForm(true);
  };

  const moSua = (d: DichVuDong) => {
    setDangSua(d);
    setTen(d.name);
    setGia(String(d.price));
    setDienGiai(d.description ?? "");
    setHoatDong(!!d.is_active);
    setMoForm(true);
  };

  if (ds.isPending) return <DangTai mat="Đang tải danh mục dịch vụ…" />;
  if (!ds.data)
    return (
      <div className="p-8 text-sm text-destructive">
        Không tải được danh sách dịch vụ.{" "}
        {ds.error instanceof ApiError ? ds.error.message : "Lỗi kết nối."}
      </div>
    );

  const { dong, tong, trang: trangHienTai, tong_trang } = ds.data;

  return (
    <>
      <Panel
        title="Dịch vụ"
        bodyClass="p-0"
        action={
          coSua && (
            <Button size="sm" onClick={moTao}>
              <Plus className="size-4" />
              Thêm dịch vụ
            </Button>
          )
        }
      >
        <div className="flex items-center border-b p-3">
          <Input
            value={tim}
            onChange={(e) => setTim(e.target.value)}
            placeholder="Lọc theo tên hoặc mô tả dịch vụ…"
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
            <Empty title="Chưa có dịch vụ" desc="Thêm dịch vụ đầu tiên từ nút Thêm mới." />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 text-left text-[11px] uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="px-4 py-2 font-medium">Mã</th>
                  <th className="px-4 py-2 font-medium">Tên dịch vụ</th>
                  <th className="px-4 py-2 text-right font-medium">Đơn giá</th>
                  <th className="px-4 py-2 font-medium">Trạng thái</th>
                  {coSua && <th className="px-4 py-2 text-right font-medium">Thao tác</th>}
                </tr>
              </thead>
              <tbody className="divide-y">
                {dong.map((d) => (
                  <tr key={d.id} className="hover:bg-muted/40">
                    <td className="tabular px-4 py-2.5 text-xs text-muted-foreground">#{d.id}</td>
                    <td className="px-4 py-2.5 font-medium">{d.name}</td>
                    <td className="tabular px-4 py-2.5 text-right font-medium">{vnd(d.price)}</td>
                    <td className="px-4 py-2.5">
                      <Pill t={d.is_active ? "success" : "neutral"} dot>
                        {d.is_active ? "Đang dùng" : "Ngừng dùng"}
                      </Pill>
                    </td>
                    {coSua && (
                      <td className="px-4 py-2.5 text-right">
                        <div className="flex justify-end gap-1">
                          <Button size="sm" variant="ghost" onClick={() => moSua(d)}>
                            <Pencil className="size-3.5" />
                            Sửa
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-destructive hover:text-destructive"
                            onClick={() => setXoaId(d.id)}
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
            Trang {trangHienTai}/{tong_trang} · {tong} dịch vụ
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
              <Wrench className="size-4" />
              {dangSua ? `Sửa dịch vụ #${dangSua.id}` : "Thêm dịch vụ"}
            </DialogTitle>
            <DialogDescription>
              Đơn giá là số đồng không âm — backend kiểm tra lại khi lưu.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 text-sm">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Tên dịch vụ</label>
              <Input
                value={ten}
                onChange={(e) => setTen(e.target.value)}
                placeholder="Thay dầu động cơ"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Đơn giá (₫)</label>
              <Input
                type="number"
                min={0}
                value={gia}
                onChange={(e) => setGia(e.target.value)}
                placeholder="350000"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Mô tả</label>
              <Textarea
                value={dienGiai}
                onChange={(e) => setDienGiai(e.target.value)}
                placeholder="Phạm vi công việc, loại dầu…"
                className="min-h-[60px]"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Trạng thái</label>
              <Select value={hoatDong ? "1" : "0"} onValueChange={(v) => setHoatDong(v === "1")}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">Đang dùng</SelectItem>
                  <SelectItem value="0">Ngừng dùng</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setMoForm(false)}>
              Huỷ
            </Button>
            <Button disabled={!hopLe || luu.isPending} onClick={() => luu.mutate()}>
              {dangSua ? "Lưu thay đổi" : "Thêm dịch vụ"}
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
            <AlertDialogTitle>Xoá dịch vụ #{xoaId}?</AlertDialogTitle>
            <AlertDialogDescription>
              Dịch vụ đã dùng trong hạng mục của phiếu thì backend từ chối xoá (409) — chỉ hiển thị
              thông báo lỗi.
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
              Xoá dịch vụ
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}

function BangPhuTung() {
  const { can } = useRole();
  const qc = useQueryClient();

  const [tim, setTim] = useState("");
  const [tuKhoa, setTuKhoa] = useState("");
  const [trang, setTrang] = useState(1);
  const [locDung, setLocDung] = useState("all");
  const [locKho, setLocKho] = useState("all");

  const [moForm, setMoForm] = useState(false);
  const [dangSua, setDangSua] = useState<PhuTungDong | null>(null);
  const [ten, setTen] = useState("");
  const [sku, setSku] = useState("");
  const [gia, setGia] = useState("");
  const [ton, setTon] = useState("0");
  const [tonCanhBao, setTonCanhBao] = useState("0");
  const [dienGiai, setDienGiai] = useState("");
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

  const ds = useQuery(
    q.parts({
      moi_trang: 20,
      trang,
      q: tuKhoa || undefined,
      dang_dung: locDung === "all" ? undefined : locDung,
      het_kho: locKho === "all" ? undefined : locKho,
    }),
  );

  const loi = (e: unknown) => toast.error(e instanceof ApiError ? e.message : "Thao tác thất bại.");

  const luu = useMutation({
    mutationFn: () =>
      api.luuPhuTung({
        id: dangSua?.id ?? null,
        name: ten.trim(),
        sku: sku.trim() || null,
        price: gia.trim(),
        stock: ton.trim(),
        min_stock: tonCanhBao.trim() || 0,
        description: dienGiai.trim() || null,
        is_active: hoatDong,
      }),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      setMoForm(false);
      await qc.invalidateQueries({ queryKey: ["parts"] });
      await qc.invalidateQueries({ queryKey: ["lookups"] });
      await qc.invalidateQueries({ queryKey: ["stock"] });
    },
    onError: loi,
  });

  const xoa = useMutation({
    mutationFn: (id: number) => api.xoaPhuTung(id),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      setXoaId(null);
      await qc.invalidateQueries({ queryKey: ["parts"] });
      await qc.invalidateQueries({ queryKey: ["lookups"] });
    },
    onError: (e) => {
      loi(e);
      setXoaId(null);
    },
  });

  const coSua = can("catalog.edit");
  const hopLe =
    ten.trim().length >= 2 &&
    soHopLe(gia, true) &&
    soHopLe(ton, true) &&
    soHopLe(tonCanhBao, false);

  const moTao = () => {
    setDangSua(null);
    setTen("");
    setSku("");
    setGia("");
    setTon("0");
    setTonCanhBao("0");
    setDienGiai("");
    setHoatDong(true);
    setMoForm(true);
  };

  const moSua = (p: PhuTungDong) => {
    setDangSua(p);
    setTen(p.name);
    setSku(p.sku ?? "");
    setGia(String(p.price));
    setTon(String(p.stock));
    setTonCanhBao(String(p.min_stock));
    setDienGiai(p.description ?? "");
    setHoatDong(!!p.is_active);
    setMoForm(true);
  };

  if (ds.isPending) return <DangTai mat="Đang tải danh mục phụ tùng…" />;
  if (!ds.data)
    return (
      <div className="p-8 text-sm text-destructive">
        Không tải được danh sách phụ tùng.{" "}
        {ds.error instanceof ApiError ? ds.error.message : "Lỗi kết nối."}
      </div>
    );

  const { dong, tong, trang: trangHienTai, tong_trang } = ds.data;

  return (
    <>
      <Panel
        title="Phụ tùng"
        bodyClass="p-0"
        action={
          <div className="flex flex-wrap items-center justify-end gap-2">
            <Select
              value={locDung}
              onValueChange={(v) => {
                setLocDung(v);
                setTrang(1);
              }}
            >
              <SelectTrigger className="h-8 w-36 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tất cả trạng thái</SelectItem>
                <SelectItem value="1">Đang dùng</SelectItem>
                <SelectItem value="0">Ngừng dùng</SelectItem>
              </SelectContent>
            </Select>
            <Select
              value={locKho}
              onValueChange={(v) => {
                setLocKho(v);
                setTrang(1);
              }}
            >
              <SelectTrigger className="h-8 w-36 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">Tồn kho: tất cả</SelectItem>
                <SelectItem value="0">Còn hàng</SelectItem>
                <SelectItem value="1">Đã hết hàng</SelectItem>
              </SelectContent>
            </Select>
            {coSua && (
              <Button size="sm" onClick={moTao}>
                <Plus className="size-4" />
                Thêm phụ tùng
              </Button>
            )}
          </div>
        }
      >
        <div className="flex items-center border-b p-3">
          <Input
            value={tim}
            onChange={(e) => setTim(e.target.value)}
            placeholder="Lọc theo tên phụ tùng…"
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
            <Empty title="Không có phụ tùng phù hợp" desc="Thử bỏ bộ lọc hoặc thêm mới." />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 text-left text-[11px] uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="px-4 py-2 font-medium">Mã</th>
                  <th className="px-4 py-2 font-medium">SKU</th>
                  <th className="px-4 py-2 font-medium">Tên phụ tùng</th>
                  <th className="px-4 py-2 text-right font-medium">Đơn giá</th>
                  <th className="px-4 py-2 text-right font-medium">Tồn</th>
                  <th className="px-4 py-2 text-right font-medium">Tồn cảnh báo</th>
                  <th className="px-4 py-2 font-medium">Trạng thái</th>
                  {coSua && <th className="px-4 py-2 text-right font-medium">Thao tác</th>}
                </tr>
              </thead>
              <tbody className="divide-y">
                {dong.map((p) => (
                  <tr key={p.id} className="hover:bg-muted/40">
                    <td className="tabular px-4 py-2.5 text-xs text-muted-foreground">#{p.id}</td>
                    <td className="px-4 py-2.5 font-mono text-xs">{p.sku ?? "—"}</td>
                    <td className="px-4 py-2.5 font-medium">{p.name}</td>
                    <td className="tabular px-4 py-2.5 text-right font-medium">{vnd(p.price)}</td>
                    <td
                      className={cn(
                        "tabular px-4 py-2.5 text-right",
                        p.stock === 0 && "font-medium text-destructive",
                      )}
                    >
                      {p.stock}
                    </td>
                    <td className="tabular px-4 py-2.5 text-right text-muted-foreground">
                      {p.min_stock}
                    </td>
                    <td className="px-4 py-2.5">
                      <Pill t={p.is_active ? "success" : "neutral"} dot>
                        {p.is_active ? "Đang dùng" : "Ngừng dùng"}
                      </Pill>
                    </td>
                    {coSua && (
                      <td className="px-4 py-2.5 text-right">
                        <div className="flex justify-end gap-1">
                          <Button size="sm" variant="ghost" onClick={() => moSua(p)}>
                            <Pencil className="size-3.5" />
                            Sửa
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            className="text-destructive hover:text-destructive"
                            onClick={() => setXoaId(p.id)}
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
            Trang {trangHienTai}/{tong_trang} · {tong} phụ tùng
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
              <Package className="size-4" />
              {dangSua ? `Sửa phụ tùng #${dangSua.id}` : "Thêm phụ tùng"}
            </DialogTitle>
            <DialogDescription>
              SKU phải duy nhất. Thay đổi tồn kho được backend ghi vào sổ cái (ADJUSTMENT).
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3 text-sm">
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Tên phụ tùng</label>
                <Input
                  value={ten}
                  onChange={(e) => setTen(e.target.value)}
                  placeholder="Lọc dầu động cơ"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">SKU</label>
                <Input
                  value={sku}
                  onChange={(e) => setSku(e.target.value)}
                  placeholder="FLT-001 (để trống nếu không dùng)"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Đơn giá (₫)</label>
              <Input
                type="number"
                min={0}
                value={gia}
                onChange={(e) => setGia(e.target.value)}
                placeholder="250000"
              />
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Tồn kho</label>
                <Input
                  type="number"
                  min={0}
                  value={ton}
                  onChange={(e) => setTon(e.target.value)}
                  placeholder="0"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Tồn cảnh báo</label>
                <Input
                  type="number"
                  min={0}
                  value={tonCanhBao}
                  onChange={(e) => setTonCanhBao(e.target.value)}
                  placeholder="0"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Mô tả</label>
              <Textarea
                value={dienGiai}
                onChange={(e) => setDienGiai(e.target.value)}
                placeholder="Xe áp dụng, thông số kỹ thuật…"
                className="min-h-[60px]"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Trạng thái</label>
              <Select value={hoatDong ? "1" : "0"} onValueChange={(v) => setHoatDong(v === "1")}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1">Đang dùng</SelectItem>
                  <SelectItem value="0">Ngừng dùng</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setMoForm(false)}>
              Huỷ
            </Button>
            <Button disabled={!hopLe || luu.isPending} onClick={() => luu.mutate()}>
              {dangSua ? "Lưu thay đổi" : "Thêm phụ tùng"}
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
            <AlertDialogTitle>Xoá phụ tùng #{xoaId}?</AlertDialogTitle>
            <AlertDialogDescription>
              Phụ tùng đã dùng trong phiếu hoặc phát sinh giao dịch kho thì backend từ chối xoá
              (409) — chỉ hiển thị thông báo lỗi.
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
              Xoá phụ tùng
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </>
  );
}
