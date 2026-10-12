# GarageTools AI — Backend Handoff (FastAPI)

Frontend types: `src/types/index.ts` (mirror as Pydantic models). Mock client: `src/services/api.ts` — each function is annotated with its endpoint; swap the mock body for `fetch`.

Conventions: JSON, money = integer VND, dates = ISO 8601 UTC, auth via bearer token carrying `role ∈ {manager, receptionist, technician, cashier}`.

## Business rules (must be enforced server-side)
- AI never approves quotations and never computes authoritative totals.
- Only `manager` may call `POST /api/ai/drafts/{id}/review`.
- Totals (`OrderTotals`: parts_subtotal, labor_subtotal, vat 10%, grand_total) are computed by the backend.
- `awaiting_approval → in_repair` requires an approved quotation (manager).
- Every review edit/approve/reject writes an `AuditEntry`.

## Endpoints

| Method | Path | Request | Response | Roles |
|---|---|---|---|---|
| GET | /api/dashboard/stats | — | DashboardStats | manager, receptionist, cashier |
| GET | /api/repair-orders | ?status= | RepairOrder[] | all |
| GET | /api/repair-orders/{id} | — | RepairOrder & { totals: OrderTotals } | all |
| PATCH | /api/repair-orders/{id}/status | { status: RepairStatus } | RepairOrder | manager, receptionist, technician |
| PATCH | /api/repair-orders/{id}/assignment | { technician_id, bay_id } | RepairOrder | manager, receptionist |
| PATCH | /api/repair-orders/{id}/tasks/{task_id} | — (toggle) | RepairTask | manager, technician |
| POST | /api/repair-orders/{id}/notes | { author, body } | TechNote | all |
| POST | /api/repair-orders/{id}/inspection | InspectionCreate | Inspection | manager, receptionist, technician |
| GET | /api/customers | — | Customer[] | all |
| GET | /api/vehicles | — | Vehicle[] | all |
| GET | /api/technicians | — | Technician[] | all |
| GET | /api/bays | — | Bay[] | all |
| GET | /api/inventory | — | InventoryItem[] | manager |
| GET | /api/invoices | — | Invoice[] | manager, cashier |
| POST | /api/payments | PaymentCreate { invoice_id, amount, method } | Invoice | manager, cashier |
| GET | /api/ai/drafts | — | AiDraft[] | manager |
| GET | /api/ai/drafts/{id}/audit | — | AuditEntry[] | manager |
| POST | /api/ai/drafts/{id}/review | { decision: "approve"\|"reject", lines: AiDraftLine[], changes: string[], reason? } | { draft: AiDraft, totals: OrderTotals } | manager only (403 otherwise) |

## Enums
- RepairStatus: intake, diagnosis, awaiting_approval, in_repair, qc, delivered
- Priority: normal, high, urgent
- InvoiceStatus: unpaid, partial, paid, void
- AiDraftStatus: pending_review, approved, rejected
- DamageType: scratch, dent, crack, missing

## Role navigation
- Quản lý: all screens
- Tiếp tân: Tổng quan, Bảng điều phối, Lệnh sửa chữa, Kiểm tra tiếp nhận
- Kỹ thuật viên: Bảng điều phối, Lệnh sửa chữa, Kiểm tra tiếp nhận
- Thu ngân: Tổng quan, Lệnh sửa chữa, Hoá đơn & Thanh toán
