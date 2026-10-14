import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState, type ReactNode } from "react";
import { toast } from "sonner";
import { Search, UserPlus } from "lucide-react";
import { api, q, ApiError } from "@/services/api";
import { useNhan, useRole } from "@/lib/rbac";
import { PageHeader, Panel, Pill, NoAccess, DangTai, Empty } from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { NguoiDungDong } from "@/types";

export const Route = createFileRoute("/users")({
  head: () => ({
    meta: [
      { title: "Người dùng — GarageTools AI" },
      {
        name: "description",
        content: "Quản lý tài khoản nhân viên, vai trò và trạng thái hoạt động.",
      },
      { property: "og:title", content: "Người dùng — GarageTools AI" },
      { property: "og:description", content: "Quản lý tài khoản và phân quyền." },
    ],
  }),
  component: Users,
});

type Form = {
  id: number | null;
  username: string;
  full_name: string;
  email: string;
  role: string;
  password: string;
  is_active: boolean;
};

const formMoi = (): Form => ({
  id: null,
  username: "",
  full_name: "",
  email: "",
  role: "",
  password: "",
  is_active: true,
});

function Truong({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="space-y-1.5">
      <div className="text-xs font-medium text-muted-foreground">{label}</div>
      {children}
    </div>
  );
}

function Users() {
  const { area, can, user } = useRole();
  const N = useNhan();
  const qc = useQueryClient();

  const [tim, setTim] = useState("");
  const [timDe, setTimDe] = useState("");
  const [vaiTroLoc, setVaiTroLoc] = useState("all");
  const [hoatDongLoc, setHoatDongLoc] = useState("all");
  const [trang, setTrang] = useState(1);
  const [form, setForm] = useState<Form | null>(null);

  useEffect(() => {
    const t = setTimeout(() => {
      setTimDe(tim);
      setTrang(1);
    }, 300);
    return () => clearTimeout(t);
  }, [tim]);

  const ds = useQuery({
    ...q.users({
      trang,
      moi_trang: 20,
      q: timDe || undefined,
      vai_tro: vaiTroLoc === "all" ? undefined : vaiTroLoc,
      dang_hoat_dong: hoatDongLoc === "all" ? undefined : hoatDongLoc,
    }),
    enabled: area("users"),
  });

  const luu = useMutation({
    mutationFn: (f: Form) => {
      const body: Parameters<typeof api.luuNguoiDung>[0] = {
        username: f.username.trim(),
        full_name: f.full_name.trim(),
        email: f.email.trim() || null,
        role: f.role,
        is_active: f.is_active,
      };
      if (f.id !== null) {
        body.id = f.id;
        if (f.password.trim()) body.password = f.password;
      } else {
        body.password = f.password;
      }
      return api.luuNguoiDung(body);
    },
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      setForm(null);
      await qc.invalidateQueries({ queryKey: ["users"] });
      await qc.invalidateQueries({ queryKey: ["lookups"] });
    },
    onError: (e) => toast.error(e instanceof ApiError ? e.message : "Lưu tài khoản thất bại."),
  });

  const batTat = useMutation({
    mutationFn: (id: number) => api.batTatNguoiDung(id),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      await qc.invalidateQueries({ queryKey: ["users"] });
      await qc.invalidateQueries({ queryKey: ["lookups"] });
    },
    onError: (e) => toast.error(e instanceof ApiError ? e.message : "Cập nhật tài khoản thất bại."),
  });

  if (!area("users")) return <NoAccess />;
  if (ds.isPending) return <DangTai mat="Đang tải danh sách tài khoản…" />;
  if (ds.isError)
    return (
      <div className="p-8 text-sm text-destructive">
        Không tải được danh sách tài khoản. {ds.error instanceof ApiError ? ds.error.message : ""}
      </div>
    );

  const { dong, tong, trang: trangHienTai, tong_trang, vai_tro } = ds.data;
  const coSua = can("user.edit");

  const moFormSua = (u: NguoiDungDong) =>
    setForm({
      id: u.id,
      username: u.username,
      full_name: u.full_name,
      email: u.email ?? "",
      role: u.role,
      password: "",
      is_active: !!u.is_active,
    });

  const hoiBatTat = (u: NguoiDungDong) => {
    const hoi = u.is_active
      ? `Khoá tài khoản ${u.username}? Tài khoản sẽ không đăng nhập được.`
      : `Mở lại tài khoản ${u.username}?`;
    if (window.confirm(hoi)) batTat.mutate(u.id);
  };

  const hopLe =
    form !== null &&
    form.username.trim().length >= 3 &&
    form.full_name.trim().length >= 2 &&
    form.role !== "" &&
    (form.id === null
      ? form.password.length >= 8
      : form.password.length === 0 || form.password.length >= 8);

  return (
    <>
      <PageHeader
        eyebrow="Hệ thống"
        title="Người dùng"
        desc="Tài khoản nhân viên và vai trò do backend quản lý — mọi thao tác tạo, sửa, khoá đều ghi vào nhật ký hệ thống."
        actions={
          coSua && (
            <Button onClick={() => setForm(formMoi())}>
              <UserPlus className="size-4" />
              Thêm tài khoản
            </Button>
          )
        }
      />
      <div className="p-6 lg:p-8">
        <Panel
          title="Danh sách tài khoản"
          bodyClass="p-0"
          action={
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="absolute left-2 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
                <Input
                  value={tim}
                  onChange={(e) => setTim(e.target.value)}
                  placeholder="Tìm username, họ tên…"
                  className="h-8 w-40 pl-7 text-xs"
                />
              </div>
              <Select
                value={vaiTroLoc}
                onValueChange={(v) => {
                  setVaiTroLoc(v);
                  setTrang(1);
                }}
              >
                <SelectTrigger className="h-8 w-36 text-xs">
                  <SelectValue placeholder="Tất cả vai trò" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tất cả vai trò</SelectItem>
                  {Object.entries(vai_tro).map(([k, v]) => (
                    <SelectItem key={k} value={k}>
                      {v}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select
                value={hoatDongLoc}
                onValueChange={(v) => {
                  setHoatDongLoc(v);
                  setTrang(1);
                }}
              >
                <SelectTrigger className="h-8 w-36 text-xs">
                  <SelectValue placeholder="Mọi trạng thái" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Mọi trạng thái</SelectItem>
                  <SelectItem value="1">Đang hoạt động</SelectItem>
                  <SelectItem value="0">Ngừng hoạt động</SelectItem>
                </SelectContent>
              </Select>
            </div>
          }
        >
          {dong.length === 0 ? (
            <div className="p-4">
              <Empty
                title="Không có tài khoản nào khớp bộ lọc"
                desc="Thử bỏ bớt bộ lọc hoặc đổi từ khoá."
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 text-left text-[11px] uppercase tracking-wider text-muted-foreground">
                  <tr>
                    <th className="px-4 py-2 font-medium">ID</th>
                    <th className="px-4 py-2 font-medium">Tên đăng nhập</th>
                    <th className="px-4 py-2 font-medium">Họ tên</th>
                    <th className="px-4 py-2 font-medium">Email</th>
                    <th className="px-4 py-2 font-medium">Vai trò</th>
                    <th className="px-4 py-2 font-medium">Trạng thái</th>
                    {coSua && <th className="px-4 py-2 text-right font-medium">Thao tác</th>}
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {dong.map((u) => {
                    const laMinh = user?.id === u.id;
                    return (
                      <tr key={u.id} className="hover:bg-muted/40">
                        <td className="px-4 py-2.5 font-mono text-xs text-muted-foreground">
                          {u.id}
                        </td>
                        <td className="px-4 py-2.5 font-medium">{u.username}</td>
                        <td className="px-4 py-2.5">{u.full_name}</td>
                        <td className="px-4 py-2.5 text-muted-foreground">{u.email ?? "—"}</td>
                        <td className="px-4 py-2.5">{N.vaiTro(u.role)}</td>
                        <td className="px-4 py-2.5">
                          <Pill t={u.is_active ? "success" : "danger"} dot>
                            {u.is_active ? "Đang hoạt động" : "Ngừng hoạt động"}
                          </Pill>
                        </td>
                        {coSua && (
                          <td className="px-4 py-2.5 text-right">
                            {laMinh ? (
                              <span className="text-xs text-muted-foreground">Đang đăng nhập</span>
                            ) : (
                              <div className="flex justify-end gap-2">
                                <Button size="sm" variant="outline" onClick={() => moFormSua(u)}>
                                  Sửa
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  disabled={batTat.isPending}
                                  onClick={() => hoiBatTat(u)}
                                >
                                  {u.is_active ? "Khoá" : "Mở"}
                                </Button>
                              </div>
                            )}
                          </td>
                        )}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
          <div className="flex items-center justify-between border-t px-4 py-3 text-xs text-muted-foreground">
            <span className="tabular">
              Trang {trangHienTai}/{tong_trang} · {tong} tài khoản
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

        <p className="mt-4 text-center text-[11px] text-muted-foreground">
          Quyền <code className="font-mono">user.manage</code> để mở màn hình,{" "}
          <code className="font-mono">user.edit</code> để tạo/sửa — backend không cho phép tự sửa
          hoặc tự khoá tài khoản của chính mình.
        </p>
      </div>

      <Dialog open={form !== null} onOpenChange={(o) => !o && setForm(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {form?.id ? `Sửa tài khoản ${form.username}` : "Thêm tài khoản"}
            </DialogTitle>
          </DialogHeader>
          {form && (
            <div className="space-y-3 text-sm">
              <Truong label="Tên đăng nhập">
                <Input
                  value={form.username}
                  onChange={(e) => setForm({ ...form, username: e.target.value })}
                  placeholder="vd: tranthib.c"
                />
              </Truong>
              <Truong label="Họ tên">
                <Input
                  value={form.full_name}
                  onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                  placeholder="vd: Trần Thị B"
                />
              </Truong>
              <Truong label="Email">
                <Input
                  type="email"
                  value={form.email}
                  onChange={(e) => setForm({ ...form, email: e.target.value })}
                  placeholder="Để trống nếu không có"
                />
              </Truong>
              <Truong label="Vai trò">
                <Select value={form.role} onValueChange={(v) => setForm({ ...form, role: v })}>
                  <SelectTrigger>
                    <SelectValue placeholder="Chọn vai trò" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(vai_tro).map(([k, v]) => (
                      <SelectItem key={k} value={k}>
                        {v}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </Truong>
              <Truong
                label={
                  form.id === null
                    ? "Mật khẩu (tối thiểu 8 ký tự)"
                    : "Đặt lại mật khẩu mới (tuỳ chọn, tối thiểu 8 ký tự)"
                }
              >
                <Input
                  type="password"
                  value={form.password}
                  onChange={(e) => setForm({ ...form, password: e.target.value })}
                  placeholder={
                    form.id === null
                      ? "Bắt buộc khi tạo mới"
                      : "Để trống nếu giữ nguyên mật khẩu cũ"
                  }
                />
              </Truong>
              <Truong label="Trạng thái">
                <Select
                  value={form.is_active ? "1" : "0"}
                  onValueChange={(v) => setForm({ ...form, is_active: v === "1" })}
                >
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">Đang hoạt động</SelectItem>
                    <SelectItem value="0">Ngừng hoạt động</SelectItem>
                  </SelectContent>
                </Select>
              </Truong>
            </div>
          )}
          <DialogFooter>
            <Button variant="outline" onClick={() => setForm(null)}>
              Đóng
            </Button>
            <Button disabled={!hopLe || luu.isPending} onClick={() => form && luu.mutate(form)}>
              {form?.id ? "Lưu thay đổi" : "Tạo tài khoản"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
