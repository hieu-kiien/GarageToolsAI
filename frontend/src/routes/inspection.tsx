import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { api, q, ApiError } from "@/services/api";
import { useLookups } from "@/services/lookups";
import { useNhan, useRole } from "@/lib/rbac";
import { PageHeader, Panel, NoAccess, DangTai, Empty, Pill } from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export const Route = createFileRoute("/inspection")({
  head: () => ({
    meta: [
      { title: "Tiếp nhận xe — GarageTools AI" },
      { name: "description", content: "Tạo phiếu sửa chữa và ghi biên bản tiếp nhận xe tại quầy." },
      { property: "og:title", content: "Tiếp nhận xe — GarageTools AI" },
      { property: "og:description", content: "Màn hình tiếp nhận xe của lễ tân." },
    ],
  }),
  component: Inspection,
});

function Inspection() {
  const { area, meta } = useRole();
  const N = useNhan();
  const L = useLookups();
  const qc = useQueryClient();

  // Bước 1 — tạo phiếu mới.
  const [xeId, setXeId] = useState("");
  const [ktvId, setKtvId] = useState("none");
  const [ghiChuPhieu, setGhiChuPhieu] = useState("");

  // Bước 2 — biên bản tiếp nhận cho một phiếu.
  const [phieuId, setPhieuId] = useState("");
  const [odo, setOdo] = useState("");
  const [nhienLieu, setNhienLieu] = useState("UNKNOWN");
  const [ngoaiThat, setNgoaiThat] = useState("");
  const [doDac, setDoDac] = useState("");
  const [ghiChu, setGhiChu] = useState("");

  const phieuMoi = useQuery(q.orders({ moi_trang: 10, trang_thai: "RECEIVED" }));
  const loi = (e: unknown) => toast.error(e instanceof ApiError ? e.message : "Thao tác thất bại.");

  const taoPhieu = useMutation({
    mutationFn: () =>
      api.taoPhieu({
        vehicle_id: Number(xeId),
        technician_id: ktvId === "none" ? null : Number(ktvId),
        technical_notes: ghiChuPhieu.trim() || undefined,
      }),
    onSuccess: async (kq) => {
      toast.success(`${kq.thong_bao} (mã #${kq.id})`);
      setPhieuId(String(kq.id));
      setGhiChuPhieu("");
      await qc.invalidateQueries({ queryKey: ["orders"] });
    },
    onError: loi,
  });

  const ghiBan = useMutation({
    mutationFn: () =>
      api.ghiTiepNhan(Number(phieuId), {
        odometer_at_intake: odo.trim() ? Number(odo) : null,
        fuel_level: nhienLieu,
        exterior_condition: ngoaiThat.trim() || undefined,
        accessories: doDac.trim() || undefined,
        notes: ghiChu.trim() || undefined,
      }),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      await qc.invalidateQueries({ queryKey: ["orders"] });
    },
    onError: loi,
  });

  if (!area("inspection")) return <NoAccess />;

  const danhSachPhieu = phieuMoi.data?.dong ?? [];

  return (
    <>
      <PageHeader
        eyebrow="Vận hành"
        title="Tiếp nhận xe"
        desc="Bước 1: tạo phiếu sửa chữa cho xe. Bước 2: ghi biên bản tiếp nhận (ODO, nhiên liệu, tình trạng, đồ đạc)."
        actions={
          phieuId && <Pill t="success">Phiếu #{phieuId} đã tạo — ghi biên bản ở bước 2</Pill>
        }
      />
      <div className="grid gap-6 p-6 lg:p-8 xl:grid-cols-2">
        <Panel title="Bước 1 · Tạo phiếu sửa chữa">
          <div className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Xe *</label>
              <Select value={xeId} onValueChange={setXeId}>
                <SelectTrigger>
                  <SelectValue placeholder="Chọn biển số…" />
                </SelectTrigger>
                <SelectContent>
                  {L.xe.map((x) => (
                    <SelectItem key={x.id} value={String(x.id)}>
                      {x.plate} — {x.brand} {x.model}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">
                Kỹ thuật viên (tuỳ chọn)
              </label>
              <Select value={ktvId} onValueChange={setKtvId}>
                <SelectTrigger>
                  <SelectValue placeholder="Chưa phân công" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Chưa phân công</SelectItem>
                  {L.ky_thuat_vien.map((t) => (
                    <SelectItem key={t.id} value={String(t.id)}>
                      {t.full_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Ghi chú tiếp nhận</label>
              <Textarea
                value={ghiChuPhieu}
                onChange={(e) => setGhiChuPhieu(e.target.value)}
                placeholder="Khách báo hư hỏng gì? Yêu cầu gì?"
                className="min-h-[70px]"
              />
            </div>
            <Button
              className="w-full"
              disabled={!xeId || taoPhieu.isPending}
              onClick={() => taoPhieu.mutate()}
            >
              Tạo phiếu sửa chữa
            </Button>
          </div>
        </Panel>

        <Panel title="Bước 2 · Biên bản tiếp nhận xe">
          {phieuMoi.isPending ? (
            <DangTai mat="Đang tải danh sách phiếu…" />
          ) : danhSachPhieu.length === 0 && !phieuId ? (
            <Empty title="Chưa có phiếu chờ tiếp nhận" desc="Hãy tạo phiếu ở bước 1." />
          ) : (
            <div className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">
                  Phiếu sửa chữa *
                </label>
                <Select value={phieuId} onValueChange={setPhieuId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Chọn phiếu…" />
                  </SelectTrigger>
                  <SelectContent>
                    {phieuId && !danhSachPhieu.some((p) => String(p.id) === phieuId) && (
                      <SelectItem value={phieuId}>Phiếu #{phieuId} (vừa tạo)</SelectItem>
                    )}
                    {danhSachPhieu.map((p) => (
                      <SelectItem key={p.id} value={String(p.id)}>
                        #{p.id} — {p.plate}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">ODO (km)</label>
                  <Input
                    type="number"
                    min={0}
                    max={2000000}
                    value={odo}
                    onChange={(e) => setOdo(e.target.value)}
                    placeholder="VD: 52300"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">
                    Mức nhiên liệu
                  </label>
                  <Select value={nhienLieu} onValueChange={setNhienLieu}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(meta?.muc_nhien_lieu ?? {}).map(([k, v]) => (
                        <SelectItem key={k} value={k}>
                          {v}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">
                  Tình trạng ngoại thất
                </label>
                <Textarea
                  value={ngoaiThat}
                  onChange={(e) => setNgoaiThat(e.target.value)}
                  placeholder="VD: trầy cản trước, móp gương phải…"
                  className="min-h-[60px]"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">
                  Đồ đạc khách để lại
                </label>
                <Input
                  value={doDac}
                  onChange={(e) => setDoDac(e.target.value)}
                  placeholder="VD: ô, giấy tờ xe, ghế trẻ em…"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Ghi chú khác</label>
                <Textarea
                  value={ghiChu}
                  onChange={(e) => setGhiChu(e.target.value)}
                  className="min-h-[50px]"
                />
              </div>
              <div className="flex items-center gap-2">
                <Button
                  className="flex-1"
                  disabled={!phieuId || ghiBan.isPending}
                  onClick={() => ghiBan.mutate()}
                >
                  Ghi biên bản tiếp nhận
                </Button>
                {phieuId && (
                  <Button variant="outline" asChild>
                    <Link to="/repair-orders/$id" params={{ id: String(phieuId) }}>
                      Xem phiếu
                    </Link>
                  </Button>
                )}
              </div>
              <p className="text-[11px] text-muted-foreground">
                Biến bản ghi một lần cho mỗi phiếu — backend chặn ghi trùng.
              </p>
            </div>
          )}
        </Panel>
      </div>
      <div className="px-6 pb-2 text-[11px] text-muted-foreground lg:px-8">
        Nhãn mức nhiên liệu lấy từ <code className="font-mono">GET /api/meta</code> — cùng nguồn với
        mọi màn hình.
      </div>
    </>
  );
}
