"use client";

import { useEffect, useState, useCallback } from "react";
import Link from "next/link";
import {
  MessageSquare, Pen, BarChart2, TrendingUp,
  AlertTriangle, CheckCircle, ArrowRight, Zap,
} from "lucide-react";
import { api } from "@/lib/api";
import { SpendPieChart } from "@/components/Charts";

// ─── KPI Card ─────────────────────────────────────────────────────────────────

function KPICard({
  label, value, sub, color,
}: {
  label: string; value: string; sub?: string; color: string;
}) {
  return (
    <div className="card p-5">
      <p className="text-sm text-slate-500 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
      {sub && <p className="text-xs text-slate-400 mt-1">{sub}</p>}
    </div>
  );
}

// ─── Quick Action ─────────────────────────────────────────────────────────────

function QuickAction({ href, icon: Icon, label, desc, color }: {
  href: string; icon: React.ElementType; label: string; desc: string; color: string;
}) {
  return (
    <Link href={href} className="card p-5 hover:shadow-md transition-shadow flex items-start gap-4 group">
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${color} flex-shrink-0`}>
        <Icon size={20} className="text-white" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-slate-800 text-sm">{label}</p>
        <p className="text-xs text-slate-500 mt-0.5">{desc}</p>
      </div>
      <ArrowRight size={16} className="text-slate-300 group-hover:text-brand-500 transition-colors mt-1 flex-shrink-0" />
    </Link>
  );
}

// ─── Main Dashboard ───────────────────────────────────────────────────────────

export default function DashboardPage() {
  const [apiStatus, setApiStatus] = useState<"checking" | "ok" | "error">("checking");
  const [agentCount, setAgentCount] = useState(0);
  const [adSpend, setAdSpend] = useState<Array<{ name: string; value: number }>>([]);

  const loadAdSpend = useCallback(async () => {
    try {
      const res = await api.unifiedAdsSummary(30);
      const configured = (res.platforms || []).filter((p: Record<string, unknown>) => p.configured && Number(p.spend_vnd) > 0);
      setAdSpend(configured.map((p: Record<string, unknown>) => ({
        name: String(p.platform),
        value: Number(p.spend_vnd),
      })));
    } catch {
      // No ads configured — hide chart
    }
  }, []);

  useEffect(() => {
    api.health()
      .then((data) => {
        setApiStatus("ok");
        setAgentCount(data.agents);
      })
      .catch(() => setApiStatus("error"));
    loadAdSpend();
  }, [loadAdSpend]);

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-slate-800">Dashboard</h1>
        <p className="text-slate-500 mt-1 text-sm">Trung tâm điều phối AI Marketing Agent FuviAI</p>
      </div>

      {/* API Status Banner */}
      <div className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium ${
        apiStatus === "ok"
          ? "bg-green-50 text-green-700 border border-green-200"
          : apiStatus === "error"
          ? "bg-red-50 text-red-700 border border-red-200"
          : "bg-slate-50 text-slate-600 border border-slate-200"
      }`}>
        {apiStatus === "ok" && <CheckCircle size={16} />}
        {apiStatus === "error" && <AlertTriangle size={16} />}
        {apiStatus === "checking" && (
          <div className="w-4 h-4 border-2 border-slate-400 border-t-transparent rounded-full spinner" />
        )}
        {apiStatus === "ok"
          ? `Backend API đang chạy — ${agentCount} AI Agents sẵn sàng`
          : apiStatus === "error"
          ? "Không kết nối được backend. Kiểm tra: python run.py"
          : "Đang kiểm tra kết nối API..."}
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label="AI Agents" value="12" sub="M1-M12 hoạt động" color="text-brand-600" />
        <KPICard label="API Routes" value="50+" sub="Tất cả phases" color="text-emerald-600" />
        <KPICard label="ROAS TB" value="4.2×" sub="Benchmark FuviAI" color="text-amber-600" />
        <KPICard label="Uptime" value="99.5%" sub="Target SLA" color="text-blue-600" />
      </div>

      {/* Ad Spend Chart */}
      {adSpend.length > 0 && (
        <SpendPieChart
          data={adSpend}
          title="Phân bổ ngân sách quảng cáo (30 ngày)"
          height={240}
        />
      )}

      {/* Quick Actions */}
      <div>
        <h2 className="text-base font-semibold text-slate-800 mb-3">Tác vụ nhanh</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <QuickAction
            href="/chat"
            icon={MessageSquare}
            label="Chat với AI Marketing Agent"
            desc="Hỏi đáp, tư vấn chiến lược marketing tiếng Việt"
            color="bg-brand-500"
          />
          <QuickAction
            href="/content"
            icon={Pen}
            label="Tạo Content đa nền tảng"
            desc="Facebook, TikTok, Zalo, Email — 1 click"
            color="bg-emerald-500"
          />
          <QuickAction
            href="/campaigns"
            icon={BarChart2}
            label="Phân tích Campaign CSV"
            desc="Upload CSV → 5 đề xuất cải thiện ngay"
            color="bg-amber-500"
          />
          <QuickAction
            href="/analytics"
            icon={TrendingUp}
            label="Social Listening & Trend"
            desc="Phát hiện trend, crisis alert, competitor scan"
            color="bg-purple-500"
          />
          <QuickAction
            href="/orchestrate"
            icon={Zap}
            label="Campaign Plan AI (Full)"
            desc="Multi-agent: Research → Content → Budget → Report"
            color="bg-rose-500"
          />
          <QuickAction
            href="/compliance"
            icon={AlertTriangle}
            label="Kiểm tra Compliance"
            desc="Rà soát Luật QC + NĐ 13/2023 trước khi đăng"
            color="bg-slate-600"
          />
        </div>
      </div>

      {/* Agent Map */}
      <div>
        <h2 className="text-base font-semibold text-slate-800 mb-3">Bản đồ 12 AI Agents</h2>
        <div className="card p-5">
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
            {[
              { id: "M1", name: "Content Agent", desc: "FB/TikTok/Zalo/Email", color: "bg-blue-50 text-blue-700" },
              { id: "M2", name: "Research Agent", desc: "Crawl + ChromaDB RAG", color: "bg-indigo-50 text-indigo-700" },
              { id: "M3", name: "Campaign Agent", desc: "CSV analysis, A/B test", color: "bg-amber-50 text-amber-700" },
              { id: "M4", name: "SEO Agent", desc: "Keywords, Meta, AEO", color: "bg-green-50 text-green-700" },
              { id: "M5", name: "Social Agent", desc: "Scheduler, auto-post", color: "bg-emerald-50 text-emerald-700" },
              { id: "M6", name: "Insight Agent", desc: "Sentiment VN, RFM, VOC", color: "bg-teal-50 text-teal-700" },
              { id: "M7", name: "Listening Agent", desc: "Trend + crisis alert", color: "bg-cyan-50 text-cyan-700" },
              { id: "M8", name: "Livestream Agent", desc: "Script, flash deal", color: "bg-rose-50 text-rose-700" },
              { id: "M9", name: "AdBudget Agent", desc: "Mùa vụ VN, ROAS", color: "bg-orange-50 text-orange-700" },
              { id: "M10", name: "Competitor Agent", desc: "Crawl + diff + strategy", color: "bg-red-50 text-red-700" },
              { id: "M11", name: "Personalize Agent", desc: "CLV, trigger, email", color: "bg-purple-50 text-purple-700" },
              { id: "M12", name: "Compliance Agent", desc: "NĐ 13/2023, Luật QC", color: "bg-slate-50 text-slate-700" },
            ].map(({ id, name, desc, color }) => (
              <div key={id} className={`rounded-lg p-3 ${color}`}>
                <span className="text-xs font-bold opacity-60">{id}</span>
                <p className="font-semibold text-sm mt-0.5">{name}</p>
                <p className="text-xs opacity-70 mt-0.5">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
