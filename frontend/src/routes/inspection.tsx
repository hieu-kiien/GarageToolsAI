import { createFileRoute } from "@tanstack/react-router";
import { useSuspenseQuery, useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { api, q } from "@/services/api";
import { ensureLookups, useLookups } from "@/services/lookups";
import { useRole } from "@/lib/rbac";
import { PageHeader, Panel, Pill, NoAccess } from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils";
import type { DamageType, InspectionMark } from "@/types";

export const Route = createFileRoute("/inspection")({
  head: () => ({ meta: [
    { title: "Kiểm tra tiếp nhận xe — GarageTools AI" },
    { name: "description", content: "Biểu mẫu kiểm tra thân vỏ, nội thất và tình trạng xe khi tiếp nhận vào xưởng." },
    { property: "og:title", content: "Kiểm tra tiếp nhận xe — GarageTools AI" },
    { property: "og:description", content: "Vehicle Walkaround Inspection." },
  ] }),
  loader: ({ context: { queryClient: qc } }) => Promise.all([qc.ensureQueryData(q.orders()), ensureLookups(qc)]),
  component: Inspection,
});

const ZONES = [
  { id: "front", label: "Cản trước", x: 38, y: 2, w: 24, h: 10 },
  { id: "hood", label: "Nắp capo", x: 32, y: 13, w: 36, h: 18 },
  { id: "roof", label: "Nóc xe", x: 32, y: 40, w: 36, h: 22 },
  { id: "trunk", label: "Cốp sau", x: 32, y: 72, w: 36, h: 14 },
  { id: "rear", label: "Cản sau", x: 38, y: 88, w: 24, h: 10 },
  { id: "fl", label: "Cửa trước trái", x: 14, y: 32, w: 16, h: 22 },
  { id: "rl", label: "Cửa sau trái", x: 14, y: 56, w: 16, h: 22 },
  { id: "fr", label: "Cửa trước phải", x: 70, y: 32, w: 16, h: 22 },
  { id: "rr", label: "Cửa sau phải", x: 70, y: 56, w: 16, h: 22 },
];
const DMG: Record<DamageType, string> = { scratch: "Trầy xước", dent: "Móp", crack: "Nứt / vỡ", missing: "Thiếu" };
const CHECK = ["Đèn pha / đèn hậu", "Gạt mưa", "Lốp dự phòng", "Bộ đồ nghề", "Thảm sàn", "Ghế & nội thất", "Điều hoà", "Màn hình / âm thanh"];

function Inspection() {
  const { can } = useRole();
  const { data: orders } = useSuspenseQuery(q.orders());
  const L = useLookups();
  const open = orders.filter((o) => o.status === "intake" || o.status === "diagnosis");
  const [roId, setRoId] = useState(open[0]?.id ?? "");
  const [type, setType] = useState<DamageType>("scratch");
  const [marks, setMarks] = useState<InspectionMark[]>([]);
  const [fuel, setFuel] = useState(50);
  const [checks, setChecks] = useState<Record<string, boolean>>(Object.fromEntries(CHECK.map((c) => [c, true])));
  const [belong, setBelong] = useState("");
  const save = useMutation({
    mutationFn: () => api.createInspection({ repair_order_id: roId, fuel_level: fuel, odo_km: L.vehicle(orders.find((o) => o.id === roId)!.vehicle_id)!.odo_km, marks, checklist: checks, belongings: belong }),
    onSuccess: () => { toast.success("Đã lưu biên bản tiếp nhận"); setMarks([]); },
  });
  if (!can("inspection")) return <NoAccess />;

  return (
    <>
      <PageHeader eyebrow="Vận hành" title="Kiểm tra tiếp nhận xe" desc="Chọn loại hư hỏng rồi nhấp vào vùng tương ứng trên sơ đồ để đánh dấu."
        actions={<Button disabled={!roId || save.isPending} onClick={() => save.mutate()}>Lưu biên bản</Button>} />
      <div className="grid gap-6 p-6 lg:p-8 xl:grid-cols-3">
        <Panel title="Sơ đồ thân vỏ" className="xl:col-span-2">
          <div className="mb-4 flex flex-wrap items-center gap-3">
            <Select value={roId} onValueChange={setRoId}>
              <SelectTrigger className="w-72"><SelectValue placeholder="Chọn lệnh sửa chữa" /></SelectTrigger>
              <SelectContent>{open.map((o) => <SelectItem key={o.id} value={o.id}>{L.vehicle(o.vehicle_id)?.plate} — {o.code}</SelectItem>)}</SelectContent>
            </Select>
            <div className="flex gap-1">{(Object.keys(DMG) as DamageType[]).map((d) => (
              <button key={d} onClick={() => setType(d)} className={cn("rounded-md border px-2.5 py-1 text-xs", type === d ? "border-primary bg-info-soft font-medium" : "hover:bg-muted")}>{DMG[d]}</button>))}</div>
          </div>
          <div className="relative mx-auto aspect-[3/4] max-w-sm rounded-[40%/22%] border-2 border-foreground/20 bg-muted/40">
            {ZONES.map((z) => { const n = marks.filter((m) => m.zone === z.id).length; return (
              <button key={z.id} onClick={() => setMarks((m) => [...m, { id: crypto.randomUUID(), zone: z.id, type }])}
                style={{ left: `${z.x}%`, top: `${z.y}%`, width: `${z.w}%`, height: `${z.h}%` }}
                className={cn("absolute flex items-center justify-center rounded-md border text-[10px] transition", n ? "border-destructive bg-danger-soft text-destructive" : "border-border bg-card hover:border-primary")}>
                {z.label}{n > 0 && <span className="ml-1 font-semibold">({n})</span>}
              </button>); })}
          </div>
          <ul className="mt-4 flex flex-wrap gap-2">
            {marks.map((m) => <li key={m.id}><button onClick={() => setMarks((x) => x.filter((y) => y.id !== m.id))}><Pill t="danger">{ZONES.find((z) => z.id === m.zone)?.label}: {DMG[m.type]} ✕</Pill></button></li>)}
            {marks.length === 0 && <li className="text-sm text-muted-foreground">Chưa đánh dấu hư hỏng nào.</li>}
          </ul>
        </Panel>
        <div className="space-y-6">
          <Panel title="Mức nhiên liệu">
            <input type="range" min={0} max={100} step={25} value={fuel} onChange={(e) => setFuel(Number(e.target.value))} className="w-full accent-primary" />
            <div className="flex justify-between text-[11px] text-muted-foreground"><span>E</span><span>1/4</span><span>1/2</span><span>3/4</span><span>F</span></div>
          </Panel>
          <Panel title="Danh mục kiểm tra">
            <ul className="space-y-1.5">{CHECK.map((c) => (
              <li key={c} className="flex items-center justify-between text-sm">{c}
                <button onClick={() => setChecks((s) => ({ ...s, [c]: !s[c] }))}><Pill t={checks[c] ? "success" : "danger"}>{checks[c] ? "Đạt" : "Lỗi / thiếu"}</Pill></button></li>))}</ul>
          </Panel>
          <Panel title="Đồ đạc khách để lại"><Textarea value={belong} onChange={(e) => setBelong(e.target.value)} placeholder="VD: ghế trẻ em, ô, giấy tờ xe…" /></Panel>
        </div>
      </div>
    </>
  );
}
