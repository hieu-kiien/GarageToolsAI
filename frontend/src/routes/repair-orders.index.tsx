import { createFileRoute, Link } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useState } from "react";
import { q } from "@/services/api";
import { ensureLookups, useLookups } from "@/services/lookups";
import { useRole, STATUS_LABEL, STATUS_ORDER, fmtTime } from "@/lib/rbac";
import { PageHeader, Panel, Plate, StatusPill, PriorityPill, NoAccess, Empty } from "@/components/app/ui-kit";
import { cn } from "@/lib/utils";
import type { RepairStatus } from "@/types";

export const Route = createFileRoute("/repair-orders/")({
  head: () => ({ meta: [
    { title: "Lệnh sửa chữa — GarageTools AI" },
    { name: "description", content: "Danh sách lệnh sửa chữa, lọc theo trạng thái, biển số và khách hàng." },
    { property: "og:title", content: "Lệnh sửa chữa — GarageTools AI" },
    { property: "og:description", content: "Tra cứu nhanh lệnh sửa chữa trong xưởng." },
  ] }),
  loader: ({ context: { queryClient: qc } }) => Promise.all([qc.ensureQueryData(q.orders()), ensureLookups(qc)]),
  component: List,
});

function List() {
  const { can } = useRole();
  const { data: orders } = useSuspenseQuery(q.orders());
  const L = useLookups();
  const [f, setF] = useState<RepairStatus | "all">("all");
  const [s, setS] = useState("");
  if (!can("orders")) return <NoAccess />;
  const rows = orders.filter((o) => (f === "all" || o.status === f) && (`${o.code} ${L.vehicle(o.vehicle_id)?.plate} ${L.customer(o.customer_id)?.full_name}`.toLowerCase().includes(s.toLowerCase())));
  return (
    <>
      <PageHeader eyebrow="Vận hành" title="Lệnh sửa chữa" desc={`${orders.length} lệnh trong tháng 10/2026`} />
      <div className="p-6 lg:p-8">
        <Panel bodyClass="p-0">
          <div className="flex flex-col gap-3 border-b p-3 md:flex-row md:items-center">
            <div className="flex flex-wrap gap-1">
              {(["all", ...STATUS_ORDER] as const).map((k) => (
                <button key={k} onClick={() => setF(k)} className={cn("rounded-md px-2.5 py-1 text-xs font-medium", f === k ? "bg-foreground text-background" : "text-muted-foreground hover:bg-muted")}>
                  {k === "all" ? "Tất cả" : STATUS_LABEL[k]}
                </button>
              ))}
            </div>
            <input value={s} onChange={(e) => setS(e.target.value)} placeholder="Lọc theo mã, biển số, khách…" className="h-8 rounded-md border bg-background px-2.5 text-sm md:ml-auto md:w-64" />
          </div>
          {rows.length === 0 ? <div className="p-6"><Empty title="Không có lệnh phù hợp" desc="Thử bỏ bộ lọc hoặc đổi từ khoá." /></div> : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 text-left text-[11px] uppercase tracking-wider text-muted-foreground">
                  <tr>{["Mã lệnh", "Biển số", "Xe", "Khách hàng", "Trạng thái", "Ưu tiên", "KTV", "Hẹn giao"].map((h) => <th key={h} className="px-4 py-2 font-medium">{h}</th>)}</tr>
                </thead>
                <tbody className="divide-y">
                  {rows.map((o) => { const v = L.vehicle(o.vehicle_id)!; return (
                    <tr key={o.id} className="hover:bg-muted/40">
                      <td className="px-4 py-2.5"><Link to="/repair-orders/$id" params={{ id: o.id }} className="font-mono text-xs font-medium text-primary">{o.code}</Link></td>
                      <td className="px-4 py-2.5"><Plate>{v.plate}</Plate></td>
                      <td className="px-4 py-2.5">{v.make} {v.model}</td>
                      <td className="px-4 py-2.5">{L.customer(o.customer_id)?.full_name}</td>
                      <td className="px-4 py-2.5"><StatusPill s={o.status} /></td>
                      <td className="px-4 py-2.5"><PriorityPill p={o.priority} /></td>
                      <td className="px-4 py-2.5 text-muted-foreground">{L.tech(o.technician_id)?.full_name ?? "—"}</td>
                      <td className="tabular px-4 py-2.5 text-xs">{fmtTime(o.promised_at)}</td>
                    </tr>); })}
                </tbody>
              </table>
            </div>
          )}
        </Panel>
      </div>
    </>
  );
}
