import type {
  AiDraft, AuditEntry, Bay, Customer, InventoryItem, Invoice, RepairOrder, Technician, Vehicle,
} from "@/types";

const d = (offsetH: number) => new Date(Date.UTC(2026, 9, 12, 8) + offsetH * 3600_000).toISOString();

export const customers: Customer[] = [
  { id: "c1", full_name: "Nguyễn Minh Khoa", phone: "0903 112 456", email: "khoa.nm@gmail.com" },
  { id: "c2", full_name: "Trần Thị Lan", phone: "0918 765 222" },
  { id: "c3", full_name: "Lê Hoàng Phúc", phone: "0987 334 901" },
  { id: "c4", full_name: "Công ty TNHH Vận tải Sao Việt", phone: "028 3822 5566" },
  { id: "c5", full_name: "Phạm Quốc Bảo", phone: "0935 448 210" },
  { id: "c6", full_name: "Võ Thanh Hằng", phone: "0909 556 731" },
];

export const vehicles: Vehicle[] = [
  { id: "v1", customer_id: "c1", plate: "51K-238.45", vin: "JTDBR32E720045812", make: "Toyota", model: "Camry 2.5Q", year: 2021, odo_km: 48210, color: "Đen" },
  { id: "v2", customer_id: "c2", plate: "30H-912.07", vin: "MRHGM6640LP031177", make: "Honda", model: "CR-V L", year: 2020, odo_km: 72650, color: "Trắng" },
  { id: "v3", customer_id: "c3", plate: "51G-776.12", vin: "RLLV5ZD6XNV004521", make: "VinFast", model: "Lux A2.0", year: 2022, odo_km: 31090, color: "Xanh" },
  { id: "v4", customer_id: "c4", plate: "51D-104.88", vin: "MHFJW8EM2K0123344", make: "Ford", model: "Transit", year: 2019, odo_km: 186400, color: "Bạc" },
  { id: "v5", customer_id: "c5", plate: "43A-551.30", vin: "KMHD841CBMU112093", make: "Hyundai", model: "Elantra", year: 2021, odo_km: 55320, color: "Đỏ" },
  { id: "v6", customer_id: "c6", plate: "51H-020.66", vin: "WDD2050401R334561", make: "Mercedes-Benz", model: "C200", year: 2020, odo_km: 64010, color: "Xám" },
  { id: "v7", customer_id: "c1", plate: "51F-889.03", vin: "MALA841CBLM556702", make: "Mazda", model: "CX-5 2.0", year: 2019, odo_km: 91200, color: "Xanh đậm" },
];

export const technicians: Technician[] = [
  { id: "t1", full_name: "Đỗ Văn Hùng", skill: "Động cơ", active_orders: 2 },
  { id: "t2", full_name: "Ngô Đức Tài", skill: "Điện – điện tử", active_orders: 1 },
  { id: "t3", full_name: "Bùi Thanh Sơn", skill: "Gầm – phanh", active_orders: 2 },
  { id: "t4", full_name: "Huỳnh Gia Bảo", skill: "Đồng sơn", active_orders: 1 },
];

export const bays: Bay[] = [
  { id: "b1", name: "Cầu nâng 01", type: "lift", repair_order_id: "ro2" },
  { id: "b2", name: "Cầu nâng 02", type: "lift", repair_order_id: "ro4" },
  { id: "b3", name: "Cầu nâng 03", type: "lift", repair_order_id: "ro5" },
  { id: "b4", name: "Cầu nâng 04", type: "lift", repair_order_id: null },
  { id: "b5", name: "Khoang cân chỉnh", type: "alignment", repair_order_id: "ro6" },
  { id: "b6", name: "Phòng sơn", type: "paint", repair_order_id: null },
  { id: "b7", name: "Khoang nhanh", type: "quick", repair_order_id: "ro1" },
];

export const inventory: InventoryItem[] = [
  { id: "p1", sku: "TOY-04152-YZZA6", name: "Lọc dầu Toyota chính hãng", category: "Lọc", on_hand: 34, min_level: 20, unit_cost: 95000, unit_price: 145000, location: "A1-03" },
  { id: "p2", sku: "CAS-EDGE-5W30-4L", name: "Dầu Castrol EDGE 5W-30 (4L)", category: "Dầu nhớt", on_hand: 12, min_level: 15, unit_cost: 780000, unit_price: 1050000, location: "B2-01" },
  { id: "p3", sku: "BRE-P83-089", name: "Má phanh trước Brembo", category: "Phanh", on_hand: 6, min_level: 8, unit_cost: 1150000, unit_price: 1650000, location: "C1-07" },
  { id: "p4", sku: "NGK-ILKAR7B11", name: "Bugi NGK Iridium", category: "Đánh lửa", on_hand: 48, min_level: 24, unit_cost: 210000, unit_price: 320000, location: "A3-11" },
  { id: "p5", sku: "BOS-0280218", name: "Cảm biến lưu lượng khí nạp (MAF)", category: "Cảm biến", on_hand: 2, min_level: 3, unit_cost: 2850000, unit_price: 3900000, location: "D1-02" },
  { id: "p6", sku: "DEN-CABIN-CF", name: "Lọc gió điều hoà than hoạt tính", category: "Lọc", on_hand: 22, min_level: 10, unit_cost: 160000, unit_price: 260000, location: "A1-08" },
  { id: "p7", sku: "GS-DIN65-MF", name: "Ắc quy GS DIN65 MF", category: "Điện", on_hand: 4, min_level: 5, unit_cost: 1750000, unit_price: 2350000, location: "E2-01" },
  { id: "p8", sku: "KYB-339278", name: "Giảm xóc trước KYB Excel-G", category: "Gầm", on_hand: 9, min_level: 4, unit_cost: 1320000, unit_price: 1890000, location: "C3-04" },
  { id: "p9", sku: "BOS-COIL-0221", name: "Mô-bin đánh lửa Bosch", category: "Đánh lửa", on_hand: 7, min_level: 6, unit_cost: 980000, unit_price: 1420000, location: "A3-02" },
];

const pl = (id: string, partId: string, qty: number) => {
  const p = inventory.find((x) => x.id === partId)!;
  return { id, part_id: p.id, sku: p.sku, name: p.name, qty, unit_price: p.unit_price };
};

export const repairOrders: RepairOrder[] = [
  { id: "ro1", code: "RO-2610-0142", customer_id: "c5", vehicle_id: "v5", status: "intake", priority: "normal", complaint: "Bảo dưỡng định kỳ 55.000 km, kiểm tra tiếng kêu khi phanh.", technician_id: null, bay_id: "b7", created_at: d(0.5), promised_at: d(8), parts: [], labor: [], tasks: [{ id: "k1", title: "Kiểm tra ngoại thất khi nhận xe", done: false }], notes: [], quotation_id: null },
  { id: "ro2", code: "RO-2610-0139", customer_id: "c1", vehicle_id: "v1", status: "diagnosis", priority: "high", complaint: "Đèn check engine sáng, xe rung khi chạy không tải.", technician_id: "t1", bay_id: "b1", created_at: d(-3), promised_at: d(6), parts: [], labor: [{ id: "l1", description: "Chẩn đoán bằng máy OBD-II", hours: 0.5, rate: 400000, technician_id: "t1" }], tasks: [{ id: "k2", title: "Đọc mã lỗi OBD", done: true }, { id: "k3", title: "Kiểm tra mô-bin & bugi", done: false }, { id: "k4", title: "Đo cảm biến MAF", done: false }], notes: [{ id: "n1", author: "Đỗ Văn Hùng", body: "Mã P0301, P0171. Máy số 1 bỏ máy, hỗn hợp nghèo. Nghi bugi + MAF bẩn.", created_at: d(-2) }], quotation_id: "q1" },
  { id: "ro3", code: "RO-2610-0136", customer_id: "c2", vehicle_id: "v2", status: "awaiting_approval", priority: "normal", complaint: "Phanh kêu rít, chân phanh sâu.", technician_id: "t3", bay_id: null, created_at: d(-26), promised_at: d(-2), parts: [pl("x1", "p3", 1)], labor: [{ id: "l2", description: "Thay má phanh trước, láng đĩa", hours: 1.5, rate: 400000, technician_id: "t3" }], tasks: [{ id: "k5", title: "Đo độ dày đĩa phanh", done: true }], notes: [], quotation_id: "q2" },
  { id: "ro4", code: "RO-2610-0131", customer_id: "c4", vehicle_id: "v4", status: "in_repair", priority: "urgent", complaint: "Xe tải dịch vụ — thay giảm xóc trước, bảo dưỡng 185.000 km.", technician_id: "t3", bay_id: "b2", created_at: d(-30), promised_at: d(2), parts: [pl("x2", "p8", 2), pl("x3", "p1", 1), pl("x4", "p2", 2)], labor: [{ id: "l3", description: "Thay cặp giảm xóc trước", hours: 2, rate: 400000, technician_id: "t3" }, { id: "l4", description: "Thay dầu, lọc dầu", hours: 0.5, rate: 400000 }], tasks: [{ id: "k6", title: "Tháo giảm xóc cũ", done: true }, { id: "k7", title: "Lắp giảm xóc mới", done: true }, { id: "k8", title: "Thay dầu & lọc", done: false }, { id: "k9", title: "Chạy thử", done: false }], notes: [{ id: "n2", author: "Bùi Thanh Sơn", body: "Cao su chân máy phải có dấu hiệu nứt — đề xuất kiểm tra ở lần sau.", created_at: d(-4) }], quotation_id: null },
  { id: "ro5", code: "RO-2610-0128", customer_id: "c6", vehicle_id: "v6", status: "in_repair", priority: "high", complaint: "Ắc quy yếu, khó khởi động buổi sáng.", technician_id: "t2", bay_id: "b3", created_at: d(-20), promised_at: d(-1), parts: [pl("x5", "p7", 1)], labor: [{ id: "l5", description: "Thay ắc quy, đăng ký lại BMS", hours: 0.8, rate: 450000, technician_id: "t2" }], tasks: [{ id: "k10", title: "Kiểm tra dòng rò", done: true }, { id: "k11", title: "Đăng ký ắc quy mới", done: false }], notes: [], quotation_id: null },
  { id: "ro6", code: "RO-2610-0125", customer_id: "c3", vehicle_id: "v3", status: "qc", priority: "normal", complaint: "Cân chỉnh thước lái, xe bị lệch phải.", technician_id: "t1", bay_id: "b5", created_at: d(-28), promised_at: d(3), parts: [], labor: [{ id: "l6", description: "Cân chỉnh góc đặt bánh xe 3D", hours: 1, rate: 400000 }], tasks: [{ id: "k12", title: "Cân chỉnh", done: true }, { id: "k13", title: "KCS chạy thử", done: false }], notes: [], quotation_id: null },
  { id: "ro7", code: "RO-2610-0119", customer_id: "c1", vehicle_id: "v7", status: "delivered", priority: "normal", complaint: "Thay lọc gió điều hoà, vệ sinh dàn lạnh.", technician_id: "t2", bay_id: null, created_at: d(-50), promised_at: d(-30), parts: [pl("x6", "p6", 1)], labor: [{ id: "l7", description: "Vệ sinh dàn lạnh", hours: 1, rate: 400000 }], tasks: [{ id: "k14", title: "Vệ sinh", done: true }], notes: [], quotation_id: null },
  { id: "ro8", code: "RO-2610-0144", customer_id: "c2", vehicle_id: "v2", status: "intake", priority: "high", complaint: "Điều hoà không mát, có mùi hôi.", technician_id: null, bay_id: null, created_at: d(1), promised_at: d(9), parts: [], labor: [], tasks: [], notes: [], quotation_id: null },
];

export const invoices: Invoice[] = [
  { id: "i1", code: "HD-2610-0088", repair_order_id: "ro7", customer_name: "Nguyễn Minh Khoa", plate: "51F-889.03", issued_at: d(-30), total: 726000, paid: 726000, status: "paid" },
  { id: "i2", code: "HD-2610-0087", repair_order_id: "ro6", customer_name: "Lê Hoàng Phúc", plate: "51G-776.12", issued_at: d(-6), total: 440000, paid: 0, status: "unpaid" },
  { id: "i3", code: "HD-2610-0085", repair_order_id: "ro4", customer_name: "Công ty TNHH Vận tải Sao Việt", plate: "51D-104.88", issued_at: d(-48), total: 8228000, paid: 4000000, status: "partial" },
  { id: "i4", code: "HD-2610-0081", repair_order_id: "ro7", customer_name: "Phạm Quốc Bảo", plate: "43A-551.30", issued_at: d(-96), total: 2156000, paid: 2156000, status: "paid" },
  { id: "i5", code: "HD-2610-0079", repair_order_id: "ro5", customer_name: "Võ Thanh Hằng", plate: "51H-020.66", issued_at: d(-120), total: 3410000, paid: 3410000, status: "paid" },
];

export const aiDrafts: AiDraft[] = [
  {
    id: "q1", repair_order_id: "ro2", model: "GarageTools-Assist v2", generated_at: d(-1.5), status: "pending_review", confidence: 0.82,
    obd_findings: [
      { code: "P0301", description: "Phát hiện bỏ máy xi-lanh số 1", severity: "high" },
      { code: "P0171", description: "Hỗn hợp nhiên liệu quá nghèo (Bank 1)", severity: "medium" },
    ],
    history_summary: "Xe đã bảo dưỡng 4 lần tại xưởng. Lần thay bugi gần nhất ở 20.000 km (cách đây ~28.000 km). Chưa từng vệ sinh/ thay cảm biến MAF. Lịch sử thay dầu đúng hạn.",
    service_explanation: "Bugi xi-lanh số 1 có khả năng mòn điện cực gây bỏ máy. Cảm biến MAF bám bẩn làm ECU đọc sai lưu lượng khí, dẫn đến hỗn hợp nghèo. Đề xuất thay bộ bugi, kiểm tra mô-bin số 1 và vệ sinh/thay MAF.",
    lines: [
      { id: "a1", kind: "part", name: "Bugi NGK Iridium", qty: 4, unit_price: 320000, ai_reason: "Quá chu kỳ thay theo khuyến nghị hãng" },
      { id: "a2", kind: "part", name: "Cảm biến lưu lượng khí nạp (MAF)", qty: 1, unit_price: 3900000, ai_reason: "Liên quan mã P0171" },
      { id: "a3", kind: "part", name: "Mô-bin đánh lửa Bosch", qty: 1, unit_price: 1420000, ai_reason: "Dự phòng nếu đo mô-bin số 1 không đạt" },
      { id: "a4", kind: "labor", name: "Thay bugi & kiểm tra mô-bin", qty: 1, unit_price: 400000, ai_reason: "Định mức 1.0 giờ" },
      { id: "a5", kind: "labor", name: "Thay cảm biến MAF, xoá lỗi", qty: 1, unit_price: 200000, ai_reason: "Định mức 0.5 giờ" },
    ],
  },
  {
    id: "q2", repair_order_id: "ro3", model: "GarageTools-Assist v2", generated_at: d(-20), status: "pending_review", confidence: 0.9,
    obd_findings: [],
    history_summary: "Lần thay má phanh trước gần nhất ở 41.000 km. Đĩa phanh chưa thay. Khách thường chạy nội thành.",
    service_explanation: "Má phanh trước mòn tới vạch báo, đĩa còn trong dung sai, có thể láng lại. Đề xuất thay má phanh và thay dầu phanh DOT4.",
    lines: [
      { id: "b1", kind: "part", name: "Má phanh trước Brembo", qty: 1, unit_price: 1650000, ai_reason: "Mòn đến vạch báo" },
      { id: "b2", kind: "labor", name: "Thay má phanh, láng đĩa", qty: 1, unit_price: 600000, ai_reason: "Định mức 1.5 giờ" },
    ],
  },
];

export const auditLog: AuditEntry[] = [
  { id: "au1", draft_id: "q1", actor: "Hệ thống AI", role: "manager", action: "generate", detail: "Tạo báo giá nháp từ mã lỗi OBD và lịch sử bảo dưỡng", at: d(-1.5) },
  { id: "au2", draft_id: "q2", actor: "Hệ thống AI", role: "manager", action: "generate", detail: "Tạo báo giá nháp từ ghi chú kỹ thuật viên", at: d(-20) },
];
