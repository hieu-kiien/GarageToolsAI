import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Car, Wallet, ClipboardList, AlertTriangle, ArrowRight } from "lucide-react";
import { api, q, ApiError } from "@/services/api";
import { useNhan, useRole, fmtTime, vnd, vndShort } from "@/lib/rbac";
import {
  PageHeader,
  Panel,
  Stat,
  StatusPill,
  Plate,
  NoAccess,
  Empty,
  DangTai,
  Pill,
} from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Tổng quan xưởng — GarageTools AI" },
      {
        name: "description",
        content: "Chỉ số vận hành xưởng: phiếu sửa chữa, doanh thu, cảnh báo tồn kho.",
      },
      { property: "og:title", content: "Tổng quan xưởng — GarageTools AI" },
      { property: "og:description", content: "Dashboard vận hành xưởng dịch vụ ô tô." },
    ],
  }),
  component: Dashboard,
});

function Dashboard() {
  const { area, user } = useRole();
  const N = useNhan();
  const dash = useQuery(q.dashboard());
  const canhBao = useQuery(q.stockWarnings());

  if (!area("dashboard")) return <NoAccess />;
  if (dash.isPending) return <DangTai mat="Đang tải số liệu tổng quan…" />;
  if (dash.isError)
    return (
      <div className="p-8 text-sm text-destructive">
        Không tải được số liệu tổng quan. {dash.error instanceof ApiError ? dash.error.message : ""}
      </div>
    );

  const { kpi, trang_thai, gan_nhat, doanh_thu } = dash.data;
  const tongTrangThai = trang_thai.reduce((s, t) => s + t.n, 0) || 1;
  const maxTrangThai = Math.max(...trang_thai.map((t) => t.n), 1);
  const bao = canhBao.data?.canh_bao ?? [];
  const gio = new Date().getHours();
  const loiChao =
    gio < 11 ? "Chào buổi sáng" : gio < 13 ? "Chào trưa" : gio < 18 ? "Chào chiều" : "Chào tối";

  return (
    <>
      <PageHeader
        eyebrow={new Date().toLocaleDateString("vi-VN", {
          weekday: "long",
          day: "2-digit",
          month: "2-digit",
          year: "numeric",
        })}
        title={`${loiChao}, ${user?.full_name ?? ""}`}
        desc="Số liệu lấy trực tiếp từ hệ thống backend — tổng tiền do hệ thống kế toán tính."
        actions={
          <>
            <Button variant="outline" asChild>
              <Link to="/inspection">Tiếp nhận xe</Link>
            </Button>
            <Button asChild>
              <Link to="/workflow">Mở bảng điều phối</Link>
            </Button>
          </>
        }
      />
      <div className="space-y-6 p-6 lg:p-8">
        <div className="grid grid-cols-2 gap-4 xl:grid-cols-4">
          <Stat
            label="Tổng phiếu sửa chữa"
            value={kpi.tong_phieu}
            icon={<ClipboardList className="size-4" />}
            sub={`${kpi.khach_hang} khách hàng · ${kpi.xe} xe`}
          />
          <Stat
            label="Đang xử lý"
            value={kpi.dang_xu_ly}
            icon={<Car className="size-4" />}
            sub={`${kpi.lich_hen} lịch hẹn`}
          />
          <Stat
            label="Đã thu"
            value={vndShort(kpi.da_thu)}
            icon={<Wallet className="size-4" />}
            sub={vnd(kpi.da_thu)}
          />
          <Stat
            label="Công nợ"
            value={<span className="text-destructive">{vndShort(kpi.chua_thu)}</span>}
            icon={<AlertTriangle className="size-4" />}
            sub={`${kpi.cho_duyet_ai} kết quả AI chờ duyệt`}
          />
        </div>

        <div className="grid gap-6 xl:grid-cols-3">
          <Panel
            title="Doanh thu 6 tháng gần nhất"
            className="xl:col-span-2"
            action={
              <span className="text-xs text-muted-foreground">
                Đơn vị: triệu ₫ · do backend tính
              </span>
            }
          >
            <div className="h-64">
              <ResponsiveContainer>
                <AreaChart
                  data={doanh_thu.map((r) => ({
                    ...r,
                    label: r.thang.slice(5),
                    v: r.tong / 1e6,
                    thu: r.da_thu / 1e6,
                  }))}
                  margin={{ left: -20, right: 8, top: 8 }}
                >
                  <defs>
                    <linearGradient id="g" x1="0" x2="0" y1="0" y2="1">
                      <stop offset="0%" stopColor="var(--chart-1)" stopOpacity={0.22} />
                      <stop offset="100%" stopColor="var(--chart-1)" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid stroke="var(--border)" vertical={false} />
                  <XAxis
                    dataKey="label"
                    tickLine={false}
                    axisLine={false}
                    fontSize={11}
                    stroke="var(--muted-foreground)"
                  />
                  <YAxis
                    tickLine={false}
                    axisLine={false}
                    fontSize={11}
                    stroke="var(--muted-foreground)"
                  />
                  <Tooltip
                    formatter={(v: number, name: string) => [
                      `${v.toFixed(1)} tr ₫`,
                      name === "thu" ? "Đã thu" : "Phát hành",
                    ]}
                    labelFormatter={(l) => `Tháng ${l}`}
                    contentStyle={{
                      borderRadius: 8,
                      border: "1px solid var(--border)",
                      fontSize: 12,
                    }}
                  />
                  <Area dataKey="v" stroke="var(--chart-1)" strokeWidth={2} fill="url(#g)" />
                  <Area
                    dataKey="thu"
                    stroke="var(--success)"
                    strokeWidth={1.5}
                    fill="transparent"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </Panel>

          <Panel title="Phân bổ theo trạng thái">
            <div className="space-y-3">
              {trang_thai.map((t) => (
                <div key={t.status}>
                  <div className="mb-1 flex justify-between text-xs">
                    <span>{N.trangThai(t.status)}</span>
                    <span className="tabular font-medium">{t.n}</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-muted">
                    <div
                      className="h-full rounded-full bg-primary"
                      style={{ width: `${(t.n / maxTrangThai) * 100}%` }}
                    />
                  </div>
                </div>
              ))}
              <p className="pt-1 text-[11px] text-muted-foreground">
                Tổng {tongTrangThai} phiếu (kể cả đã huỷ).
              </p>
            </div>
          </Panel>
        </div>

        <div className="grid gap-6 xl:grid-cols-3">
          <Panel
            title={
              <span className="flex items-center gap-2">
                <AlertTriangle className="size-4 text-destructive" />
                Cảnh báo tồn kho
              </span>
            }
            action={<Pill t={bao.length ? "danger" : "success"}>{bao.length}</Pill>}
            bodyClass="p-0"
            className="xl:col-span-1"
          >
            {bao.length === 0 ? (
              <div className="p-4">
                <Empty title="Tồn kho ổn định" desc="Không mã nào dưới mức tối thiểu." />
              </div>
            ) : (
              <ul className="divide-y">
                {bao.slice(0, 6).map((p) => (
                  <li
                    key={p.id}
                    className="flex items-center justify-between gap-3 px-4 py-2.5 text-sm"
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

          <Panel
            title="Xe gần đây"
            bodyClass="p-0"
            className="xl:col-span-2"
            action={
              <Link to="/repair-orders" className="text-xs font-medium text-primary">
                Xem tất cả
              </Link>
            }
          >
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead className="bg-muted/50 text-left text-[11px] uppercase tracking-wider text-muted-foreground">
                  <tr>
                    <th className="px-4 py-2 font-medium">Mã phiếu</th>
                    <th className="px-4 py-2 font-medium">Biển số</th>
                    <th className="px-4 py-2 font-medium">Trạng thái</th>
                    <th className="px-4 py-2 font-medium">Ghi chú</th>
                    <th className="px-4 py-2 font-medium">Ngày tạo</th>
                  </tr>
                </thead>
                <tbody className="divide-y">
                  {gan_nhat.map((o) => (
                    <tr key={o.id} className="hover:bg-muted/40">
                      <td className="px-4 py-2.5">
                        <Link
                          to="/repair-orders/$id"
                          params={{ id: String(o.id) }}
                          className="inline-flex items-center gap-1 font-mono text-xs font-medium text-primary"
                        >
                          #{o.id} <ArrowRight className="size-3" />
                        </Link>
                      </td>
                      <td className="px-4 py-2.5">
                        <Plate>{o.plate}</Plate>
                      </td>
                      <td className="px-4 py-2.5">
                        <StatusPill s={o.status} />
                      </td>
                      <td className="max-w-[280px] truncate px-4 py-2.5 text-xs text-muted-foreground">
                        {o.technical_notes ?? "—"}
                      </td>
                      <td className="tabular px-4 py-2.5 text-xs">{fmtTime(o.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {gan_nhat.length === 0 && (
              <div className="p-4">
                <Empty title="Chưa có phiếu nào" />
              </div>
            )}
          </Panel>
        </div>

        <p className="text-center text-[11px] text-muted-foreground">
          Số liệu do backend tính toán — AI và giao diện không tự tính tổng tiền.
        </p>
      </div>
    </>
  );
}
