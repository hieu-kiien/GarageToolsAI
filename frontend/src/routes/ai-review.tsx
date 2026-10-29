import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import {
  Sparkles,
  CheckCircle2,
  XCircle,
  Cpu,
  ListFilter,
  ExternalLink,
  FileText,
  MessageSquare,
  Send,
  RotateCcw,
  Bot,
  User,
} from "lucide-react";
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
import { Input } from "@/components/ui/input";
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
        content:
          "Trò chuyện trực tiếp với Trợ lý AI xưởng và chạy ba chức năng AI01, AI02, AI03 kèm duyệt kết quả.",
      },
      { property: "og:title", content: "Trợ lý AI — GarageTools AI" },
      {
        property: "og:description",
        content: "Human-in-the-loop & AI Chat cho xưởng dịch vụ ô tô.",
      },
    ],
  }),
  component: Review,
});

const reviewTone = { PENDING: "warning", APPROVED: "success", REJECTED: "danger" } as const;

type TinNhanChat = {
  id: string;
  role: "user" | "assistant";
  content: string;
  provider?: string;
  model?: string;
  fallback?: boolean;
};

const CAU_HOI_GOI_Y = [
  "Tóm tắt các phiếu sửa chữa đang mở tại xưởng và tổng tiền từng phiếu",
  "Phụ tùng nào trong kho đang hết hàng hoặc chạm mức cảnh báo?",
  "Xe 30A-1111 đã sửa những gì và còn bảo hành nào đang hiệu lực?",
  "Khách báo phanh kêu ken két và đèn pha tối thì nên tư vấn dịch vụ/phụ tùng nào trong danh mục?",
];

function Review() {
  const { area, can, meta } = useRole();
  const N = useNhan();
  const L = useLookups();
  const qc = useQueryClient();
  const nav = useNavigate();

  const coDuyet = can("ai.review");

  const kinhAi = meta?.kinh_ai ?? {
    history: "Tóm tắt lịch sử",
    explain: "Giải thích dịch vụ",
    quote: "Báo giá nháp",
  };
  const kinhDuocPhep = (Object.entries(kinhAi) as [AiKind, string][]).filter(([k]) =>
    can(`ai.${k}`),
  );

  // Chạy AI01 / AI02 / AI03 chuẩn hoá
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

  // Hàng chờ duyệt / danh sách kết quả
  const [loc, setLoc] = useState<"" | "PENDING" | "APPROVED" | "REJECTED">("PENDING");
  const [dangChon, setDangChon] = useState<number | null>(null);

  // Trạng thái hội thoại AI Chat trực tiếp
  const [tinNhan, setTinNhan] = useState<TinNhanChat[]>([
    {
      id: "welcome",
      role: "assistant",
      content:
        "Xin chào! Tôi là Trợ lý AI của xưởng dịch vụ GarageTools AI (kết nối trực tiếp với dữ liệu xe, phiếu sửa chữa, bảng giá dịch vụ, tồn kho phụ tùng và bảo hành). Bạn có thể hỏi bất kỳ thông tin nghiệp vụ nào hoặc bấm vào các câu hỏi gợi ý bên dưới.",
    },
  ]);
  const [cauHoi, setCauHoi] = useState("");
  const [chatXeId, setChatXeId] = useState<string>("all");
  const [chatPhieuId, setChatPhieuId] = useState<string>("all");
  const khungChatRef = useRef<HTMLDivElement | null>(null);

  // Luôn khai báo đủ hook — chỉ bật query theo quyền duyệt
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
      if (coDuyet) setLoc("PENDING");
      setDangChon(kq.id);
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

  const taoBgTuAi = useMutation({
    mutationFn: (id: number) => api.aiToQuotation(id),
    onSuccess: async (kq) => {
      toast.success(kq.thong_bao);
      await qc.invalidateQueries({ queryKey: ["quotations"] });
      await qc.invalidateQueries({ queryKey: ["ai-results"] });
      await qc.invalidateQueries({ queryKey: ["ai-recent"] });
      nav({ to: "/quotations/$id", params: { id: String(kq.quotation_id) } });
    },
    onError: loi,
  });

  const guiChat = useMutation({
    mutationFn: (dsTin: { role: "user" | "assistant"; content: string }[]) =>
      api.aiChat({
        messages: dsTin,
        vehicle_id: chatXeId !== "all" ? Number(chatXeId) : null,
        repair_order_id: chatPhieuId !== "all" ? Number(chatPhieuId) : null,
      }),
    onSuccess: (kq) => {
      setTinNhan((prev) => [
        ...prev,
        {
          id: `ai-${Date.now()}`,
          role: "assistant",
          content: kq.reply,
          provider: kq.provider_thuc_te,
          model: kq.model,
          fallback: kq.fallback_used,
        },
      ]);
      setTimeout(() => {
        if (khungChatRef.current) {
          khungChatRef.current.scrollTop = khungChatRef.current.scrollHeight;
        }
      }, 50);
    },
    onError: loi,
  });

  const thucHienGuiChat = (noiDung?: string) => {
    const text = (noiDung ?? cauHoi).trim();
    if (!text || guiChat.isPending) return;
    const tinMoi: TinNhanChat = {
      id: `u-${Date.now()}`,
      role: "user",
      content: text,
    };
    const capNhat = [...tinNhan, tinMoi];
    setTinNhan(capNhat);
    if (!noiDung) setCauHoi("");
    setTimeout(() => {
      if (khungChatRef.current) {
        khungChatRef.current.scrollTop = khungChatRef.current.scrollHeight;
      }
    }, 30);

    const payload = capNhat
      .filter((m) => m.id !== "welcome")
      .map((m) => ({ role: m.role, content: m.content }));
    guiChat.mutate(payload);
  };

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
        eyebrow="Trợ lý thông minh"
        title="Trung tâm AI & Trợ lý Hội thoại"
        desc="Trò chuyện trực tiếp với AI dựa trên dữ liệu thực của xưởng, hoặc sinh bản nháp chuẩn hoá (AI01 / AI02 / AI03) kèm cơ chế duyệt Human-in-the-loop."
        actions={
          <Pill t="ai" dot>
            {meta?.ai_provider ?? "AI"}
          </Pill>
        }
      />

      <div className="space-y-6 p-6 lg:p-8">
        {/* Khung Chat Trợ lý AI trực tiếp */}
        <Panel
          title={
            <span className="flex items-center gap-2">
              <MessageSquare className="size-4 text-ai" />
              Chat trực tiếp với Trợ lý AI Xưởng (Dữ liệu thời gian thực)
            </span>
          }
          action={
            <div className="flex flex-wrap items-center gap-2">
              <Select value={chatXeId} onValueChange={setChatXeId}>
                <SelectTrigger className="h-7 w-44 text-xs">
                  <SelectValue placeholder="Ngữ cảnh xe…" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tất cả xe trong xưởng</SelectItem>
                  {L.xe.map((x) => (
                    <SelectItem key={x.id} value={String(x.id)}>
                      Xe {x.plate} ({x.brand} {x.model})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={chatPhieuId} onValueChange={setChatPhieuId}>
                <SelectTrigger className="h-7 w-44 text-xs">
                  <SelectValue placeholder="Ngữ cảnh phiếu…" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Tất cả phiếu sửa chữa</SelectItem>
                  {L.phieu.map((p) => (
                    <SelectItem key={p.id} value={String(p.id)}>
                      Phiếu #{p.id} — {p.plate}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Button
                variant="ghost"
                size="sm"
                className="h-7 text-xs"
                onClick={() =>
                  setTinNhan([
                    {
                      id: "welcome",
                      role: "assistant",
                      content:
                        "Đã làm mới cuộc trò chuyện. Bạn cần tra cứu xe, phiếu sửa chữa, tồn kho phụ tùng hay tư vấn báo giá dịch vụ nào?",
                    },
                  ])
                }
              >
                <RotateCcw className="size-3" />
                Làm mới chat
              </Button>
            </div>
          }
        >
          <div className="space-y-3">
            <div className="flex flex-wrap gap-1.5">
              {CAU_HOI_GOI_Y.map((qText) => (
                <button
                  key={qText}
                  type="button"
                  disabled={guiChat.isPending}
                  onClick={() => thucHienGuiChat(qText)}
                  className="rounded-full border border-ai/30 bg-ai-soft/40 px-2.5 py-1 text-left text-[11px] font-medium text-foreground transition-colors hover:bg-ai-soft disabled:opacity-50"
                >
                  <Sparkles className="mr-1 inline size-3 text-ai" />
                  {qText}
                </button>
              ))}
            </div>

            <div
              ref={khungChatRef}
              className="max-h-[340px] min-h-[220px] space-y-3 overflow-y-auto rounded-md border bg-muted/30 p-3"
            >
              {tinNhan.map((m) => (
                <div
                  key={m.id}
                  className={cn(
                    "flex items-start gap-2.5",
                    m.role === "user" ? "justify-end" : "justify-start",
                  )}
                >
                  {m.role === "assistant" && (
                    <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-ai/15 text-ai">
                      <Bot className="size-4" />
                    </div>
                  )}
                  <div
                    className={cn(
                      "max-w-[85%] rounded-lg px-3.5 py-2.5 text-sm leading-relaxed",
                      m.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "border bg-background text-foreground shadow-xs",
                    )}
                  >
                    {m.role === "assistant" && m.provider && (
                      <div className="mb-1 flex items-center gap-1.5 text-[10px] text-muted-foreground">
                        <Pill t={m.fallback ? "warning" : "ai"}>
                          {m.provider}
                          {m.model ? ` · ${m.model}` : ""}
                        </Pill>
                      </div>
                    )}
                    <div className="whitespace-pre-wrap font-sans">{m.content}</div>
                  </div>
                  {m.role === "user" && (
                    <div className="flex size-7 shrink-0 items-center justify-center rounded-full bg-primary/15 text-primary">
                      <User className="size-4" />
                    </div>
                  )}
                </div>
              ))}
              {guiChat.isPending && (
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <div className="flex size-7 items-center justify-center rounded-full bg-ai/15 text-ai">
                    <Bot className="size-4 animate-pulse" />
                  </div>
                  <span>Trợ lý AI đang phân tích dữ liệu xưởng và phản hồi…</span>
                </div>
              )}
            </div>

            <form
              onSubmit={(e) => {
                e.preventDefault();
                thucHienGuiChat();
              }}
              className="flex gap-2"
            >
              <Input
                value={cauHoi}
                onChange={(e) => setCauHoi(e.target.value)}
                placeholder="Nhập câu hỏi cho Trợ lý AI (VD: Xe 30F-6666 đang làm gì? Báo giá thay má phanh và dầu máy bao nhiêu?)…"
                disabled={guiChat.isPending}
                className="flex-1"
              />
              <Button type="submit" disabled={!cauHoi.trim() || guiChat.isPending}>
                <Send className="size-4" />
                {guiChat.isPending ? "Đang gửi…" : "Gửi"}
              </Button>
            </form>
          </div>
        </Panel>

        {/* Ba chức năng AI chuẩn hoá & Hàng chờ duyệt */}
        <div className="grid gap-6 xl:grid-cols-3">
          <Panel
            title={
              <span className="flex items-center gap-2">
                <Sparkles className="size-4 text-ai" />
                Sinh bản nháp AI chuẩn hoá (AI01 / AI02 / AI03)
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
                  <label className="text-xs font-medium text-muted-foreground">
                    Phiếu sửa chữa
                  </label>
                  <Select value={phieuId} onValueChange={setPhieuId}>
                    <SelectTrigger>
                      <SelectValue placeholder="Chọn phiếu…" />
                    </SelectTrigger>
                    <SelectContent>
                      {L.phieu.map((p) => (
                        <SelectItem key={p.id} value={String(p.id)}>
                          #{p.id} — {p.plate}
                          {p.status ? ` (${N.trangThai(p.status)})` : ""}
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
                <Sparkles className="size-4" />
                {chay.isPending ? "Đang sinh bản nháp AI…" : "Chạy AI"}
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
                <span className="text-[11px] text-muted-foreground">25 kết quả mới nhất</span>
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
                <ul className="max-h-[420px] divide-y overflow-y-auto border-r">
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
                          <div className="mt-1 flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground">
                            {d.plate && <Plate>{d.plate}</Plate>}
                            {d.service_name && (
                              <span className="truncate font-medium text-foreground/80">
                                {d.service_name}
                              </span>
                            )}
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
                        <div className="flex flex-wrap items-center gap-2 text-sm font-semibold">
                          <Cpu className="size-4 text-ai" /> Kết quả #{chon.id}
                          <StatusPill s={chon.review_status} />
                          {chon.provider_thuc_te && (
                            <Pill t={chon.fallback_used ? "warning" : "ai"}>
                              {chon.provider_thuc_te}
                              {chon.model ? ` · ${chon.model}` : ""}
                            </Pill>
                          )}
                        </div>
                        <div className="flex flex-wrap items-center gap-2">
                          {chon.kind === "quote" &&
                            chon.repair_order_id &&
                            can("quote.manage") &&
                            chon.review_status !== "REJECTED" && (
                              <Button
                                variant="secondary"
                                size="sm"
                                className="h-7 text-xs"
                                disabled={taoBgTuAi.isPending}
                                onClick={() => taoBgTuAi.mutate(chon.id)}
                              >
                                <FileText className="size-3" />
                                Lập báo giá nháp từ AI03
                              </Button>
                            )}
                          {chon.repair_order_id && (
                            <Button variant="outline" size="sm" className="h-7 text-xs" asChild>
                              <Link
                                to="/repair-orders/$id"
                                params={{ id: String(chon.repair_order_id) }}
                              >
                                <ExternalLink className="size-3" />
                                Mở phiếu #{chon.repair_order_id}
                              </Link>
                            </Button>
                          )}
                          {"nguoi_duyet" in chon &&
                            (chon as { nguoi_duyet: string | null }).nguoi_duyet && (
                              <span className="text-[11px] text-muted-foreground">
                                Duyệt bởi {(chon as { nguoi_duyet: string | null }).nguoi_duyet}
                              </span>
                            )}
                        </div>
                      </div>
                      <div className="max-h-[320px] overflow-y-auto rounded-md border bg-muted/40 p-3">
                        <pre className="whitespace-pre-wrap font-sans text-sm leading-relaxed">
                          {chon.output_text}
                        </pre>
                      </div>
                      <p className="mt-2 text-[11px] text-muted-foreground">
                        Đây là bản nháp do AI tạo — chưa có giá trị nghiệp vụ cho tới khi được
                        duyệt.
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
      </div>
    </>
  );
}
