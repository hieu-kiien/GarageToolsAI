import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { Role, RepairStatus, Priority, InvoiceStatus } from "@/types";

export const ROLE_LABEL: Record<Role, string> = {
  manager: "Quản lý",
  receptionist: "Tiếp tân",
  technician: "Kỹ thuật viên",
  cashier: "Thu ngân",
};
export const ROLE_USER: Record<Role, string> = {
  manager: "Trương Quang Tú",
  receptionist: "Lý Ngọc Hân",
  technician: "Đỗ Văn Hùng",
  cashier: "Mai Thu Trang",
};

export type Area = "dashboard" | "board" | "orders" | "inspection" | "ai" | "inventory" | "finance";

/** Which screens each role may open. Mirrors backend permission dependencies. */
export const PERMISSIONS: Record<Role, Area[]> = {
  manager: ["dashboard", "board", "orders", "inspection", "ai", "inventory", "finance"],
  receptionist: ["dashboard", "board", "orders", "inspection"],
  technician: ["board", "orders", "inspection"],
  cashier: ["dashboard", "orders", "finance"],
};

export const STATUS_LABEL: Record<RepairStatus, string> = {
  intake: "Tiếp nhận",
  diagnosis: "Kiểm tra chẩn đoán",
  awaiting_approval: "Chờ duyệt báo giá",
  in_repair: "Đang sửa chữa",
  qc: "Nghiệm thu / KCS",
  delivered: "Đã giao xe",
};
export const STATUS_ORDER: RepairStatus[] = ["intake", "diagnosis", "awaiting_approval", "in_repair", "qc", "delivered"];
export const PRIORITY_LABEL: Record<Priority, string> = { normal: "Thường", high: "Ưu tiên", urgent: "Khẩn" };
export const INVOICE_LABEL: Record<InvoiceStatus, string> = { unpaid: "Chưa thanh toán", partial: "Thanh toán một phần", paid: "Đã thanh toán", void: "Đã huỷ" };

type Ctx = { role: Role; setRole: (r: Role) => void; can: (a: Area) => boolean; user: string };
const RoleCtx = createContext<Ctx | null>(null);

export function RoleProvider({ children }: { children: ReactNode }) {
  const [role, setRoleState] = useState<Role>("manager");
  useEffect(() => {
    const r = localStorage.getItem("gt-role") as Role | null;
    if (r && r in ROLE_LABEL) setRoleState(r);
  }, []);
  const setRole = (r: Role) => { setRoleState(r); localStorage.setItem("gt-role", r); };
  return (
    <RoleCtx.Provider value={{ role, setRole, can: (a) => PERMISSIONS[role].includes(a), user: ROLE_USER[role] }}>
      {children}
    </RoleCtx.Provider>
  );
}

export function useRole() {
  const c = useContext(RoleCtx);
  if (!c) throw new Error("useRole outside RoleProvider");
  return c;
}

export const vnd = (n: number) => new Intl.NumberFormat("vi-VN").format(n) + " ₫";
export const vndShort = (n: number) => (n >= 1e9 ? (n / 1e9).toFixed(2) + " tỷ" : n >= 1e6 ? (n / 1e6).toFixed(1).replace(".0", "") + " tr" : vnd(n));
export const fmtTime = (iso: string) => new Date(iso).toLocaleString("vi-VN", { hour: "2-digit", minute: "2-digit", day: "2-digit", month: "2-digit", timeZone: "Asia/Ho_Chi_Minh" });
