import { createFileRoute, Link } from "@tanstack/react-router";
import { useSuspenseQuery, useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { Sparkles, ShieldCheck, Trash2, Plus, History, AlertCircle, CheckCircle2, XCircle, Cpu } from "lucide-react";
import { api, q, computeTotals } from "@/services/api";
import { ensureLookups, useLookups } from "@/services/lookups";
import { useRole, vnd, fmtTime, ROLE_LABEL } from "@/lib/rbac";
import { PageHeader, Panel, Plate, Pill, NoAccess } from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { cn } from "@/lib/utils";
import type { AiDraftLine } from "@/types";

export const Route = createFileRoute("/ai-review")({
  validateSearch: (s: Record<string, unknown>): { draft?: string | undefined } => ({ draft: typeof s["draft"] === "string" ? (s["draft"] as string) : undefined }),
  head: () => ({ meta: [
    { title: "Trợ lý AI & Duyệt nháp — GarageTools AI" },
    { name: "description", content: "So sánh song song phân tích AI và màn hình duyệt của Quản lý trước khi xuất báo giá chính thức." },
    { property: "og:title", content: "Trợ lý AI & Duyệt nháp — GarageTools AI" },
    { property: "og:description", content: "Human-in-the-loop review cho báo giá AI." },
  ] }),
  loader: ({ context: { queryClient: qc } }) => Promise.all([qc.ensureQueryData(q.drafts()), qc.ensureQueryData(q.orders()), ensureLookups(qc)]),
  component: Review,
});

const sevTone = { low: "neutral", medium: "warning", high: "danger" } as const;
const sevLabel = { low: "Thấp", medium: "Trung bình", high: "Cao" };

function Review() {
  const { can, role, user } = useRole();
  const search = Route.useSearch();
  const { data: drafts } = useSuspenseQuery(q.drafts());
  const { data: orders } = useSuspenseQuery(q.orders());
  const L = useLookups();
  const qc = useQueryClient();
  const [activeId, setActiveId] = useState(search.draft ?? drafts[0]?.id);
  const draft = drafts.find((d) => d.id === activeId)!;
  const [lines, setLines] = useState<AiDraftLine[]>(draft.lines);
  const [reason, setReason] = useState("");
  useEffect(() => { setLines(draft.lines); setReason(""); }, [draft.id, draft.lines]);
  const audit = useQuery(q.audit(draft.id));
  const isManager = role === "manager";
  const locked = draft.status !== "pending_review" || !isManager;

  const changes = useMemo(() => {
    const out: string[] = [];
    const orig = new Map(draft.lines.map((l) => [l.id, l]));
    lines.forEach((l) => {
      const o = orig.get(l.id);
      if (!o) out.push(`Thêm dòng "${l.name}" (${l.qty} × ${vnd(l.unit_price)})`);
      else {
        if (o.qty !== l.qty) out.push(`"${l.name}": SL ${o.qty} → ${l.qty}`);
        if (o.unit_price !== l.unit_price) out.push(`"${l.name}": đơn giá ${vnd(o.unit_price)} → ${vnd(l.unit_price)}`);
        if (o.name !== l.name) out.push(`Đổi tên "${o.name}" → "${l.name}"`);
      }
    });
    draft.lines.forEach((o) => { if (!lines.find((l) => l.id === o.id)) out.push(`Xoá dòng "${o.name}"`); });
    return out;
  }, [lines, draft.lines]);

  const preview = computeTotals(lines.filter((l) => l.kind === "part"), lines.filter((l) => l.kind === "labor"));

  const review = useMutation({
    mutationFn: (decision: "approve" | "reject") => api.reviewDraft(draft.id, { decision, lines, actor: user, role, changes, reason }),
    onSuccess: (r) => { qc.invalidateQueries(); toast.success(r.draft.status === "approved" ? `Đã xuất báo giá chính thức — ${vnd(r.totals.grand_total)}` : "Đã từ chối bản nháp"); },
    onError: (e: Error) => toast.error(e.message),
  });

  if (!can("ai")) return <NoAccess />;
  const ro = orders.find((o) => o.id === draft.repair_order_id)!;
  const v = L.vehicle(ro.vehicle_id)!;
  const upd = (id: string, patch: Partial<AiDraftLine>) => setLines((ls) => ls.map((l) => (l.id === id ? { ...l, ...patch } : l)));

  return (
    <>
      <PageHeader eyebrow="Trợ lý" title="Trung tâm AI & Duyệt nháp" desc="AI chỉ tạo bản nháp. Mọi báo giá chính thức phải được Quản lý kiểm tra, chỉnh sửa và phê duyệt — mọi thao tác đều được lưu vết." />
      <div className="flex gap-2 overflow-x-auto border-b bg-card px-6 py-3 lg:px-8">
        {drafts.map((d) => { const r = orders.find((o) => o.id === d.repair_order_id)!; return (
          <button key={d.id} onClick={() => setActiveId(d.id)} className={cn("flex shrink-0 items-center gap-2 rounded-md border px-3 py-1.5 text-xs", d.id === activeId ? "border-primary bg-info-soft" : "hover:bg-muted")}>
            <Plate>{L.vehicle(r.vehicle_id)?.plate}</Plate><span className="font-mono">{r.code}</span>
            <Pill t={d.status === "approved" ? "success" : d.status === "rejected" ? "danger" : "warning"}>{d.status === "approved" ? "Đã duyệt" : d.status === "rejected" ? "Từ chối" : "Chờ duyệt"}</Pill>
          </button>); })}
      </div>

      <div className="grid gap-6 p-6 lg:p-8 xl:grid-cols-2">
        {/* AI side */}
        <div className="space-y-4">
          <div className="flex items-center justify-between rounded-lg border border-ai/25 bg-ai-soft px-4 py-3">
            <div className="flex items-center gap-2 text-sm font-semibold text-ai"><Sparkles className="size-4" />Phân tích của AI <span className="font-normal opacity-80">— bản nháp, chưa có giá trị pháp lý</span></div>
            <span className="flex items-center gap-1 text-[11px] text-ai"><Cpu className="size-3" />{draft.model} · tin cậy {Math.round(draft.confidence * 100)}%</span>
          </div>
          <Panel title="Mã lỗi OBD-II">
            {draft.obd_findings.length === 0 ? <p className="text-sm text-muted-foreground">Không có mã lỗi — phân tích dựa trên ghi chú kỹ thuật.</p> : (
              <ul className="space-y-2">{draft.obd_findings.map((f) => (
                <li key={f.code} className="flex items-center gap-3 rounded-md border p-2.5"><span className="rounded bg-foreground px-1.5 py-0.5 font-mono text-xs font-semibold text-background">{f.code}</span><span className="flex-1 text-sm">{f.description}</span><Pill t={sevTone[f.severity]}>{sevLabel[f.severity]}</Pill></li>
              ))}</ul>)}
          </Panel>
          <Panel title="Tóm tắt lịch sử bảo dưỡng"><p className="text-sm leading-relaxed">{draft.history_summary}</p><p className="mt-2 text-xs text-muted-foreground">{v.make} {v.model} · ODO {v.odo_km.toLocaleString("vi-VN")} km</p></Panel>
          <Panel title="Giải thích dịch vụ cho khách"><p className="text-sm leading-relaxed">{draft.service_explanation}</p></Panel>
          <Panel title="Đề xuất báo giá nháp (gốc)" bodyClass="p-0">
            <ul className="divide-y">{draft.lines.map((l) => (
              <li key={l.id} className="flex items-start justify-between gap-3 px-4 py-2.5 text-sm">
                <div><div>{l.name} <span className="text-muted-foreground">× {l.qty}</span></div><div className="text-[11px] text-ai">↳ {l.ai_reason}</div></div>
                <span className="tabular shrink-0 text-muted-foreground">{vnd(l.unit_price)}</span>
              </li>))}</ul>
            <p className="border-t px-4 py-2 text-[11px] text-muted-foreground">AI không tính tổng tiền. Tổng chính thức do hệ thống tính sau khi duyệt.</p>
          </Panel>
        </div>

        {/* Human side */}
        <div className="space-y-4">
          <div className="flex items-center justify-between rounded-lg border bg-card px-4 py-3">
            <div className="flex items-center gap-2 text-sm font-semibold"><ShieldCheck className="size-4 text-primary" />Kiểm tra của Quản lý</div>
            <span className="text-[11px] text-muted-foreground">{user} · {ROLE_LABEL[role]}</span>
          </div>
          {!isManager && <div className="flex items-center gap-2 rounded-md border border-warning/40 bg-warning-soft px-3 py-2 text-xs"><AlertCircle className="size-4" />Chế độ chỉ xem — chỉ Quản lý được chỉnh sửa và phê duyệt.</div>}
          <Panel title={<>Báo giá đang duyệt · <Link to="/repair-orders/$id" params={{ id: ro.id }} className="font-mono text-primary">{ro.code}</Link></>} bodyClass="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="text-left text-[11px] uppercase tracking-wider text-muted-foreground"><tr className="border-b"><th className="px-3 py-2 font-medium">Hạng mục</th><th className="w-16 px-2 py-2 text-right font-medium">SL</th><th className="w-32 px-2 py-2 text-right font-medium">Đơn giá</th><th className="w-8" /></tr></thead>
                <tbody className="divide-y">
                  {lines.map((l) => { const o = draft.lines.find((x) => x.id === l.id); const edited = !o || o.qty !== l.qty || o.unit_price !== l.unit_price || o.name !== l.name; return (
                    <tr key={l.id} className={cn(edited && "bg-warning-soft/60")}>
                      <td className="px-3 py-1.5"><div className="flex items-center gap-2"><Pill t={l.kind === "part" ? "info" : "neutral"}>{l.kind === "part" ? "PT" : "Công"}</Pill><Input disabled={locked} value={l.name} onChange={(e) => upd(l.id, { name: e.target.value })} className="h-8" /></div></td>
                      <td className="px-2"><Input disabled={locked} type="number" min={0} value={l.qty} onChange={(e) => upd(l.id, { qty: Number(e.target.value) })} className="tabular h-8 text-right" /></td>
                      <td className="px-2"><Input disabled={locked} type="number" min={0} step={10000} value={l.unit_price} onChange={(e) => upd(l.id, { unit_price: Number(e.target.value) })} className="tabular h-8 text-right" /></td>
                      <td className="pr-2"><button disabled={locked} onClick={() => setLines((ls) => ls.filter((x) => x.id !== l.id))} className="rounded p-1 text-muted-foreground hover:text-destructive disabled:opacity-30" aria-label="Xoá dòng"><Trash2 className="size-4" /></button></td>
                    </tr>); })}
                </tbody>
              </table>
            </div>
            {!locked && <div className="flex gap-2 border-t px-3 py-2">
              <Button variant="ghost" size="sm" onClick={() => setLines((ls) => [...ls, { id: crypto.randomUUID(), kind: "part", name: "Phụ tùng mới", qty: 1, unit_price: 0, ai_reason: "Thêm bởi Quản lý" }])}><Plus className="size-4" />Phụ tùng</Button>
              <Button variant="ghost" size="sm" onClick={() => setLines((ls) => [...ls, { id: crypto.randomUUID(), kind: "labor", name: "Hạng mục công", qty: 1, unit_price: 0, ai_reason: "Thêm bởi Quản lý" }])}><Plus className="size-4" />Tiền công</Button>
            </div>}
            <dl className="space-y-1 border-t bg-muted/40 px-4 py-3 text-sm">
              <div className="flex justify-between"><dt className="text-muted-foreground">Phụ tùng</dt><dd className="tabular">{vnd(preview.parts_subtotal)}</dd></div>
              <div className="flex justify-between"><dt className="text-muted-foreground">Tiền công</dt><dd className="tabular">{vnd(preview.labor_subtotal)}</dd></div>
              <div className="flex justify-between"><dt className="text-muted-foreground">VAT 10%</dt><dd className="tabular">{vnd(preview.vat)}</dd></div>
              <div className="flex justify-between border-t pt-1 font-semibold"><dt>Tổng tạm tính (hệ thống)</dt><dd className="tabular">{vnd(preview.grand_total)}</dd></div>
            </dl>
          </Panel>

          <Panel title={`Thay đổi so với bản AI (${changes.length})`}>
            {changes.length === 0 ? <p className="text-sm text-muted-foreground">Chưa có chỉnh sửa.</p> : <ul className="space-y-1 text-sm">{changes.map((c, i) => <li key={i} className="flex gap-2"><span className="text-warning">●</span>{c}</li>)}</ul>}
            {draft.status === "pending_review" && isManager && <>
              <Textarea value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Ghi chú duyệt / lý do từ chối (bắt buộc khi từ chối)" className="mt-3 min-h-[60px]" />
              <div className="mt-3 flex gap-2">
                <Button className="flex-1" disabled={review.isPending || lines.length === 0} onClick={() => review.mutate("approve")}><CheckCircle2 className="size-4" />Duyệt & xuất báo giá chính thức</Button>
                <Button variant="outline" disabled={review.isPending || !reason.trim()} onClick={() => review.mutate("reject")}><XCircle className="size-4" />Từ chối</Button>
              </div></>}
            {draft.status !== "pending_review" && <div className="mt-3"><Pill t={draft.status === "approved" ? "success" : "danger"}>{draft.status === "approved" ? "Báo giá đã được phê duyệt" : "Bản nháp đã bị từ chối"}</Pill></div>}
          </Panel>

          <Panel title={<span className="flex items-center gap-2"><History className="size-4" />Nhật ký kiểm toán</span>}>
            <ol className="space-y-3 border-l pl-4">
              {(audit.data ?? []).map((a) => (
                <li key={a.id} className="relative"><span className={cn("absolute -left-[21px] top-1.5 size-2 rounded-full", a.action === "generate" ? "bg-ai" : a.action === "approve" ? "bg-success" : a.action === "reject" ? "bg-destructive" : "bg-warning")} />
                  <div className="text-xs text-muted-foreground"><span className="font-medium text-foreground">{a.actor}</span> · {fmtTime(a.at)}</div>
                  <div className="text-sm">{a.detail}</div></li>
              ))}
              {audit.isLoading && <li className="text-sm text-muted-foreground">Đang tải…</li>}
            </ol>
          </Panel>
        </div>
      </div>
    </>
  );
}
