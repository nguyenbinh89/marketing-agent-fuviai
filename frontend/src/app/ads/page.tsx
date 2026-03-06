"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Layers, TrendingUp, BarChart2, BookOpen, Zap,
  RefreshCw, AlertTriangle, CheckCircle, ExternalLink,
} from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import { cn, formatVND } from "@/lib/utils";
import { SpendPieChart, PlatformBarChart } from "@/components/Charts";

type Tab = "overview" | "compare" | "benchmark" | "ai-allocate";

const TABS: { value: Tab; label: string; icon: React.ElementType }[] = [
  { value: "overview",    label: "Tổng quan",       icon: TrendingUp },
  { value: "compare",     label: "So sánh Platform", icon: BarChart2 },
  { value: "benchmark",   label: "Benchmark",        icon: BookOpen },
  { value: "ai-allocate", label: "AI Phân bổ Budget", icon: Zap },
];

const INDUSTRIES = [
  { value: "fmcg",       label: "FMCG" },
  { value: "fb",         label: "F&B" },
  { value: "realestate", label: "Bất động sản" },
  { value: "ecommerce",  label: "E-commerce" },
  { value: "saas",       label: "SaaS" },
  { value: "education",  label: "Giáo dục" },
];

const PLATFORM_LINKS: Record<string, string> = {
  google:   "/google-ads",
  facebook: "/facebook-ads",
  tiktok:   "/tiktok-ads",
};

const PLATFORM_COLORS: Record<string, string> = {
  google:   "bg-blue-500",
  facebook: "bg-indigo-500",
  tiktok:   "bg-slate-800",
};

// ─── Overview Tab ─────────────────────────────────────────────────────────────

function OverviewTab() {
  type Summary = {
    days: number;
    platforms: Array<Record<string, unknown>>;
    totals: Record<string, unknown>;
    configured_count: number;
  };

  const [data, setData]       = useState<Summary | null>(null);
  const [loading, setLoading] = useState(false);
  const [days, setDays]       = useState(30);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setData(await api.unifiedAdsSummary(days));
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => { load(); }, [load]);

  const totals = data?.totals;
  const platforms = data?.platforms || [];
  const configured = platforms.filter((p) => p.configured);

  return (
    <div className="space-y-6">
      {/* Day selector */}
      <div className="flex items-center gap-3 flex-wrap">
        <label className="text-sm text-slate-600">Khoảng thời gian:</label>
        {[7, 14, 30, 90].map((d) => (
          <button key={d} onClick={() => setDays(d)}
            className={cn("px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors",
              days === d ? "bg-brand-50 border-brand-300 text-brand-700" : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
            )}>
            {d} ngày
          </button>
        ))}
        <button onClick={load} className="ml-auto text-slate-400 hover:text-brand-500">
          <RefreshCw size={15} className={loading ? "spinner" : ""} />
        </button>
      </div>

      {/* Total KPIs */}
      {loading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 7 }).map((_, i) => (
            <div key={i} className="card p-5 animate-pulse">
              <div className="h-3 bg-slate-200 rounded w-20 mb-3" />
              <div className="h-6 bg-slate-200 rounded w-16" />
            </div>
          ))}
        </div>
      ) : totals ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: "Tổng chi tiêu",  value: formatVND(Number(totals.spend_vnd || 0)),          color: "text-red-500" },
            { label: "Tổng Clicks",    value: Number(totals.clicks || 0).toLocaleString(),        color: "text-blue-600" },
            { label: "Impressions",    value: Number(totals.impressions || 0).toLocaleString(),    color: "text-slate-700" },
            { label: "Conversions",    value: String(totals.conversions || 0),                    color: "text-green-600" },
            { label: "Blended ROAS",   value: `${totals.blended_roas || 0}x`,                    color: "text-purple-600" },
            { label: "CTR Blended",    value: `${totals.avg_ctr || 0}%`,                         color: "text-brand-600" },
            { label: "CPC Blended",    value: formatVND(Number(totals.avg_cpc_vnd || 0)),         color: "text-orange-500" },
            { label: "Platforms kết nối", value: String(data?.configured_count || 0) + "/3",     color: "text-slate-600" },
          ].map(({ label, value, color }) => (
            <div key={label} className="card p-5">
              <p className="text-xs text-slate-500 mb-1">{label}</p>
              <p className={cn("text-2xl font-bold", color)}>{value}</p>
            </div>
          ))}
        </div>
      ) : (
        <div className="card p-8 text-center text-slate-400 text-sm">
          Không thể tải dữ liệu. Kiểm tra kết nối backend.
        </div>
      )}

      {/* Platform cards */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {(loading ? [
          { key: "google", platform: "Google Ads" },
          { key: "facebook", platform: "Facebook Ads" },
          { key: "tiktok", platform: "TikTok Ads" },
        ] : platforms).map((p) => {
          const key = String(p.key || "");
          const isConfigured = Boolean(p.configured);
          const spend = Number(p.spend_vnd || 0);
          const pct = Number(p.spend_pct || 0);

          return (
            <div key={key} className={cn("card p-5 space-y-4", !isConfigured && "opacity-60")}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className={cn("w-2.5 h-2.5 rounded-full", PLATFORM_COLORS[key] || "bg-slate-400")} />
                  <p className="font-semibold text-slate-800 text-sm">{String(p.platform || "")}</p>
                </div>
                {isConfigured ? (
                  <CheckCircle size={14} className="text-green-500" />
                ) : (
                  <AlertTriangle size={14} className="text-amber-400" />
                )}
              </div>

              {loading ? (
                <div className="space-y-2 animate-pulse">
                  <div className="h-4 bg-slate-200 rounded w-20" />
                  <div className="h-3 bg-slate-200 rounded w-16" />
                </div>
              ) : isConfigured ? (
                <>
                  <div>
                    <p className="text-2xl font-bold text-slate-800">{formatVND(spend)}</p>
                    <p className="text-xs text-slate-500 mt-0.5">Chi tiêu {days} ngày</p>
                  </div>

                  {/* Spend bar */}
                  <div>
                    <div className="flex justify-between text-xs text-slate-500 mb-1">
                      <span>Tỷ trọng ngân sách</span>
                      <span className="font-medium text-slate-700">{pct}%</span>
                    </div>
                    <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                      <div
                        className={cn("h-full rounded-full transition-all", PLATFORM_COLORS[key] || "bg-slate-400")}
                        style={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-3 gap-2 pt-1">
                    {[
                      { label: "CTR",  value: `${p.ctr || 0}%` },
                      { label: "CPC",  value: spend > 0 ? formatVND(Number(p.cpc_vnd || 0)) : "—" },
                      { label: "ROAS", value: Number(p.roas) > 0 ? `${p.roas}x` : "—" },
                    ].map(({ label, value }) => (
                      <div key={label} className="text-center">
                        <p className="text-xs text-slate-400">{label}</p>
                        <p className="text-sm font-semibold text-slate-700">{value}</p>
                      </div>
                    ))}
                  </div>

                  <Link
                    href={PLATFORM_LINKS[key] || "/"}
                    className="flex items-center gap-1 text-xs text-brand-500 hover:text-brand-700 font-medium transition-colors"
                  >
                    Chi tiết <ExternalLink size={11} />
                  </Link>
                </>
              ) : (
                <div className="space-y-2">
                  <p className="text-xs text-slate-400">Chưa cấu hình</p>
                  <p className="text-xs text-slate-400 leading-relaxed">{String(p.error || "")}</p>
                  <Link
                    href={PLATFORM_LINKS[key] || "/"}
                    className="text-xs text-brand-500 hover:text-brand-700 font-medium"
                  >
                    Cấu hình ngay →
                  </Link>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Spend breakdown chart */}
      {configured.length > 1 && (
        <SpendPieChart
          data={configured.map((p) => ({
            name: String(p.platform || ""),
            value: Number(p.spend_vnd || 0),
            pct: Number(p.spend_pct || 0),
          }))}
          title="Phân bổ ngân sách theo platform"
          height={260}
        />
      )}
    </div>
  );
}

// ─── Compare Tab ──────────────────────────────────────────────────────────────

function CompareTab() {
  type Summary = {
    days: number;
    platforms: Array<Record<string, unknown>>;
    totals: Record<string, unknown>;
    configured_count: number;
  };

  const [data, setData]       = useState<Summary | null>(null);
  const [loading, setLoading] = useState(false);
  const [days, setDays]       = useState(30);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setData(await api.unifiedAdsSummary(days));
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => { load(); }, [load]);

  const platforms = (data?.platforms || []).filter((p) => p.configured);

  const metrics: Array<{ key: string; label: string; fmt: (v: unknown) => string; best: "max" | "min" }> = [
    { key: "spend_vnd",    label: "Chi tiêu",    fmt: (v) => formatVND(Number(v)),        best: "min" },
    { key: "impressions",  label: "Impressions", fmt: (v) => Number(v).toLocaleString(),  best: "max" },
    { key: "clicks",       label: "Clicks",      fmt: (v) => Number(v).toLocaleString(),  best: "max" },
    { key: "conversions",  label: "Conversions", fmt: (v) => String(v),                   best: "max" },
    { key: "ctr",          label: "CTR",         fmt: (v) => `${v}%`,                     best: "max" },
    { key: "cpc_vnd",      label: "CPC",         fmt: (v) => formatVND(Number(v)),        best: "min" },
    { key: "roas",         label: "ROAS",        fmt: (v) => Number(v) > 0 ? `${v}x` : "—", best: "max" },
    { key: "spend_pct",    label: "% Budget",    fmt: (v) => `${v}%`,                     best: "max" },
  ];

  if (loading) return (
    <div className="card p-12 text-center text-slate-400 text-sm animate-pulse">Đang tải dữ liệu so sánh...</div>
  );

  if (platforms.length === 0) return (
    <div className="card p-8 text-center text-slate-400 text-sm">
      Chưa có platform nào được cấu hình. Cấu hình ít nhất 2 platform để so sánh.
    </div>
  );

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        {[7, 14, 30, 90].map((d) => (
          <button key={d} onClick={() => setDays(d)}
            className={cn("px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors",
              days === d ? "bg-brand-50 border-brand-300 text-brand-700" : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
            )}>
            {d} ngày
          </button>
        ))}
        <button onClick={load} className="ml-auto text-slate-400 hover:text-brand-500">
          <RefreshCw size={15} className={loading ? "spinner" : ""} />
        </button>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-100 bg-slate-50">
              <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">Metric</th>
              {platforms.map((p) => (
                <th key={String(p.key)} className="px-4 py-3 text-right text-xs font-semibold text-slate-500">
                  <div className="flex items-center justify-end gap-1.5">
                    <div className={cn("w-2 h-2 rounded-full", PLATFORM_COLORS[String(p.key)] || "bg-slate-400")} />
                    {String(p.platform)}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {metrics.map(({ key, label, fmt, best }) => {
              // Find best value
              const vals = platforms.map((p) => Number(p[key] || 0));
              const bestVal = best === "max" ? Math.max(...vals) : Math.min(...vals.filter((v) => v > 0));

              return (
                <tr key={key} className="border-b border-slate-50 hover:bg-slate-50/50">
                  <td className="px-4 py-3 text-xs font-medium text-slate-600">{label}</td>
                  {platforms.map((p) => {
                    const raw = Number(p[key] || 0);
                    const isBest = raw === bestVal && raw > 0;
                    return (
                      <td key={String(p.key)} className="px-4 py-3 text-right">
                        <span className={cn(
                          "text-sm font-medium",
                          isBest ? "text-green-600" : "text-slate-700"
                        )}>
                          {fmt(p[key])}
                          {isBest && platforms.length > 1 && (
                            <span className="ml-1 text-xs bg-green-50 text-green-600 px-1 rounded">best</span>
                          )}
                        </span>
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <p className="text-xs text-slate-400 text-center">
        <span className="text-green-600 font-medium">best</span> = giá trị tốt nhất trong khoảng thời gian đã chọn
      </p>

      {/* Bar chart comparison */}
      {platforms.length > 1 && (
        <PlatformBarChart
          data={[
            { metric: "CTR (%)",     ...Object.fromEntries(platforms.map((p) => [String(p.platform), Number(p.ctr || 0)])) },
            { metric: "ROAS",        ...Object.fromEntries(platforms.map((p) => [String(p.platform), Number(p.roas || 0)])) },
            { metric: "CPC (×1000)", ...Object.fromEntries(platforms.map((p) => [String(p.platform), Math.round(Number(p.cpc_vnd || 0) / 1000)])) },
          ]}
          platforms={platforms.map((p) => String(p.platform))}
          title="So sánh CTR / ROAS / CPC theo platform"
          height={240}
        />
      )}
    </div>
  );
}

// ─── Benchmark Tab ────────────────────────────────────────────────────────────

function BenchmarkTab() {
  const [industry, setIndustry] = useState("saas");
  const [data, setData]         = useState<{ google: Record<string, unknown>; facebook: Record<string, unknown>; tiktok: Record<string, unknown> } | null>(null);
  const [loading, setLoading]   = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.unifiedAdsBenchmarks(industry);
      setData({ google: res.google, facebook: res.facebook, tiktok: res.tiktok });
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [industry]);

  useEffect(() => { load(); }, [load]);

  const platforms = data ? [
    { key: "google",   label: "Google Ads",   color: PLATFORM_COLORS.google,   d: data.google },
    { key: "facebook", label: "Facebook Ads", color: PLATFORM_COLORS.facebook, d: data.facebook },
    { key: "tiktok",   label: "TikTok Ads",   color: PLATFORM_COLORS.tiktok,   d: data.tiktok },
  ] : [];

  const rows = [
    { key: "cpc",  label: "CPC",  fmt: (v: unknown) => formatVND(Number(v)) },
    { key: "cpm",  label: "CPM",  fmt: (v: unknown) => formatVND(Number(v)) },
    { key: "ctr",  label: "CTR",  fmt: (v: unknown) => `${v}%` },
    { key: "roas", label: "ROAS", fmt: (v: unknown) => `${v}x` },
  ];

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2 flex-wrap">
        {INDUSTRIES.map(({ value, label }) => (
          <button key={value} onClick={() => setIndustry(value)}
            className={cn("px-4 py-2 rounded-lg border text-xs font-medium transition-colors",
              industry === value ? "bg-brand-50 border-brand-300 text-brand-700" : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
            )}>
            {label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="card p-12 text-center text-slate-400 text-sm animate-pulse">Đang tải benchmarks...</div>
      ) : data ? (
        <>
          <div className="card overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">Metric</th>
                  {platforms.map(({ key, label, color }) => (
                    <th key={key} className="px-4 py-3 text-right text-xs font-semibold text-slate-500">
                      <div className="flex items-center justify-end gap-1.5">
                        <div className={cn("w-2 h-2 rounded-full", color)} />
                        {label}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map(({ key, label, fmt }) => (
                  <tr key={key} className="border-b border-slate-50 hover:bg-slate-50/50">
                    <td className="px-4 py-3 text-xs font-medium text-slate-600">{label}</td>
                    {platforms.map(({ key: pk, d }) => (
                      <td key={pk} className="px-4 py-3 text-right font-semibold text-brand-600">
                        {fmt(d[key])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Platform-specific extra metrics */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {platforms.map(({ key, label, color, d }) => (
              <div key={key} className="card p-4 space-y-2">
                <div className="flex items-center gap-2">
                  <div className={cn("w-2.5 h-2.5 rounded-full", color)} />
                  <p className="text-xs font-semibold text-slate-700">{label}</p>
                </div>
                {key === "google" && (
                  <p className="text-xs text-slate-500">Conversion Rate: <span className="font-medium text-slate-700">{String(d.conversion_rate || 0)}%</span></p>
                )}
                {key === "facebook" && (
                  <p className="text-xs text-slate-500">Frequency tối ưu: <span className="font-medium text-slate-700">{String(d.frequency || 0)}×</span></p>
                )}
                {key === "tiktok" && (
                  <p className="text-xs text-slate-500">VTR (6s): <span className="font-medium text-slate-700">{String(d.vtr || 0)}%</span></p>
                )}
                <p className="text-xs text-slate-400 italic leading-relaxed">{String(d.note || "")}</p>
              </div>
            ))}
          </div>
        </>
      ) : null}
    </div>
  );
}

// ─── AI Allocate Tab ──────────────────────────────────────────────────────────

function AIAllocateTab() {
  const [budget, setBudget]     = useState(50000000);
  const [goal, setGoal]         = useState("conversion");
  const [industry, setIndustry] = useState("saas");
  const [result, setResult]     = useState("");
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");

  const run = async () => {
    setLoading(true);
    setError("");
    setResult("");
    try {
      const res = await api.optimizeBudget({
        current_budget: {
          "Google Ads": Math.round(budget * 0.4),
          "Facebook Ads": Math.round(budget * 0.35),
          "TikTok Ads": Math.round(budget * 0.25),
        },
        goal,
        season: industry,
      });
      setResult(res.recommendation);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Lỗi kết nối AI");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-5">
      <div className="card p-5 space-y-4">
        <h3 className="font-semibold text-slate-800 text-sm flex items-center gap-2">
          <Zap size={15} className="text-brand-500" />
          AI Budget Optimizer — Phân bổ tối ưu giữa 3 platform
        </h3>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div>
            <label className="text-sm font-medium text-slate-700 block mb-1.5">Tổng ngân sách (VNĐ)</label>
            <input
              type="number"
              className="input"
              value={budget}
              min={1000000}
              step={1000000}
              onChange={(e) => setBudget(Number(e.target.value))}
            />
            <p className="text-xs text-slate-400 mt-1">{formatVND(budget)}/tháng</p>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700 block mb-1.5">Mục tiêu</label>
            <select className="input" value={goal} onChange={(e) => setGoal(e.target.value)}>
              <option value="awareness">Brand Awareness (nhận biết)</option>
              <option value="conversion">Conversion (chuyển đổi)</option>
              <option value="retention">Retention (giữ chân)</option>
              <option value="cân bằng">Cân bằng tất cả</option>
            </select>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700 block mb-1.5">Ngành</label>
            <select className="input" value={industry} onChange={(e) => setIndustry(e.target.value)}>
              {INDUSTRIES.map(({ value, label }) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Current split preview */}
        <div className="bg-slate-50 rounded-lg p-3 space-y-2">
          <p className="text-xs font-medium text-slate-600">Phân bổ hiện tại (mặc định):</p>
          <div className="flex gap-4 text-xs text-slate-500">
            {[
              { label: "Google Ads", pct: 40 },
              { label: "Facebook Ads", pct: 35 },
              { label: "TikTok Ads", pct: 25 },
            ].map(({ label, pct }) => (
              <span key={label}>
                {label}: <span className="font-medium text-slate-700">{formatVND(Math.round(budget * pct / 100))}</span> ({pct}%)
              </span>
            ))}
          </div>
        </div>

        <button
          onClick={run}
          disabled={loading || budget <= 0}
          className="btn-primary flex items-center gap-2"
        >
          {loading ? (
            <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full spinner" /> AI đang phân tích...</>
          ) : (
            <><Zap size={15} /> Phân tích & Đề xuất</>
          )}
        </button>

        {error && <p className="text-sm text-red-600 bg-red-50 p-3 rounded-lg">{error}</p>}
      </div>

      {result && (
        <div className="card p-5">
          <h4 className="text-sm font-semibold text-slate-800 mb-3 flex items-center gap-2">
            <Zap size={14} className="text-brand-500" /> Đề xuất phân bổ từ AI
          </h4>
          <div className="prose prose-sm max-w-none text-slate-700 text-sm leading-relaxed whitespace-pre-wrap">
            {result}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function UnifiedAdsPage() {
  const [tab, setTab] = useState<Tab>("overview");

  return (
    <div className="max-w-5xl space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-800 flex items-center gap-2">
          <Layers size={20} className="text-brand-500" />
          Unified Ads Dashboard
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Tổng hợp Google Ads + Facebook Ads + TikTok Ads — so sánh hiệu quả và tối ưu phân bổ ngân sách
        </p>
      </div>

      <div className="flex gap-1 bg-slate-100 p-1 rounded-xl flex-wrap">
        {TABS.map(({ value, label, icon: Icon }) => (
          <button
            key={value}
            onClick={() => setTab(value)}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all",
              tab === value ? "bg-white text-slate-800 shadow-sm" : "text-slate-500 hover:text-slate-700"
            )}
          >
            <Icon size={14} />
            {label}
          </button>
        ))}
      </div>

      {tab === "overview"    && <OverviewTab />}
      {tab === "compare"     && <CompareTab />}
      {tab === "benchmark"   && <BenchmarkTab />}
      {tab === "ai-allocate" && <AIAllocateTab />}
    </div>
  );
}
