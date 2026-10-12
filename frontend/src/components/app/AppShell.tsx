import { Link, useRouterState } from "@tanstack/react-router";
import { useState, type ReactNode } from "react";
import {
  LayoutDashboard, KanbanSquare, ClipboardList, ScanSearch, Sparkles, Boxes, Receipt, Menu, X, Search, Bell, Wrench,
} from "lucide-react";
import { useRole, ROLE_LABEL, type Area } from "@/lib/rbac";
import type { Role } from "@/types";
import { cn } from "@/lib/utils";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const NAV: { group: string; items: { to: string; label: string; icon: typeof Menu; area: Area }[] }[] = [
  { group: "Vận hành", items: [
    { to: "/", label: "Tổng quan", icon: LayoutDashboard, area: "dashboard" },
    { to: "/workflow", label: "Bảng điều phối", icon: KanbanSquare, area: "board" },
    { to: "/repair-orders", label: "Lệnh sửa chữa", icon: ClipboardList, area: "orders" },
    { to: "/inspection", label: "Kiểm tra tiếp nhận", icon: ScanSearch, area: "inspection" },
  ] },
  { group: "Trợ lý", items: [{ to: "/ai-review", label: "AI & Duyệt nháp", icon: Sparkles, area: "ai" }] },
  { group: "Kho & Tài chính", items: [
    { to: "/inventory", label: "Kho phụ tùng", icon: Boxes, area: "inventory" },
    { to: "/finance", label: "Hoá đơn & Thanh toán", icon: Receipt, area: "finance" },
  ] },
];

function Sidebar({ onNav }: { onNav?: () => void }) {
  const { can, role, user } = useRole();
  const path = useRouterState({ select: (s) => s.location.pathname });
  return (
    <div className="flex h-full flex-col bg-sidebar text-sidebar-foreground">
      <div className="flex h-14 items-center gap-2.5 border-b border-sidebar-border px-5">
        <div className="flex size-7 items-center justify-center rounded-md bg-sidebar-primary text-sidebar-primary-foreground"><Wrench className="size-4" /></div>
        <div className="leading-tight">
          <div className="text-sm font-semibold text-sidebar-accent-foreground">GarageTools<span className="text-sidebar-primary"> AI</span></div>
          <div className="text-[10px] uppercase tracking-[0.16em] opacity-60">Xưởng Quận 7</div>
        </div>
      </div>
      <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-4">
        {NAV.map((g) => {
          const items = g.items.filter((i) => can(i.area));
          if (!items.length) return null;
          return (
            <div key={g.group}>
              <div className="mb-1.5 px-2 text-[10px] font-semibold uppercase tracking-[0.16em] opacity-50">{g.group}</div>
              {items.map((i) => {
                const active = i.to === "/" ? path === "/" : path.startsWith(i.to);
                return (
                  <Link key={i.to} to={i.to} onClick={onNav}
                    className={cn("group flex items-center gap-2.5 rounded-md px-2 py-1.5 text-[13px] transition-colors",
                      active ? "bg-sidebar-accent font-medium text-sidebar-accent-foreground" : "hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground")}>
                    <i.icon className={cn("size-4", active ? "text-sidebar-primary" : "opacity-70")} />
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
            {user.split(" ").slice(-1)[0]?.[0]}
          </div>
          <div className="min-w-0 leading-tight">
            <div className="truncate text-[13px] font-medium text-sidebar-accent-foreground">{user}</div>
            <div className="text-[11px] opacity-60">{ROLE_LABEL[role]}</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function AppShell({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const { role, setRole } = useRole();
  return (
    <div className="min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-60 lg:block"><Sidebar /></aside>
      {open && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-foreground/40" onClick={() => setOpen(false)} />
          <div className="absolute inset-y-0 left-0 w-64"><Sidebar onNav={() => setOpen(false)} /></div>
          <button className="absolute left-[17rem] top-4 rounded-md bg-card p-1.5" onClick={() => setOpen(false)} aria-label="Đóng menu"><X className="size-4" /></button>
        </div>
      )}
      <div className="lg:pl-60">
        <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b bg-card/90 px-4 backdrop-blur lg:px-8">
          <button className="rounded-md p-1.5 hover:bg-muted lg:hidden" onClick={() => setOpen(true)} aria-label="Mở menu"><Menu className="size-5" /></button>
          <div className="relative hidden max-w-sm flex-1 md:block">
            <Search className="absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <input placeholder="Tìm biển số, VIN, khách hàng, mã lệnh…" className="h-9 w-full rounded-md border bg-background pl-8 pr-12 text-sm outline-none focus:ring-2 focus:ring-ring/30" />
            <kbd className="absolute right-2 top-1/2 -translate-y-1/2 rounded border bg-card px-1.5 font-mono text-[10px] text-muted-foreground">⌘K</kbd>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <button className="relative rounded-md p-2 hover:bg-muted" aria-label="Thông báo">
              <Bell className="size-4" /><span className="absolute right-1.5 top-1.5 size-1.5 rounded-full bg-destructive" />
            </button>
            <span className="hidden text-xs text-muted-foreground sm:inline">Vai trò</span>
            <Select value={role} onValueChange={(v) => setRole(v as Role)}>
              <SelectTrigger className="h-9 w-[150px] text-sm"><SelectValue /></SelectTrigger>
              <SelectContent>
                {(Object.keys(ROLE_LABEL) as Role[]).map((r) => <SelectItem key={r} value={r}>{ROLE_LABEL[r]}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
        </header>
        <main>{children}</main>
      </div>
    </div>
  );
}
