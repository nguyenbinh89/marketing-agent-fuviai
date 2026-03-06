"use client";

import { useState, useEffect, useCallback } from "react";
import {
  Settings, CheckCircle, AlertTriangle, ExternalLink,
  RefreshCw, Copy, Check, ChevronDown, ChevronRight,
  Cpu, Database, Megaphone, ShoppingBag, Search, Layers,
} from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

// ─── Types ────────────────────────────────────────────────────────────────────

interface Integration {
  id: string;
  name: string;
  description: string;
  configured: boolean;
  masked_value: string;
  env_vars: string[];
  action_url: string | null;
  docs_url: string | null;
  required: boolean;
}

interface Group {
  group: string;
  integrations: Integration[];
}

// ─── Group icons ──────────────────────────────────────────────────────────────

const GROUP_ICONS: Record<string, React.ElementType> = {
  "Core AI":           Cpu,
  "Infrastructure":    Database,
  "Quảng cáo":        Layers,
  "Social & Messaging":Megaphone,
  "Thương mại":       ShoppingBag,
  "Search & Research": Search,
};

// ─── Integration Card ─────────────────────────────────────────────────────────

function IntegrationCard({ integration }: { integration: Integration }) {
  const [expanded, setExpanded] = useState(!integration.configured);
  const [copied, setCopied]     = useState<string | null>(null);

  const copyVar = async (v: string) => {
    await navigator.clipboard.writeText(v);
    setCopied(v);
    setTimeout(() => setCopied(null), 1500);
  };

  return (
    <div className={cn(
      "border rounded-xl overflow-hidden transition-all",
      integration.configured ? "border-slate-200" : "border-amber-200"
    )}>
      {/* Header row */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 px-4 py-3 bg-white hover:bg-slate-50 text-left transition-colors"
      >
        {integration.configured ? (
          <CheckCircle size={16} className="text-green-500 flex-shrink-0" />
        ) : (
          <AlertTriangle size={16} className="text-amber-400 flex-shrink-0" />
        )}

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="text-sm font-semibold text-slate-800">{integration.name}</p>
            {integration.required && (
              <span className="text-[10px] bg-red-100 text-red-600 px-1.5 py-0.5 rounded-full font-medium">
                Bắt buộc
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 mt-0.5 truncate">{integration.description}</p>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          <span className={cn(
            "text-xs px-2 py-1 rounded-full font-medium",
            integration.configured
              ? "bg-green-50 text-green-700"
              : "bg-amber-50 text-amber-700"
          )}>
            {integration.configured ? "Đã kết nối" : "Chưa cấu hình"}
          </span>
          {expanded
            ? <ChevronDown size={14} className="text-slate-400" />
            : <ChevronRight size={14} className="text-slate-400" />
          }
        </div>
      </button>

      {/* Expanded detail */}
      {expanded && (
        <div className="px-4 pb-4 pt-1 bg-slate-50 border-t border-slate-100 space-y-3">
          {/* Masked value */}
          {integration.configured && integration.masked_value && (
            <p className="text-xs text-slate-500 font-mono">
              Key: <span className="text-slate-700">{integration.masked_value}</span>
            </p>
          )}

          {/* Env vars */}
          <div>
            <p className="text-xs font-semibold text-slate-600 mb-1.5">Biến môi trường (.env)</p>
            <div className="space-y-1">
              {integration.env_vars.map((v) => (
                <div key={v} className="flex items-center gap-2">
                  <code className={cn(
                    "flex-1 text-xs px-2 py-1 rounded font-mono",
                    integration.configured
                      ? "bg-green-50 text-green-800"
                      : "bg-amber-50 text-amber-800"
                  )}>
                    {v}=
                  </code>
                  <button
                    onClick={() => copyVar(v)}
                    className="p-1 text-slate-400 hover:text-slate-700 transition-colors"
                    title="Copy tên biến"
                  >
                    {copied === v
                      ? <Check size={12} className="text-green-500" />
                      : <Copy size={12} />
                    }
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Links */}
          <div className="flex gap-2 flex-wrap">
            {integration.action_url && (
              <a
                href={integration.action_url}
                className="flex items-center gap-1 text-xs text-brand-600 hover:text-brand-800 font-medium"
              >
                Mở trang <ExternalLink size={10} />
              </a>
            )}
            {integration.docs_url && (
              <a
                href={integration.docs_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1 text-xs text-slate-500 hover:text-slate-700"
              >
                Tài liệu API <ExternalLink size={10} />
              </a>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function SettingsPage() {
  const [data, setData]     = useState<{
    summary: { total: number; configured: number; not_configured: number; required_missing: number };
    groups: Group[];
    model: string; env: string; version: string;
  } | null>(null);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setData(await api.integrations());
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const summary = data?.summary;

  return (
    <div className="max-w-4xl space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-800 flex items-center gap-2">
            <Settings size={20} className="text-brand-500" />
            Settings & Integrations
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Trạng thái kết nối tất cả platform API — thêm env vars vào file <code className="text-xs bg-slate-100 px-1 py-0.5 rounded">.env</code> để kích hoạt
          </p>
        </div>
        <button onClick={load} disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 bg-white text-xs font-medium text-slate-600 hover:bg-slate-50 transition-colors"
        >
          <RefreshCw size={13} className={cn(loading && "spinner")} />
          Refresh
        </button>
      </div>

      {/* Summary KPIs */}
      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {[
            { label: "Tổng integrations",  value: summary.total,          color: "text-slate-700", bg: "" },
            { label: "Đã kết nối",         value: summary.configured,     color: "text-green-600", bg: "bg-green-50 border-green-200" },
            { label: "Chưa cấu hình",      value: summary.not_configured, color: "text-amber-600", bg: "bg-amber-50 border-amber-200" },
            { label: "Bắt buộc còn thiếu", value: summary.required_missing, color: "text-red-600", bg: "bg-red-50 border-red-200" },
          ].map(({ label, value, color, bg }) => (
            <div key={label} className={cn("card p-4 border", bg)}>
              <p className="text-xs text-slate-500">{label}</p>
              <p className={cn("text-3xl font-bold mt-1", color)}>{value}</p>
            </div>
          ))}
        </div>
      )}

      {/* System info */}
      {data && (
        <div className="card p-4 flex flex-wrap gap-4">
          {[
            { label: "Version",    value: data.version },
            { label: "Môi trường", value: data.env },
            { label: "AI Model",   value: data.model },
          ].map(({ label, value }) => (
            <div key={label} className="flex items-center gap-2">
              <span className="text-xs text-slate-400">{label}:</span>
              <code className="text-xs bg-slate-100 text-slate-700 px-2 py-0.5 rounded font-mono">{value}</code>
            </div>
          ))}
          <div className="ml-auto">
            <div className="flex items-center gap-1.5">
              <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
              <span className="text-xs text-slate-500">Backend online</span>
            </div>
          </div>
        </div>
      )}

      {/* Integration groups */}
      {loading ? (
        <div className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="card p-5 animate-pulse space-y-3">
              <div className="h-4 bg-slate-200 rounded w-32" />
              <div className="h-12 bg-slate-100 rounded" />
              <div className="h-12 bg-slate-100 rounded" />
            </div>
          ))}
        </div>
      ) : data ? (
        <div className="space-y-6">
          {data.groups.map(({ group, integrations }) => {
            const Icon = GROUP_ICONS[group] || Settings;
            const configuredCount = integrations.filter((i) => i.configured).length;

            return (
              <div key={group} className="space-y-2">
                {/* Group header */}
                <div className="flex items-center gap-2">
                  <Icon size={14} className="text-slate-400" />
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">{group}</p>
                  <span className="text-xs text-slate-400 ml-auto">
                    {configuredCount}/{integrations.length} kết nối
                  </span>
                </div>
                <div className="space-y-2">
                  {integrations.map((integration) => (
                    <IntegrationCard key={integration.id} integration={integration} />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="card p-10 text-center text-slate-400 text-sm">
          Không thể tải thông tin. Kiểm tra backend đang chạy.
        </div>
      )}

      {/* How to configure */}
      <div className="card p-5 space-y-3 bg-slate-50">
        <p className="text-sm font-semibold text-slate-700">Cách cấu hình</p>
        <ol className="space-y-2 text-xs text-slate-600 list-decimal list-inside leading-relaxed">
          <li>Mở file <code className="bg-white px-1 rounded">.env</code> ở thư mục gốc (copy từ <code className="bg-white px-1 rounded">.env.example</code>)</li>
          <li>Thêm giá trị cho các biến môi trường muốn kích hoạt</li>
          <li>Restart backend: <code className="bg-white px-1.5 py-0.5 rounded font-mono">uvicorn backend.api.main:app --reload</code></li>
          <li>Nhấn <strong>Refresh</strong> để kiểm tra lại trạng thái</li>
        </ol>
      </div>
    </div>
  );
}
