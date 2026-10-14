import { Link, useRouterState } from "@tanstack/react-router";
import { useState, type FormEvent, type ReactNode } from "react";
import {
  LayoutDashboard,
  KanbanSquare,
  ClipboardList,
  ScanSearch,
  Sparkles,
  Boxes,
  Receipt,
  Menu,
  X,
  Wrench,
  LogOut,
  CalendarDays,
  Car,
  FileText,
  ShieldCheck,
  Tags,
  UserCog,
  BarChart3,
  KeyRound,
} from "lucide-react";
import { toast } from "sonner";
import { useNhan, useRole, type Area } from "@/lib/rbac";
import { api, ApiError } from "@/services/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const NAV: {
  group: string;
  items: { to: string; label: string; icon: typeof Menu; area: Area }[];
}[] = [
  {
    group: "Vận hành",
    items: [
      { to: "/", label: "Tổng quan", icon: LayoutDashboard, area: "dashboard" },
      { to: "/workflow", label: "Bảng điều phối", icon: KanbanSquare, area: "board" },
      { to: "/repair-orders", label: "Phiếu sửa chữa", icon: ClipboardList, area: "orders" },
      { to: "/inspection", label: "Tiếp nhận xe", icon: ScanSearch, area: "inspection" },
      { to: "/appointments", label: "Lịch hẹn", icon: CalendarDays, area: "appointments" },
      { to: "/customers", label: "Khách hàng & Xe", icon: Car, area: "customers" },
      { to: "/quotations", label: "Báo giá", icon: FileText, area: "quotes" },
    ],
  },
  {
    group: "Trợ lý",
    items: [{ to: "/ai-review", label: "AI & Duyệt kết quả", icon: Sparkles, area: "ai" }],
  },
  {
    group: "Kho & Tài chính",
    items: [
      { to: "/inventory", label: "Kho phụ tung", icon: Boxes, area: "inventory" },
      { to: "/catalog", label: "Danh mục DV/PT", icon: Tags, area: "catalog" },
      { to: "/warranties", label: "Bảo hành", icon: ShieldCheck, area: "warranty" },
      { to: "/finance", label: "Hoá đơn & Thanh toán", icon: Receipt, area: "finance" },
      { to: "/reports", label: "Báo cáo & Lịch sử", icon: BarChart3, area: "reports" },
    ],
  },
  {
    group: "Hệ thống",
    items: [{ to: "/users", label: "Người dùng", icon: UserCog, area: "users" }],
  },
];

function Sidebar({ onNav }: { onNav?: () => void }) {
  const { area, user, dangXuat } = useRole();
  const N = useNhan();
  const path = useRouterState({ select: (s) => s.location.pathname });
  return (
    <div className="flex h-full flex-col bg-sidebar text-sidebar-foreground">
      <div className="flex h-14 items-center gap-2.5 border-b border-sidebar-border px-5">
        <div className="flex size-7 items-center justify-center rounded-md bg-sidebar-primary text-sidebar-primary-foreground">
          <Wrench className="size-4" />
        </div>
        <div className="leading-tight">
          <div className="text-sm font-semibold text-sidebar-accent-foreground">
            GarageTools<span className="text-sidebar-primary"> AI</span>
          </div>
          <div className="text-[10px] uppercase tracking-[0.16em] opacity-60">Xưởng Quận 7</div>
        </div>
      </div>
      <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-4">
        {NAV.map((g) => {
          const items = g.items.filter((i) => area(i.area));
          if (!items.length) return null;
          return (
            <div key={g.group}>
              <div className="mb-1.5 px-2 text-[10px] font-semibold uppercase tracking-[0.16em] opacity-50">
                {g.group}
              </div>
              {items.map((i) => {
                const active = i.to === "/" ? path === "/" : path.startsWith(i.to);
                return (
                  <Link
                    key={i.to}
                    to={i.to}
                    onClick={onNav}
                    className={cn(
                      "group flex items-center gap-2.5 rounded-md px-2 py-1.5 text-[13px] transition-colors",
                      active
                        ? "bg-sidebar-accent font-medium text-sidebar-accent-foreground"
                        : "hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground",
                    )}
                  >
                    <i.icon
                      className={cn("size-4", active ? "text-sidebar-primary" : "opacity-70")}
                    />
                    {i.label}
                  </Link>
                );
              })}
            </div>
          );
        })}
      </nav>
      <div className="border-t border-sidebar-border p-4">
        <div className="flex items-center gap-2.5">
          <div className="flex size-8 items-center justify-center rounded-full bg-sidebar-accent text-xs font-semibold text-sidebar-accent-foreground">
            {user?.full_name?.split(" ").slice(-1)[0]?.[0] ?? "?"}
          </div>
          <div className="min-w-0 flex-1 leading-tight">
            <div className="truncate text-[13px] font-medium text-sidebar-accent-foreground">
              {user?.full_name}
            </div>
            <div className="text-[11px] opacity-60">{user ? N.vaiTro(user.role) : ""}</div>
          </div>
          <button
            onClick={() => void dangXuat()}
            title="Đăng xuất"
            className="rounded-md p-1.5 opacity-70 hover:bg-sidebar-accent hover:opacity-100"
          >
            <LogOut className="size-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

/** Màn đăng nhập thật — gọi `POST /api/auth/login`, cookie phiên do backend cấp. */
function DangNhap() {
  const { dangNhap } = useRole();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [dangGui, setDangGui] = useState(false);

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) return;
    setDangGui(true);
    try {
      const tb = await dangNhap(username.trim(), password);
      toast.success(tb);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Đăng nhập thất bại.");
    } finally {
      setDangGui(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm rounded-lg border bg-card p-6 shadow-card">
        <div className="mb-6 flex items-center gap-2.5">
          <div className="flex size-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Wrench className="size-5" />
          </div>
          <div className="leading-tight">
            <div className="font-semibold">
              GarageTools<span className="text-primary"> AI</span>
            </div>
            <div className="text-xs text-muted-foreground">Hệ thống quản lý xưởng dịch vụ</div>
          </div>
        </div>
        <form onSubmit={submit} className="space-y-4">
          <div className="space-y-1.5">
            <label htmlFor="username" className="text-xs font-medium text-muted-foreground">
              Tên đăng nhập
            </label>
            <Input
              id="username"
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="VD: quan_ly"
              required
            />
          </div>
          <div className="space-y-1.5">
            <label htmlFor="password" className="text-xs font-medium text-muted-foreground">
              Mật khẩu
            </label>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </div>
          <Button
            type="submit"
            className="w-full"
            disabled={dangGui || !username.trim() || !password}
          >
            {dangGui ? "Đang đăng nhập…" : "Đăng nhập"}
          </Button>
        </form>
        <p className="mt-4 text-center text-[11px] text-muted-foreground">
          Dùng tài khoản do quản trị viên cấp phát.
        </p>
      </div>
    </div>
  );
}

/** Đổi mật khẩu cá nhân — backend tăng phiên bản, mọi phiên đang mở bị vô hiệu. */
function DoiMatKhau({ open, onOpenChange }: { open: boolean; onOpenChange: (o: boolean) => void }) {
  const { dangXuat } = useRole();
  const [cu, setCu] = useState("");
  const [moi, setMoi] = useState("");
  const [xac, setXac] = useState("");
  const [dangGui, setDangGui] = useState(false);
  const [loi, setLoi] = useState("");

  const dong = (o: boolean) => {
    if (dangGui) return;
    setCu("");
    setMoi("");
    setXac("");
    setLoi("");
    onOpenChange(o);
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    if (!cu || !moi || !xac) return setLoi("Nhập đủ cả ba trường.");
    if (moi.length < 8) return setLoi("Mật khẩu mới cần ít nhất 8 ký tự.");
    if (moi === cu) return setLoi("Mật khẩu mới phải khác mật khẩu cũ.");
    if (moi !== xac) return setLoi("Xác nhận mật khẩu không khớp.");
    setLoi("");
    setDangGui(true);
    try {
      await api.doiMatKhau({ mat_khau_cu: cu, mat_khau_moi: moi });
      onOpenChange(false);
      toast.success("Đã đổi mật khẩu. Vui lòng đăng nhập lại bằng mật khẩu mới.");
      await dangXuat();
    } catch (err) {
      setLoi(err instanceof ApiError ? err.message : "Đổi mật khẩu thất bại.");
    } finally {
      setDangGui(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={dong}>
      <DialogContent className="sm:max-w-sm">
        <DialogHeader>
          <DialogTitle>Đổi mật khẩu</DialogTitle>
          <DialogDescription>
            Sau khi đổi, mọi phiên đang mở sẽ bị đăng xuất để bảo mật.
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={submit} className="space-y-3">
          <div className="space-y-1.5">
            <label htmlFor="mk-cu" className="text-xs font-medium text-muted-foreground">
              Mật khẩu hiện tại
            </label>
            <Input
              id="mk-cu"
              type="password"
              autoComplete="current-password"
              value={cu}
              onChange={(e) => setCu(e.target.value)}
              required
            />
          </div>
          <div className="space-y-1.5">
            <label htmlFor="mk-moi" className="text-xs font-medium text-muted-foreground">
              Mật khẩu mới
            </label>
            <Input
              id="mk-moi"
              type="password"
              autoComplete="new-password"
              value={moi}
              onChange={(e) => setMoi(e.target.value)}
              placeholder="Ít nhất 8 ký tự"
              required
            />
          </div>
          <div className="space-y-1.5">
            <label htmlFor="mk-xac" className="text-xs font-medium text-muted-foreground">
              Xác nhận mật khẩu mới
            </label>
            <Input
              id="mk-xac"
              type="password"
              autoComplete="new-password"
              value={xac}
              onChange={(e) => setXac(e.target.value)}
              required
            />
          </div>
          {loi && <p className="text-xs text-destructive">{loi}</p>}
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => dong(false)} disabled={dangGui}>
              Huỷ
            </Button>
            <Button type="submit" disabled={dangGui}>
              {dangGui ? "Đang lưu…" : "Đổi mật khẩu"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [doiMk, setDoiMk] = useState(false);
  const { trangThaiPhien, dangXuat } = useRole();

  if (trangThaiPhien === "dang_tai") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background text-sm text-muted-foreground">
        <span className="mr-2 size-4 animate-spin rounded-full border-2 border-muted border-t-primary" />
        Đang kiểm tra phiên đăng nhập…
      </div>
    );
  }
  if (trangThaiPhien === "chua_dang_nhap") return <DangNhap />;

  return (
    <div className="min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 lg:block">
        <Sidebar />
      </aside>
      {open && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-foreground/40" onClick={() => setOpen(false)} />
          <div className="absolute inset-y-0 left-0 w-64">
            <Sidebar onNav={() => setOpen(false)} />
          </div>
          <button
            className="absolute left-[17rem] top-4 rounded-md bg-card p-1.5"
            onClick={() => setOpen(false)}
            aria-label="Đóng menu"
          >
            <X className="size-4" />
          </button>
        </div>
      )}
      <div className="lg:pl-60">
        <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b bg-card/90 px-4 backdrop-blur lg:px-8">
          <button
            className="rounded-md p-1.5 hover:bg-muted lg:hidden"
            onClick={() => setOpen(true)}
            aria-label="Mở menu"
          >
            <Menu className="size-5" />
          </button>
          <div className="hidden text-sm font-medium text-foreground md:block">
            GarageTools AI — Xưởng Quận 7
          </div>
          <div className="ml-auto flex items-center gap-2">
            <span className="hidden text-xs text-muted-foreground sm:inline">Đã đăng nhập</span>
            <Button variant="outline" size="sm" onClick={() => setDoiMk(true)}>
              <KeyRound className="size-4" /> <span className="hidden sm:inline">Đổi mật khẩu</span>
            </Button>
            <Button variant="outline" size="sm" onClick={() => void dangXuat()}>
              <LogOut className="size-4" /> Đăng xuất
            </Button>
          </div>
        </header>
        <main>{children}</main>
      </div>
      <DoiMatKhau open={doiMk} onOpenChange={setDoiMk} />
    </div>
  );
}
