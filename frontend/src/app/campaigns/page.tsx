"use client";

import { useState } from "react";
import { BarChart2, DollarSign } from "lucide-react";
import { api } from "@/lib/api";
import { formatVND } from "@/lib/utils";

const SAMPLE_CSV = `ad_name,impressions,clicks,spend,conversions
Ad A - Awareness,50000,900,5000000,45
Ad B - Retarget,20000,600,3000000,62
Ad C - Lookalike,35000,420,4000000,28
Ad D - Interest,45000,540,6000000,38`;

export default function CampaignsPage() {
  const [csv, setCsv] = useState("");
  const [platform, setPlatform] = useState("facebook");
  const [analysis, setAnalysis] = useState("");
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);

  const [budgets, setBudgets] = useState<Record<string, string>>({
    facebook: "15000000",
    tiktok: "8000000",
    shopee: "5000000",
  });
  const [goal, setGoal] = useState("tối đa ROAS");
  const [season, setSeason] = useState("");
  const [budgetRec, setBudgetRec] = useState("");
  const [loadingBudget, setLoadingBudget] = useState(false);

  const analyzeCampaign = async () => {
    const content = csv.trim();
    if (!content) return;
    setLoadingAnalysis(true);
    setAnalysis("");
    try {
      const res = await api.analyzeCampaign(content, platform);
      setAnalysis(res.analysis);
    } catch (err: unknown) {
      setAnalysis(`❌ ${err instanceof Error ? err.message : "Lỗi"}`);
    } finally {
      setLoadingAnalysis(false);
    }
  };

  const optimizeBudget = async () => {
    const current_budget = Object.fromEntries(
      Object.entries(budgets).map(([k, v]) => [k, parseFloat(v) || 0])
    );
    setLoadingBudget(true);
    setBudgetRec("");
    try {
      const res = await api.optimizeBudget({ current_budget, goal, season: season || undefined });
      setBudgetRec(res.recommendation);
    } catch (err: unknown) {
      setBudgetRec(`❌ ${err instanceof Error ? err.message : "Lỗi"}`);
    } finally {
      setLoadingBudget(false);
    }
  };

  const SEASONS = [
    { value: "", label: "Không có mùa vụ" },
    { value: "tet", label: "Tết Nguyên Đán" },
    { value: "11_11", label: "11/11 Shopee" },
    { value: "black_friday", label: "Black Friday" },
    { value: "8_3", label: "8/3 Quốc tế Phụ nữ" },
    { value: "20_10", label: "20/10 Phụ nữ VN" },
  ];

  return (
    <div className="max-w-5xl space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-800">Phân tích Campaign</h1>
        <p className="text-sm text-slate-500 mt-1">Upload CSV → AI đưa ra 5 đề xuất cải thiện + tối ưu budget</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* CSV Analysis */}
        <div className="card p-5 space-y-4">
          <h3 className="font-semibold text-slate-800 flex items-center gap-2">
            <BarChart2 size={16} className="text-brand-500" /> Phân tích CSV Campaign
          </h3>
          <select className="input" value={platform} onChange={(e) => setPlatform(e.target.value)}>
            {["facebook", "google", "tiktok", "shopee"].map((p) => (
              <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
            ))}
          </select>
          <textarea
            className="textarea h-36 font-mono text-xs"
            placeholder={`Paste CSV data:\n${SAMPLE_CSV}`}
            value={csv}
            onChange={(e) => setCsv(e.target.value)}
          />
          <div className="flex gap-2">
            <button
              onClick={() => setCsv(SAMPLE_CSV)}
              className="btn-outline text-xs"
            >
              Load mẫu
            </button>
            <button
              onClick={analyzeCampaign}
              disabled={!csv.trim() || loadingAnalysis}
              className="btn-primary flex-1"
            >
              {loadingAnalysis ? "Đang phân tích..." : "Phân tích ngay"}
            </button>
          </div>
          {analysis && (
            <div className="bg-amber-50 rounded-lg p-3 max-h-64 overflow-y-auto scrollbar-thin">
              <div
                className="prose-ai text-xs"
                dangerouslySetInnerHTML={{
                  __html: analysis
                    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                    .replace(/\n/g, "<br/>"),
                }}
              />
            </div>
          )}
        </div>

        {/* Budget Optimizer */}
        <div className="card p-5 space-y-4">
          <h3 className="font-semibold text-slate-800 flex items-center gap-2">
            <DollarSign size={16} className="text-emerald-500" /> Tối ưu Budget
          </h3>
          {Object.keys(budgets).map((platform) => (
            <div key={platform} className="flex items-center gap-2">
              <span className="text-sm text-slate-600 w-24 flex-shrink-0 capitalize">{platform}</span>
              <input
                type="number"
                className="input flex-1 text-sm"
                value={budgets[platform]}
                onChange={(e) => setBudgets((prev) => ({ ...prev, [platform]: e.target.value }))}
              />
              <span className="text-xs text-slate-400">đ</span>
            </div>
          ))}
          <div className="text-xs text-slate-500 text-right">
            Tổng: {formatVND(Object.values(budgets).reduce((s, v) => s + (parseFloat(v) || 0), 0))}
          </div>
          <div className="flex gap-2">
            <input
              className="input flex-1 text-sm"
              placeholder="Mục tiêu (VD: tối đa ROAS)"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
            />
            <select className="input w-40 text-sm" value={season} onChange={(e) => setSeason(e.target.value)}>
              {SEASONS.map(({ value, label }) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </div>
          <button onClick={optimizeBudget} disabled={loadingBudget} className="btn-primary w-full">
            {loadingBudget ? "Đang tính toán..." : "Tối ưu Budget"}
          </button>
          {budgetRec && (
            <div className="bg-emerald-50 rounded-lg p-3 max-h-64 overflow-y-auto scrollbar-thin">
              <div
                className="prose-ai text-xs"
                dangerouslySetInnerHTML={{
                  __html: budgetRec
                    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                    .replace(/\n/g, "<br/>"),
                }}
              />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
