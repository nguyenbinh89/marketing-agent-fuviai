"use client";

import { useState, useEffect, useCallback } from "react";
import {
  MousePointerClick, TrendingUp, Key, Search, Lightbulb, BarChart2,
  RefreshCw, AlertTriangle, Check, X, Play, Pause,
} from "lucide-react";
import { api } from "@/lib/api";
import { cn, formatVND } from "@/lib/utils";

type Tab = "overview" | "campaigns" | "keywords" | "search-terms" | "keyword-ideas" | "benchmark";

const TABS: { value: Tab; label: string; icon: React.ElementType }[] = [
  { value: "overview",       label: "Tổng quan",       icon: TrendingUp },
  { value: "campaigns",      label: "Campaigns",       icon: MousePointerClick },
  { value: "keywords",       label: "Từ khoá",         icon: Key },
  { value: "search-terms",   label: "Search Terms",    icon: Search },
  { value: "keyword-ideas",  label: "Gợi ý từ khoá",  icon: Lightbulb },
  { value: "benchmark",      label: "Benchmark ngành", icon: BarChart2 },
];

const INDUSTRIES = [
  { value: "fmcg",       label: "FMCG" },
  { value: "fb",         label: "F&B" },
  { value: "realestate", label: "Bất động sản" },
  { value: "ecommerce",  label: "E-commerce" },
  { value: "saas",       label: "SaaS" },
  { value: "education",  label: "Giáo dục" },
];

function NotConfiguredBanner() {
  return (
    <div className="card p-6 flex items-start gap-4 bg-amber-50 border-amber-200">
      <AlertTriangle size={20} className="text-amber-500 flex-shrink-0 mt-0.5" />
      <div>
        <p className="font-semibold text-amber-800 text-sm">Google Ads chưa được cấu hình</p>
        <p className="text-amber-700 text-xs mt-1 leading-relaxed">
          Thêm các biến sau vào file <code className="bg-amber-100 px-1 rounded">.env</code>:{" "}
          <code className="bg-amber-100 px-1 rounded">GOOGLE_ADS_DEVELOPER_TOKEN</code>,{" "}
          <code className="bg-amber-100 px-1 rounded">GOOGLE_ADS_CLIENT_ID</code>,{" "}
          <code className="bg-amber-100 px-1 rounded">GOOGLE_ADS_CLIENT_SECRET</code>,{" "}
          <code className="bg-amber-100 px-1 rounded">GOOGLE_ADS_REFRESH_TOKEN</code>,{" "}
          <code className="bg-amber-100 px-1 rounded">GOOGLE_ADS_CUSTOMER_ID</code>.
        </p>
      </div>
    </div>
  );
}

// ─── Overview Tab ─────────────────────────────────────────────────────────────

function OverviewTab() {
  const [data, setData]   = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [days, setDays]   = useState(30);
  const [notConfigured, setNotConfigured] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setNotConfigured(false);
    try {
      const res = await api.googleAdsPerfSummary(days);
      if ((res as Record<string, unknown>).error) {
        setNotConfigured(true);
      } else {
        setData(res as Record<string, unknown>);
      }
    } catch {
      setNotConfigured(true);
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => { load(); }, [load]);

  if (notConfigured) return <NotConfiguredBanner />;

  const metrics = [
    { label: "Tổng chi phí", value: data ? formatVND(Number(data.total_cost_vnd || 0)) : "—", color: "text-red-500" },
    { label: "Clicks", value: data ? Number(data.total_clicks || 0).toLocaleString() : "—", color: "text-blue-600" },
    { label: "Impressions", value: data ? Number(data.total_impressions || 0).toLocaleString() : "—", color: "text-slate-700" },
    { label: "Conversions", value: data ? String(data.total_conversions || 0) : "—", color: "text-green-600" },
    { label: "CTR trung bình", value: data ? `${data.avg_ctr || 0}%` : "—", color: "text-brand-600" },
    { label: "CPC trung bình", value: data ? formatVND(Number(data.avg_cpc_vnd || 0)) : "—", color: "text-orange-500" },
    { label: "ROAS tổng", value: data ? `${data.overall_roas || 0}x` : "—", color: "text-purple-600" },
    { label: "Số ngày", value: String(days), color: "text-slate-500" },
  ];

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3 flex-wrap">
        <label className="text-sm text-slate-600">Khoảng thời gian:</label>
        {[7, 14, 30, 90].map((d) => (
          <button
            key={d}
            onClick={() => setDays(d)}
            className={cn(
              "px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors",
              days === d
                ? "bg-brand-50 border-brand-300 text-brand-700"
                : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
            )}
          >
            {d} ngày
          </button>
        ))}
        <button onClick={load} className="ml-auto text-slate-400 hover:text-brand-500 transition-colors">
          <RefreshCw size={15} className={loading ? "spinner" : ""} />
        </button>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="card p-5 animate-pulse">
              <div className="h-3 bg-slate-200 rounded w-24 mb-3" />
              <div className="h-6 bg-slate-200 rounded w-16" />
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {metrics.map(({ label, value, color }) => (
            <div key={label} className="card p-5">
              <p className="text-xs text-slate-500 mb-1">{label}</p>
              <p className={cn("text-2xl font-bold", color)}>{value}</p>
            </div>
          ))}
        </div>
      )}

      {data && Array.isArray(data.top_campaigns) && data.top_campaigns.length > 0 && (
        <div className="card overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-100 bg-slate-50">
            <p className="text-xs font-semibold text-slate-600">Top Campaigns theo Chi phí</p>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100">
                <th className="px-4 py-2 text-left text-xs font-semibold text-slate-500">Campaign</th>
                <th className="px-4 py-2 text-right text-xs font-semibold text-slate-500">Chi phí</th>
                <th className="px-4 py-2 text-right text-xs font-semibold text-slate-500">Clicks</th>
                <th className="px-4 py-2 text-right text-xs font-semibold text-slate-500">CTR</th>
                <th className="px-4 py-2 text-right text-xs font-semibold text-slate-500">ROAS</th>
              </tr>
            </thead>
            <tbody>
              {(data.top_campaigns as Array<Record<string, unknown>>).map((c, i) => (
                <tr key={i} className="border-b border-slate-50 hover:bg-slate-50/50">
                  <td className="px-4 py-2 font-medium text-slate-800 truncate max-w-xs">{String(c.campaign || "—")}</td>
                  <td className="px-4 py-2 text-right text-slate-600">{formatVND(Number(c.cost_vnd || 0))}</td>
                  <td className="px-4 py-2 text-right text-slate-600">{Number(c.clicks || 0).toLocaleString()}</td>
                  <td className="px-4 py-2 text-right text-slate-600">{String(c.ctr || 0)}%</td>
                  <td className="px-4 py-2 text-right font-semibold text-purple-600">{String(c.roas || 0)}x</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── Campaigns Tab ────────────────────────────────────────────────────────────

function CampaignsTab() {
  const [campaigns, setCampaigns] = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading]     = useState(false);
  const [status, setStatus]       = useState("ENABLED");
  const [notConfigured, setNotConfigured] = useState(false);

  // Edit budget
  const [editBudgetId, setEditBudgetId] = useState<string | null>(null);
  const [budgetVal, setBudgetVal]       = useState("");
  const [savingBudget, setSavingBudget] = useState(false);
  const [savedId, setSavedId]           = useState<string | null>(null);

  // Toggle status
  const [togglingId, setTogglingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setNotConfigured(false);
    try {
      const res = await api.googleAdsCampaigns(status);
      if (!res.campaigns || res.campaigns.length === 0) {
        setNotConfigured(true);
      }
      setCampaigns(res.campaigns || []);
    } catch {
      setNotConfigured(true);
    } finally {
      setLoading(false);
    }
  }, [status]);

  useEffect(() => { load(); }, [load]);

  const saveBudget = async (budgetId: string) => {
    const val = parseFloat(budgetVal);
    if (!val || val <= 0) return;
    setSavingBudget(true);
    try {
      await api.googleAdsUpdateBudget(budgetId, val);
      setSavedId(budgetId);
      setEditBudgetId(null);
      setTimeout(() => setSavedId(null), 3000);
      load();
    } catch { /* ignore */ } finally {
      setSavingBudget(false);
    }
  };

  const toggleStatus = async (campaignId: string, currentStatus: string) => {
    setTogglingId(campaignId);
    try {
      const newStatus = currentStatus === "ENABLED" ? "PAUSED" : "ENABLED";
      await api.googleAdsUpdateStatus(campaignId, newStatus as "ENABLED" | "PAUSED");
      load();
    } catch { /* ignore */ } finally {
      setTogglingId(null);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        {["ENABLED", "PAUSED", "REMOVED"].map((s) => (
          <button
            key={s}
            onClick={() => setStatus(s)}
            className={cn(
              "px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors",
              status === s
                ? "bg-brand-50 border-brand-300 text-brand-700"
                : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
            )}
          >
            {s === "ENABLED" ? "Đang chạy" : s === "PAUSED" ? "Tạm dừng" : "Đã xoá"}
          </button>
        ))}
        <button onClick={load} className="ml-auto text-slate-400 hover:text-brand-500">
          <RefreshCw size={15} className={loading ? "spinner" : ""} />
        </button>
      </div>

      {notConfigured ? <NotConfiguredBanner /> : loading ? (
        <div className="card p-12 text-center text-slate-400 text-sm">Đang tải campaigns...</div>
      ) : campaigns.length === 0 ? (
        <div className="card p-12 text-center text-slate-400 text-sm">Không có campaign nào</div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50">
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">Campaign</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">Kênh</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Ngân sách/ngày</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-slate-500">Trạng thái</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Hành động</th>
              </tr>
            </thead>
            <tbody>
              {campaigns.map((c) => {
                const id = String(c.id || "");
                const name = String(c.name || "—");
                const channel = String(c.channel || "—");
                const budget = Number(c.daily_budget || 0);
                const cStatus = String(c.status || "ENABLED");
                return (
                  <tr key={id} className="border-b border-slate-50 hover:bg-slate-50/50">
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-800 truncate max-w-xs">{name}</p>
                      <p className="text-xs text-slate-400">ID: {id}</p>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">{channel}</td>
                    <td className="px-4 py-3 text-right">
                      {savedId === id ? (
                        <span className="text-green-600 flex items-center justify-end gap-1 text-xs">
                          <Check size={12} /> Đã lưu
                        </span>
                      ) : editBudgetId === id ? (
                        <div className="flex items-center gap-1 justify-end">
                          <input
                            type="number"
                            value={budgetVal}
                            onChange={(e) => setBudgetVal(e.target.value)}
                            className="input w-28 text-right text-xs py-1"
                            placeholder="VNĐ/ngày"
                          />
                          <button onClick={() => saveBudget(id)} disabled={savingBudget} className="text-green-600 hover:text-green-700">
                            <Check size={14} />
                          </button>
                          <button onClick={() => setEditBudgetId(null)} className="text-slate-400 hover:text-slate-600">
                            <X size={14} />
                          </button>
                        </div>
                      ) : (
                        <span className="font-medium text-slate-800">{budget > 0 ? formatVND(budget) : "—"}</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={cn(
                        "text-xs px-2 py-0.5 rounded-full font-medium",
                        cStatus === "ENABLED" ? "bg-green-50 text-green-700" : "bg-slate-100 text-slate-600"
                      )}>
                        {cStatus === "ENABLED" ? "Đang chạy" : "Tạm dừng"}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        {editBudgetId !== id && (
                          <button
                            onClick={() => { setEditBudgetId(id); setBudgetVal(budget > 0 ? String(budget) : ""); }}
                            className="text-xs text-brand-500 hover:text-brand-700 font-medium"
                          >
                            Sửa budget
                          </button>
                        )}
                        <button
                          onClick={() => toggleStatus(id, cStatus)}
                          disabled={togglingId === id}
                          className={cn(
                            "p-1 rounded transition-colors",
                            cStatus === "ENABLED"
                              ? "text-amber-500 hover:text-amber-700 hover:bg-amber-50"
                              : "text-green-500 hover:text-green-700 hover:bg-green-50"
                          )}
                          title={cStatus === "ENABLED" ? "Tạm dừng" : "Kích hoạt"}
                        >
                          {togglingId === id ? (
                            <div className="w-3 h-3 border-2 border-current border-t-transparent rounded-full spinner" />
                          ) : cStatus === "ENABLED" ? (
                            <Pause size={13} />
                          ) : (
                            <Play size={13} />
                          )}
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── Keywords Tab ─────────────────────────────────────────────────────────────

function KeywordsTab() {
  const [rows, setRows]     = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading] = useState(false);
  const [days, setDays]     = useState(30);
  const [minClicks, setMinClicks] = useState(0);
  const [notConfigured, setNotConfigured] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setNotConfigured(false);
    try {
      const res = await api.googleAdsPerfKeywords(days, minClicks);
      if (!res.rows || res.rows.length === 0) setNotConfigured(true);
      setRows(res.rows || []);
    } catch {
      setNotConfigured(true);
    } finally {
      setLoading(false);
    }
  }, [days, minClicks]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        {[7, 14, 30, 90].map((d) => (
          <button key={d} onClick={() => setDays(d)}
            className={cn("px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors",
              days === d ? "bg-brand-50 border-brand-300 text-brand-700" : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
            )}>
            {d} ngày
          </button>
        ))}
        <div className="flex items-center gap-2 ml-auto">
          <label className="text-xs text-slate-500">Min clicks:</label>
          <input
            type="number"
            min={0}
            value={minClicks}
            onChange={(e) => setMinClicks(Number(e.target.value))}
            className="input w-16 text-xs py-1"
          />
          <button onClick={load} className="text-slate-400 hover:text-brand-500">
            <RefreshCw size={15} className={loading ? "spinner" : ""} />
          </button>
        </div>
      </div>

      {notConfigured ? <NotConfiguredBanner /> : loading ? (
        <div className="card p-12 text-center text-slate-400 text-sm">Đang tải từ khoá...</div>
      ) : rows.length === 0 ? (
        <div className="card p-12 text-center text-slate-400 text-sm">Không có dữ liệu từ khoá</div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50">
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">Từ khoá</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">Match</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">QS</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Clicks</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">CPC</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Chi phí</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Conversions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i} className="border-b border-slate-50 hover:bg-slate-50/50">
                  <td className="px-4 py-2 font-medium text-slate-800">{String(r.keyword || "—")}</td>
                  <td className="px-4 py-2 text-xs text-slate-500">{String(r.match_type || "—")}</td>
                  <td className="px-4 py-2 text-right">
                    <span className={cn(
                      "text-xs font-bold",
                      Number(r.quality_score) >= 7 ? "text-green-600" : Number(r.quality_score) >= 5 ? "text-amber-500" : "text-red-500"
                    )}>
                      {String(r.quality_score || "—")}
                    </span>
                  </td>
                  <td className="px-4 py-2 text-right text-slate-600">{Number(r.clicks || 0).toLocaleString()}</td>
                  <td className="px-4 py-2 text-right text-slate-600">{r.avg_cpc ? formatVND(Number(r.avg_cpc)) : "—"}</td>
                  <td className="px-4 py-2 text-right text-slate-600">{r.cost_vnd ? formatVND(Number(r.cost_vnd)) : "—"}</td>
                  <td className="px-4 py-2 text-right text-green-600 font-medium">{String(r.conversions || 0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── Search Terms Tab ─────────────────────────────────────────────────────────

function SearchTermsTab() {
  const [rows, setRows]     = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading] = useState(false);
  const [days, setDays]     = useState(30);
  const [notConfigured, setNotConfigured] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setNotConfigured(false);
    try {
      const res = await api.googleAdsSearchTerms(days);
      if (!res.rows || res.rows.length === 0) setNotConfigured(true);
      setRows(res.rows || []);
    } catch {
      setNotConfigured(true);
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => { load(); }, [load]);

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

      {notConfigured ? <NotConfiguredBanner /> : loading ? (
        <div className="card p-12 text-center text-slate-400 text-sm">Đang tải search terms...</div>
      ) : rows.length === 0 ? (
        <div className="card p-12 text-center text-slate-400 text-sm">Không có dữ liệu</div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50">
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">Search Term</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Impressions</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Clicks</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">CTR</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">CPC</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Conversions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i} className="border-b border-slate-50 hover:bg-slate-50/50">
                  <td className="px-4 py-2 font-medium text-slate-800">{String(r.search_term || "—")}</td>
                  <td className="px-4 py-2 text-right text-slate-600">{Number(r.impressions || 0).toLocaleString()}</td>
                  <td className="px-4 py-2 text-right text-slate-600">{Number(r.clicks || 0).toLocaleString()}</td>
                  <td className="px-4 py-2 text-right text-slate-600">{String(r.ctr || 0)}%</td>
                  <td className="px-4 py-2 text-right text-slate-600">{r.avg_cpc ? formatVND(Number(r.avg_cpc)) : "—"}</td>
                  <td className="px-4 py-2 text-right text-green-600 font-medium">{String(r.conversions || 0)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── Keyword Ideas Tab ────────────────────────────────────────────────────────

function KeywordIdeasTab() {
  const [seeds, setSeeds]   = useState("");
  const [ideas, setIdeas]   = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError]   = useState("");

  const search = async () => {
    const kws = seeds.split(",").map((s) => s.trim()).filter(Boolean);
    if (kws.length === 0) return;
    setLoading(true);
    setError("");
    try {
      const res = await api.googleAdsKeywordIdeas(kws);
      setIdeas(res.ideas || []);
      if (res.ideas.length === 0) setError("Không tìm được gợi ý. Kiểm tra Google Ads đã cấu hình chưa.");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Lỗi kết nối Google Ads");
      setIdeas([]);
    } finally {
      setLoading(false);
    }
  };

  const COMP_COLOR: Record<string, string> = {
    LOW: "text-green-600",
    MEDIUM: "text-amber-500",
    HIGH: "text-red-500",
  };

  return (
    <div className="space-y-5">
      <div className="card p-5 space-y-4">
        <h3 className="font-semibold text-slate-800 flex items-center gap-2 text-sm">
          <Lightbulb size={15} /> Google Keyword Planner — Gợi ý từ khoá
        </h3>
        <div>
          <label className="text-sm font-medium text-slate-700 block mb-1.5">
            Seed keywords <span className="text-slate-400 font-normal">(phân cách bằng dấu phẩy, tối đa 10)</span>
          </label>
          <input
            className="input"
            placeholder="VD: marketing automation, AI marketing, phần mềm bán hàng"
            value={seeds}
            onChange={(e) => setSeeds(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && search()}
          />
        </div>
        <button
          onClick={search}
          disabled={loading || !seeds.trim()}
          className="btn-primary flex items-center gap-2"
        >
          {loading
            ? <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full spinner" /> Đang tìm...</>
            : <><Search size={15} /> Tìm từ khoá</>
          }
        </button>
        {error && (
          <p className="text-sm text-red-600 bg-red-50 p-3 rounded-lg">{error}</p>
        )}
      </div>

      {ideas.length > 0 && (
        <div className="card overflow-hidden">
          <div className="px-4 py-3 border-b border-slate-100 bg-slate-50 flex items-center justify-between">
            <p className="text-xs font-semibold text-slate-600">
              {ideas.length} gợi ý từ khoá — sắp xếp theo lượng tìm kiếm
            </p>
          </div>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100">
                <th className="px-4 py-2 text-left text-xs font-semibold text-slate-500">Từ khoá</th>
                <th className="px-4 py-2 text-right text-xs font-semibold text-slate-500">Tìm kiếm/tháng</th>
                <th className="px-4 py-2 text-center text-xs font-semibold text-slate-500">Cạnh tranh</th>
                <th className="px-4 py-2 text-right text-xs font-semibold text-slate-500">Bid thấp</th>
                <th className="px-4 py-2 text-right text-xs font-semibold text-slate-500">Bid cao</th>
              </tr>
            </thead>
            <tbody>
              {ideas.map((idea, i) => {
                const comp = String(idea.competition || "UNSPECIFIED");
                return (
                  <tr key={i} className="border-b border-slate-50 hover:bg-slate-50/50">
                    <td className="px-4 py-2 font-medium text-slate-800">{String(idea.keyword || "—")}</td>
                    <td className="px-4 py-2 text-right text-blue-600 font-semibold">
                      {Number(idea.avg_monthly_searches || 0).toLocaleString()}
                    </td>
                    <td className="px-4 py-2 text-center">
                      <span className={cn("text-xs font-medium", COMP_COLOR[comp] || "text-slate-500")}>
                        {comp === "LOW" ? "Thấp" : comp === "MEDIUM" ? "Trung bình" : comp === "HIGH" ? "Cao" : comp}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-right text-slate-600">
                      {Number(idea.low_top_of_page_bid) > 0 ? formatVND(Number(idea.low_top_of_page_bid)) : "—"}
                    </td>
                    <td className="px-4 py-2 text-right text-slate-600">
                      {Number(idea.high_top_of_page_bid) > 0 ? formatVND(Number(idea.high_top_of_page_bid)) : "—"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── Benchmark Tab ────────────────────────────────────────────────────────────

function BenchmarkTab() {
  const [industry, setIndustry] = useState("saas");
  const [data, setData]         = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading]   = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.googleAdsBenchmark(industry);
      setData(res as Record<string, unknown>);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [industry]);

  useEffect(() => { load(); }, [load]);

  const metrics = data ? [
    { label: "CPC trung bình", value: formatVND(Number(data.cpc || 0)), desc: "Cost Per Click" },
    { label: "CPM trung bình", value: formatVND(Number(data.cpm || 0)), desc: "Cost Per 1000 Impressions" },
    { label: "CTR benchmark", value: `${data.ctr || 0}%`, desc: "Click Through Rate" },
    { label: "ROAS benchmark", value: `${data.roas || 0}x`, desc: "Return on Ad Spend" },
    { label: "Tỷ lệ chuyển đổi", value: `${data.conversion_rate || 0}%`, desc: "Conversion Rate" },
  ] : [];

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-2 flex-wrap">
        {INDUSTRIES.map(({ value, label }) => (
          <button
            key={value}
            onClick={() => setIndustry(value)}
            className={cn(
              "px-4 py-2 rounded-lg border text-xs font-medium transition-colors",
              industry === value
                ? "bg-brand-50 border-brand-300 text-brand-700"
                : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
            )}
          >
            {label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="card p-5 animate-pulse">
              <div className="h-3 bg-slate-200 rounded w-24 mb-3" />
              <div className="h-6 bg-slate-200 rounded w-16" />
            </div>
          ))}
        </div>
      ) : data ? (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
            {metrics.map(({ label, value, desc }) => (
              <div key={label} className="card p-5">
                <p className="text-xs text-slate-500 mb-1">{label}</p>
                <p className="text-2xl font-bold text-brand-600">{value}</p>
                <p className="text-xs text-slate-400 mt-1">{desc}</p>
              </div>
            ))}
          </div>
          {data.note && (
            <div className="card p-4 bg-slate-50 border-slate-200">
              <p className="text-xs text-slate-500">{String(data.note)}</p>
              <p className="text-xs text-slate-400 mt-1">Source: {String(data.source || "FuviAI benchmark VN 2026")}</p>
            </div>
          )}
        </>
      ) : null}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function GoogleAdsPage() {
  const [tab, setTab] = useState<Tab>("overview");

  return (
    <div className="max-w-5xl space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-800">Google Ads</h1>
        <p className="text-sm text-slate-500 mt-1">
          Quản lý campaigns, theo dõi performance, nghiên cứu từ khoá và benchmark ngành
        </p>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 bg-slate-100 p-1 rounded-xl flex-wrap">
        {TABS.map(({ value, label, icon: Icon }) => (
          <button
            key={value}
            onClick={() => setTab(value)}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all",
              tab === value
                ? "bg-white text-slate-800 shadow-sm"
                : "text-slate-500 hover:text-slate-700"
            )}
          >
            <Icon size={14} />
            {label}
          </button>
        ))}
      </div>

      {tab === "overview"       && <OverviewTab />}
      {tab === "campaigns"      && <CampaignsTab />}
      {tab === "keywords"       && <KeywordsTab />}
      {tab === "search-terms"   && <SearchTermsTab />}
      {tab === "keyword-ideas"  && <KeywordIdeasTab />}
      {tab === "benchmark"      && <BenchmarkTab />}
    </div>
  );
}
