"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Target, TrendingUp, Users, Image, BarChart2, Search, BookOpen,
  RefreshCw, AlertTriangle, Check, X, Play, Pause,
} from "lucide-react";
import { api } from "@/lib/api";
import { cn, formatVND } from "@/lib/utils";

type Tab = "overview" | "campaigns" | "adsets" | "ads" | "delivery" | "ad-library" | "benchmark";

const TABS: { value: Tab; label: string; icon: React.ElementType }[] = [
  { value: "overview",    label: "Tổng quan",      icon: TrendingUp },
  { value: "campaigns",   label: "Campaigns",      icon: Target },
  { value: "adsets",      label: "Ad Sets",        icon: Users },
  { value: "ads",         label: "Ads",            icon: Image },
  { value: "delivery",    label: "Audience",       icon: BarChart2 },
  { value: "ad-library",  label: "Ad Library",     icon: Search },
  { value: "benchmark",   label: "Benchmark",      icon: BookOpen },
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
        <p className="font-semibold text-amber-800 text-sm">Facebook Ads chưa được cấu hình</p>
        <p className="text-amber-700 text-xs mt-1 leading-relaxed">
          Thêm <code className="bg-amber-100 px-1 rounded">FACEBOOK_ACCESS_TOKEN</code> và{" "}
          <code className="bg-amber-100 px-1 rounded">FACEBOOK_AD_ACCOUNT_ID</code> vào file{" "}
          <code className="bg-amber-100 px-1 rounded">.env</code>.{" "}
          Token cần quyền <code className="bg-amber-100 px-1 rounded">ads_read</code> và{" "}
          <code className="bg-amber-100 px-1 rounded">ads_management</code>.
        </p>
      </div>
    </div>
  );
}

// ─── Overview Tab ─────────────────────────────────────────────────────────────

function OverviewTab() {
  const [data, setData]       = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [days, setDays]       = useState(30);
  const [notConfigured, setNotConfigured] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setNotConfigured(false);
    try {
      const res = await api.facebookAdsAccountInsights(days);
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
    { label: "Tổng chi tiêu",    value: data ? formatVND(Number(data.spend_vnd || 0))       : "—", color: "text-red-500" },
    { label: "Impressions",      value: data ? Number(data.impressions || 0).toLocaleString(): "—", color: "text-slate-700" },
    { label: "Clicks",           value: data ? Number(data.clicks || 0).toLocaleString()    : "—", color: "text-blue-600" },
    { label: "Reach",            value: data ? Number(data.reach || 0).toLocaleString()     : "—", color: "text-indigo-600" },
    { label: "Frequency",        value: data ? String(data.frequency || 0)                  : "—", color: "text-slate-500" },
    { label: "CTR",              value: data ? `${data.ctr || 0}%`                          : "—", color: "text-brand-600" },
    { label: "CPC",              value: data ? formatVND(Number(data.cpc_vnd || 0))         : "—", color: "text-orange-500" },
    { label: "ROAS",             value: data ? `${data.roas || 0}x`                         : "—", color: "text-purple-600" },
    { label: "Purchases",        value: data ? String(data.purchases || 0)                  : "—", color: "text-green-600" },
    { label: "Purchase Value",   value: data ? formatVND(Number(data.purchase_value_vnd || 0)): "—", color: "text-green-700" },
  ];

  return (
    <div className="space-y-5">
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
        <button onClick={load} className="ml-auto text-slate-400 hover:text-brand-500 transition-colors">
          <RefreshCw size={15} className={loading ? "spinner" : ""} />
        </button>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          {Array.from({ length: 10 }).map((_, i) => (
            <div key={i} className="card p-5 animate-pulse">
              <div className="h-3 bg-slate-200 rounded w-20 mb-3" />
              <div className="h-6 bg-slate-200 rounded w-14" />
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
          {metrics.map(({ label, value, color }) => (
            <div key={label} className="card p-5">
              <p className="text-xs text-slate-500 mb-1">{label}</p>
              <p className={cn("text-xl font-bold", color)}>{value}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Campaigns Tab ────────────────────────────────────────────────────────────

function CampaignsTab() {
  const [campaigns, setCampaigns] = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading]     = useState(false);
  const [status, setStatus]       = useState("ACTIVE");
  const [notConfigured, setNotConfigured] = useState(false);

  // Insights
  const [insights, setInsights]   = useState<Array<Record<string, unknown>>>([]);
  const [insightDays, setInsightDays] = useState(7);
  const [loadingInsights, setLoadingInsights] = useState(false);

  // Edit budget
  const [editId, setEditId]       = useState<string | null>(null);
  const [budgetVal, setBudgetVal] = useState("");
  const [saving, setSaving]       = useState(false);
  const [savedId, setSavedId]     = useState<string | null>(null);

  // Toggle
  const [togglingId, setTogglingId] = useState<string | null>(null);

  const loadCampaigns = useCallback(async () => {
    setLoading(true);
    setNotConfigured(false);
    try {
      const res = await api.facebookAdsCampaigns(status);
      setCampaigns(res.campaigns || []);
      if (!res.campaigns || res.campaigns.length === 0) setNotConfigured(true);
    } catch {
      setNotConfigured(true);
    } finally {
      setLoading(false);
    }
  }, [status]);

  const loadInsights = useCallback(async () => {
    setLoadingInsights(true);
    try {
      const res = await api.facebookAdsCampaignInsights(insightDays);
      setInsights(res.rows || []);
    } catch {
      setInsights([]);
    } finally {
      setLoadingInsights(false);
    }
  }, [insightDays]);

  useEffect(() => { loadCampaigns(); }, [loadCampaigns]);
  useEffect(() => { loadInsights(); }, [loadInsights]);

  const saveBudget = async (campaignId: string) => {
    const val = parseFloat(budgetVal);
    if (!val || val <= 0) return;
    setSaving(true);
    try {
      await api.facebookAdsUpdateBudget(campaignId, val);
      setSavedId(campaignId);
      setEditId(null);
      setTimeout(() => setSavedId(null), 3000);
      loadCampaigns();
    } catch { /* ignore */ } finally {
      setSaving(false);
    }
  };

  const toggleStatus = async (campaignId: string, currentStatus: string) => {
    setTogglingId(campaignId);
    try {
      const newStatus = currentStatus === "ACTIVE" ? "PAUSED" : "ACTIVE";
      await api.facebookAdsUpdateStatus(campaignId, newStatus as "ACTIVE" | "PAUSED");
      loadCampaigns();
    } catch { /* ignore */ } finally {
      setTogglingId(null);
    }
  };

  // merge insights by campaign_id
  const insightMap = Object.fromEntries(insights.map((r) => [String(r.campaign_id), r]));

  return (
    <div className="space-y-5">
      {/* Campaign list */}
      <div className="space-y-3">
        <div className="flex items-center gap-3 flex-wrap">
          {["ACTIVE", "PAUSED", "ARCHIVED"].map((s) => (
            <button key={s} onClick={() => setStatus(s)}
              className={cn("px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors",
                status === s ? "bg-brand-50 border-brand-300 text-brand-700" : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
              )}>
              {s === "ACTIVE" ? "Đang chạy" : s === "PAUSED" ? "Tạm dừng" : "Lưu trữ"}
            </button>
          ))}
          <button onClick={loadCampaigns} className="ml-auto text-slate-400 hover:text-brand-500">
            <RefreshCw size={15} className={loading ? "spinner" : ""} />
          </button>
        </div>

        {notConfigured ? <NotConfiguredBanner /> : loading ? (
          <div className="card p-12 text-center text-slate-400 text-sm">Đang tải campaigns...</div>
        ) : campaigns.length === 0 ? (
          <div className="card p-8 text-center text-slate-400 text-sm">Không có campaign nào</div>
        ) : (
          <div className="card overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100 bg-slate-50">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">Campaign</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">Mục tiêu</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Budget/ngày</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Chi tiêu ({insightDays}d)</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">ROAS</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-slate-500">Status</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Hành động</th>
                </tr>
              </thead>
              <tbody>
                {campaigns.map((c) => {
                  const id = String(c.id || "");
                  const name = String(c.name || "—");
                  const objective = String(c.objective || "—");
                  const budget = Number(c.daily_budget_vnd || 0);
                  const cStatus = String(c.status || "ACTIVE");
                  const perf = insightMap[id];
                  return (
                    <tr key={id} className="border-b border-slate-50 hover:bg-slate-50/50">
                      <td className="px-4 py-3">
                        <p className="font-medium text-slate-800 truncate max-w-[200px]">{name}</p>
                        <p className="text-xs text-slate-400">ID: {id}</p>
                      </td>
                      <td className="px-4 py-3 text-xs text-slate-500">{objective.replace(/_/g, " ")}</td>
                      <td className="px-4 py-3 text-right">
                        {savedId === id ? (
                          <span className="text-green-600 flex items-center justify-end gap-1 text-xs"><Check size={12} /> Đã lưu</span>
                        ) : editId === id ? (
                          <div className="flex items-center gap-1 justify-end">
                            <input
                              type="number"
                              value={budgetVal}
                              onChange={(e) => setBudgetVal(e.target.value)}
                              className="input w-28 text-right text-xs py-1"
                              placeholder="VNĐ/ngày"
                            />
                            <button onClick={() => saveBudget(id)} disabled={saving} className="text-green-600 hover:text-green-700">
                              <Check size={14} />
                            </button>
                            <button onClick={() => setEditId(null)} className="text-slate-400 hover:text-slate-600">
                              <X size={14} />
                            </button>
                          </div>
                        ) : (
                          <span className="font-medium text-slate-800">{budget > 0 ? formatVND(budget) : "—"}</span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-right text-slate-600">
                        {perf ? formatVND(Number(perf.spend_vnd || 0)) : loadingInsights ? "…" : "—"}
                      </td>
                      <td className="px-4 py-3 text-right font-semibold text-purple-600">
                        {perf ? `${perf.roas || 0}x` : "—"}
                      </td>
                      <td className="px-4 py-3 text-center">
                        <span className={cn("text-xs px-2 py-0.5 rounded-full font-medium",
                          cStatus === "ACTIVE" ? "bg-green-50 text-green-700" : "bg-slate-100 text-slate-600"
                        )}>
                          {cStatus === "ACTIVE" ? "Đang chạy" : "Tạm dừng"}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right">
                        <div className="flex items-center justify-end gap-2">
                          {editId !== id && (
                            <button
                              onClick={() => { setEditId(id); setBudgetVal(budget > 0 ? String(budget) : ""); }}
                              className="text-xs text-brand-500 hover:text-brand-700 font-medium"
                            >
                              Budget
                            </button>
                          )}
                          <button
                            onClick={() => toggleStatus(id, cStatus)}
                            disabled={togglingId === id}
                            className={cn("p-1 rounded transition-colors",
                              cStatus === "ACTIVE" ? "text-amber-500 hover:text-amber-700 hover:bg-amber-50" : "text-green-500 hover:text-green-700 hover:bg-green-50"
                            )}
                            title={cStatus === "ACTIVE" ? "Tạm dừng" : "Kích hoạt"}
                          >
                            {togglingId === id
                              ? <div className="w-3 h-3 border-2 border-current border-t-transparent rounded-full spinner" />
                              : cStatus === "ACTIVE" ? <Pause size={13} /> : <Play size={13} />
                            }
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

      {/* Insights day selector */}
      <div className="flex items-center gap-2">
        <p className="text-xs text-slate-500">Insight period:</p>
        {[7, 14, 30].map((d) => (
          <button key={d} onClick={() => setInsightDays(d)}
            className={cn("px-2 py-1 rounded border text-xs font-medium transition-colors",
              insightDays === d ? "bg-brand-50 border-brand-300 text-brand-700" : "bg-white border-slate-200 text-slate-600"
            )}>
            {d}d
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── Ad Sets Tab ──────────────────────────────────────────────────────────────

function AdsetsTab() {
  const [adsets, setAdsets]   = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading] = useState(false);
  const [days, setDays]       = useState(7);
  const [insights, setInsights] = useState<Array<Record<string, unknown>>>([]);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const [adsetRes, insightRes] = await Promise.all([
          api.facebookAdsAdsets(),
          api.facebookAdsAdsetInsights(days),
        ]);
        setAdsets(adsetRes.adsets || []);
        setInsights(insightRes.rows || []);
      } catch {
        setAdsets([]);
      } finally {
        setLoading(false);
      }
    })();
  }, [days]);

  const insightMap = Object.fromEntries(insights.map((r) => [String(r.adset_id), r]));

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        {[7, 14, 30].map((d) => (
          <button key={d} onClick={() => setDays(d)}
            className={cn("px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors",
              days === d ? "bg-brand-50 border-brand-300 text-brand-700" : "bg-white border-slate-200 text-slate-600"
            )}>
            {d} ngày
          </button>
        ))}
        <button onClick={() => setDays(days)} className="ml-auto text-slate-400 hover:text-brand-500">
          <RefreshCw size={15} className={loading ? "spinner" : ""} />
        </button>
      </div>

      {loading ? (
        <div className="card p-12 text-center text-slate-400 text-sm">Đang tải Ad Sets...</div>
      ) : adsets.length === 0 ? (
        <NotConfiguredBanner />
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50">
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">Ad Set</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">Mục tiêu tối ưu</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Budget/ngày</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Chi tiêu</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">CTR</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-slate-500">Status</th>
              </tr>
            </thead>
            <tbody>
              {adsets.map((s) => {
                const id = String(s.id || "");
                const perf = insightMap[id];
                return (
                  <tr key={id} className="border-b border-slate-50 hover:bg-slate-50/50">
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-800 truncate max-w-[200px]">{String(s.name || "—")}</p>
                      <p className="text-xs text-slate-400">ID: {id}</p>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">{String(s.optimization_goal || "—")}</td>
                    <td className="px-4 py-3 text-right text-slate-600">
                      {Number(s.daily_budget_vnd) > 0 ? formatVND(Number(s.daily_budget_vnd)) : "—"}
                    </td>
                    <td className="px-4 py-3 text-right text-slate-600">
                      {perf ? formatVND(Number(perf.spend_vnd || 0)) : "—"}
                    </td>
                    <td className="px-4 py-3 text-right text-brand-600">
                      {perf ? `${perf.ctr || 0}%` : "—"}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={cn("text-xs px-2 py-0.5 rounded-full font-medium",
                        String(s.status) === "ACTIVE" ? "bg-green-50 text-green-700" : "bg-slate-100 text-slate-600"
                      )}>
                        {String(s.status || "—")}
                      </span>
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

// ─── Ads Tab ──────────────────────────────────────────────────────────────────

function AdsTab() {
  const [rows, setRows]       = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading] = useState(false);
  const [days, setDays]       = useState(7);
  const [notConfigured, setNotConfigured] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setNotConfigured(false);
    try {
      const res = await api.facebookAdsAdInsights(days);
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
        {[7, 14, 30].map((d) => (
          <button key={d} onClick={() => setDays(d)}
            className={cn("px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors",
              days === d ? "bg-brand-50 border-brand-300 text-brand-700" : "bg-white border-slate-200 text-slate-600"
            )}>
            {d} ngày
          </button>
        ))}
        <button onClick={load} className="ml-auto text-slate-400 hover:text-brand-500">
          <RefreshCw size={15} className={loading ? "spinner" : ""} />
        </button>
      </div>

      {notConfigured ? <NotConfiguredBanner /> : loading ? (
        <div className="card p-12 text-center text-slate-400 text-sm">Đang tải Ads...</div>
      ) : rows.length === 0 ? (
        <div className="card p-8 text-center text-slate-400 text-sm">Không có dữ liệu</div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50">
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">Ad</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">Ad Set</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Chi tiêu</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Impressions</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Clicks</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">CTR</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">CPC</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i} className="border-b border-slate-50 hover:bg-slate-50/50">
                  <td className="px-4 py-2">
                    <p className="font-medium text-slate-800 truncate max-w-[180px]">{String(r.ad || "—")}</p>
                    <p className="text-xs text-slate-400">{String(r.campaign || "")}</p>
                  </td>
                  <td className="px-4 py-2 text-xs text-slate-500 truncate max-w-[150px]">{String(r.adset || "—")}</td>
                  <td className="px-4 py-2 text-right text-slate-600">{formatVND(Number(r.spend_vnd || 0))}</td>
                  <td className="px-4 py-2 text-right text-slate-600">{Number(r.impressions || 0).toLocaleString()}</td>
                  <td className="px-4 py-2 text-right text-slate-600">{Number(r.clicks || 0).toLocaleString()}</td>
                  <td className="px-4 py-2 text-right text-brand-600">{String(r.ctr || 0)}%</td>
                  <td className="px-4 py-2 text-right text-orange-500">{r.cpc_vnd ? formatVND(Number(r.cpc_vnd)) : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── Delivery (Audience) Tab ──────────────────────────────────────────────────

function DeliveryTab() {
  const [rows, setRows]           = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading]     = useState(false);
  const [days, setDays]           = useState(30);
  const [breakdown, setBreakdown] = useState("age,gender");
  const [notConfigured, setNotConfigured] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setNotConfigured(false);
    try {
      const res = await api.facebookAdsDelivery(days, breakdown);
      if (!res.rows || res.rows.length === 0) setNotConfigured(true);
      setRows(res.rows || []);
    } catch {
      setNotConfigured(true);
    } finally {
      setLoading(false);
    }
  }, [days, breakdown]);

  useEffect(() => { load(); }, [load]);

  const breakdownCols = breakdown.split(",");

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        {[
          { value: "age,gender",         label: "Tuổi & Giới tính" },
          { value: "country",            label: "Quốc gia" },
          { value: "publisher_platform", label: "Platform" },
          { value: "device_platform",    label: "Thiết bị" },
        ].map(({ value, label }) => (
          <button key={value} onClick={() => setBreakdown(value)}
            className={cn("px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors",
              breakdown === value ? "bg-brand-50 border-brand-300 text-brand-700" : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
            )}>
            {label}
          </button>
        ))}
        <div className="flex items-center gap-2 ml-auto">
          {[7, 30].map((d) => (
            <button key={d} onClick={() => setDays(d)}
              className={cn("px-2 py-1 rounded border text-xs font-medium",
                days === d ? "bg-brand-50 border-brand-300 text-brand-700" : "bg-white border-slate-200 text-slate-600"
              )}>
              {d}d
            </button>
          ))}
          <button onClick={load} className="text-slate-400 hover:text-brand-500">
            <RefreshCw size={15} className={loading ? "spinner" : ""} />
          </button>
        </div>
      </div>

      {notConfigured ? <NotConfiguredBanner /> : loading ? (
        <div className="card p-12 text-center text-slate-400 text-sm">Đang tải audience data...</div>
      ) : rows.length === 0 ? (
        <div className="card p-8 text-center text-slate-400 text-sm">Không có dữ liệu</div>
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50">
                {breakdownCols.map((col) => (
                  <th key={col} className="px-4 py-3 text-left text-xs font-semibold text-slate-500 capitalize">{col}</th>
                ))}
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Impressions</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Clicks</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">CTR</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Chi tiêu</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i} className="border-b border-slate-50 hover:bg-slate-50/50">
                  {breakdownCols.map((col) => (
                    <td key={col} className="px-4 py-2 font-medium text-slate-700">{String(r[col.trim()] || "—")}</td>
                  ))}
                  <td className="px-4 py-2 text-right text-slate-600">{Number(r.impressions || 0).toLocaleString()}</td>
                  <td className="px-4 py-2 text-right text-slate-600">{Number(r.clicks || 0).toLocaleString()}</td>
                  <td className="px-4 py-2 text-right text-brand-600">{String(r.ctr || 0)}%</td>
                  <td className="px-4 py-2 text-right text-slate-600">{formatVND(Number(r.spend_vnd || 0))}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── Ad Library Tab ───────────────────────────────────────────────────────────

function AdLibraryTab() {
  const [query, setQuery]   = useState("");
  const [country, setCountry] = useState("VN");
  const [ads, setAds]       = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError]   = useState("");

  const search = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setError("");
    try {
      const res = await api.facebookAdsLibrary(query, country);
      setAds(res.ads || []);
      if (res.ads.length === 0) setError("Không tìm thấy ads. Thử từ khoá khác.");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Lỗi kết nối Facebook Ad Library");
      setAds([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-5">
      <div className="card p-5 space-y-4">
        <h3 className="font-semibold text-slate-800 text-sm flex items-center gap-2">
          <Search size={15} /> Facebook Ad Library — Research Ads Đối Thủ
        </h3>
        <div className="flex gap-3">
          <input
            className="input flex-1"
            placeholder="VD: cà phê Hà Nội, phần mềm quản lý bán hàng..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && search()}
          />
          <select
            className="input w-24"
            value={country}
            onChange={(e) => setCountry(e.target.value)}
          >
            {["VN", "US", "SG", "TH", "MY", "PH"].map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
          <button onClick={search} disabled={loading || !query.trim()} className="btn-primary flex items-center gap-2 whitespace-nowrap">
            {loading
              ? <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full spinner" /> Đang tìm...</>
              : <><Search size={15} /> Tìm kiếm</>
            }
          </button>
        </div>
        {error && <p className="text-sm text-red-600 bg-red-50 p-3 rounded-lg">{error}</p>}
      </div>

      {ads.length > 0 && (
        <div className="space-y-3">
          <p className="text-sm text-slate-600">{ads.length} ads tìm thấy</p>
          {ads.map((ad, i) => (
            <div key={i} className="card p-4 space-y-2">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="font-semibold text-slate-800 text-sm">{String(ad.page_name || "Unknown Page")}</p>
                  {ad.link_title && (
                    <p className="text-xs text-brand-600 mt-0.5">{String(ad.link_title)}</p>
                  )}
                </div>
                {ad.impressions && ad.impressions !== "N/A" && (
                  <span className="text-xs text-slate-400 whitespace-nowrap">
                    {String(ad.impressions)}+ impressions
                  </span>
                )}
              </div>
              {ad.body && (
                <p className="text-sm text-slate-600 leading-relaxed">{String(ad.body)}</p>
              )}
              {ad.snapshot_url && (
                <a
                  href={String(ad.snapshot_url)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-brand-500 hover:text-brand-700 underline"
                >
                  Xem ad gốc →
                </a>
              )}
            </div>
          ))}
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
      const res = await api.facebookAdsBenchmark(industry);
      setData(res as Record<string, unknown>);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [industry]);

  useEffect(() => { load(); }, [load]);

  const metrics = data ? [
    { label: "CPC trung bình",    value: formatVND(Number(data.cpc || 0)),  desc: "Cost Per Click" },
    { label: "CPM trung bình",    value: formatVND(Number(data.cpm || 0)),  desc: "Cost Per 1000 Impressions" },
    { label: "CTR benchmark",     value: `${data.ctr || 0}%`,               desc: "Click Through Rate" },
    { label: "ROAS benchmark",    value: `${data.roas || 0}x`,              desc: "Return on Ad Spend" },
    { label: "Frequency tối ưu",  value: `${data.frequency || 0}x`,        desc: "Lần hiển thị trung bình/người" },
  ] : [];

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
              <p className="text-xs text-slate-400 mt-1">Source: {String(data.source || "")}</p>
            </div>
          )}
        </>
      ) : null}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function FacebookAdsPage() {
  const [tab, setTab] = useState<Tab>("overview");

  return (
    <div className="max-w-5xl space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-800">Facebook Ads</h1>
        <p className="text-sm text-slate-500 mt-1">
          Quản lý campaigns, theo dõi performance, phân tích audience và research đối thủ qua Ad Library
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
              tab === value ? "bg-white text-slate-800 shadow-sm" : "text-slate-500 hover:text-slate-700"
            )}
          >
            <Icon size={14} />
            {label}
          </button>
        ))}
      </div>

      {tab === "overview"   && <OverviewTab />}
      {tab === "campaigns"  && <CampaignsTab />}
      {tab === "adsets"     && <AdsetsTab />}
      {tab === "ads"        && <AdsTab />}
      {tab === "delivery"   && <DeliveryTab />}
      {tab === "ad-library" && <AdLibraryTab />}
      {tab === "benchmark"  && <BenchmarkTab />}
    </div>
  );
}
