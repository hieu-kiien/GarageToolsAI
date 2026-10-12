import { createFileRoute } from "@tanstack/react-router";
import { useSuspenseQuery } from "@tanstack/react-query";
import { AlertTriangle, Boxes } from "lucide-react";
import { q } from "@/services/api";
import { useRole, vnd, vndShort } from "@/lib/rbac";
import { PageHeader, Panel, Pill, Stat, NoAccess } from "@/components/app/ui-kit";

export const Route = createFileRoute("/inventory")({
  head: () => ({ meta: [
    { title: "Kho phụ tùng — GarageTools AI" },
    { name: "description", content: "Danh mục phụ tùng tồn kho và cảnh báo mức tồn tối thiểu." },
    { property: "og:title", content: "Kho phụ tùng — GarageTools AI" },
    { property: "og:description", content: "Quản lý tồn kho phụ tùng ô tô." },
  ] }),
  loader: ({ context: { queryClient: qc } }) => qc.ensureQueryData(q.inventory()),
  component: Inventory,
});

function Inventory() {
  const { can } = useRole();
  const { data: items } = useSuspenseQuery(q.inventory());
  if (!can("inventory")) return <NoAccess />;
  const low = items.filter((i) => i.on_hand < i.min_level);
  return (
    <>
      <PageHeader eyebrow="Kho & Tài chính" title="Kho phụ tùng" desc={`${items.length} mã phụ tùng đang theo dõi`} />
      <div className="space-y-6 p-6 lg:p-8">
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
          <Stat label="Giá trị tồn kho (giá vốn)" value={vndShort(items.reduce((s, i) => s + i.on_hand * i.unit_cost, 0))} icon={<Boxes className="size-4" />} />
          <Stat label="Dưới mức tối thiểu" value={low.length} icon={<AlertTriangle className="size-4 text-destructive" />} sub="Cần lập đề nghị nhập hàng" />
          <Stat label="Tổng số lượng" value={items.reduce((s, i) => s + i.on_hand, 0)} />
        </div>
        <Panel bodyClass="p-0" title="Danh mục tồn kho">
          <div className="overflow-x-auto"><table className="w-full text-sm">
            <thead className="bg-muted/50 text-left text-[11px] uppercase tracking-wider text-muted-foreground"><tr>{["SKU", "Tên phụ tùng", "Nhóm", "Vị trí", "Tồn / Tối thiểu", "Giá vốn", "Giá bán", ""].map((h) => <th key={h} className="px-4 py-2 font-medium">{h}</th>)}</tr></thead>
            <tbody className="divide-y">{items.map((i) => { const isLow = i.on_hand < i.min_level; return (
              <tr key={i.id} className={isLow ? "bg-danger-soft/50" : "hover:bg-muted/40"}>
                <td className="px-4 py-2.5 font-mono text-xs">{i.sku}</td><td className="px-4">{i.name}</td><td className="px-4 text-muted-foreground">{i.category}</td><td className="px-4 font-mono text-xs">{i.location}</td>
                <td className="px-4"><div className="flex items-center gap-2"><span className="tabular w-14">{i.on_hand} / {i.min_level}</span><div className="h-1.5 w-20 rounded-full bg-muted"><div className={`h-full rounded-full ${isLow ? "bg-destructive" : "bg-success"}`} style={{ width: `${Math.min(100, (i.on_hand / (i.min_level * 2)) * 100)}%` }} /></div></div></td>
                <td className="tabular px-4">{vnd(i.unit_cost)}</td><td className="tabular px-4">{vnd(i.unit_price)}</td>
                <td className="px-4">{isLow && <Pill t="danger">Sắp hết</Pill>}</td>
              </tr>); })}</tbody>
          </table></div>
        </Panel>
      </div>
    </>
  );
}
