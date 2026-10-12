import { createFileRoute } from "@tanstack/react-router";
import { useSuspenseQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { api, q } from "@/services/api";
import { useRole, vnd, vndShort, fmtTime } from "@/lib/rbac";
import { PageHeader, Panel, Plate, InvoicePill, Stat, NoAccess } from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import type { Invoice, PaymentCreate } from "@/types";

export const Route = createFileRoute("/finance")({
  head: () => ({ meta: [
    { title: "Hoá đơn & Thanh toán — GarageTools AI" },
    { name: "description", content: "Theo dõi hoá đơn, công nợ và ghi nhận thanh toán của khách hàng." },
    { property: "og:title", content: "Hoá đơn & Thanh toán — GarageTools AI" },
    { property: "og:description", content: "Quản lý tài chính xưởng dịch vụ." },
  ] }),
  loader: ({ context: { queryClient: qc } }) => qc.ensureQueryData(q.invoices()),
  component: Finance,
});

function Finance() {
  const { can, role } = useRole();
  const { data: inv } = useSuspenseQuery(q.invoices());
  const qc = useQueryClient();
  const [sel, setSel] = useState<Invoice | null>(null);
  const [amt, setAmt] = useState(0);
  const [method, setMethod] = useState<PaymentCreate["method"]>("transfer");
  const pay = useMutation({ mutationFn: () => api.createPayment({ invoice_id: sel!.id, amount: amt, method }), onSuccess: (i) => { qc.invalidateQueries(); setSel(null); toast.success(`Đã ghi nhận thanh toán ${i.code}`); } });
  if (!can("finance")) return <NoAccess />;
  const canPay = role === "cashier" || role === "manager";
  const debt = inv.reduce((s, i) => s + (i.total - i.paid), 0);
  return (
    <>
      <PageHeader eyebrow="Kho & Tài chính" title="Hoá đơn & Thanh toán" desc="Số tiền hoá đơn do hệ thống kế toán phát hành; màn hình này chỉ ghi nhận thanh toán." />
      <div className="space-y-6 p-6 lg:p-8">
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-3">
          <Stat label="Tổng phát hành" value={vndShort(inv.reduce((s, i) => s + i.total, 0))} />
          <Stat label="Đã thu" value={vndShort(inv.reduce((s, i) => s + i.paid, 0))} />
          <Stat label="Công nợ" value={<span className="text-destructive">{vndShort(debt)}</span>} sub={`${inv.filter((i) => i.status !== "paid").length} hoá đơn chưa tất toán`} />
        </div>
        <Panel bodyClass="p-0" title="Danh sách hoá đơn">
          <div className="overflow-x-auto"><table className="w-full text-sm">
            <thead className="bg-muted/50 text-left text-[11px] uppercase tracking-wider text-muted-foreground"><tr>{["Số HĐ", "Khách hàng", "Biển số", "Ngày", "Tổng tiền", "Đã thu", "Trạng thái", ""].map((h) => <th key={h} className="px-4 py-2 font-medium">{h}</th>)}</tr></thead>
            <tbody className="divide-y">{inv.map((i) => (
              <tr key={i.id} className="hover:bg-muted/40">
                <td className="px-4 py-2.5 font-mono text-xs font-medium">{i.code}</td><td className="px-4">{i.customer_name}</td><td className="px-4"><Plate>{i.plate}</Plate></td>
                <td className="tabular px-4 text-xs">{fmtTime(i.issued_at)}</td><td className="tabular px-4 font-medium">{vnd(i.total)}</td><td className="tabular px-4">{vnd(i.paid)}</td>
                <td className="px-4"><InvoicePill s={i.status} /></td>
                <td className="px-4 text-right">{canPay && i.status !== "paid" && <Button size="sm" variant="outline" onClick={() => { setSel(i); setAmt(i.total - i.paid); }}>Thu tiền</Button>}</td>
              </tr>))}</tbody>
          </table></div>
        </Panel>
      </div>
      <Dialog open={!!sel} onOpenChange={(o) => !o && setSel(null)}>
        <DialogContent>
          <DialogHeader><DialogTitle>Ghi nhận thanh toán · {sel?.code}</DialogTitle></DialogHeader>
          {sel && <div className="space-y-3 text-sm">
            <div className="flex justify-between"><span className="text-muted-foreground">Còn phải thu</span><span className="tabular font-semibold">{vnd(sel.total - sel.paid)}</span></div>
            <Input type="number" value={amt} max={sel.total - sel.paid} onChange={(e) => setAmt(Number(e.target.value))} />
            <Select value={method} onValueChange={(v) => setMethod(v as PaymentCreate["method"])}><SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent><SelectItem value="cash">Tiền mặt</SelectItem><SelectItem value="card">Thẻ</SelectItem><SelectItem value="transfer">Chuyển khoản</SelectItem></SelectContent></Select>
          </div>}
          <DialogFooter><Button disabled={amt <= 0 || pay.isPending} onClick={() => pay.mutate()}>Xác nhận</Button></DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
