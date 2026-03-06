"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Bell, RefreshCw, AlertTriangle, CheckCircle, Info,
  ExternalLink, Zap, Settings, TrendingDown,
} from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

type Severity = "critical" | "warning" | "info";
type AlertType = "performance" | "budget" | "config" | "crisis" | "system";

interface Alert {
  id: string;
  type: AlertType;
  severity: Severity;
  title: string;
  message: string;
  platform: string | null;
  timestamp: string;
  action_url: string | null;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const SEVERITY_CONFIG: Record<Severity, {
  icon: React.ElementType;
  badge: string;
  border: string;
  bg: string;
  label: string;
}> = {
  critical: {
    icon: AlertTriangle,
    badge: "bg-red-100 text-red-700",
    border: "border-l-red-500",
    bg: "bg-red-50/40",
    label: "Nghiêm trọng",
  },
  warning: {
    icon: AlertTriangle,
    badge: "bg-amber-100 text-amber-700",
    border: "border-l-amber-400",
    bg: "bg-amber-50/30",
    label: "Cảnh báo",
  },
  info: {
    icon: Info,
    badge: "bg-blue-100 text-blue-600",
    border: "border-l-blue-400",
    bg: "",
    label: "Thông tin",
  },
};

const TYPE_ICONS: Record<AlertType, React.ElementType> = {
  performance: TrendingDown,
  budget: Zap,
  config: Settings,
  crisis: AlertTriangle,
  system: Info,
};

const PLATFORM_COLORS: Record<string, string> = {
  "Google Ads":   "bg-blue-500",
  "Facebook Ads": "bg-indigo-500",
  "TikTok Ads":   "bg-slate-800",
};

function formatTime(iso: string): string {
  try {
    return new Date(iso).toLocaleString("vi-VN", {
      day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

// ─── Alert Card ───────────────────────────────────────────────────────────────

function AlertCard({ alert }: { alert: Alert }) {
  const sev = SEVERITY_CONFIG[alert.severity] || SEVERITY_CONFIG.info;
  const SevIcon = sev.icon;
  const TypeIcon = TYPE_ICONS[alert.type] || Info;

  return (
    <div className={cn(
      "card border-l-4 p-4 space-y-2 transition-all",
      sev.border, sev.bg,
    )}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 flex-1 min-w-0">
          <SevIcon size={16} className={cn(
            "mt-0.5 flex-shrink-0",
            alert.severity === "critical" ? "text-red-500"
              : alert.severity === "warning" ? "text-amber-500"
              : "text-blue-500"
          )} />
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-slate-800 text-sm leading-tight">{alert.title}</p>
            <p className="text-xs text-slate-500 mt-1 leading-relaxed">{alert.message}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          <span className={cn("text-xs px-2 py-0.5 rounded-full font-medium", sev.badge)}>
            {sev.label}
          </span>
        </div>
      </div>

      <div className="flex items-center gap-3 pt-1">
        {alert.platform && (
          <div className="flex items-center gap-1.5">
            <div className={cn("w-1.5 h-1.5 rounded-full", PLATFORM_COLORS[alert.platform] || "bg-slate-400")} />
            <span className="text-xs text-slate-500">{alert.platform}</span>
          </div>
        )}
        <div className="flex items-center gap-1">
          <TypeIcon size={10} className="text-slate-400" />
          <span className="text-xs text-slate-400 capitalize">{alert.type}</span>
        </div>
        <span className="text-xs text-slate-400 ml-auto">{formatTime(alert.timestamp)}</span>
        {alert.action_url && (
          <Link
            href={alert.action_url}
            className="flex items-center gap-1 text-xs text-brand-500 hover:text-brand-700 font-medium"
          >
            Xem chi tiết <ExternalLink size={10} />
          </Link>
        )}
      </div>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function NotificationsPage() {
  const [alerts, setAlerts]         = useState<Alert[]>([]);
  const [loading, setLoading]       = useState(false);
  const [days, setDays]             = useState(30);
  const [filterSev, setFilterSev]   = useState<Severity | "all">("all");
  const [filterPlat, setFilterPlat] = useState<string>("all");

  const load = useCallback(async (refresh = false) => {
    setLoading(true);
    try {
      const data = refresh
        ? await api.notificationsCheck(days) as unknown as Alert[]
        : await api.notifications(days);
      setAlerts(data as Alert[]);
    } catch {
      setAlerts([]);
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => { load(); }, [load]);

  const platforms = ["all", ...Array.from(new Set(alerts.map((a) => a.platform).filter(Boolean) as string[]))];

  const filtered = alerts.filter((a) => {
    if (filterSev !== "all" && a.severity !== filterSev) return false;
    if (filterPlat !== "all" && a.platform !== filterPlat) return false;
    return true;
  });

  const counts = {
    critical: alerts.filter((a) => a.severity === "critical").length,
    warning:  alerts.filter((a) => a.severity === "warning").length,
    info:     alerts.filter((a) => a.severity === "info").length,
  };

  return (
    <div className="max-w-4xl space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            <Bell size={20} className="text-brand-500" />
            Notification Center
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Alerts tự động từ Google Ads, Facebook Ads, TikTok Ads — phát hiện bất thường campaign
          </p>
        </div>
        <button
          onClick={() => load(true)}
          disabled={loading}
          className="btn-primary flex items-center gap-2 flex-shrink-0"
        >
          <RefreshCw size={14} className={cn(loading && "spinner")} />
          Refresh
        </button>
      </div>

      {/* Summary KPIs */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: "Nghiêm trọng", value: counts.critical, color: "text-red-600",   bg: "bg-red-50",   border: "border-red-200" },
          { label: "Cảnh báo",     value: counts.warning,  color: "text-amber-600", bg: "bg-amber-50", border: "border-amber-200" },
          { label: "Thông tin",    value: counts.info,      color: "text-blue-600",  bg: "bg-blue-50",  border: "border-blue-200" },
        ].map(({ label, value, color, bg, border }) => (
          <div key={label} className={cn("card p-4 border", border, bg)}>
            <p className="text-xs text-slate-500">{label}</p>
            <p className={cn("text-3xl font-bold mt-1", color)}>{value}</p>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        {/* Day range */}
        <div className="flex gap-1">
          {[7, 14, 30, 90].map((d) => (
            <button key={d} onClick={() => setDays(d)}
              className={cn("px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors",
                days === d
                  ? "bg-brand-50 border-brand-300 text-brand-700"
                  : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
              )}>
              {d} ngày
            </button>
          ))}
        </div>

        <div className="w-px h-5 bg-slate-200" />

        {/* Severity filter */}
        {(["all", "critical", "warning", "info"] as const).map((s) => (
          <button key={s} onClick={() => setFilterSev(s)}
            className={cn("px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors",
              filterSev === s
                ? "bg-slate-800 border-slate-800 text-white"
                : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
            )}>
            {s === "all" ? "Tất cả" : SEVERITY_CONFIG[s]?.label || s}
          </button>
        ))}

        <div className="w-px h-5 bg-slate-200" />

        {/* Platform filter */}
        <select
          className="input text-xs py-1.5 w-40"
          value={filterPlat}
          onChange={(e) => setFilterPlat(e.target.value)}
        >
          <option value="all">Tất cả platform</option>
          {platforms.filter((p) => p !== "all").map((p) => (
            <option key={p} value={p}>{p}</option>
          ))}
        </select>

        <span className="ml-auto text-xs text-slate-400">
          {filtered.length} / {alerts.length} alerts
        </span>
      </div>

      {/* Alert list */}
      {loading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="card p-4 animate-pulse border-l-4 border-l-slate-200">
              <div className="h-3 bg-slate-200 rounded w-2/3 mb-2" />
              <div className="h-3 bg-slate-100 rounded w-full" />
            </div>
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <div className="card p-12 text-center space-y-3">
          <CheckCircle size={32} className="text-green-400 mx-auto" />
          <p className="font-semibold text-slate-700">Không có alerts nào</p>
          <p className="text-sm text-slate-400">
            {alerts.length === 0
              ? "Kết nối ít nhất 1 platform quảng cáo để nhận alerts tự động."
              : "Không có alert nào khớp với bộ lọc hiện tại."}
          </p>
          {alerts.length === 0 && (
            <Link href="/ads" className="btn-primary inline-flex items-center gap-2 mx-auto">
              Kết nối Platform <ExternalLink size={13} />
            </Link>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((alert) => (
            <AlertCard key={alert.id} alert={alert} />
          ))}
        </div>
      )}
    </div>
  );
}
