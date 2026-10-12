// TypeScript models mirroring FastAPI Pydantic schemas (see README_AI_HANDOFF.md).
// Money values are integers in VND. Dates are ISO 8601 strings.

export type Role = "manager" | "receptionist" | "technician" | "cashier";

export type RepairStatus =
  | "intake" // Tiếp nhận
  | "diagnosis" // Kiểm tra chẩn đoán
  | "awaiting_approval" // Chờ duyệt báo giá
  | "in_repair" // Đang sửa chữa
  | "qc" // Nghiệm thu / KCS
  | "delivered"; // Đã giao xe

export type Priority = "normal" | "high" | "urgent";

export interface Customer {
  id: string;
  full_name: string;
  phone: string;
  email?: string;
  address?: string;
}

export interface Vehicle {
  id: string;
  customer_id: string;
  plate: string;
  vin: string;
  make: string;
  model: string;
  year: number;
  odo_km: number;
  color: string;
}

export interface Technician {
  id: string;
  full_name: string;
  skill: string;
  active_orders: number;
}

export interface Bay {
  id: string;
  name: string;
  type: "lift" | "alignment" | "paint" | "quick";
  repair_order_id: string | null;
}

export interface PartLine {
  id: string;
  part_id: string;
  sku: string;
  name: string;
  qty: number;
  unit_price: number;
}

export interface LaborLine {
  id: string;
  description: string;
  hours: number;
  rate: number;
  technician_id?: string;
}

export interface RepairTask {
  id: string;
  title: string;
  done: boolean;
}

export interface TechNote {
  id: string;
  author: string;
  body: string;
  created_at: string;
}

export interface RepairOrder {
  id: string;
  code: string;
  customer_id: string;
  vehicle_id: string;
  status: RepairStatus;
  priority: Priority;
  complaint: string;
  technician_id: string | null;
  bay_id: string | null;
  created_at: string;
  promised_at: string;
  parts: PartLine[];
  labor: LaborLine[];
  tasks: RepairTask[];
  notes: TechNote[];
  quotation_id: string | null;
}

/** Totals are always computed by the backend — never by AI or the client. */
export interface OrderTotals {
  parts_subtotal: number;
  labor_subtotal: number;
  vat: number;
  grand_total: number;
}

export interface InventoryItem {
  id: string;
  sku: string;
  name: string;
  category: string;
  on_hand: number;
  min_level: number;
  unit_cost: number;
  unit_price: number;
  location: string;
}

export type InvoiceStatus = "unpaid" | "partial" | "paid" | "void";

export interface Invoice {
  id: string;
  code: string;
  repair_order_id: string;
  customer_name: string;
  plate: string;
  issued_at: string;
  total: number;
  paid: number;
  status: InvoiceStatus;
}

export interface PaymentCreate {
  invoice_id: string;
  amount: number;
  method: "cash" | "card" | "transfer";
}

export type AiDraftStatus = "pending_review" | "approved" | "rejected";

export interface ObdFinding {
  code: string;
  description: string;
  severity: "low" | "medium" | "high";
}

export interface AiDraftLine {
  id: string;
  kind: "part" | "labor";
  name: string;
  qty: number;
  unit_price: number;
  ai_reason: string;
}

export interface AiDraft {
  id: string;
  repair_order_id: string;
  model: string;
  generated_at: string;
  status: AiDraftStatus;
  obd_findings: ObdFinding[];
  history_summary: string;
  service_explanation: string;
  lines: AiDraftLine[];
  confidence: number;
}

export interface AuditEntry {
  id: string;
  draft_id: string;
  actor: string;
  role: Role;
  action: "edit_line" | "add_line" | "remove_line" | "approve" | "reject" | "generate";
  detail: string;
  at: string;
}

export type DamageType = "scratch" | "dent" | "crack" | "missing";

export interface InspectionMark {
  id: string;
  zone: string;
  type: DamageType;
  note?: string;
}

export interface InspectionCreate {
  repair_order_id: string;
  fuel_level: number;
  odo_km: number;
  marks: InspectionMark[];
  checklist: Record<string, boolean>;
  belongings: string;
}

export interface DashboardStats {
  in_shop: number;
  bays_used: number;
  bays_total: number;
  revenue_today: number;
  revenue_month: number;
  overdue: number;
  awaiting_approval: number;
  revenue_series: { day: string; value: number }[];
}
