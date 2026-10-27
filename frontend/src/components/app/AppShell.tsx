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
  Eye,
  EyeOff,
  CheckCircle2,
  Lock,
  ArrowRight,
  AlertCircle,
  Users,
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
      { to: "/inventory", label: "Kho phụ tùng", icon: Boxes, area: "inventory" },
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
          <div className="text-[10px] uppercase tracking-[0.16em] opacity-60">
            Quản trị Xưởng &amp; AI
          </div>
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

const TAI_KHOAN_DEMO = [
  {
    username: "quan_ly",
    fullName: "Nguyễn Quang Huy",
    vaiTro: "Quản lý",
    badgeClass: "bg-primary/10 text-primary border-primary/20",
    moTa: "Toàn quyền hệ thống, duyệt báo giá & kết quả AI, quản trị danh mục và báo cáo.",
  },
  {
    username: "le_tan",
    fullName: "Trần Thu Hà",
    vaiTro: "Lễ tân",
    badgeClass: "bg-info-soft text-foreground border-border",
    moTa: "Tiếp nhận xe, quản lý lịch hẹn, lập báo giá nháp, kho phụ tùng & bảo hành.",
  },
  {
    username: "ky_thuat_vien",
    fullName: "Lê Minh Đức",
    vaiTro: "Kỹ thuật viên",
    badgeClass: "bg-warning-soft text-foreground border-border",
    moTa: "Chỉ xem & xử lý phiếu được phân công, cập nhật hạng mục sửa chữa, chạy AI03.",
  },
  {
    username: "thu_ngan",
    fullName: "Phạm Thu Hà",
    vaiTro: "Thu ngân",
    badgeClass: "bg-success-soft text-foreground border-border",
    moTa: "Lập hoá đơn cho phiếu đã hoàn thành, ghi nhận thanh toán & theo dõi công nợ.",
  },
] as const;

const MAT_KHAU_DEMO = "Garage@2026";

/** Màn đăng nhập thật — gọi `POST /api/auth/login`, cookie phiên do backend cấp. */
function DangNhap() {
  const { dangNhap } = useRole();
  const [username, setUsername] = useState("quan_ly");
  const [password, setPassword] = useState(MAT_KHAU_DEMO);
  const [hienMatKhau, setHienMatKhau] = useState(false);
  const [dangGui, setDangGui] = useState(false);
  const [loi, setLoi] = useState<string | null>(null);

  const thucHienDangNhap = async (u: string, p: string) => {
    if (!u.trim() || !p) return;
    setLoi(null);
    setDangGui(true);
    try {
      const tb = await dangNhap(u.trim(), p);
      toast.success(tb);
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Đăng nhập thất bại.";
      setLoi(msg);
      toast.error(msg);
    } finally {
      setDangGui(false);
    }
  };

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    await thucHienDangNhap(username, password);
  };

  return (
    <div className="grid min-h-screen bg-background lg:grid-cols-12">
      {/* Cột trái — Giới thiệu kiến trúc & điểm nhấn nghiệp vụ */}
      <div className="hidden flex-col justify-between bg-sidebar p-10 text-sidebar-foreground lg:col-span-5 lg:flex xl:col-span-6 xl:p-14">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground shadow-sm">
              <Wrench className="size-5" />
            </div>
            <div>
              <div className="text-lg font-bold tracking-tight text-sidebar-accent-foreground">
                GarageTools<span className="text-sidebar-primary"> AI</span>
              </div>
              <div className="text-[11px] uppercase tracking-[0.16em] opacity-65">
                Hệ thống Quản trị Xưởng Dịch vụ Ô tô
              </div>
            </div>
          </div>
          <span className="rounded-full border border-sidebar-border bg-sidebar-accent px-3 py-1 font-mono text-[11px] text-sidebar-accent-foreground">
            AIA331 · Nhóm 23
          </span>
        </div>

        <div className="my-auto py-8">
          <div className="inline-flex items-center gap-2 rounded-full border border-sidebar-border bg-sidebar-accent/70 px-3 py-1 text-xs font-medium text-sidebar-accent-foreground">
            <Sparkles className="size-3.5 text-sidebar-primary" />
            Vận hành chuẩn xác · AI có kiểm duyệt con người
          </div>
          <h1 className="mt-4 text-2xl font-bold leading-snug tracking-tight text-sidebar-accent-foreground xl:text-3xl">
            Quản lý trọn vẹn vòng đời sửa chữa ô tô từ tiếp nhận đến quyết toán.
          </h1>
          <p className="mt-3 max-w-xl text-sm leading-relaxed opacity-80">
            Mọi số liệu tài chính và tồn kho phụ tùng được kiểm soát chặt chẽ bởi CSDL giao dịch.
            Trợ lý AI đóng vai trò tham mưu tốc độ cao và luôn đi qua bước phê duyệt trước khi sử
            dụng.
          </p>

          <div className="mt-8 grid gap-3.5 sm:grid-cols-2">
            {[
              {
                tieuDe: "Điều phối Kanban 6 bước",
                moTa: "Theo dõi trực quan Tiếp nhận → Kiểm tra → Báo giá → Sửa chữa → Hoàn thành, hỗ trợ kéo tiến và kéo lùi linh hoạt.",
              },
              {
                tieuDe: "3 Trợ lý AI + Human Review",
                moTa: "Tóm tắt lịch sử xe (AI01), Giải thích dịch vụ (AI02), Soạn diễn giải báo giá (AI03) có kiểm duyệt.",
              },
              {
                tieuDe: "Chốt chặn giá từ CSDL",
                moTa: "AI không tự quyết định giá tiền; đơn giá dịch vụ/phụ tùng và tổng hoá đơn luôn lấy từ Backend.",
              },
              {
                tieuDe: "Phân quyền RBAC 4 vai trò",
                moTa: "Tách bạch quyền hạn Quản lý, Lễ tân, Kỹ thuật viên (cô lập theo phiếu phân công) và Thu ngân.",
              },
            ].map((item) => (
              <div
                key={item.tieuDe}
                className="rounded-lg border border-sidebar-border bg-sidebar-accent/50 p-3.5"
              >
                <div className="flex items-center gap-2 text-xs font-semibold text-sidebar-accent-foreground">
                  <CheckCircle2 className="size-3.5 shrink-0 text-sidebar-primary" />
                  {item.tieuDe}
                </div>
                <p className="mt-1.5 text-xs leading-relaxed opacity-75">{item.moTa}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="flex flex-wrap items-center justify-between gap-2 border-t border-sidebar-border pt-5 text-xs opacity-65">
          <span className="flex items-center gap-1.5">
            <Lock className="size-3.5" />
            Cookie phiên ký số HMAC-SHA256 (HttpOnly) · Mật khẩu băm Argon2id / PBKDF2
          </span>
          <span className="font-mono text-[11px]">FastAPI + React 19</span>
        </div>
      </div>

      {/* Cột phải — Form đăng nhập & Chọn nhanh tài khoản theo vai trò */}
      <div className="flex flex-col justify-center px-4 py-8 sm:px-8 lg:col-span-7 xl:col-span-6 xl:px-14">
        <div className="mx-auto w-full max-w-lg space-y-6">
          {/* Logo trên màn hình nhỏ */}
          <div className="flex items-center gap-2.5 lg:hidden">
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

          <div className="rounded-xl border bg-card p-6 shadow-card sm:p-7">
            <div className="mb-5">
              <h2 className="text-xl font-bold tracking-tight text-foreground">
                Đăng nhập hệ thống
              </h2>
              <p className="mt-1 text-xs text-muted-foreground">
                Nhập tài khoản nhân sự hoặc bấm chọn một trong 4 vai trò mẫu bên dưới để đăng nhập
                nhanh.
              </p>
            </div>

            {loi && (
              <div className="mb-4 flex items-start gap-2 rounded-md border border-destructive/30 bg-danger-soft px-3 py-2.5 text-xs text-destructive">
                <AlertCircle className="mt-0.5 size-4 shrink-0" />
                <span>{loi}</span>
              </div>
            )}

            <form onSubmit={submit} className="space-y-4">
              <div className="space-y-1.5">
                <label htmlFor="username" className="text-xs font-medium text-muted-foreground">
                  Tên đăng nhập
                </label>
                <Input
                  id="username"
                  autoComplete="username"
                  value={username}
                  onChange={(e) => {
                    setUsername(e.target.value);
                    if (loi) setLoi(null);
                  }}
                  placeholder="VD: quan_ly, le_tan, ky_thuat_vien, thu_ngan"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label htmlFor="password" className="text-xs font-medium text-muted-foreground">
                    Mật khẩu
                  </label>
                  <span className="font-mono text-[11px] text-muted-foreground">
                    Mặc định demo: <b>{MAT_KHAU_DEMO}</b>
                  </span>
                </div>
                <div className="relative">
                  <Input
                    id="password"
                    type={hienMatKhau ? "text" : "password"}
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      if (loi) setLoi(null);
                    }}
                    placeholder="••••••••"
                    className="pr-9"
                    required
                  />
                  <button
                    type="button"
                    tabIndex={-1}
                    onClick={() => setHienMatKhau((v) => !v)}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                    aria-label={hienMatKhau ? "Ẩn mật khẩu" : "Hiện mật khẩu"}
                  >
                    {hienMatKhau ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
                  </button>
                </div>
              </div>

              <Button
                type="submit"
                className="w-full gap-2"
                disabled={dangGui || !username.trim() || !password}
              >
                {dangGui ? "Đang xác thực phiên…" : "Đăng nhập vào xưởng"}
                {!dangGui && <ArrowRight className="size-4" />}
              </Button>
            </form>
          </div>

          {/* Khu vực chọn nhanh 4 vai trò để test phân quyền */}
          <div className="rounded-xl border bg-card p-5 shadow-card">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                <Users className="size-3.5 text-primary" />
                Đăng nhập nhanh 4 vai trò (Kiểm thử RBAC)
              </div>
              <span className="text-[11px] text-muted-foreground">1 chạm để vào ngay</span>
            </div>

            <div className="grid gap-2.5 sm:grid-cols-2">
              {TAI_KHOAN_DEMO.map((tk) => {
                const dangChon = username === tk.username;
                return (
                  <div
                    key={tk.username}
                    onClick={() => {
                      setUsername(tk.username);
                      setPassword(MAT_KHAU_DEMO);
                      setLoi(null);
                    }}
                    className={cn(
                      "group flex cursor-pointer flex-col justify-between rounded-lg border p-3 text-left transition-all",
                      dangChon
                        ? "border-primary bg-primary/5 ring-1 ring-primary/30"
                        : "hover:border-primary/40 hover:bg-muted/50",
                    )}
                  >
                    <div>
                      <div className="flex items-center justify-between gap-2">
                        <span
                          className={cn(
                            "inline-flex items-center rounded border px-1.5 py-0.5 text-[10px] font-semibold",
                            tk.badgeClass,
                          )}
                        >
                          {tk.vaiTro}
                        </span>
                        <code className="font-mono text-[11px] text-muted-foreground">
                          @{tk.username}
                        </code>
                      </div>
                      <div className="mt-1.5 text-xs font-semibold text-foreground">
                        {tk.fullName}
                      </div>
                      <p className="mt-1 line-clamp-2 text-[11px] leading-relaxed text-muted-foreground">
                        {tk.moTa}
                      </p>
                    </div>
                    <div className="mt-2.5 flex items-center justify-between border-t pt-2">
                      <span className="text-[10px] text-muted-foreground">
                        MK: <code className="font-mono">{MAT_KHAU_DEMO}</code>
                      </span>
                      <button
                        type="button"
                        disabled={dangGui}
                        onClick={(e) => {
                          e.stopPropagation();
                          setUsername(tk.username);
                          setPassword(MAT_KHAU_DEMO);
                          void thucHienDangNhap(tk.username, MAT_KHAU_DEMO);
                        }}
                        className="inline-flex items-center gap-1 text-[11px] font-semibold text-primary hover:underline disabled:opacity-50"
                      >
                        Vào ngay
                        <ArrowRight className="size-3" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
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
  const { trangThaiPhien, user, dangNhap, dangXuat } = useRole();
  const N = useNhan();
  const [dangDoiVaiTro, setDangDoiVaiTro] = useState(false);

  const chuyenNhanhVaiTro = async (u: string) => {
    if (!u || u === user?.username || dangDoiVaiTro) return;
    setDangDoiVaiTro(true);
    try {
      const tb = await dangNhap(u, MAT_KHAU_DEMO);
      toast.success(tb);
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Không thể chuyển nhanh tài khoản.");
    } finally {
      setDangDoiVaiTro(false);
    }
  };

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
            GarageTools AI — Hệ thống Quản trị Xưởng Dịch vụ &amp; Trợ lý AI
          </div>
          <div className="ml-auto flex items-center gap-2">
            {user && (
              <div className="hidden items-center gap-2 rounded-md border bg-muted/40 px-2.5 py-1 text-xs sm:flex">
                <span className="rounded bg-primary/10 px-1.5 py-0.5 text-[10px] font-semibold text-primary">
                  {N.vaiTro(user.role)}
                </span>
                <span className="font-medium text-foreground">{user.full_name}</span>
                <span className="font-mono text-[11px] text-muted-foreground">
                  @{user.username}
                </span>
              </div>
            )}
            <div className="hidden items-center gap-1 rounded-md border bg-background p-0.5 xl:flex">
              <span className="px-1.5 text-[10px] font-medium text-muted-foreground">
                Đổi vai trò:
              </span>
              {TAI_KHOAN_DEMO.map((tk) => {
                const active = user?.username === tk.username;
                return (
                  <button
                    key={tk.username}
                    type="button"
                    disabled={active || dangDoiVaiTro}
                    onClick={() => void chuyenNhanhVaiTro(tk.username)}
                    title={`Chuyển sang ${tk.vaiTro} (@${tk.username})`}
                    className={cn(
                      "rounded px-2 py-0.5 text-[11px] font-medium transition-colors",
                      active
                        ? "bg-primary text-primary-foreground"
                        : "text-muted-foreground hover:bg-muted hover:text-foreground",
                    )}
                  >
                    {tk.vaiTro}
                  </button>
                );
              })}
            </div>
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
