import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { AlertTriangle, Boxes, ArrowDownToLine, SlidersHorizontal } from "lucide-react";
import { api, q, ApiError } from "@/services/api";
import { useLookups } from "@/services/lookups";
import { useNhan, useRole, fmtTime, vnd } from "@/lib/rbac";
import { PageHeader, Panel, Stat, NoAccess, Empty, DangTai, Pill } from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export const Route = createFileRoute("/inventory")({
  head: () => ({
    meta: [
      { title: "Kho phụ tùng — GarageTools AI" },
      {
        name: "description",
        content: "Sổ giao dịch kho, nhập kho, điều chỉnh tồn và cảnh báo mức tối thiểu.",
      },
      { property: "og:title", content: "Kho phụ tùng — GarageTools AI" },
      { property: "og:description", content: "Quản lý tồn kho phụ tùng ô tô." },
    ],
  }),
  component: Inventory,
});

function Inventory() {
  const { area, can } = useRole();
  const N = useNhan();
  const L = useLookups();
  const qc = useQueryClient();

  const [locLyDo, setLocLyDo] = useState("all");
  const [trang, setTrang] = useState(1);

  // Form nhập kho.
  const [nhapMa, setNhapMa] = useState("");
  const [nhapSl, setNhapSl] = useState(1);
  const [nhapGhiChu, setNhapGhiChu] = useState("");
  // Form điều chỉnh.
  const [dcMa, setDcMa] = useState("");
  const [dcMoi, setDcMoi] = useState(0);
  const [dcGhiChu, setDcGhiChu] = useState("");

  const ds = useQuery(
    q.stock({ moi_trang: 30, trang, reason: locLyDo === "all" ? undefined : locLyDo || undefined }),
  );
  const loi = (e: unknown) => toast.error(e instanceof ApiError ? e.message : "Thao tác thất bại.");

  const nhap = useMutation({
    mutationFn: () =>
      api.nhapKho({ part_id: Number(nhapMa), qty: nhapSl, note: nhapGhiChu.trim() || undefined }),
    onSuccess: async (kq) => {
      toast.success(`${kq.thong_bao} Tồn hiện tại: ${kq.ton_kho}.`);
      setNhapMa("");
      setNhapSl(1);
      setNhapGhiChu("");
      await qc.invalidateQueries({ queryKey: ["stock"] });
      await qc.invalidateQueries({ queryKey: ["parts"] });
      await qc.invalidateQueries({ queryKey: ["lookups"] });
    },
    onError: loi,
  });

  const dieuChinh = useMutation({
    mutationFn: () =>
      api.dieuChinhKho({ part_id: Number(dcMa), moi: dcMoi, note: dcGhiChu.trim() || undefined }),
    onSuccess: async (kq) => {
      toast.success(`${kq.thong_bao} Tồn hiện tại: ${kq.ton_kho}.`);
      setDcMa("");
      setDcMoi(0);
      setDcGhiChu("");
      await qc.invalidateQueries({ queryKey: ["stock"] });
      await qc.invalidateQueries({ queryKey: ["parts"] });
      await qc.invalidateQueries({ queryKey: ["lookups"] });
    },
    onError: loi,
  });

  if (!area("inventory")) return <NoAccess />;
  if (ds.isPending) return <DangTai mat="Đang tải sổ kho…" />;
  if (ds.isError)
    return (
      <div className="p-8 text-sm text-destructive">
        Không tải được sổ kho. {ds.error instanceof ApiError ? ds.error.message : ""}
      </div>
    );
  if (!ds.data) return <DangTai mat="Đang tải sổ kho…" />;

  const { dong, tong, trang: trangHienTai, tong_trang, canh_bao, lech, ly_do } = ds.data;
  const coQuanLyKho = can("stock.manage");

  return (
    <>
      <PageHeader
        eyebrow="Kho & Tài chính"
        title="Kho phụ tùng"
        desc="Sổ giao dịch tồn kho — mọi biến động đều được backend ghi lại kèm người thực hiện."
      />
      <div className="space-y-6 p-6 lg:p-8">
        <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
          <Stat label="Giao dịch (theo bộ lọc)" value={tong} icon={<Boxes className="size-4" />} />
          <Stat
            label="Cảnh báo tồn"
            value={canh_bao.length}
            icon={<AlertTriangle className="size-4 text-destructive" />}
            sub="Tồn <= mức tối thiểu"
          />
          <Stat
            label="Lệch sổ"
            value={<span className={lech.length ? "text-destructive" : ""}>{lech.length}</span>}
            icon={<SlidersHorizontal className="size-4" />}
            sub={lech.length ? "Cần kiểm kê đối chiếu" : "Sổ khớp tồn thực tế"}
          />
          <Stat label="Mã đang theo dõi" value={L.phu_tung.length} sub="Danh mục hoạt động" />
        </div>

        <div className="grid gap-6 xl:grid-cols-3">
          {coQuanLyKho && (
            <>
              <Panel title="Nhập kho" className="xl:col-span-1">
                <div className="space-y-3">
                  <Select value={nhapMa} onValueChange={setNhapMa}>
                    <SelectTrigger>
                      <SelectValue placeholder="Chọn phụ tùng…" />
                    </SelectTrigger>
                    <SelectContent>
                      {L.phu_tung.map((p) => (
                        <SelectItem key={p.id} value={String(p.id)}>
                          {p.name} — còn {p.stock}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Input
                    type="number"
                    min={1}
                    value={nhapSl}
                    onChange={(e) => setNhapSl(Number(e.target.value))}
                    placeholder="Số lượng nhập"
                  />
                  <Input
                    value={nhapGhiChu}
                    onChange={(e) => setNhapGhiChu(e.target.value)}
                    placeholder="Ghi chú (nhà cung cấp, phiếu…)"
                  />
                  <Button
                    className="w-full"
                    disabled={!nhapMa || nhapSl < 1 || nhap.isPending}
                    onClick={() => nhap.mutate()}
                  >
                    <ArrowDownToLine className="size-4" />
                    Ghi nhận nhập kho
                  </Button>
                </div>
              </Panel>

              <Panel title="Điều chỉnh tồn (kiểm kê)" className="xl:col-span-1">
                <div className="space-y-3">
                  <Select value={dcMa} onValueChange={setDcMa}>
                    <SelectTrigger>
                      <SelectValue placeholder="Chọn phụ tùng…" />
                    </SelectTrigger>
                    <SelectContent>
                      {L.phu_tung.map((p) => (
                        <SelectItem key={p.id} value={String(p.id)}>
                          {p.name} — tồn {p.stock}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Input
                    type="number"
                    min={0}
                    value={dcMoi}
                    onChange={(e) => setDcMoi(Number(e.target.value))}
                    placeholder="Số lượng tồn thực tế mới"
                  />
                  <Input
                    value={dcGhiChu}
                    onChange={(e) => setDcGhiChu(e.target.value)}
                    placeholder="Lý do điều chỉnh"
                  />
                  <Button
                    className="w-full"
                    variant="outline"
                    disabled={!dcMa || dieuChinh.isPending}
                    onClick={() => dieuChinh.mutate()}
                  >
                    <SlidersHorizontal className="size-4" />
                    Điều chỉnh tồn
                  </Button>
                </div>
              </Panel>
            </>
          )}

          <Panel
            className="xl:col-span-1"
            title="Cảnh báo tồn"
            action={<Pill t={canh_bao.length ? "danger" : "success"}>{canh_bao.length}</Pill>}
            bodyClass="p-0"
          >
            {canh_bao.length === 0 ? (
              <div className="p-4">
                <Empty title="Không có mã nào sắp hết" />
              </div>
            ) : (
              <ul className="divide-y">
                {canh_bao.map((p) => (
                  <li
                    key={p.id}
                    className="flex items-center justify-between gap-2 px-4 py-2.5 text-sm"
                  >
                    <div>
                      <div>{p.name}</div>
                      <div className="font-mono text-[11px] text-muted-foreground">{p.sku}</div>
                    </div>
                    <span className="tabular text-xs font-medium text-destructive">
                      {p.stock}/{p.min_stock}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </Panel>
        </div>

        {lech.length > 0 && (
          <Panel title="Lệch sổ (cần đối chiếu)" bodyClass="p-0">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 text-left text-[11px] uppercase tracking-wider text-muted-foreground">
                <tr>
                  <th className="px-4 py-2 font-medium">Phụ tùng</th>
                  <th className="px-4 py-2 text-right font-medium">Tồn (parts.stock)</th>
                  <th className="px-4 py-2 text-right font-medium">Tổng sổ giao dịch</th>
                  <th className="px-4 py-2 text-right font-medium">Lệch</th>
                </tr>
              </thead>
              <tbody className="divide-y">
                {lech.map((l) => (
                  <tr key={l.part_id} className="bg-danger-soft/40">
                    <td className="px-4 py-2.5">{l.name}</td>
                    <td className="tabular px-4 text-right">{l.stock}</td>
                    <td className="tabular px-4 text-right">{l.tong_sach}</td>
                    <td className="tabular px-4 text-right font-medium text-destructive">
                      {l.lech}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Panel>
        )}

        <Panel
          title="Sổ giao dịch kho"
          bodyClass="p-0"
          action={
            <div className="flex items-center gap-2">
              <Select
                value={locLyDo}
                onValueChange={(v) => {
                  setLocLyDo(v);
                  setTrang(1);
                }}
              >
                <SelectTrigger className="h-8 w-44 text-xs">
                  <SelectValue placeholder="Tất cả lý do" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tất cả lý do</SelectItem>
                  {Object.entries(ly_do).map(([k, v]) => (
                    <SelectItem key={k} value={k}>
                      {v}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          }
        >
          {dong.length === 0 ? (
            <div className="p-4">
              <Empty title="Chưa có giao dịch kho" desc="Nhập kho ở ô bên trên để bắt đầu." />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 text-left text-[11px] uppercase tracking-wider text-muted-foreground">
                  <tr>
                    {[
                      "Thời gian",
                      "Phụ tùng",
                      "SL",
                      "Lý do",
                      "Phiếu",
                      "Người thực hiện",
                      "Ghi chú",
                    ].map((h) => (
                      <th key={h} className="px-4 py-2 font-medium">
                        {h}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {dong.map((g) => (
                    <tr key={g.id} className="hover:bg-muted/40">
                      <td className="tabular px-4 py-2.5 text-xs">{fmtTime(g.created_at)}</td>
                      <td className="px-4 py-2.5">{g.ten_phu_tung}</td>
                      <td
                        className={[
                          "tabular",
                          "px-4",
                          "py-2.5",
                          "font-medium",
                          g.qty > 0 ? "text-success" : "text-destructive",
                        ].join(" ")}
                      >
                        {g.qty > 0 ? `+${g.qty}` : g.qty}
                      </td>
                      <td className="px-4 py-2.5">
                        <Pill
                          t={
                            g.reason === "RECEIPT"
                              ? "success"
                              : g.reason === "USAGE"
                                ? "danger"
                                : g.reason === "ADJUSTMENT"
                                  ? "warning"
                                  : "info"
                          }
                        >
                          {N.lyDoKho(g.reason)}
                        </Pill>
                      </td>
                      <td className="px-4 py-2.5">
                        {g.repair_order_id ? (
                          <Link
                            to="/repair-orders/$id"
                            params={{ id: String(g.repair_order_id) }}
                            className="font-mono text-xs text-primary"
                          >
                            #{g.repair_order_id}
                          </Link>
                        ) : (
                          <span className="text-muted-foreground">—</span>
                        )}
                      </td>
                      <td className="px-4 py-2.5 text-muted-foreground">{g.nguoi_tao ?? "—"}</td>
                      <td className="max-w-[240px] truncate px-4 py-2.5 text-xs text-muted-foreground">
                        {g.note ?? "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <div className="flex items-center justify-between border-t px-4 py-3 text-xs text-muted-foreground">
            <span className="tabular">
              Trang {trangHienTai}/{tong_trang} · {tong} giao dịch
            </span>
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                disabled={trangHienTai <= 1}
                onClick={() => setTrang(trangHienTai - 1)}
              >
                Trước
              </Button>
              <Button
                size="sm"
                variant="outline"
                disabled={trangHienTai >= tong_trang}
                onClick={() => setTrang(trangHienTai + 1)}
              >
                Sau
              </Button>
            </div>
          </div>
        </Panel>

        <p className="text-center text-[11px] text-muted-foreground">
          Giá trị tồn kho và mọi biến động do backend tính — thao tác ghi đều bắt buộc quyền{" "}
          <code className="font-mono">stock.manage</code>.
        </p>
      </div>
    </>
  );
}
