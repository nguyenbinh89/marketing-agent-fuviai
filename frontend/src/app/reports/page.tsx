"use client";

import { useState, useEffect, useCallback } from "react";
import {
  FileText, Zap, RefreshCw, Copy, Check,
  Calendar, BarChart2, TrendingUp, Layers,
} from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

// ─── Types ────────────────────────────────────────────────────────────────────

interface Template {
  type: string;
  label: string;
  description: string;
  recommended_days: number;
}

interface ReportResult {
  report_type: string;
  days: number;
  brand_name: string;
  generated_at: string;
  platforms_included: string[];
  report_markdown: string;
  word_count: number;
}

// ─── Constants ────────────────────────────────────────────────────────────────

const INDUSTRIES = [
  { value: "fmcg",       label: "FMCG" },
  { value: "fb",         label: "F&B" },
  { value: "realestate", label: "Bất động sản" },
  { value: "ecommerce",  label: "E-commerce" },
  { value: "saas",       label: "SaaS" },
  { value: "education",  label: "Giáo dục" },
  { value: "fashion",    label: "Thời trang" },
  { value: "health",     label: "Sức khoẻ & Làm đẹp" },
];

const TYPE_ICONS: Record<string, React.ElementType> = {
  weekly:              Calendar,
  monthly:             BarChart2,
  campaign_summary:    TrendingUp,
  platform_comparison: Layers,
};

const PLATFORM_COLORS: Record<string, string> = {
  "Google Ads":   "bg-blue-500",
  "Facebook Ads": "bg-indigo-500",
  "TikTok Ads":   "bg-slate-800",
};

// ─── Markdown renderer (lightweight — no external dep) ────────────────────────

function MarkdownView({ md }: { md: string }) {
  const html = md
    .replace(/^### (.+)$/gm, '<h3 class="text-base font-bold text-slate-800 mt-5 mb-2">$1</h3>')
    .replace(/^## (.+)$/gm,  '<h2 class="text-lg font-bold text-slate-800 mt-6 mb-2 border-b border-slate-200 pb-1">$2</h2>'.replace('$2', '$1'))
    .replace(/^# (.+)$/gm,   '<h1 class="text-xl font-bold text-slate-800 mt-4 mb-3">$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g,    '<em>$1</em>')
    .replace(/^- (.+)$/gm,   '<li class="ml-4 list-disc text-slate-700">$1</li>')
    .replace(/^(\d+)\. (.+)$/gm, '<li class="ml-4 list-decimal text-slate-700">$2</li>')
    .replace(/\n\n/g, '</p><p class="mt-3 text-slate-700">')
    .replace(/\n/g, '<br/>');

  return (
    <div
      className="prose prose-sm max-w-none text-sm leading-relaxed text-slate-700"
      dangerouslySetInnerHTML={{ __html: `<p class="text-slate-700">${html}</p>` }}
    />
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function ReportsPage() {
  const [templates, setTemplates] = useState<Template[]>([]);
  const [selectedType, setSelectedType] = useState("monthly");
  const [brandName, setBrandName]       = useState("");
  const [industry, setIndustry]         = useState("ecommerce");
  const [days, setDays]                 = useState(30);
  const [extraNotes, setExtraNotes]     = useState("");
  const [inclGoogle, setInclGoogle]     = useState(true);
  const [inclFacebook, setInclFacebook] = useState(true);
  const [inclTikTok, setInclTikTok]     = useState(true);

  const [loading, setLoading] = useState(false);
  const [result, setResult]   = useState<ReportResult | null>(null);
  const [error, setError]     = useState("");
  const [copied, setCopied]   = useState(false);

  const loadTemplates = useCallback(async () => {
    try {
      const res = await api.reportTemplates();
      setTemplates(res.templates);
    } catch {
      // backend offline — use fallback
    }
  }, []);

  useEffect(() => { loadTemplates(); }, [loadTemplates]);

  // Auto-fill days when template selected
  useEffect(() => {
    const tpl = templates.find((t) => t.type === selectedType);
    if (tpl) setDays(tpl.recommended_days);
  }, [selectedType, templates]);

  const generate = async () => {
    if (!brandName.trim()) { setError("Nhập tên thương hiệu."); return; }
    if (!inclGoogle && !inclFacebook && !inclTikTok) { setError("Chọn ít nhất 1 platform."); return; }

    setLoading(true);
    setError("");
    setResult(null);
    try {
      const res = await api.generateReport({
        report_type:      selectedType,
        days,
        brand_name:       brandName.trim(),
        industry,
        include_google:   inclGoogle,
        include_facebook: inclFacebook,
        include_tiktok:   inclTikTok,
        extra_notes:      extraNotes,
      });
      setResult(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Lỗi tạo báo cáo");
    } finally {
      setLoading(false);
    }
  };

  const copyReport = async () => {
    if (!result) return;
    await navigator.clipboard.writeText(result.report_markdown);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const downloadReport = () => {
    if (!result) return;
    const blob = new Blob([result.report_markdown], { type: "text/markdown;charset=utf-8" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = `report-${result.brand_name.replace(/\s+/g, "-")}-${result.days}d.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const activeTpl = templates.find((t) => t.type === selectedType);

  return (
    <div className="max-w-5xl space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-xl font-bold text-slate-800 flex items-center gap-2">
          <FileText size={20} className="text-brand-500" />
          AI Report Generator
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Tổng hợp dữ liệu thực từ tất cả platform → Claude AI viết báo cáo marketing tiếng Việt chuyên nghiệp
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* ─── Config panel ──────────────────────────────────────────────── */}
        <div className="lg:col-span-2 space-y-4">

          {/* Report type */}
          <div className="card p-4 space-y-3">
            <p className="text-sm font-semibold text-slate-700">Loại báo cáo</p>
            <div className="grid grid-cols-2 gap-2">
              {(templates.length ? templates : [
                { type: "weekly",              label: "Báo cáo Tuần",      description: "7 ngày",  recommended_days: 7 },
                { type: "monthly",             label: "Báo cáo Tháng",     description: "30 ngày", recommended_days: 30 },
                { type: "campaign_summary",    label: "Tóm tắt Campaign",  description: "14 ngày", recommended_days: 14 },
                { type: "platform_comparison", label: "So sánh Platform",  description: "30 ngày", recommended_days: 30 },
              ]).map((tpl) => {
                const Icon = TYPE_ICONS[tpl.type] || FileText;
                const active = selectedType === tpl.type;
                return (
                  <button key={tpl.type} onClick={() => setSelectedType(tpl.type)}
                    className={cn(
                      "flex flex-col items-start gap-1 p-3 rounded-xl border text-left transition-all",
                      active
                        ? "bg-brand-50 border-brand-300 text-brand-700"
                        : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
                    )}>
                    <Icon size={14} />
                    <span className="text-xs font-semibold leading-tight">{tpl.label}</span>
                  </button>
                );
              })}
            </div>
            {activeTpl && (
              <p className="text-xs text-slate-400 leading-relaxed">{activeTpl.description}</p>
            )}
          </div>

          {/* Brand & config */}
          <div className="card p-4 space-y-3">
            <p className="text-sm font-semibold text-slate-700">Thông tin thương hiệu</p>

            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Tên thương hiệu *</label>
              <input
                className="input"
                placeholder="VD: Highlands Coffee, Bitis, ..."
                value={brandName}
                onChange={(e) => setBrandName(e.target.value)}
              />
            </div>

            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Ngành</label>
              <select className="input" value={industry} onChange={(e) => setIndustry(e.target.value)}>
                {INDUSTRIES.map(({ value, label }) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Kỳ phân tích</label>
              <div className="flex gap-2 flex-wrap">
                {[7, 14, 30, 60, 90].map((d) => (
                  <button key={d} onClick={() => setDays(d)}
                    className={cn("px-3 py-1 rounded-lg border text-xs font-medium transition-colors",
                      days === d
                        ? "bg-brand-50 border-brand-300 text-brand-700"
                        : "bg-white border-slate-200 text-slate-500 hover:bg-slate-50"
                    )}>
                    {d} ngày
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Platform selection */}
          <div className="card p-4 space-y-3">
            <p className="text-sm font-semibold text-slate-700">Platforms đưa vào báo cáo</p>
            {[
              { label: "Google Ads",   value: inclGoogle,   set: setInclGoogle,   color: "bg-blue-500" },
              { label: "Facebook Ads", value: inclFacebook, set: setInclFacebook, color: "bg-indigo-500" },
              { label: "TikTok Ads",   value: inclTikTok,   set: setInclTikTok,   color: "bg-slate-800" },
            ].map(({ label, value, set, color }) => (
              <label key={label} className="flex items-center gap-3 cursor-pointer">
                <div className={cn("w-2 h-2 rounded-full", color)} />
                <span className="text-sm text-slate-700 flex-1">{label}</span>
                <div
                  onClick={() => set(!value)}
                  className={cn(
                    "w-9 h-5 rounded-full transition-colors cursor-pointer relative",
                    value ? "bg-brand-500" : "bg-slate-200"
                  )}
                >
                  <div className={cn(
                    "absolute top-0.5 w-4 h-4 bg-white rounded-full shadow transition-transform",
                    value ? "translate-x-4" : "translate-x-0.5"
                  )} />
                </div>
              </label>
            ))}
          </div>

          {/* Extra notes */}
          <div className="card p-4 space-y-2">
            <label className="text-xs font-medium text-slate-600 block">Ghi chú thêm (tuỳ chọn)</label>
            <textarea
              className="textarea h-20 text-xs"
              placeholder="VD: Tập trung vào campaign Tết Nguyên Đán, so sánh với Q4 2025..."
              value={extraNotes}
              onChange={(e) => setExtraNotes(e.target.value)}
            />
          </div>

          {/* Generate button */}
          {error && <p className="text-sm text-red-600 bg-red-50 p-3 rounded-lg">{error}</p>}
          <button
            onClick={generate}
            disabled={loading || !brandName.trim()}
            className="btn-primary w-full flex items-center justify-center gap-2 py-3"
          >
            {loading ? (
              <><RefreshCw size={15} className="spinner" /> Claude đang viết báo cáo...</>
            ) : (
              <><Zap size={15} /> Tạo báo cáo AI</>
            )}
          </button>
        </div>

        {/* ─── Report output ─────────────────────────────────────────────── */}
        <div className="lg:col-span-3">
          {loading ? (
            <div className="card p-10 flex flex-col items-center gap-4 text-center">
              <div className="w-12 h-12 border-4 border-brand-300 border-t-brand-600 rounded-full spinner" />
              <p className="font-semibold text-slate-700">Claude đang phân tích dữ liệu...</p>
              <p className="text-xs text-slate-400 leading-relaxed max-w-xs">
                Thu thập số liệu từ {[inclGoogle && "Google Ads", inclFacebook && "Facebook Ads", inclTikTok && "TikTok Ads"].filter(Boolean).join(", ")} và tổng hợp insights.
              </p>
            </div>
          ) : result ? (
            <div className="card p-5 space-y-4">
              {/* Report header */}
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-bold text-slate-800">{result.brand_name} — {result.days} ngày</p>
                  <div className="flex items-center gap-2 flex-wrap mt-1">
                    {result.platforms_included.map((p) => (
                      <span key={p} className="flex items-center gap-1 text-xs text-slate-500">
                        <div className={cn("w-1.5 h-1.5 rounded-full", PLATFORM_COLORS[p] || "bg-slate-400")} />
                        {p}
                      </span>
                    ))}
                    <span className="text-xs text-slate-400">· ~{result.word_count} từ</span>
                  </div>
                </div>
                <div className="flex gap-2 flex-shrink-0">
                  <button
                    onClick={copyReport}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors"
                  >
                    {copied ? <Check size={13} className="text-green-500" /> : <Copy size={13} />}
                    {copied ? "Đã copy" : "Copy"}
                  </button>
                  <button
                    onClick={downloadReport}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors"
                  >
                    <FileText size={13} />
                    .md
                  </button>
                  <button
                    onClick={generate}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-brand-200 bg-brand-50 text-xs font-medium text-brand-700 hover:bg-brand-100 transition-colors"
                  >
                    <RefreshCw size={13} />
                    Tạo lại
                  </button>
                </div>
              </div>

              <div className="border-t border-slate-100 pt-4 max-h-[70vh] overflow-y-auto scrollbar-thin pr-1">
                <MarkdownView md={result.report_markdown} />
              </div>
            </div>
          ) : (
            <div className="card p-10 flex flex-col items-center gap-4 text-center text-slate-400">
              <FileText size={40} className="text-slate-200" />
              <div>
                <p className="font-semibold text-slate-600">Báo cáo sẽ xuất hiện ở đây</p>
                <p className="text-xs mt-1 leading-relaxed max-w-xs">
                  Điền thông tin bên trái và nhấn{" "}
                  <span className="text-brand-600 font-medium">Tạo báo cáo AI</span> — Claude sẽ viết
                  báo cáo tiếng Việt chuyên nghiệp trong ~15 giây.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
