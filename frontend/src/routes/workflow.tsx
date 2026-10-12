import { createFileRoute, Link } from "@tanstack/react-router";
import { useSuspenseQuery, useQueryClient, useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { ChevronRight, User, MapPin, Clock } from "lucide-react";
import { api, q } from "@/services/api";
import { ensureLookups, useLookups } from "@/services/lookups";
import { useRole, STATUS_LABEL, STATUS_ORDER, fmtTime } from "@/lib/rbac";
import { PageHeader, Plate, PriorityPill, NoAccess } from "@/components/app/ui-kit";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetDescription } from "@/components/ui/sheet";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import type { RepairOrder, RepairStatus } from "@/types";

export const Route = createFileRoute("/workflow")({
  head: () => ({ meta: [
    { title: "Bảng điều phối sửa chữa — GarageTools AI" },
    { name: "description", content: "Kanban luồng sửa chữa từ tiếp nhận đến giao xe, phân công kỹ thuật viên và cầu nâng." },
    { property: "og:title", content: "Bảng điều phối sửa chữa — GarageTools AI" },
    { property: "og:description", content: "Repair Workflow Board cho xưởng dịch vụ ô tô." },
  ] }),
  loader: ({ context: { queryClient: qc } }) => Promise.all([qc.ensureQueryData(q.orders()), ensureLookups(qc)]),
  component: Board,
});

const NOW = Date.UTC(2026, 9, 12, 11);

function Board() {
  const { can, role } = useRole();
  const { data: orders } = useSuspenseQuery(q.orders());
  const L = useLookups();
  const qc = useQueryClient();
  const [sel, setSel] = useState<RepairOrder | null>(null);
  const [drag, setDrag] = useState<string | null>(null);
  const move = useMutation({
    mutationFn: ({ id, status }: { id: string; status: RepairStatus }) => api.updateStatus(id, status),
    onSuccess: (ro) => { qc.invalidateQueries(); toast.success(`${ro.code} → ${STATUS_LABEL[ro.status]}`); },
  });
  const assign = useMutation({
    mutationFn: (v: { id: string; technician_id: string | null; bay_id: string | null }) => api.assign(v.id, v),
    onSuccess: (ro) => { qc.invalidateQueries(); setSel(ro); toast.success("Đã cập nhật phân công"); },
  });
  if (!can("board")) return <NoAccess />;
  const canAssign = role === "manager" || role === "receptionist";

  const tryMove = (id: string, status: RepairStatus) => {
    if (status === "in_repair" && orders.find((o) => o.id === id)?.status === "awaiting_approval" && role !== "manager")
      return toast.error("Cần Quản lý duyệt báo giá trước khi chuyển sang Đang sửa chữa");
    move.mutate({ id, status });
    return undefined;
  };

  return (
    <>
      <PageHeader eyebrow="Vận hành" title="Bảng điều phối sửa chữa" desc="Kéo thả thẻ giữa các cột để cập nhật trạng thái. Nhấp vào thẻ để phân công kỹ thuật viên và cầu nâng." />
      <div className="overflow-x-auto p-4 lg:p-6">
        <div className="flex min-w-max gap-3">
          {STATUS_ORDER.map((st) => {
            const col = orders.filter((o) => o.status === st);
            return (
              <div key={st} onDragOver={(e) => e.preventDefault()} onDrop={() => { if (drag) tryMove(drag, st); setDrag(null); }}
                className="flex w-72 flex-col rounded-lg border bg-muted/50">
                <div className="flex items-center justify-between px-3 py-2.5">
                  <span className="text-[13px] font-semibold">{STATUS_LABEL[st]}</span>
                  <span className="tabular rounded bg-card px-1.5 text-xs text-muted-foreground">{col.length}</span>
                </div>
                <div className="flex min-h-[60vh] flex-col gap-2 px-2 pb-2">
                  {col.map((o) => {
                    const v = L.vehicle(o.vehicle_id)!;
                    const late = o.status !== "delivered" && new Date(o.promised_at).getTime() < NOW;
                    const done = o.tasks.filter((t) => t.done).length;
                    return (
                      <button key={o.id} draggable onDragStart={() => setDrag(o.id)} onClick={() => setSel(o)}
                        className="cursor-grab rounded-md border bg-card p-3 text-left shadow-card transition hover:border-primary/40 active:cursor-grabbing">
                        <div className="flex items-center justify-between"><Plate>{v.plate}</Plate>{o.priority !== "normal" && <PriorityPill p={o.priority} />}</div>
                        <div className="mt-2 text-[13px] font-medium">{v.make} {v.model}</div>
                        <div className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">{o.complaint}</div>
                        {o.tasks.length > 0 && <div className="mt-2.5 h-1 rounded-full bg-muted"><div className="h-full rounded-full bg-primary" style={{ width: `${(done / o.tasks.length) * 100}%` }} /></div>}
                        <div className="mt-2.5 flex items-center justify-between text-[11px] text-muted-foreground">
                          <span className="flex items-center gap-1"><User className="size-3" />{L.tech(o.technician_id)?.full_name.split(" ").slice(-1)[0] ?? "—"}</span>
                          <span className="flex items-center gap-1"><MapPin className="size-3" />{L.bay(o.bay_id)?.name.replace("Cầu nâng", "CN") ?? "—"}</span>
                          <span className={`flex items-center gap-1 tabular ${late ? "font-medium text-destructive" : ""}`}><Clock className="size-3" />{fmtTime(o.promised_at).split(" ")[0]}</span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <Sheet open={!!sel} onOpenChange={(o) => !o && setSel(null)}>
        <SheetContent className="w-full sm:max-w-md">
          {sel && (() => {
            const v = L.vehicle(sel.vehicle_id)!;
            const idx = STATUS_ORDER.indexOf(sel.status);
            return (
              <>
                <SheetHeader>
                  <SheetTitle className="flex items-center gap-2"><Plate>{v.plate}</Plate><span className="font-mono text-sm text-muted-foreground">{sel.code}</span></SheetTitle>
                  <SheetDescription>{v.make} {v.model} · {L.customer(sel.customer_id)?.full_name}</SheetDescription>
                </SheetHeader>
                <div className="space-y-5 px-4">
                  <p className="rounded-md bg-muted p-3 text-sm">{sel.complaint}</p>
                  <div className="space-y-1.5">
                    <label className="text-xs font-medium text-muted-foreground">Kỹ thuật viên</label>
                    <Select disabled={!canAssign} value={sel.technician_id ?? "none"} onValueChange={(t) => assign.mutate({ id: sel.id, technician_id: t === "none" ? null : t, bay_id: sel.bay_id })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent><SelectItem value="none">Chưa phân công</SelectItem>{L.technicians.map((t) => <SelectItem key={t.id} value={t.id}>{t.full_name} — {t.skill}</SelectItem>)}</SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-medium text-muted-foreground">Vị trí cầu nâng / khoang</label>
                    <Select disabled={!canAssign} value={sel.bay_id ?? "none"} onValueChange={(b) => assign.mutate({ id: sel.id, technician_id: sel.technician_id, bay_id: b === "none" ? null : b })}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent><SelectItem value="none">Chưa xếp vị trí</SelectItem>{L.bays.map((b) => <SelectItem key={b.id} value={b.id} disabled={!!b.repair_order_id && b.repair_order_id !== sel.id}>{b.name}{b.repair_order_id && b.repair_order_id !== sel.id ? " (đang dùng)" : ""}</SelectItem>)}</SelectContent>
                    </Select>
                    {!canAssign && <p className="text-[11px] text-muted-foreground">Chỉ Quản lý hoặc Tiếp tân được phân công.</p>}
                  </div>
                  <div className="flex gap-2">
                    {idx < STATUS_ORDER.length - 1 && <Button className="flex-1" onClick={() => { tryMove(sel.id, STATUS_ORDER[idx + 1]!); setSel(null); }}>Chuyển: {STATUS_LABEL[STATUS_ORDER[idx + 1]!]}</Button>}
                    <Button variant="outline" asChild><Link to="/repair-orders/$id" params={{ id: sel.id }}>Chi tiết <ChevronRight className="size-4" /></Link></Button>
                  </div>
                </div>
              </>
            );
          })()}
        </SheetContent>
      </Sheet>
    </>
  );
}
