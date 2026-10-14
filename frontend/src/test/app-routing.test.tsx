import { QueryClient } from "@tanstack/react-query";
import { createRouter, rootRouteId } from "@tanstack/react-router";
import { describe, expect, it } from "vitest";

import { routeTree } from "@/routeTree.gen";

// Match routes without running loaders or rendering: loaders may need a server or
// network the test run lacks, and jsdom never loads the stylesheets React waits on.
const TRANG = [
  "/",
  "/workflow",
  "/repair-orders",
  "/repair-orders/12",
  "/inspection",
  "/inventory",
  "/finance",
  "/ai-review",
  "/appointments",
  "/customers",
  "/quotations",
  "/quotations/3",
  "/warranties",
  "/catalog",
  "/users",
  "/reports",
];

describe("App routing", () => {
  it.each(TRANG)("khớp trang cho %s thay vì rơi vào not found", (path) => {
    const router = createRouter({ routeTree, context: { queryClient: new QueryClient() } });

    const matches = router.matchRoutes(path);

    expect(matches.at(-1)?.routeId).not.toBe(rootRouteId);
  });

  it("gọi /bất-kỳ-trang-nào-không-tồn-tại vẫn rơi vào not found", () => {
    const router = createRouter({ routeTree, context: { queryClient: new QueryClient() } });

    const matches = router.matchRoutes("/khong-ton-tai");

    expect(matches.at(-1)?.routeId).toBe(rootRouteId);
  });
});
