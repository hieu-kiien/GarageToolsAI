import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Sparkles, CheckCircle2, XCircle, Cpu, ListFilter } from "lucide-react";
import { api, q, ApiError } from "@/services/api";
import { useLookups } from "@/services/lookups";
import { useNhan, useRole, fmtTime } from "@/lib/rbac";
import {
  PageHeader,
  Panel,
  Plate,
  Pill,
  NoAccess,
  DangTai,
  Empty,
  StatusPill,
} from "@/components/app/ui-kit";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { cn } from "@/lib/utils";
import type { AiKind } from "@/types";

export const Route = createFileRoute("/ai-review")({
  head: () => ({
    meta: [
      { title: "Trợ lý AI — GarageTools AI" },
      {
        name: "description",
        content: "Chạy ba chức năng AI và duyệt kết quả trước khi đưa vào sử dụng.",
      },
      { property: "og:title", content: "Trợ lý AI — GarageTools AI" },
      { property: "og:description", content: "Human-in-the-loop cho kết quả AI." },
    ],
  }),
  component: Review,
});

const reviewTone = { PENDING: "warning", APPROVED: "success", REJECTED: "danger" } as const;

function Review() {
  const { area, can, meta } = useRole();
  const N = useNhan();
  const L = useLookups();
  const qc = useQueryClient();

  const coDuyet = can("ai.review");

  const kinhAi = meta?.kinh_ai ?? {
    history: "Tóm tắt lịch sử",
    explain: "Giải thích dịch vụ",
    quote: "Báo giá nháp",
  };
  const kinhDuocPhep = (Object.entries(kinhAi) as [AiKind, string][]).filter(([k]) =>
    can(`ai.${k}`),
  );

  // Chạy AI.
  const [kind, setKind] = useState<AiKind>(() => kinhDuocPhep[0]?.[0] ?? "history");
  const [vehicleId, setVehicleId] = useState("");
  const [serviceId, setServiceId] = useState("");
  const [phieuId, setPhieuId] = useState("");

  useEffect(() => {
    const dauTien = kinhDuocPhep[0]?.[0];
    if (dauTien && !kinhDuocPhep.some(([k]) => k === kind)) {
      setKind(dauTien);
    }
  }, [kinhDuocPhep, kind]);

  // Hàng chờ duyệt / danh sách kết quả.
  const [loc, setLoc] = useState<"" | "PENDING" | "APPROVED" | "REJECTED">("PENDING");
  const [dangChon, setDangChon] = useState<number | null>(null);

  // Luôn khai báo đủ hook — chỉ bật query theo quyền duyệt.
  const hangCho = useQuery({
    ...q.aiResults({ moi_trang: 20, trang_thai: loc || undefined }),
    enabled: coDuyet,
  });
  const ganNhat = useQuery({ ...q.aiRecent(), enabled: !coDuyet });
  const ketQua = coDuyet ? hangCho : ganNhat;

  const loi = (e: unknown) => toast.error(e instanceof ApiError ? e.message : "Thao tác thất bại.");

  const chay = useMutation({
    mutationFn: () =>
      api.aiRun({
        kind,
        ...(kind === "history" ? { vehicle_id: Number(vehicleId) } : {}),
        ...(kind === "explain" ? { service_id: Number(serviceId) } : {}),
        ...(kind === "quote" ? { repair_order_id: Number(phieuId) } : {}),
      }),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      await qc.invalidateQueries({ queryKey: ["ai-results"] });
      await qc.invalidateQueries({ queryKey: ["ai-recent"] });
      await qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: loi,
  });

  const duyet = useMutation({
    mutationFn: ({ id, quyet_dinh }: { id: number; quyet_dinh: "APPROVED" | "REJECTED" }) =>
      api.aiReview(id, quyet_dinh),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      setDangChon(null);
      await qc.invalidateQueries({ queryKey: ["ai-results"] });
      await qc.invalidateQueries({ queryKey: ["ai-recent"] });
      await qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: loi,
  });

  if (!area("ai")) return <NoAccess />;

  const dong = coDuyet ? (ketQua.data?.dong ?? []) : (ketQua.data?.dong ?? []);
  const chon = dong.find((d) => d.id === dangChon) ?? dong[0];
  const coTheChay =
    kinhDuocPhep.some(([k]) => k === kind) &&
    ((kind === "history" && !!vehicleId) ||
      (kind === "explain" && !!serviceId) ||
      (kind === "quote" && !!phieuId));

  return (
    <>
      <PageHeader
        eyebrow="Trợ lý"
        title="Trung tâm AI"
        desc="AI tạo bản nháp/kết quả ở trạng thái Chờ duyệt — phải được người có quyền `ai.review` duyệt thì mới dùng. AI không tính tổng tiền."
        actions={
          <Pill t="ai" dot>
            {meta?.ai_provider ?? "AI"}
          </Pill>
        }
      />

      <div className="grid gap-6 p-6 lg:p-8 xl:grid-cols-3">
        <Panel
          title={
            <span className="flex items-center gap-2">
              <Sparkles className="size-4 text-ai" />
              Chạy chức năng AI
            </span>
          }
        >
          <div className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">Chức năng</label>
              <Select value={kind} onValueChange={(v) => setKind(v as AiKind)}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {kinhDuocPhep.map(([k, v]) => (
                    <SelectItem key={k} value={k}>
                      {v}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {kind === "history" && (
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Xe</label>
                <Select value={vehicleId} onValueChange={setVehicleId}>
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
            )}
            {kind === "explain" && (
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Dịch vụ</label>
                <Select value={serviceId} onValueChange={setServiceId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Chọn dịch vụ…" />
                  </SelectTrigger>
                  <SelectContent>
                    {L.dich_vu.map((s) => (
                      <SelectItem key={s.id} value={String(s.id)}>
                        {s.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}
            {kind === "quote" && (
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Phiếu sửa chữa</label>
                <Select value={phieuId} onValueChange={setPhieuId}>
                  <SelectTrigger>
                    <SelectValue placeholder="Chọn phiếu…" />
                  </SelectTrigger>
                  <SelectContent>
                    {L.phieu.map((p) => (
                      <SelectItem key={p.id} value={String(p.id)}>
                        #{p.id} — {p.plate}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            <Button
              className="w-full"
              disabled={!coTheChay || chay.isPending}
              onClick={() => chay.mutate()}
            >
              Chạy AI
            </Button>
            <p className="text-[11px] text-muted-foreground">
              Kết quả lưu ở trạng thái <b>Chờ duyệt</b>. Quyền chạy từng chức năng do backend kiểm
              tra.
            </p>
          </div>
        </Panel>

        <Panel
          className="xl:col-span-2"
          title={
            <span className="flex items-center gap-2">
              <ListFilter className="size-4" />
              {coDuyet ? "Hàng chờ duyệt kết quả" : "Kết quả gần đây"}
            </span>
          }
          action={
            coDuyet ? (
              <div className="flex gap-1">
                {(["PENDING", "APPROVED", "REJECTED"] as const).map((k) => (
                  <button
                    key={k}
                    onClick={() => {
                      setLoc(k);
                      setDangChon(null);
                    }}
                    className={cn(
                      "rounded-md px-2 py-0.5 text-[11px] font-medium",
                      loc === k
                        ? "bg-foreground text-background"
                        : "text-muted-foreground hover:bg-muted",
                    )}
                  >
                    {N.trangThai(k)}
                  </button>
                ))}
              </div>
            ) : (
              <span className="text-[11px] text-muted-foreground">5 kết quả mới nhất</span>
            )
          }
          bodyClass="p-0"
        >
          {ketQua.isPending ? (
            <DangTai mat="Đang tải kết quả AI…" />
          ) : dong.length === 0 ? (
            <div className="p-4">
              <Empty title="Chưa có kết quả AI" desc="Chạy một chức năng ở cột bên trái." />
            </div>
          ) : (
            <div className="grid md:grid-cols-2">
              <ul className="divide-y border-r">
                {dong.map((d) => (
                  <li key={d.id}>
                    <button
                      onClick={() => setDangChon(d.id)}
                      className={cn(
                        "flex w-full items-start gap-2 px-4 py-3 text-left hover:bg-muted/60",
                        chon?.id === d.id && "bg-muted/80",
                      )}
                    >
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-medium">{kinhAi[d.kind] ?? d.kind}</span>
                          <Pill t={reviewTone[d.review_status] ?? "neutral"}>
                            {N.trangThai(d.review_status)}
                          </Pill>
                        </div>
                        <div className="mt-1 flex items-center gap-2 text-[11px] text-muted-foreground">
                          {d.plate && <Plate>{d.plate}</Plate>}
                          <span className="tabular">{fmtTime(d.created_at)}</span>
                        </div>
                      </div>
                    </button>
                  </li>
                ))}
              </ul>

              <div className="min-h-[280px] p-4">
                {chon && (
                  <>
                    <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                      <div className="flex items-center gap-2 text-sm font-semibold">
                        <Cpu className="size-4 text-ai" /> Kết quả #{chon.id}
                        <StatusPill s={chon.review_status} />
                      </div>
                      {"nguoi_duyet" in chon &&
                        (chon as { nguoi_duyet: string | null }).nguoi_duyet && (
                          <span className="text-[11px] text-muted-foreground">
                            Duyệt bởi {(chon as { nguoi_duyet: string | null }).nguoi_duyet}
                          </span>
                        )}
                    </div>
                    <div className="max-h-[320px] overflow-y-auto rounded-md border bg-muted/40 p-3">
                      <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">
                        {chon.output_text}
                      </pre>
                    </div>
                    <p className="mt-2 text-[11px] text-muted-foreground">
                      Đây là bản nháp do AI tạo — chưa có giá trị nghiệp vụ cho tới khi được duyệt.
                    </p>
                    {coDuyet && chon.review_status === "PENDING" && (
                      <div className="mt-3 flex gap-2">
                        <Button
                          className="flex-1"
                          size="sm"
                          disabled={duyet.isPending}
                          onClick={() => duyet.mutate({ id: chon.id, quyet_dinh: "APPROVED" })}
                        >
                          <CheckCircle2 className="size-4" />
                          Duyệt kết quả
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          disabled={duyet.isPending}
                          onClick={() => duyet.mutate({ id: chon.id, quyet_dinh: "REJECTED" })}
                        >
                          <XCircle className="size-4" />
                          Từ chối
                        </Button>
                      </div>
                    )}
                    {!coDuyet && (
                      <p className="mt-3 text-[11px] text-muted-foreground">
                        Chế độ chỉ xem — cần quyền duyệt kết quả AI.
                      </p>
                    )}
                  </>
                )}
              </div>
            </div>
          )}
        </Panel>
      </div>
    </>
  );
}
