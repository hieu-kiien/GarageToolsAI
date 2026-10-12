import { createFileRoute, Link } from "@tanstack/react-router";
import { useSuspenseQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { ArrowLeft, Check, Sparkles, Phone, Gauge, Fingerprint, Calendar, MapPin, User } from "lucide-react";
import { api, q } from "@/services/api";
import { ensureLookups, useLookups } from "@/services/lookups";
import { useRole, vnd, fmtTime, STATUS_LABEL, STATUS_ORDER } from "@/lib/rbac";
import { PageHeader, Panel, Plate, StatusPill, PriorityPill, NoAccess, Empty } from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/repair-orders/$id")({
  head: () => ({ meta: [
    { title: "Chi tiết lệnh sửa chữa — GarageTools AI" },
    { name: "description", content: "Không gian làm việc lệnh sửa chữa: khách hàng, xe, phụ tùng, tiền công, tiến độ và ghi chú kỹ thuật." },
    { property: "og:title", content: "Chi tiết lệnh sửa chữa — GarageTools AI" },
    { property: "og:description", content: "Repair Order Detail Workspace." },
  ] }),
  loader: ({ context: { queryClient: qc }, params }) => Promise.all([qc.ensureQueryData(q.order(params.id)), ensureLookups(qc)]),
  component: Detail,
});

function Detail() {
  const { id } = Route.useParams();
  const { can, user, role } = useRole();
  const { data: ro } = useSuspenseQuery(q.order(id));
  const L = useLookups();
  const qc = useQueryClient();
  const [note, setNote] = useState("");
  const toggle = useMutation({ mutationFn: (t: string) => api.toggleTask(id, t), onSuccess: () => qc.invalidateQueries() });
  const addNote = useMutation({ mutationFn: () => api.addNote(id, { author: user, body: note }), onSuccess: () => { setNote(""); qc.invalidateQueries(); toast.success("Đã thêm ghi chú"); } });
  if (!can("orders")) return <NoAccess />;
  const v = L.vehicle(ro.vehicle_id)!;
  const c = L.customer(ro.customer_id)!;
  const step = STATUS_ORDER.indexOf(ro.status);
  const done = ro.tasks.filter((t) => t.done).length;
  const canEditTasks = role === "technician" || role === "manager";

  return (
    <>
      <PageHeader eyebrow={<Link to="/repair-orders" className="inline-flex items-center gap-1 hover:text-foreground"><ArrowLeft className="size-3" />Lệnh sửa chữa</Link>}
        title={`${ro.code} · ${v.make} ${v.model}`}
        desc={ro.complaint}
        actions={<><StatusPill s={ro.status} /><PriorityPill p={ro.priority} />
          {ro.quotation_id && can("ai") && <Button variant="outline" size="sm" asChild><Link to="/ai-review" search={{ draft: ro.quotation_id }}><Sparkles className="size-4" />Báo giá AI nháp</Link></Button>}</>} />

      <div className="border-b bg-card px-6 py-4 lg:px-8">
        <ol className="flex gap-1 overflow-x-auto">
          {STATUS_ORDER.map((s, i) => (
            <li key={s} className="flex min-w-[120px] flex-1 flex-col gap-1.5">
              <div className={cn("h-1 rounded-full", i <= step ? "bg-primary" : "bg-muted")} />
              <span className={cn("text-[11px]", i === step ? "font-semibold text-foreground" : "text-muted-foreground")}>{STATUS_LABEL[s]}</span>
            </li>
          ))}
        </ol>
      </div>

      <div className="grid gap-6 p-6 lg:p-8 xl:grid-cols-3">
        <div className="space-y-6 xl:col-span-2">
          <Panel title="Phụ tùng" bodyClass="p-0">
            {ro.parts.length === 0 ? <div className="p-4"><Empty title="Chưa có phụ tùng" desc="Phụ tùng được thêm sau khi báo giá được duyệt." /></div> : (
              <table className="w-full text-sm">
                <thead className="text-left text-[11px] uppercase tracking-wider text-muted-foreground"><tr className="border-b"><th className="px-4 py-2 font-medium">Mã / Tên</th><th className="px-4 py-2 text-right font-medium">SL</th><th className="px-4 py-2 text-right font-medium">Đơn giá</th><th className="px-4 py-2 text-right font-medium">Thành tiền</th></tr></thead>
                <tbody className="divide-y">{ro.parts.map((p) => (
                  <tr key={p.id}><td className="px-4 py-2.5"><div>{p.name}</div><div className="font-mono text-[11px] text-muted-foreground">{p.sku}</div></td><td className="tabular px-4 text-right">{p.qty}</td><td className="tabular px-4 text-right">{vnd(p.unit_price)}</td><td className="tabular px-4 text-right font-medium">{vnd(p.qty * p.unit_price)}</td></tr>
                ))}</tbody>
              </table>)}
          </Panel>
          <Panel title="Tiền công thợ" bodyClass="p-0">
            {ro.labor.length === 0 ? <div className="p-4"><Empty title="Chưa có hạng mục công" /></div> : (
              <table className="w-full text-sm">
                <thead className="text-left text-[11px] uppercase tracking-wider text-muted-foreground"><tr className="border-b"><th className="px-4 py-2 font-medium">Hạng mục</th><th className="px-4 py-2 font-medium">KTV</th><th className="px-4 py-2 text-right font-medium">Giờ</th><th className="px-4 py-2 text-right font-medium">Đơn giá/giờ</th><th className="px-4 py-2 text-right font-medium">Thành tiền</th></tr></thead>
                <tbody className="divide-y">{ro.labor.map((l) => (
                  <tr key={l.id}><td className="px-4 py-2.5">{l.description}</td><td className="px-4 text-muted-foreground">{L.tech(l.technician_id ?? null)?.full_name ?? "—"}</td><td className="tabular px-4 text-right">{l.hours}</td><td className="tabular px-4 text-right">{vnd(l.rate)}</td><td className="tabular px-4 text-right font-medium">{vnd(l.hours * l.rate)}</td></tr>
                ))}</tbody>
              </table>)}
            <dl className="space-y-1.5 border-t bg-muted/40 px-4 py-3 text-sm">
              <div className="flex justify-between"><dt className="text-muted-foreground">Phụ tùng</dt><dd className="tabular">{vnd(ro.totals.parts_subtotal)}</dd></div>
              <div className="flex justify-between"><dt className="text-muted-foreground">Tiền công</dt><dd className="tabular">{vnd(ro.totals.labor_subtotal)}</dd></div>
              <div className="flex justify-between"><dt className="text-muted-foreground">VAT 10%</dt><dd className="tabular">{vnd(ro.totals.vat)}</dd></div>
              <div className="flex justify-between border-t pt-1.5 font-semibold"><dt>Tổng cộng</dt><dd className="tabular">{vnd(ro.totals.grand_total)}</dd></div>
              <p className="pt-1 text-[11px] text-muted-foreground">Tổng tiền do hệ thống tính từ dữ liệu đã duyệt.</p>
            </dl>
          </Panel>
          <Panel title="Ghi chú kỹ thuật">
            <div className="flex gap-2">
              <Textarea value={note} onChange={(e) => setNote(e.target.value)} placeholder="Ghi nhận phát hiện, đo đạc, khuyến nghị…" className="min-h-[60px]" />
              <Button disabled={!note.trim() || addNote.isPending} onClick={() => addNote.mutate()}>Lưu</Button>
            </div>
            <ol className="mt-4 space-y-4 border-l pl-4">
              {ro.notes.length === 0 && <li className="text-sm text-muted-foreground">Chưa có ghi chú.</li>}
              {ro.notes.map((n) => (
                <li key={n.id} className="relative"><span className="absolute -left-[21px] top-1.5 size-2 rounded-full bg-primary" />
                  <div className="text-xs text-muted-foreground"><span className="font-medium text-foreground">{n.author}</span> · {fmtTime(n.created_at)}</div>
                  <p className="mt-0.5 text-sm">{n.body}</p></li>
              ))}
            </ol>
          </Panel>
        </div>

        <div className="space-y-6">
          <Panel title="Xe">
            <div className="flex items-center justify-between"><Plate className="text-sm">{v.plate}</Plate><span className="text-xs text-muted-foreground">{v.color} · {v.year}</span></div>
            <dl className="mt-4 space-y-2.5 text-sm">
              <Row icon={Fingerprint} k="VIN" v={<span className="font-mono text-xs">{v.vin}</span>} />
              <Row icon={Gauge} k="ODO" v={<span className="tabular">{v.odo_km.toLocaleString("vi-VN")} km</span>} />
              <Row icon={MapPin} k="Vị trí" v={L.bay(ro.bay_id)?.name ?? "—"} />
              <Row icon={User} k="KTV" v={L.tech(ro.technician_id)?.full_name ?? "Chưa phân công"} />
              <Row icon={Calendar} k="Hẹn giao" v={fmtTime(ro.promised_at)} />
            </dl>
          </Panel>
          <Panel title="Khách hàng">
            <div className="font-medium">{c.full_name}</div>
            <div className="mt-1 flex items-center gap-1.5 text-sm text-muted-foreground"><Phone className="size-3.5" />{c.phone}</div>
            {c.email && <div className="text-sm text-muted-foreground">{c.email}</div>}
          </Panel>
          <Panel title="Tiến độ công việc" action={<span className="tabular text-xs text-muted-foreground">{done}/{ro.tasks.length}</span>}>
            <ul className="space-y-1">
              {ro.tasks.map((t) => (
                <li key={t.id}>
                  <button disabled={!canEditTasks} onClick={() => toggle.mutate(t.id)} className="flex w-full items-center gap-2.5 rounded-md px-2 py-1.5 text-left text-sm hover:bg-muted disabled:cursor-default">
                    <span className={cn("flex size-4 items-center justify-center rounded border", t.done && "border-primary bg-primary text-primary-foreground")}>{t.done && <Check className="size-3" />}</span>
                    <span className={cn(t.done && "text-muted-foreground line-through")}>{t.title}</span>
                  </button>
                </li>
              ))}
              {ro.tasks.length === 0 && <li className="text-sm text-muted-foreground">Chưa có hạng mục.</li>}
            </ul>
          </Panel>
        </div>
      </div>
    </>
  );
}

function Row({ icon: I, k, v }: { icon: typeof Phone; k: string; v: React.ReactNode }) {
  return <div className="flex items-center justify-between gap-3"><dt className="flex items-center gap-1.5 text-muted-foreground"><I className="size-3.5" />{k}</dt><dd className="text-right">{v}</dd></div>;
}
