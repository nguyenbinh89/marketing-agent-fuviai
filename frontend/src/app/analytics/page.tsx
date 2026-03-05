"use client";

import { useState } from "react";
import { Search, TrendingUp, AlertTriangle, Plus, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

// ─── Sentiment Panel ──────────────────────────────────────────────────────────

function SentimentPanel() {
  const [input, setInput] = useState("");
  const [result, setResult] = useState<{
    summary: Record<string, number>;
    top_positive: string[];
    top_negative: string[];
    ai_insight: string;
  } | null>(null);
  const [loading, setLoading] = useState(false);

  const analyze = async () => {
    const texts = input.split("\n").map((t) => t.trim()).filter(Boolean);
    if (!texts.length) return;
    setLoading(true);
    try {
      const res = await api.analyzeSentiment(texts);
      setResult(res);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Lỗi");
    } finally {
      setLoading(false);
    }
  };

  const total = result?.summary.total || 1;
  const pct = (n: number) => Math.round((n / total) * 100);

  return (
    <div className="card p-5 space-y-4">
      <h3 className="font-semibold text-slate-800 flex items-center gap-2">
        <TrendingUp size={16} className="text-brand-500" /> Phân tích Sentiment
      </h3>
      <textarea
        className="textarea h-28"
        placeholder={"Nhập mỗi comment/review 1 dòng:\nSản phẩm quá đỉnh!\nGiao hàng chậm quá\nỔn thôi"}
        value={input}
        onChange={(e) => setInput(e.target.value)}
      />
      <button onClick={analyze} disabled={loading || !input.trim()} className="btn-primary w-full">
        {loading ? "Đang phân tích..." : "Phân tích Sentiment"}
      </button>

      {result && (
        <div className="space-y-3">
          {/* Bar */}
          <div className="flex rounded-full overflow-hidden h-5 text-xs font-medium">
            {result.summary.positive > 0 && (
              <div className="bg-green-500 flex items-center justify-center text-white" style={{ width: `${pct(result.summary.positive)}%` }}>
                {pct(result.summary.positive)}%
              </div>
            )}
            {result.summary.neutral > 0 && (
              <div className="bg-slate-300 flex items-center justify-center text-white" style={{ width: `${pct(result.summary.neutral)}%` }}>
                {pct(result.summary.neutral)}%
              </div>
            )}
            {result.summary.negative > 0 && (
              <div className="bg-red-500 flex items-center justify-center text-white" style={{ width: `${pct(result.summary.negative)}%` }}>
                {pct(result.summary.negative)}%
              </div>
            )}
          </div>
          <div className="flex gap-4 text-xs text-slate-600">
            <span className="text-green-600 font-medium">✅ Tích cực: {result.summary.positive}</span>
            <span className="text-slate-500">⬜ Trung tính: {result.summary.neutral}</span>
            <span className="text-red-500 font-medium">❌ Tiêu cực: {result.summary.negative}</span>
          </div>

          {result.top_negative.length > 0 && (
            <div className="bg-red-50 rounded-lg p-3">
              <p className="text-xs font-semibold text-red-700 mb-1">Top tiêu cực:</p>
              {result.top_negative.map((t, i) => <p key={i} className="text-xs text-red-600">• {t}</p>)}
            </div>
          )}

          {result.ai_insight && (
            <div className="bg-brand-50 rounded-lg p-3">
              <p className="text-xs font-semibold text-brand-700 mb-1">AI Insight:</p>
              <p className="text-xs text-brand-800 leading-relaxed">{result.ai_insight.slice(0, 300)}...</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Trend Scanner ────────────────────────────────────────────────────────────

function TrendScanner() {
  const [industry, setIndustry] = useState("marketing");
  const [result, setResult] = useState<{
    articles_found: number;
    trend_analysis: string;
    crisis_risk: { is_crisis: boolean; severity: string };
    scan_time: string;
  } | null>(null);
  const [loading, setLoading] = useState(false);

  const scan = async () => {
    setLoading(true);
    try {
      const res = await api.scanTrends(industry);
      setResult(res as typeof result);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Lỗi");
    } finally {
      setLoading(false);
    }
  };

  const INDUSTRIES = ["marketing", "fmcg", "fb", "realestate", "ecommerce"];

  return (
    <div className="card p-5 space-y-4">
      <h3 className="font-semibold text-slate-800 flex items-center gap-2">
        <Search size={16} className="text-purple-500" /> Social Listening & Trend
      </h3>

      <div className="flex gap-2">
        <select className="input flex-1" value={industry} onChange={(e) => setIndustry(e.target.value)}>
          {INDUSTRIES.map((i) => <option key={i} value={i}>{i}</option>)}
        </select>
        <button onClick={scan} disabled={loading} className="btn-primary flex items-center gap-2">
          <RefreshCw size={14} className={cn(loading && "spinner")} /> Scan
        </button>
      </div>

      {result && (
        <div className="space-y-3">
          <div className="flex items-center gap-3 text-sm">
            <span className="badge-blue">{result.articles_found} bài viết</span>
            {result.crisis_risk?.is_crisis ? (
              <span className="badge-red flex items-center gap-1">
                <AlertTriangle size={11} /> Crisis: {result.crisis_risk.severity}
              </span>
            ) : (
              <span className="badge-green">✅ Không có khủng hoảng</span>
            )}
          </div>

          {result.trend_analysis && (
            <div className="bg-purple-50 rounded-lg p-3">
              <p className="text-xs font-semibold text-purple-700 mb-2">Phân tích xu hướng:</p>
              <div
                className="prose-ai text-xs"
                dangerouslySetInnerHTML={{
                  __html: result.trend_analysis
                    .slice(0, 600)
                    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                    .replace(/\n/g, "<br/>"),
                }}
              />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Competitor Panel ─────────────────────────────────────────────────────────

function CompetitorPanel() {
  const [name, setName] = useState("");
  const [website, setWebsite] = useState("");
  const [trigger, setTrigger] = useState("");
  const [strategy, setStrategy] = useState("");
  const [loading, setLoading] = useState(false);

  const getStrategy = async () => {
    if (!name.trim() || !trigger.trim()) return;
    setLoading(true);
    try {
      const res = await api.counterStrategy({ competitor_name: name, trigger_event: trigger });
      setStrategy(res.strategy);
    } catch (err: unknown) {
      setStrategy(`❌ ${err instanceof Error ? err.message : "Lỗi"}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card p-5 space-y-4">
      <h3 className="font-semibold text-slate-800 flex items-center gap-2">
        <Plus size={16} className="text-rose-500" /> Counter-Strategy (< 30 giây)
      </h3>

      <input className="input" placeholder="Tên đối thủ (VD: Haravan)" value={name} onChange={(e) => setName(e.target.value)} />
      <input className="input" placeholder="Sự kiện (VD: Vừa giảm giá 30%, chạy TVC trên VTV)" value={trigger} onChange={(e) => setTrigger(e.target.value)} />

      <button onClick={getStrategy} disabled={loading || !name.trim() || !trigger.trim()} className="btn-primary w-full">
        {loading ? "Đang tạo counter-strategy..." : "Tạo Counter-Strategy"}
      </button>

      {strategy && (
        <div className="bg-rose-50 rounded-lg p-3 max-h-60 overflow-y-auto scrollbar-thin">
          <div
            className="prose-ai text-xs"
            dangerouslySetInnerHTML={{
              __html: strategy
                .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                .replace(/\n/g, "<br/>"),
            }}
          />
        </div>
      )}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function AnalyticsPage() {
  return (
    <div className="max-w-5xl space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-800">Analytics</h1>
        <p className="text-sm text-slate-500 mt-1">Social Listening, Sentiment Analysis, Competitor Intelligence</p>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SentimentPanel />
        <TrendScanner />
        <CompetitorPanel />
      </div>
    </div>
  );
}
