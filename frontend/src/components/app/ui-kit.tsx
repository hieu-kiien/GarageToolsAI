import type { ReactNode } from "react";
import { cn } from "@/lib/utils";
import { STATUS_LABEL, PRIORITY_LABEL, INVOICE_LABEL } from "@/lib/rbac";
import type { RepairStatus, Priority, InvoiceStatus } from "@/types";
import { ShieldAlert } from "lucide-react";

export function PageHeader({ eyebrow, title, desc, actions }: { eyebrow?: ReactNode; title: string; desc?: string; actions?: ReactNode }) {
  return (
    <div className="flex flex-col gap-4 border-b bg-card px-6 py-5 md:flex-row md:items-end md:justify-between lg:px-8">
      <div>
        {eyebrow && <div className="mb-1 text-xs font-medium uppercase tracking-[0.14em] text-muted-foreground">{eyebrow}</div>}
        <h1 className="text-[22px] font-semibold tracking-tight text-foreground">{title}</h1>
        {desc && <p className="mt-1 max-w-2xl text-sm text-muted-foreground">{desc}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

export function Panel({ title, action, children, className, bodyClass }: { title?: ReactNode; action?: ReactNode; children: ReactNode; className?: string; bodyClass?: string }) {
  return (
    <section className={cn("rounded-lg border bg-card shadow-card", className)}>
      {title && (
        <header className="flex items-center justify-between border-b px-4 py-3">
          <h2 className="text-sm font-semibold text-foreground">{title}</h2>
          {action}
        </header>
      )}
      <div className={cn("p-4", bodyClass)}>{children}</div>
    </section>
  );
}

const tone = {
  neutral: "bg-secondary text-secondary-foreground border-border",
  info: "bg-info-soft text-accent-foreground border-primary/20",
  success: "bg-success-soft text-success border-success/25",
  warning: "bg-warning-soft text-foreground border-warning/40",
  danger: "bg-danger-soft text-destructive border-destructive/25",
  ai: "bg-ai-soft text-ai border-ai/25",
} as const;
export type Tone = keyof typeof tone;

export function Pill({ t = "neutral", children, dot, className }: { t?: Tone; children: ReactNode; dot?: boolean; className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-1.5 whitespace-nowrap rounded-md border px-1.5 py-0.5 text-[11px] font-medium", tone[t], className)}>
      {dot && <span className="size-1.5 rounded-full bg-current" />}
      {children}
    </span>
  );
}

const statusTone: Record<RepairStatus, Tone> = { intake: "neutral", diagnosis: "info", awaiting_approval: "warning", in_repair: "info", qc: "ai", delivered: "success" };
export const StatusPill = ({ s }: { s: RepairStatus }) => <Pill t={statusTone[s]} dot>{STATUS_LABEL[s]}</Pill>;
const prioTone: Record<Priority, Tone> = { normal: "neutral", high: "warning", urgent: "danger" };
export const PriorityPill = ({ p }: { p: Priority }) => <Pill t={prioTone[p]}>{PRIORITY_LABEL[p]}</Pill>;
const invTone: Record<InvoiceStatus, Tone> = { unpaid: "danger", partial: "warning", paid: "success", void: "neutral" };
export const InvoicePill = ({ s }: { s: InvoiceStatus }) => <Pill t={invTone[s]} dot>{INVOICE_LABEL[s]}</Pill>;

export function Plate({ children, className }: { children: ReactNode; className?: string }) {
  return <span className={cn("inline-flex rounded border border-foreground/25 bg-card px-1.5 py-px font-mono text-[12px] font-semibold tracking-wide text-foreground", className)}>{children}</span>;
}

export function Stat({ label, value, sub, icon, accent }: { label: string; value: ReactNode; sub?: ReactNode; icon?: ReactNode; accent?: string }) {
  return (
    <div className="rounded-lg border bg-card p-4 shadow-card">
      <div className="flex items-center justify-between text-xs font-medium text-muted-foreground">
        {label}
        <span className={cn("text-muted-foreground", accent)}>{icon}</span>
      </div>
      <div className="tabular mt-2 text-2xl font-semibold tracking-tight text-foreground">{value}</div>
      {sub && <div className="mt-1 text-xs text-muted-foreground">{sub}</div>}
    </div>
  );
}

export function NoAccess() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center p-8">
      <div className="max-w-sm text-center">
        <div className="mx-auto mb-4 flex size-11 items-center justify-center rounded-full bg-danger-soft text-destructive"><ShieldAlert className="size-5" /></div>
        <h2 className="font-semibold">Không có quyền truy cập</h2>
        <p className="mt-1 text-sm text-muted-foreground">Vai trò hiện tại không được phép mở màn hình này. Đổi vai trò ở góc trên bên phải hoặc liên hệ Quản lý.</p>
      </div>
    </div>
  );
}

export function Empty({ title, desc }: { title: string; desc?: string }) {
  return (
    <div className="rounded-md border border-dashed px-4 py-8 text-center">
      <div className="text-sm font-medium">{title}</div>
      {desc && <div className="mt-1 text-xs text-muted-foreground">{desc}</div>}
    </div>
  );
}
