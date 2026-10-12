import { createFileRoute, Link } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { AlertTriangle, Car, Gauge, Wallet, Sparkles, ArrowUpRight, Clock } from "lucide-react";
import { q } from "@/services/api";
import { ensureLookups, useLookups } from "@/services/lookups";
import { useRole, vnd, vndShort, fmtTime, STATUS_LABEL, STATUS_ORDER } from "@/lib/rbac";
import { PageHeader, Panel, Stat, StatusPill, Plate, NoAccess, Pill } from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/")({
  head: () => ({ meta: [
    { title: "Tổng quan xưởng — GarageTools AI" },
    { name: "description", content: "Chỉ số vận hành xưởng: xe đang sửa, công suất cầu nâng, doanh thu và cảnh báo trễ hạn." },
    { property: "og:title", content: "Tổng quan xưởng — GarageTools AI" },
    { property: "og:description", content: "Executive Dashboard cho xưởng dịch vụ ô tô." },
  ] }),
  loader: ({ context: { queryClient: qc } }) => Promise.all([qc.ensureQueryData(q.dashboard()), qc.ensureQueryData(q.orders()), ensureLookups(qc)]),
  component: Dashboard,
});

const NOW = Date.UTC(2026, 9, 12, 11);

function Dashboard() {
  const { can, user } = useRole();
  const { data: s } = useSuspenseQuery(q.dashboard());
  const { data: orders } = useSuspenseQuery(q.orders());
  const L = useLookups();
  if (!can("dashboard")) return <NoAccess />;
  const active = orders.filter((o) => o.status !== "delivered");
  const overdue = active.filter((o) => new Date(o.promised_at).getTime() < NOW);
  const util = Math.round((s.bays_used / s.bays_total) * 100);

  return (
    <>
      <PageHeader eyebrow="Thứ Hai, 12/10/2026" title={`Chào buổi sáng, ${user.split(" ").slice(-1)[0]}`} desc="Tình hình xưởng theo thời gian thực — cập nhật lúc 18:00."
        actions={<><Button variant="outline" asChild><Link to="/inspection">Tiếp nhận xe</Link></Button><Button asChild><Link to="/workflow">Mở bảng điều phối</Link></Button></>} />
      <div className="space-y-6 p-6 lg:p-8">
        <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
          <Stat label="Xe trong xưởng" value={s.in_shop} icon={<Car className="size-4" />} sub={<>{active.filter((o) => o.status === "in_repair").length} đang sửa · {active.filter((o) => o.status === "intake").length} chờ tiếp nhận</>} />
          <Stat label="Công suất cầu nâng" value={`${util}%`} icon={<Gauge className="size-4" />} sub={`${s.bays_used}/${s.bays_total} vị trí đang sử dụng`} />
          <Stat label="Doanh thu hôm nay" value={vndShort(s.revenue_today)} icon={<Wallet className="size-4" />} sub={<span className="text-success">+8,4% so với thứ Hai trước</span>} />
          <Stat label="Doanh thu tháng 10" value={vndShort(s.revenue_month)} icon={<ArrowUpRight className="size-4" />} sub="Mục tiêu 850 tr · đạt 37,5%" />
        </div>

        <div className="grid gap-6 xl:grid-cols-3">
          <Panel title="Doanh thu 12 ngày gần nhất" className="xl:col-span-2" action={<span className="text-xs text-muted-foreground">Đơn vị: triệu ₫</span>}>
            <div className="h-64">
              <ResponsiveContainer>
                <AreaChart data={s.revenue_series.map((r) => ({ ...r, v: r.value / 1e6 }))} margin={{ left: -20, right: 8, top: 8 }}>
                  <defs><linearGradient id="g" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="var(--chart-1)" stopOpacity={0.22} /><stop offset="100%" stopColor="var(--chart-1)" stopOpacity={0} /></linearGradient></defs>
                  <CartesianGrid stroke="var(--border)" vertical={false} />
                  <XAxis dataKey="day" tickLine={false} axisLine={false} fontSize={11} stroke="var(--muted-foreground)" />
                  <YAxis tickLine={false} axisLine={false} fontSize={11} stroke="var(--muted-foreground)" />
                  <Tooltip formatter={(v: number) => [`${v} tr ₫`, "Doanh thu"]} labelFormatter={(l) => `Ngày ${l}/10`} contentStyle={{ borderRadius: 8, border: "1px solid var(--border)", fontSize: 12 }} />
                  <Area dataKey="v" stroke="var(--chart-1)" strokeWidth={2} fill="url(#g)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Panel>

          <Panel title={<span className="flex items-center gap-2"><AlertTriangle className="size-4 text-destructive" />Cảnh báo trễ hạn</span>} action={<Pill t="danger">{overdue.length}</Pill>} bodyClass="p-0">
            <ul className="divide-y">
              {overdue.map((o) => (
                <li key={o.id}>
                  <Link to="/repair-orders/$id" params={{ id: o.id }} className="flex items-start justify-between gap-3 px-4 py-3 hover:bg-muted/60">
                    <div>
                      <div className="flex items-center gap-2"><Plate>{L.vehicle(o.vehicle_id)?.plate}</Plate><span className="font-mono text-xs text-muted-foreground">{o.code}</span></div>
                      <div className="mt-1 text-xs text-muted-foreground">{STATUS_LABEL[o.status]} · hẹn {fmtTime(o.promised_at)}</div>
                    </div>
                    <span className="tabular text-xs font-medium text-destructive">-{Math.round((NOW - new Date(o.promised_at).getTime()) / 3600000)}h</span>
                  </Link>
                </li>
              ))}
            </ul>
            <div className="border-t px-4 py-3">
              <Link to="/ai-review" search={{}} className="flex items-center justify-between rounded-md bg-ai-soft px-3 py-2 text-xs font-medium text-ai">
                <span className="flex items-center gap-2"><Sparkles className="size-3.5" />{s.awaiting_approval} báo giá AI chờ Quản lý duyệt</span><ArrowUpRight className="size-3.5" />
              </Link>
            </div>
          </Panel>
        </div>

        <div className="grid gap-6 xl:grid-cols-3">
          <Panel title="Sơ đồ cầu nâng & khoang" className="xl:col-span-2">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
              {L.bays.map((b) => {
                const o = orders.find((x) => x.id === b.repair_order_id);
                return (
                  <div key={b.id} className={`rounded-md border p-3 ${o ? "bg-card" : "border-dashed bg-muted/40"}`}>
                    <div className="flex items-center justify-between text-[11px] font-medium text-muted-foreground">{b.name}<span className={`size-2 rounded-full ${o ? "bg-primary" : "bg-success"}`} /></div>
                    {o ? (
                      <Link to="/repair-orders/$id" params={{ id: o.id }} className="mt-2 block">
                        <Plate>{L.vehicle(o.vehicle_id)?.plate}</Plate>
                        <div className="mt-1.5 truncate text-xs">{L.tech(o.technician_id)?.full_name ?? "Chưa phân công"}</div>
                      </Link>
                    ) : <div className="mt-2 text-xs text-success">Trống — sẵn sàng</div>}
                  </div>
                );
              })}
            </div>
          </Panel>
          <Panel title="Phân bổ theo trạng thái">
            <div className="space-y-3">
              {STATUS_ORDER.map((st) => {
                const n = orders.filter((o) => o.status === st).length;
                return (
                  <div key={st}>
                    <div className="mb-1 flex justify-between text-xs"><span>{STATUS_LABEL[st]}</span><span className="tabular font-medium">{n}</span></div>
                    <div className="h-1.5 rounded-full bg-muted"><div className="h-full rounded-full bg-primary" style={{ width: `${(n / orders.length) * 100}%` }} /></div>
                  </div>
                );
              })}
            </div>
          </Panel>
        </div>

        <Panel title="Lệnh sửa chữa đang mở" bodyClass="p-0" action={<Link to="/repair-orders" className="text-xs font-medium text-primary">Xem tất cả</Link>}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 text-left text-[11px] uppercase tracking-wider text-muted-foreground">
                <tr><th className="px-4 py-2 font-medium">Mã lệnh</th><th className="px-4 py-2 font-medium">Xe</th><th className="px-4 py-2 font-medium">Khách hàng</th><th className="px-4 py-2 font-medium">Trạng thái</th><th className="px-4 py-2 font-medium">KTV</th><th className="px-4 py-2 font-medium">Hẹn giao</th></tr>
              </thead>
              <tbody className="divide-y">
                {active.slice(0, 6).map((o) => (
                  <tr key={o.id} className="hover:bg-muted/40">
                    <td className="px-4 py-2.5"><Link to="/repair-orders/$id" params={{ id: o.id }} className="font-mono text-xs font-medium text-primary">{o.code}</Link></td>
                    <td className="px-4 py-2.5"><Plate>{L.vehicle(o.vehicle_id)?.plate}</Plate></td>
                    <td className="px-4 py-2.5">{L.customer(o.customer_id)?.full_name}</td>
                    <td className="px-4 py-2.5"><StatusPill s={o.status} /></td>
                    <td className="px-4 py-2.5 text-muted-foreground">{L.tech(o.technician_id)?.full_name ?? "—"}</td>
                    <td className="px-4 py-2.5 text-xs"><span className="inline-flex items-center gap-1 tabular"><Clock className="size-3" />{fmtTime(o.promised_at)}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
        <p className="text-center text-[11px] text-muted-foreground">Số liệu doanh thu do hệ thống kế toán tính — {vnd(s.revenue_today)} hôm nay.</p>
      </div>
    </>
  );
}
