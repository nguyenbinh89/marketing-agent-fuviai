"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Video, TrendingUp, Users, Image, BarChart2, BookOpen,
  RefreshCw, AlertTriangle, Check, X, Play, Pause,
} from "lucide-react";
import { api } from "@/lib/api";
import { cn, formatVND } from "@/lib/utils";

type Tab = "overview" | "campaigns" | "adgroups" | "ads" | "audience" | "benchmark";

const TABS: { value: Tab; label: string; icon: React.ElementType }[] = [
  { value: "overview",   label: "Tổng quan",    icon: TrendingUp },
  { value: "campaigns",  label: "Campaigns",    icon: Video },
  { value: "adgroups",   label: "Ad Groups",    icon: Users },
  { value: "ads",        label: "Ads (Video)",  icon: Image },
  { value: "audience",   label: "Audience",     icon: BarChart2 },
  { value: "benchmark",  label: "Benchmark",    icon: BookOpen },
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
        <p className="font-semibold text-amber-800 text-sm">TikTok Ads chưa được cấu hình</p>
        <p className="text-amber-700 text-xs mt-1 leading-relaxed">
          Thêm <code className="bg-amber-100 px-1 rounded">TIKTOK_ADS_ACCESS_TOKEN</code> và{" "}
          <code className="bg-amber-100 px-1 rounded">TIKTOK_ADS_ADVERTISER_ID</code> vào file{" "}
          <code className="bg-amber-100 px-1 rounded">.env</code>.{" "}
          Lấy token tại{" "}
          <span className="font-medium">TikTok for Business → App Management → Access Token</span>.
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
      const res = await api.tiktokAdsAccountInsights(days);
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
    { label: "Tổng chi tiêu",   value: data ? formatVND(Number(data.spend_vnd || 0))        : "—", color: "text-red-500" },
    { label: "Impressions",     value: data ? Number(data.impressions || 0).toLocaleString() : "—", color: "text-slate-700" },
    { label: "Clicks",          value: data ? Number(data.clicks || 0).toLocaleString()      : "—", color: "text-blue-600" },
    { label: "Reach",           value: data ? Number(data.reach || 0).toLocaleString()       : "—", color: "text-indigo-600" },
    { label: "CTR",             value: data ? `${data.ctr || 0}%`                            : "—", color: "text-brand-600" },
    { label: "CPC",             value: data ? formatVND(Number(data.cpc_vnd || 0))           : "—", color: "text-orange-500" },
    { label: "CPM",             value: data ? formatVND(Number(data.cpm_vnd || 0))           : "—", color: "text-amber-600" },
    { label: "Conversions",     value: data ? String(data.conversions || 0)                  : "—", color: "text-green-600" },
    { label: "Video Plays",     value: data ? Number(data.video_plays || 0).toLocaleString() : "—", color: "text-purple-600" },
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
        <button onClick={load} className="ml-auto text-slate-400 hover:text-brand-500">
          <RefreshCw size={15} className={loading ? "spinner" : ""} />
        </button>
      </div>

      {loading ? (
        <div className="grid grid-cols-3 gap-4">
          {Array.from({ length: 9 }).map((_, i) => (
            <div key={i} className="card p-5 animate-pulse">
              <div className="h-3 bg-slate-200 rounded w-20 mb-3" />
              <div className="h-6 bg-slate-200 rounded w-14" />
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-3 gap-4">
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
  const [status, setStatus]       = useState("CAMPAIGN_STATUS_ENABLE");
  const [notConfigured, setNotConfigured] = useState(false);

  const [insights, setInsights]   = useState<Array<Record<string, unknown>>>([]);
  const [insightDays, setInsightDays] = useState(7);

  const [editId, setEditId]       = useState<string | null>(null);
  const [budgetVal, setBudgetVal] = useState("");
  const [saving, setSaving]       = useState(false);
  const [savedId, setSavedId]     = useState<string | null>(null);
  const [togglingId, setTogglingId] = useState<string | null>(null);

  const loadCampaigns = useCallback(async () => {
    setLoading(true);
    setNotConfigured(false);
    try {
      const res = await api.tiktokAdsCampaigns(status);
      setCampaigns(res.campaigns || []);
      if (!res.campaigns || res.campaigns.length === 0) setNotConfigured(true);
    } catch {
      setNotConfigured(true);
    } finally {
      setLoading(false);
    }
  }, [status]);

  const loadInsights = useCallback(async () => {
    try {
      const res = await api.tiktokAdsCampaignInsights(insightDays);
      setInsights(res.rows || []);
    } catch {
      setInsights([]);
    }
  }, [insightDays]);

  useEffect(() => { loadCampaigns(); }, [loadCampaigns]);
  useEffect(() => { loadInsights(); }, [loadInsights]);

  const saveBudget = async (id: string) => {
    const val = parseFloat(budgetVal);
    if (!val || val <= 0) return;
    setSaving(true);
    try {
      await api.tiktokAdsUpdateBudget(id, val);
      setSavedId(id);
      setEditId(null);
      setTimeout(() => setSavedId(null), 3000);
      loadCampaigns();
    } catch { /* ignore */ } finally {
      setSaving(false);
    }
  };

  const toggleStatus = async (id: string, currentStatus: string) => {
    setTogglingId(id);
    try {
      const next = currentStatus.includes("ENABLE") ? "DISABLE" : "ENABLE";
      await api.tiktokAdsUpdateStatus(id, next as "ENABLE" | "DISABLE");
      loadCampaigns();
    } catch { /* ignore */ } finally {
      setTogglingId(null);
    }
  };

  const insightMap = Object.fromEntries(insights.map((r) => [String(r.campaign_id), r]));
  const isEnabled = (s: string) => s.includes("ENABLE") && !s.includes("DIS");

  return (
    <div className="space-y-5">
      <div className="flex items-center gap-3 flex-wrap">
        {[
          { value: "CAMPAIGN_STATUS_ENABLE",  label: "Đang chạy" },
          { value: "CAMPAIGN_STATUS_DISABLE", label: "Tạm dừng" },
          { value: "CAMPAIGN_STATUS_ALL",     label: "Tất cả" },
        ].map(({ value, label }) => (
          <button key={value} onClick={() => setStatus(value)}
            className={cn("px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors",
              status === value ? "bg-brand-50 border-brand-300 text-brand-700" : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
            )}>
            {label}
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
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Ngân sách</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Chi tiêu ({insightDays}d)</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">CTR</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-slate-500">Status</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Hành động</th>
              </tr>
            </thead>
            <tbody>
              {campaigns.map((c) => {
                const id = String(c.id || "");
                const cStatus = String(c.status || "");
                const budget = Number(c.budget_vnd || 0);
                const perf = insightMap[id];
                const enabled = isEnabled(cStatus);
                return (
                  <tr key={id} className="border-b border-slate-50 hover:bg-slate-50/50">
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-800 truncate max-w-[180px]">{String(c.name || "—")}</p>
                      <p className="text-xs text-slate-400">ID: {id}</p>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">{String(c.objective_label || c.objective || "—")}</td>
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
                            placeholder="VNĐ"
                          />
                          <button onClick={() => saveBudget(id)} disabled={saving} className="text-green-600 hover:text-green-700"><Check size={14} /></button>
                          <button onClick={() => setEditId(null)} className="text-slate-400 hover:text-slate-600"><X size={14} /></button>
                        </div>
                      ) : (
                        <span className="font-medium text-slate-800">{budget > 0 ? formatVND(budget) : "—"}</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right text-slate-600">
                      {perf ? formatVND(Number(perf.spend_vnd || 0)) : "—"}
                    </td>
                    <td className="px-4 py-3 text-right text-brand-600">
                      {perf ? `${perf.ctr || 0}%` : "—"}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={cn("text-xs px-2 py-0.5 rounded-full font-medium",
                        enabled ? "bg-green-50 text-green-700" : "bg-slate-100 text-slate-600"
                      )}>
                        {enabled ? "Đang chạy" : "Tạm dừng"}
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
                            enabled ? "text-amber-500 hover:text-amber-700 hover:bg-amber-50" : "text-green-500 hover:text-green-700 hover:bg-green-50"
                          )}
                        >
                          {togglingId === id
                            ? <div className="w-3 h-3 border-2 border-current border-t-transparent rounded-full spinner" />
                            : enabled ? <Pause size={13} /> : <Play size={13} />
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

      <div className="flex items-center gap-2">
        <p className="text-xs text-slate-500">Insight period:</p>
        {[7, 14, 30].map((d) => (
          <button key={d} onClick={() => setInsightDays(d)}
            className={cn("px-2 py-1 rounded border text-xs font-medium",
              insightDays === d ? "bg-brand-50 border-brand-300 text-brand-700" : "bg-white border-slate-200 text-slate-600"
            )}>
            {d}d
          </button>
        ))}
      </div>
    </div>
  );
}

// ─── Ad Groups Tab ────────────────────────────────────────────────────────────

function AdGroupsTab() {
  const [adgroups, setAdgroups] = useState<Array<Record<string, unknown>>>([]);
  const [insights, setInsights] = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading]   = useState(false);
  const [days, setDays]         = useState(7);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const [agRes, insRes] = await Promise.all([
          api.tiktokAdsAdgroups(),
          api.tiktokAdsAdgroupInsights(days),
        ]);
        setAdgroups(agRes.adgroups || []);
        setInsights(insRes.rows || []);
      } catch {
        setAdgroups([]);
      } finally {
        setLoading(false);
      }
    })();
  }, [days]);

  const insightMap = Object.fromEntries(insights.map((r) => [String(r.adgroup_id), r]));

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
      </div>
      {loading ? (
        <div className="card p-12 text-center text-slate-400 text-sm">Đang tải Ad Groups...</div>
      ) : adgroups.length === 0 ? (
        <NotConfiguredBanner />
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50">
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">Ad Group</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">Placement</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Budget</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Bid</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Chi tiêu</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">CTR</th>
                <th className="px-4 py-3 text-center text-xs font-semibold text-slate-500">Status</th>
              </tr>
            </thead>
            <tbody>
              {adgroups.map((g) => {
                const id = String(g.id || "");
                const perf = insightMap[id];
                return (
                  <tr key={id} className="border-b border-slate-50 hover:bg-slate-50/50">
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-800 truncate max-w-[180px]">{String(g.name || "—")}</p>
                      <p className="text-xs text-slate-400">ID: {id}</p>
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500">{String(g.placement_type || "—")}</td>
                    <td className="px-4 py-3 text-right text-slate-600">{Number(g.budget_vnd) > 0 ? formatVND(Number(g.budget_vnd)) : "—"}</td>
                    <td className="px-4 py-3 text-right text-slate-600">{Number(g.bid_price_vnd) > 0 ? formatVND(Number(g.bid_price_vnd)) : "—"}</td>
                    <td className="px-4 py-3 text-right text-slate-600">{perf ? formatVND(Number(perf.spend_vnd || 0)) : "—"}</td>
                    <td className="px-4 py-3 text-right text-brand-600">{perf ? `${perf.ctr || 0}%` : "—"}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={cn("text-xs px-2 py-0.5 rounded-full font-medium",
                        String(g.status).includes("ENABLE") ? "bg-green-50 text-green-700" : "bg-slate-100 text-slate-600"
                      )}>
                        {String(g.status || "—")}
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

// ─── Ads (Video) Tab ──────────────────────────────────────────────────────────

function AdsTab() {
  const [rows, setRows]       = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading] = useState(false);
  const [days, setDays]       = useState(7);
  const [notConfigured, setNotConfigured] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setNotConfigured(false);
    try {
      const res = await api.tiktokAdsAdInsights(days);
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
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">Ad ID</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Chi tiêu</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Impressions</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">CTR</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">CPC</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Video Plays</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">VTR (6s)</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">P100</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i} className="border-b border-slate-50 hover:bg-slate-50/50">
                  <td className="px-4 py-2 font-mono text-xs text-slate-600">{String(r.ad_id || "—")}</td>
                  <td className="px-4 py-2 text-right text-slate-600">{formatVND(Number(r.spend_vnd || 0))}</td>
                  <td className="px-4 py-2 text-right text-slate-600">{Number(r.impressions || 0).toLocaleString()}</td>
                  <td className="px-4 py-2 text-right text-brand-600">{String(r.ctr || 0)}%</td>
                  <td className="px-4 py-2 text-right text-orange-500">{r.cpc_vnd ? formatVND(Number(r.cpc_vnd)) : "—"}</td>
                  <td className="px-4 py-2 text-right text-slate-600">{Number(r.video_plays || 0).toLocaleString()}</td>
                  <td className="px-4 py-2 text-right">
                    <span className={cn("font-semibold",
                      Number(r.vtr_6s) >= 15 ? "text-green-600" : Number(r.vtr_6s) >= 10 ? "text-amber-500" : "text-red-500"
                    )}>
                      {String(r.vtr_6s || 0)}%
                    </span>
                  </td>
                  <td className="px-4 py-2 text-right text-purple-600">{Number(r.watched_p100 || 0).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── Audience Tab ─────────────────────────────────────────────────────────────

function AudienceTab() {
  const [rows, setRows]           = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading]     = useState(false);
  const [days, setDays]           = useState(30);
  const [breakdown, setBreakdown] = useState("age");
  const [notConfigured, setNotConfigured] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setNotConfigured(false);
    try {
      const res = await api.tiktokAdsAudience(days, breakdown);
      if (!res.rows || res.rows.length === 0) setNotConfigured(true);
      setRows(res.rows || []);
    } catch {
      setNotConfigured(true);
    } finally {
      setLoading(false);
    }
  }, [days, breakdown]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3 flex-wrap">
        {[
          { value: "age",      label: "Tuổi" },
          { value: "gender",   label: "Giới tính" },
          { value: "country",  label: "Quốc gia" },
          { value: "platform", label: "Platform" },
          { value: "device",   label: "Thiết bị" },
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
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 capitalize">{breakdown}</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Impressions</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Clicks</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">CTR</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Reach</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Chi tiêu</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={i} className="border-b border-slate-50 hover:bg-slate-50/50">
                  <td className="px-4 py-2 font-medium text-slate-700">{String(r[breakdown] || "—")}</td>
                  <td className="px-4 py-2 text-right text-slate-600">{Number(r.impressions || 0).toLocaleString()}</td>
                  <td className="px-4 py-2 text-right text-slate-600">{Number(r.clicks || 0).toLocaleString()}</td>
                  <td className="px-4 py-2 text-right text-brand-600">{String(r.ctr || 0)}%</td>
                  <td className="px-4 py-2 text-right text-indigo-600">{Number(r.reach || 0).toLocaleString()}</td>
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

// ─── Benchmark Tab ────────────────────────────────────────────────────────────

function BenchmarkTab() {
  const [industry, setIndustry] = useState("saas");
  const [data, setData]         = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading]   = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setData(await api.tiktokAdsBenchmark(industry) as Record<string, unknown>);
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
    { label: "VTR benchmark",     value: `${data.vtr || 0}%`,              desc: "Video Through Rate (6s)" },
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

export default function TikTokAdsPage() {
  const [tab, setTab] = useState<Tab>("overview");

  return (
    <div className="max-w-5xl space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-800">TikTok Ads</h1>
        <p className="text-sm text-slate-500 mt-1">
          Quản lý campaigns, theo dõi video performance, phân tích audience và benchmark ngành
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

      {tab === "overview"  && <OverviewTab />}
      {tab === "campaigns" && <CampaignsTab />}
      {tab === "adgroups"  && <AdGroupsTab />}
      {tab === "ads"       && <AdsTab />}
      {tab === "audience"  && <AudienceTab />}
      {tab === "benchmark" && <BenchmarkTab />}
    </div>
  );
}
