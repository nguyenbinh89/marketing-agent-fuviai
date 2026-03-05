"use client";

import { useState } from "react";
import { Sparkles, ChevronRight, Loader2, CheckCircle } from "lucide-react";
import { api, streamCampaignPlan } from "@/lib/api";
import { cn } from "@/lib/utils";

const INDUSTRIES = [
  { value: "fmcg", label: "FMCG" },
  { value: "fb", label: "F&B" },
  { value: "realestate", label: "Bất động sản" },
  { value: "ecommerce", label: "Thương mại điện tử" },
  { value: "saas", label: "SaaS / Phần mềm" },
  { value: "fashion", label: "Thời trang" },
];

const GOALS = [
  "Tăng brand awareness",
  "Tăng doanh thu 30%",
  "Thu thập leads B2B",
  "Mở rộng thị trường mới",
  "Ra mắt sản phẩm mới",
];

const NODE_LABELS: Record<string, string> = {
  research: "Nghiên cứu thị trường",
  competitor: "Phân tích đối thủ",
  seo: "Từ khoá SEO",
  content: "Kế hoạch Content",
  budget: "Phân bổ Budget",
  compliance: "Kiểm tra Compliance",
  report: "Tạo báo cáo",
};

interface ProgressChunk {
  type: "progress" | "complete" | "error";
  node?: string;
  message?: string;
  plan?: string;
  error?: string;
}

export default function OrchestratePage() {
  const [product, setProduct] = useState("");
  const [industry, setIndustry] = useState("fmcg");
  const [budget, setBudget] = useState("50000000");
  const [goal, setGoal] = useState(GOALS[0]);
  const [season, setSeason] = useState("");

  const [running, setRunning] = useState(false);
  const [completedNodes, setCompletedNodes] = useState<string[]>([]);
  const [currentNode, setCurrentNode] = useState<string | null>(null);
  const [plan, setPlan] = useState("");
  const [error, setError] = useState("");

  const [useStream, setUseStream] = useState(true);

  const nodes = Object.keys(NODE_LABELS);

  const run = async () => {
    if (!product.trim()) return;
    setRunning(true);
    setCompletedNodes([]);
    setCurrentNode(null);
    setPlan("");
    setError("");

    const payload = {
      task: goal,
      product,
      industry,
      budget: parseFloat(budget) || 50_000_000,
      season: season || undefined,
    };

    if (useStream) {
      try {
        await streamCampaignPlan(payload, {
          onChunk: (chunk: ProgressChunk) => {
            if (chunk.type === "progress" && chunk.node) {
              setCurrentNode(chunk.node);
              setCompletedNodes((prev) =>
                prev.includes(chunk.node!) ? prev : [...prev, chunk.node!]
              );
            } else if (chunk.type === "complete" && chunk.plan) {
              setPlan(chunk.plan);
              setCurrentNode(null);
            } else if (chunk.type === "error") {
              setError(chunk.error || "Lỗi không xác định");
            }
          },
          onDone: () => setRunning(false),
        });
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Lỗi kết nối");
        setRunning(false);
      }
    } else {
      try {
        // Fake progress for non-stream mode
        for (const node of nodes) {
          setCurrentNode(node);
          await new Promise((r) => setTimeout(r, 400));
          setCompletedNodes((prev) => [...prev, node]);
        }
        const res = await api.campaignPlan(payload);
        setPlan(res.final_report || res.plan || JSON.stringify(res, null, 2));
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Lỗi");
      } finally {
        setRunning(false);
        setCurrentNode(null);
      }
    }
  };

  return (
    <div className="max-w-5xl space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-800 flex items-center gap-2">
          <Sparkles size={20} className="text-brand-500" />
          Campaign Plan AI
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          7 AI agents phối hợp — nghiên cứu · đối thủ · SEO · content · budget · compliance · báo cáo
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Form */}
        <div className="card p-5 space-y-4">
          <h3 className="font-semibold text-slate-800">Thông tin chiến dịch</h3>

          <div>
            <label className="text-sm font-medium text-slate-700 block mb-1.5">
              Sản phẩm / Dịch vụ <span className="text-red-500">*</span>
            </label>
            <input
              className="input"
              placeholder="VD: FuviAI Marketing Agent — phần mềm AI cho SME"
              value={product}
              onChange={(e) => setProduct(e.target.value)}
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1.5">Ngành</label>
              <select className="input" value={industry} onChange={(e) => setIndustry(e.target.value)}>
                {INDUSTRIES.map(({ value, label }) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1.5">Budget (đ)</label>
              <input
                type="number"
                className="input"
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
              />
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700 block mb-1.5">Mục tiêu</label>
            <select className="input" value={goal} onChange={(e) => setGoal(e.target.value)}>
              {GOALS.map((g) => <option key={g} value={g}>{g}</option>)}
            </select>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700 block mb-1.5">Mùa vụ (tuỳ chọn)</label>
            <select className="input" value={season} onChange={(e) => setSeason(e.target.value)}>
              <option value="">Không có</option>
              <option value="tet">Tết Nguyên Đán</option>
              <option value="11_11">11/11 Shopee</option>
              <option value="black_friday">Black Friday</option>
              <option value="8_3">8/3 Quốc tế Phụ nữ</option>
              <option value="20_10">20/10 Phụ nữ VN</option>
            </select>
          </div>

          <div className="flex items-center gap-2 text-sm text-slate-600">
            <input
              type="checkbox"
              id="stream"
              checked={useStream}
              onChange={(e) => setUseStream(e.target.checked)}
              className="rounded"
            />
            <label htmlFor="stream">Streaming (xem tiến độ realtime)</label>
          </div>

          <button
            onClick={run}
            disabled={!product.trim() || running}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {running ? (
              <><Loader2 size={15} className="spinner" /> Đang chạy {Object.keys(NODE_LABELS).length} agents...</>
            ) : (
              <><Sparkles size={15} /> Chạy Campaign Plan AI</>
            )}
          </button>
        </div>

        {/* Progress + Result */}
        <div className="space-y-4">
          {/* Node pipeline */}
          <div className="card p-5">
            <p className="text-sm font-semibold text-slate-800 mb-4">Tiến độ xử lý</p>
            <div className="space-y-2">
              {nodes.map((node, idx) => {
                const done = completedNodes.includes(node);
                const active = currentNode === node;
                return (
                  <div key={node} className="flex items-center gap-3">
                    <div
                      className={cn(
                        "w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 text-xs font-bold transition-all",
                        done ? "bg-green-500 text-white" :
                        active ? "bg-brand-500 text-white animate-pulse" :
                        "bg-slate-100 text-slate-400"
                      )}
                    >
                      {done ? <CheckCircle size={14} /> : idx + 1}
                    </div>
                    <span
                      className={cn(
                        "text-sm transition-colors",
                        done ? "text-green-700 font-medium" :
                        active ? "text-brand-600 font-semibold" :
                        "text-slate-400"
                      )}
                    >
                      {NODE_LABELS[node]}
                    </span>
                    {active && <Loader2 size={13} className="spinner text-brand-500 ml-auto" />}
                    {done && !active && idx < nodes.length - 1 && (
                      <ChevronRight size={13} className="text-green-400 ml-auto" />
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {error && (
            <div className="card p-4 bg-red-50 border-red-200 border text-sm text-red-700">
              ❌ {error}
            </div>
          )}
        </div>
      </div>

      {/* Plan output */}
      {plan && (
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <p className="font-semibold text-slate-800 flex items-center gap-2">
              <Sparkles size={16} className="text-brand-500" /> Kế hoạch Campaign hoàn chỉnh
            </p>
            <button
              onClick={() => navigator.clipboard.writeText(plan)}
              className="text-xs text-slate-500 hover:text-brand-600 transition-colors"
            >
              Copy
            </button>
          </div>
          <div className="bg-slate-50 rounded-lg p-4 max-h-[500px] overflow-y-auto scrollbar-thin">
            <div
              className="prose-ai text-sm"
              dangerouslySetInnerHTML={{
                __html: plan
                  .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                  .replace(/### (.*)/g, "<h3 class='text-slate-800 font-bold mt-4 mb-1'>$1</h3>")
                  .replace(/## (.*)/g, "<h2 class='text-slate-900 font-bold mt-5 mb-2 text-base'>$1</h2>")
                  .replace(/---/g, "<hr class='my-3'/>")
                  .replace(/\n/g, "<br/>"),
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
