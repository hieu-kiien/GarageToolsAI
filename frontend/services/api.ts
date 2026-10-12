/**
 * Mock REST client. Every function maps 1:1 to a FastAPI endpoint documented in
 * README_AI_HANDOFF.md. Replace the body of `request` with `fetch(BASE_URL + path)`
 * to connect the real backend; signatures stay the same.
 */
import { queryOptions } from "@tanstack/react-query";
import * as db from "./mock-db";
import type {
  AiDraft, AiDraftLine, AuditEntry, DashboardStats, InspectionCreate, OrderTotals,
  PaymentCreate, RepairOrder, RepairStatus, Role,
} from "@/types";

const VAT_RATE = 0.1;
const wait = <T,>(v: T, ms = 180) => new Promise<T>((r) => setTimeout(() => r(structuredClone(v)), ms));
const nowIso = () => new Date().toISOString();
const uid = () => Math.random().toString(36).slice(2, 10);

/** Server-side authoritative totals (backend business rule, mirrored here for the mock). */
export function computeTotals(parts: { qty: number; unit_price: number }[], labor: { hours?: number; qty?: number; rate?: number; unit_price?: number }[]): OrderTotals {
  const parts_subtotal = parts.reduce((s, p) => s + p.qty * p.unit_price, 0);
  const labor_subtotal = labor.reduce((s, l) => s + (l.hours ?? l.qty ?? 0) * (l.rate ?? l.unit_price ?? 0), 0);
  const vat = Math.round((parts_subtotal + labor_subtotal) * VAT_RATE);
  return { parts_subtotal, labor_subtotal, vat, grand_total: parts_subtotal + labor_subtotal + vat };
}

export const api = {
  // GET /api/dashboard/stats
  getDashboard: (): Promise<DashboardStats> => {
    const active = db.repairOrders.filter((r) => r.status !== "delivered");
    const now = Date.UTC(2026, 9, 12, 11);
    return wait({
      in_shop: active.length,
      bays_used: db.bays.filter((b) => b.repair_order_id).length,
      bays_total: db.bays.length,
      revenue_today: 12_460_000,
      revenue_month: 318_750_000,
      overdue: active.filter((r) => new Date(r.promised_at).getTime() < now).length,
      awaiting_approval: db.aiDrafts.filter((a) => a.status === "pending_review").length,
      revenue_series: ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"].map((day, i) => ({
        day, value: [21, 26, 18, 31, 29, 12, 24, 33, 27, 30, 35, 12.46][i]! * 1_000_000,
      })),
    });
  },
  // GET /api/repair-orders
  listRepairOrders: () => wait(db.repairOrders),
  // GET /api/repair-orders/{id}
  getRepairOrder: (id: string) => {
    const ro = db.repairOrders.find((r) => r.id === id);
    if (!ro) return Promise.reject(new Error("Không tìm thấy lệnh sửa chữa"));
    return wait({ ...ro, totals: computeTotals(ro.parts, ro.labor) });
  },
  // PATCH /api/repair-orders/{id}/status
  updateStatus: (id: string, status: RepairStatus) => {
    const ro = db.repairOrders.find((r) => r.id === id)!;
    ro.status = status;
    return wait(ro);
  },
  // PATCH /api/repair-orders/{id}/assignment
  assign: (id: string, body: { technician_id: string | null; bay_id: string | null }) => {
    const ro = db.repairOrders.find((r) => r.id === id)!;
    db.bays.forEach((b) => { if (b.repair_order_id === id) b.repair_order_id = null; });
    ro.technician_id = body.technician_id;
    ro.bay_id = body.bay_id;
    const bay = db.bays.find((b) => b.id === body.bay_id);
    if (bay) bay.repair_order_id = id;
    return wait(ro);
  },
  // PATCH /api/repair-orders/{id}/tasks/{task_id}
  toggleTask: (id: string, taskId: string) => {
    const t = db.repairOrders.find((r) => r.id === id)!.tasks.find((x) => x.id === taskId)!;
    t.done = !t.done;
    return wait(t);
  },
  // POST /api/repair-orders/{id}/notes
  addNote: (id: string, body: { author: string; body: string }) => {
    const n = { id: uid(), ...body, created_at: nowIso() };
    db.repairOrders.find((r) => r.id === id)!.notes.unshift(n);
    return wait(n);
  },
  // POST /api/repair-orders/{id}/inspection
  createInspection: (body: InspectionCreate) => wait({ id: uid(), ...body, created_at: nowIso() }, 400),

  listCustomers: () => wait(db.customers), // GET /api/customers
  listVehicles: () => wait(db.vehicles), // GET /api/vehicles
  listTechnicians: () => wait(db.technicians), // GET /api/technicians
  listBays: () => wait(db.bays), // GET /api/bays
  listInventory: () => wait(db.inventory), // GET /api/inventory
  listInvoices: () => wait(db.invoices), // GET /api/invoices

  // POST /api/payments
  createPayment: (body: PaymentCreate) => {
    const inv = db.invoices.find((i) => i.id === body.invoice_id)!;
    inv.paid = Math.min(inv.total, inv.paid + body.amount);
    inv.status = inv.paid >= inv.total ? "paid" : inv.paid > 0 ? "partial" : "unpaid";
    return wait(inv);
  },

  // GET /api/ai/drafts
  listDrafts: () => wait(db.aiDrafts),
  // GET /api/ai/drafts/{id}/audit
  listAudit: (draftId: string) => wait(db.auditLog.filter((a) => a.draft_id === draftId).sort((a, b) => b.at.localeCompare(a.at))),
  /**
   * POST /api/ai/drafts/{id}/review — the ONLY way a draft becomes an official quotation.
   * Requires role=manager. Totals are recomputed server-side from reviewed lines.
   */
  reviewDraft: (draftId: string, body: { decision: "approve" | "reject"; lines: AiDraftLine[]; actor: string; role: Role; changes: string[]; reason?: string }) => {
    if (body.role !== "manager") return Promise.reject(new Error("403: Chỉ Quản lý được duyệt báo giá"));
    const draft = db.aiDrafts.find((a) => a.id === draftId)!;
    const push = (action: AuditEntry["action"], detail: string) =>
      db.auditLog.push({ id: uid(), draft_id: draftId, actor: body.actor, role: body.role, action, detail, at: nowIso() });
    body.changes.forEach((c) => push("edit_line", c));
    draft.lines = body.lines;
    draft.status = body.decision === "approve" ? "approved" : "rejected";
    push(body.decision, body.decision === "approve" ? "Duyệt & xuất báo giá chính thức" : `Từ chối: ${body.reason ?? "—"}`);
    const parts = body.lines.filter((l) => l.kind === "part");
    const labor = body.lines.filter((l) => l.kind === "labor");
    return wait({ draft, totals: computeTotals(parts, labor) }, 350);
  },
};

export type RepairOrderDetail = Awaited<ReturnType<typeof api.getRepairOrder>>;

export const q = {
  dashboard: () => queryOptions({ queryKey: ["dashboard"], queryFn: api.getDashboard }),
  orders: () => queryOptions({ queryKey: ["orders"], queryFn: api.listRepairOrders }),
  order: (id: string) => queryOptions({ queryKey: ["orders", id], queryFn: () => api.getRepairOrder(id) }),
  customers: () => queryOptions({ queryKey: ["customers"], queryFn: api.listCustomers }),
  vehicles: () => queryOptions({ queryKey: ["vehicles"], queryFn: api.listVehicles }),
  technicians: () => queryOptions({ queryKey: ["technicians"], queryFn: api.listTechnicians }),
  bays: () => queryOptions({ queryKey: ["bays"], queryFn: api.listBays }),
  inventory: () => queryOptions({ queryKey: ["inventory"], queryFn: api.listInventory }),
  invoices: () => queryOptions({ queryKey: ["invoices"], queryFn: api.listInvoices }),
  drafts: () => queryOptions({ queryKey: ["drafts"], queryFn: api.listDrafts }),
  audit: (id: string) => queryOptions({ queryKey: ["audit", id], queryFn: () => api.listAudit(id) }),
};
