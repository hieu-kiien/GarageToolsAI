import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { useEffect, useState, type ReactNode } from "react";
import { q, ApiError } from "@/services/api";
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
} from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/reports")({
  head: () => ({
    meta: [
      { title: "Báo cáo & Lịch sử — GarageTools AI" },
      {
        name: "description",
        content: "Báo cáo doanh thu, dịch vụ, phụ tùng và lịch sử hoạt động của xưởng.",
      },
      { property: "og:title", content: "Báo cáo & Lịch sử — GarageTools AI" },
      {
        property: "og:description",
        content: "Báo cáo quản trị và lịch sử thao tác trong xưởng dịch vụ.",
      },
    ],
  }),
  component: Reports,
});

type DongBaoCao = Record<string, string | number | null>;
type Nhan = ReturnType<typeof useNhan>;
type The = { nhan: string; giaTri: ReactNode; phu?: ReactNode; canh?: boolean };
type Cot = { tieuDe: string; hien: (d: DongBaoCao) => ReactNode };
type CauHinh = {
  ten: string;
  cot?: Cot[];
  kpi?: (dong: DongBaoCao[], N: Nhan) => The[];
};

const laySo = (d: DongBaoCao, k: string) => Number(d[k] ?? 0);
const layChuoi = (d: DongBaoCao, k: string) => String(d[k] ?? "—");

const tien = (lay: (d: DongBaoCao) => number) => (d: DongBaoCao) => (
  <span className="tabular">{vnd(lay(d))}</span>
);
const dem = (lay: (d: DongBaoCao) => number) => (d: DongBaoCao) => (
  <span className="tabular">{lay(d)}</span>
);

/** Cột + thẻ KPI cho từng `kind` mà `GET /api/reports/{kind}` trả về. */
const CAC_BAO_CAO: Record<string, CauHinh> = {
  "doanh-thu": {
    ten: "Doanh thu",
    cot: [
      { tieuDe: "Tháng", hien: (d) => layChuoi(d, "thang") },
      { tieuDe: "Số hoá đơn", hien: dem((d) => laySo(d, "so_hoa_don")) },
      { tieuDe: "Tổng", hien: tien((d) => laySo(d, "tong")) },
      { tieuDe: "Đã thu", hien: tien((d) => laySo(d, "da_thu")) },
      { tieuDe: "Còn phải thu", hien: tien((d) => laySo(d, "tong") - laySo(d, "da_thu")) },
    ],
    kpi: (dong) => {
      const d = dong[0];
      if (!d) return [];
      const tong = laySo(d, "tong");
      const thu = laySo(d, "da_thu");
      const ky = layChuoi(d, "thang");
      return [
        { nhan: `Doanh thu ${ky}`, giaTri: vndShort(tong), phu: vnd(tong) },
        { nhan: `Đã thu ${ky}`, giaTri: vndShort(thu), phu: vnd(thu) },
        {
          nhan: `Còn phải thu ${ky}`,
          giaTri: vndShort(tong - thu),
          phu: vnd(tong - thu),
          canh: true,
        },
      ];
    },
  },
  "dich-vu": {
    ten: "Dịch vụ",
    cot: [
      { tieuDe: "Tên", hien: (d) => layChuoi(d, "ten") },
      { tieuDe: "Số lượng", hien: dem((d) => laySo(d, "so_luong")) },
      { tieuDe: "Doanh thu", hien: tien((d) => laySo(d, "doanh_thu")) },
    ],
  },
  "phu-tung": {
    ten: "Phụ tùng",
    cot: [
      { tieuDe: "Tên", hien: (d) => layChuoi(d, "ten") },
      { tieuDe: "Số lượng", hien: dem((d) => laySo(d, "so_luong")) },
      { tieuDe: "Doanh thu", hien: tien((d) => laySo(d, "doanh_thu")) },
      { tieuDe: "Tồn kho", hien: dem((d) => laySo(d, "ton_kho")) },
    ],
  },
  "khach-hang": {
    ten: "Khách hàng",
    cot: [
      { tieuDe: "Khách hàng", hien: (d) => layChuoi(d, "name") },
      { tieuDe: "Số xe", hien: dem((d) => laySo(d, "so_xe")) },
      { tieuDe: "Số lần sửa", hien: dem((d) => laySo(d, "so_lan_sua")) },
      { tieuDe: "Tổng đã thanh toán", hien: tien((d) => laySo(d, "tong_chi")) },
    ],
  },
  "trang-thai": {
    ten: "Trạng thái phiếu",
    kpi: (dong, N) =>
      dong.map((d) => ({ nhan: N.trangThai(layChuoi(d, "status")), giaTri: laySo(d, "so_luong") })),
  },
};

const LOAI_MAC_DINH = ["doanh-thu", "dich-vu", "phu-tung", "khach-hang", "trang-thai"];

function cotChot(dong: DongBaoCao[]): Cot[] {
  return Object.keys(dong[0] ?? {}).map((k) => ({
    tieuDe: k,
    hien: (d: DongBaoCao) => layChuoi(d, k),
  }));
}

function Reports() {
  const { area } = useRole();
  const [tab, setTab] = useState<"bao-cao" | "lich-su">("bao-cao");

  if (!area("reports")) return <NoAccess />;

  return (
    <>
      <PageHeader
        eyebrow="Quản trị"
        title="Báo cáo & Lịch sử"
        desc="Số liệu do backend tổng hợp từ cơ sở dữ liệu — chọn loại báo cáo hoặc tra cứu lịch sử hoạt động."
      />
      <div className="space-y-4 p-6 lg:p-8">
        <div className="flex w-fit gap-1 rounded-lg border bg-card p-1 shadow-card">
          {(
            [
              ["bao-cao", "Báo cáo"],
              ["lich-su", "Lịch sử"],
            ] as const
          ).map(([k, ten]) => (
            <button
              key={k}
              onClick={() => setTab(k)}
              className={cn(
                "rounded-md px-3 py-1.5 text-sm font-medium",
                tab === k
                  ? "bg-foreground text-background"
                  : "text-muted-foreground hover:bg-muted",
              )}
            >
              {ten}
            </button>
          ))}
        </div>

        {tab === "bao-cao" ? <TabBaoCao /> : <TabLichSu />}
      </div>
    </>
  );
}

function TabBaoCao() {
  const N = useNhan();
  const [kind, setKind] = useState("doanh-thu");
  const bc = useQuery(q.baoCao(kind));

  const loai = bc.data?.loai?.length ? bc.data.loai : LOAI_MAC_DINH;
  const cauHinh = CAC_BAO_CAO[kind];
  const dong = bc.data?.dong ?? [];
  const cot = !bc.data ? undefined : (cauHinh?.cot ?? cotChot(dong));
  const kpi = cauHinh?.kpi && dong.length ? cauHinh.kpi(dong, N) : [];

  return (
    <Panel
      title={cauHinh?.ten ?? kind}
      bodyClass="p-0"
      action={
        <span className="text-xs text-muted-foreground">
          Nguồn <code className="font-mono">{`GET /api/reports/${kind}`}</code>
        </span>
      }
    >
      <div className="flex flex-wrap gap-1 border-b p-3">
        {loai.map((k) => (
          <button
            key={k}
            onClick={() => setKind(k)}
            className={cn(
              "rounded-md px-2.5 py-1 text-xs font-medium",
              kind === k ? "bg-foreground text-background" : "text-muted-foreground hover:bg-muted",
            )}
          >
            {CAC_BAO_CAO[k]?.ten ?? k}
          </button>
        ))}
      </div>

      {bc.isPending && <DangTai mat="Đang tải báo cáo…" />}

      {bc.isError && (
        <div className="p-6 text-sm text-destructive">
          Không tải được báo cáo. {bc.error instanceof ApiError ? bc.error.message : "Lỗi kết nối."}
        </div>
      )}

      {bc.data &&
        (dong.length === 0 ? (
          <div className="p-4">
            <Empty title="Chưa có dữ liệu" desc="Báo cáo này chưa có dòng nào." />
          </div>
        ) : (
          <>
            {kpi.length > 0 && (
              <div className="grid gap-4 p-4 sm:grid-cols-2 xl:grid-cols-3">
                {kpi.map((t) => (
                  <Stat
                    key={t.nhan}
                    label={t.nhan}
                    value={t.canh ? <span className="text-destructive">{t.giaTri}</span> : t.giaTri}
                    sub={t.phu}
                  />
                ))}
              </div>
            )}
            {cot && cot.length > 0 && (
              <div className={cn("overflow-x-auto", kpi.length > 0 && "border-t")}>
                <table className="w-full text-sm">
                  <thead className="bg-muted/50 text-left text-[11px] uppercase tracking-wider text-muted-foreground">
                    <tr>
                      {cot.map((c) => (
                        <th key={c.tieuDe} className="px-4 py-2 font-medium">
                          {c.tieuDe}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y">
                    {dong.map((d, i) => (
                      <tr key={i} className="hover:bg-muted/40">
                        {cot.map((c) => (
                          <td key={c.tieuDe} className="px-4 py-2.5">
                            {c.hien(d)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </>
        ))}
    </Panel>
  );
}

function TabLichSu() {
  const [tim, setTim] = useState("");
  const [tuKhoa, setTuKhoa] = useState("");
  const [trang, setTrang] = useState(1);

  // Gõ xong 300ms mới gọi backend — tránh một request cho mỗi phím bấm.
  useEffect(() => {
    const h = setTimeout(() => {
      setTuKhoa(tim.trim());
      setTrang(1);
    }, 300);
    return () => clearTimeout(h);
  }, [tim]);

  const ds = useQuery(q.lichSu({ trang, moi_trang: 20, q: tuKhoa || undefined }));
  const duLieu = ds.data;

  return (
    <Panel
      title="Lịch sử hoạt động"
      bodyClass="p-0"
      action={
        <span className="text-xs text-muted-foreground">
          Nguồn <code className="font-mono">GET /api/history</code>
        </span>
      }
    >
      <div className="flex justify-end border-b p-3">
        <input
          value={tim}
          onChange={(e) => setTim(e.target.value)}
          placeholder="Lọc theo biển số, tên khách, số điện thoại…"
          className="h-8 rounded-md border bg-background px-2.5 text-sm md:w-72"
        />
      </div>

      {ds.isPending && <DangTai mat="Đang tải lịch sử…" />}

      {ds.isError && (
        <div className="p-6 text-sm text-destructive">
          Không tải được lịch sử. {ds.error instanceof ApiError ? ds.error.message : "Lỗi kết nối."}
        </div>
      )}

      {duLieu &&
        (duLieu.dong.length === 0 ? (
          <div className="p-4">
            <Empty title="Không có lịch sử phù hợp" desc="Thử đổi từ khoá tìm kiếm." />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-muted/50 text-left text-[11px] uppercase tracking-wider text-muted-foreground">
                <tr>
                  {["Thời gian", "Khách hàng", "Xe", "Trạng thái", "KTV", "Phiếu"].map((h) => (
                    <th key={h} className="px-4 py-2 font-medium">
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y">
                {duLieu.dong.map((o) => (
                  <tr key={o.id} className="hover:bg-muted/40">
                    <td className="tabular px-4 py-2.5 text-xs">{fmtTime(o.created_at)}</td>
                    <td className="px-4 py-2.5">
                      <div>{o.khach}</div>
                      <div className="text-xs text-muted-foreground">{o.phone ?? "—"}</div>
                    </td>
                    <td className="px-4 py-2.5">
                      <div className="flex items-center gap-2">
                        <Plate>{o.plate}</Plate>
                        <span className="text-xs text-muted-foreground">
                          {o.brand} {o.model}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-2.5">
                      <StatusPill s={o.status} />
                    </td>
                    <td className="px-4 py-2.5 text-muted-foreground">
                      {o.technician_id ? `KTV #${o.technician_id}` : "—"}
                    </td>
                    <td className="px-4 py-2.5">
                      <Link
                        to="/repair-orders/$id"
                        params={{ id: String(o.id) }}
                        className="font-mono text-xs font-medium text-primary"
                      >
                        #{o.id}
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ))}

      {duLieu && duLieu.dong.length > 0 && (
        <div className="flex items-center justify-between border-t px-4 py-3 text-xs text-muted-foreground">
          <span className="tabular">
            Trang {duLieu.trang}/{duLieu.tong_trang} · {duLieu.tong} bản ghi
          </span>
          <div className="flex gap-2">
            <Button
              size="sm"
              variant="outline"
              disabled={duLieu.trang <= 1}
              onClick={() => setTrang(duLieu.trang - 1)}
            >
              Trước
            </Button>
            <Button
              size="sm"
              variant="outline"
              disabled={duLieu.trang >= duLieu.tong_trang}
              onClick={() => setTrang(duLieu.trang + 1)}
            >
              Sau
            </Button>
          </div>
        </div>
      )}
    </Panel>
  );
}
