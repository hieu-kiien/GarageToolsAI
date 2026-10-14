import { describe, expect, it } from "vitest";

import { AREA_QUYEN, fmtNgay, fmtTime, vnd, vndShort, type Area } from "@/lib/rbac";

describe("fmtNgay/fmtTime — UTC của backend phải hiển thị giờ VN", () => {
  it("giờ UTC 00:00 là 07:00 sáng VN cùng ngày (không được lệch thành 00:00)", () => {
    expect(fmtTime("2026-10-13 00:00:00")).toContain("07:00");
    expect(fmtNgay("2026-10-13 00:00:00")).toBe("13/10/2026");
  });

  it("17:00 UTC hôm trước là 00:00 VN hôm sau — nếu thiếu Z sẽ hiển thị sai ngày", () => {
    expect(fmtNgay("2026-10-13 17:00:00")).toBe("14/10/2026");
    expect(fmtTime("2026-10-13 17:00:00")).toContain("00:00");
  });

  it("chuỗi đã có múi giờ hoặc không parse được thì giữ nguyên", () => {
    expect(fmtTime("2026-10-13T00:00:00Z")).toContain("07:00");
    expect(fmtTime("không-phải-ngày")).toBe("không-phải-ngày");
  });
});

describe("vnd", () => {
  it("định dạng tiền Việt", () => {
    expect(vnd(1500000)).toBe("1.500.000 ₫");
    expect(vndShort(2500000000)).toBe("2.50 tỷ");
  });
});

describe("AREA_QUYEN — ánh xạ màn hình → quyền backend", () => {
  it("mọi area đều có ít nhất một quyền backend", () => {
    for (const [area, ds] of Object.entries(AREA_QUYEN)) {
      expect(ds.length, `area ${area} không có quyền nào`).toBeGreaterThan(0);
    }
  });

  it("thu ngân (payment.record) mở được màn Hoá đơn dù không có report.view (ADR-4)", () => {
    expect(AREA_QUYEN.finance).toContain("payment.record");
  });

  it("màn Báo giá chỉ dành cho quyền quote.manage — khớp backend GET /api/quotations", () => {
    expect(AREA_QUYEN.quotes).toEqual(["quote.manage"]);
  });

  it("Người dùng chỉ quản lý mới mở được (user.manage)", () => {
    expect(AREA_QUYEN.users).toEqual(["user.manage"]);
  });

  it("Tiếp nhận xe chỉ dành cho quyền order.create — khớp POST /api/orders", () => {
    expect(AREA_QUYEN.inspection).toEqual(["order.create"]);
  });

  it("Kho và Bảo hành khớp quyền backend (stock.manage | order.view / warranty.manage)", () => {
    expect(AREA_QUYEN.inventory).toEqual(["stock.manage", "order.view"]);
    expect(AREA_QUYEN.warranty).toEqual(["warranty.manage"]);
  });

  it("mọi area khai báo là khóa hợp lệ của kiểu Area", () => {
    const hopLe: Area[] = [
      "dashboard",
      "board",
      "orders",
      "inspection",
      "ai",
      "inventory",
      "finance",
      "appointments",
      "customers",
      "quotes",
      "warranty",
      "catalog",
      "users",
      "reports",
      "history",
    ];
    expect(Object.keys(AREA_QUYEN).sort()).toEqual([...hopLe].sort());
  });
});
