"use client";

/**
 * FuviAI — Reusable Chart Components (recharts v2)
 * SpendPieChart | PlatformBarChart | SentimentDonut | TrendAreaChart | MetricRadarChart
 */

import {
  PieChart, Pie, Cell, Tooltip as ReTooltip, Legend, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  AreaChart, Area,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from "recharts";
import { formatVND } from "@/lib/utils";

// ─── Colour palette ───────────────────────────────────────────────────────────

export const PLATFORM_COLORS: Record<string, string> = {
  "Google Ads":   "#4285F4",
  "Facebook Ads": "#1877F2",
  "TikTok Ads":   "#2D2D2D",
};

const SENTIMENT_COLORS = {
  positive: "#22c55e",
  negative: "#ef4444",
  neutral:  "#94a3b8",
};

const CHART_COLORS = [
  "#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#06b6d4",
];

// ─── Shared tooltip style ─────────────────────────────────────────────────────

const TooltipStyle = {
  backgroundColor: "#fff",
  border: "1px solid #e2e8f0",
  borderRadius: 8,
  fontSize: 12,
  boxShadow: "0 4px 6px -1px rgb(0 0 0 / .1)",
};

// ─── SpendPieChart ────────────────────────────────────────────────────────────

export interface SpendSlice {
  name: string;
  value: number;   // VNĐ
  pct?: number;
}

export function SpendPieChart({
  data,
  title = "Phân bổ ngân sách",
  height = 280,
}: {
  data: SpendSlice[];
  title?: string;
  height?: number;
}) {
  if (!data.length) return null;

  const colored = data.map((d, i) => ({
    ...d,
    color: PLATFORM_COLORS[d.name] || CHART_COLORS[i % CHART_COLORS.length],
  }));

  return (
    <div className="card p-5 space-y-2">
      <p className="text-sm font-semibold text-slate-700">{title}</p>
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Pie
            data={colored}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={95}
            paddingAngle={3}
            dataKey="value"
          >
            {colored.map((entry, i) => (
              <Cell key={i} fill={entry.color} />
            ))}
          </Pie>
          <ReTooltip
            contentStyle={TooltipStyle}
            formatter={(value: number, name: string) => [formatVND(value), name]}
          />
          <Legend
            iconType="circle"
            iconSize={8}
            formatter={(value) => <span className="text-xs text-slate-600">{value}</span>}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

// ─── PlatformBarChart ─────────────────────────────────────────────────────────

export interface PlatformBarData {
  metric: string;
  [platform: string]: number | string;
}

export function PlatformBarChart({
  data,
  platforms,
  title = "So sánh theo Platform",
  height = 260,
  formatValue,
}: {
  data: PlatformBarData[];
  platforms: string[];
  title?: string;
  height?: number;
  formatValue?: (v: number) => string;
}) {
  if (!data.length) return null;

  return (
    <div className="card p-5 space-y-2">
      <p className="text-sm font-semibold text-slate-700">{title}</p>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} barCategoryGap="30%" barGap={4}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
          <XAxis
            dataKey="metric"
            tick={{ fontSize: 11, fill: "#94a3b8" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "#94a3b8" }}
            axisLine={false}
            tickLine={false}
            tickFormatter={formatValue}
            width={55}
          />
          <ReTooltip
            contentStyle={TooltipStyle}
            formatter={(v: number, name: string) => [formatValue ? formatValue(v) : v, name]}
          />
          <Legend
            iconType="circle"
            iconSize={8}
            formatter={(value) => <span className="text-xs text-slate-600">{value}</span>}
          />
          {platforms.map((p, i) => (
            <Bar
              key={p}
              dataKey={p}
              fill={PLATFORM_COLORS[p] || CHART_COLORS[i % CHART_COLORS.length]}
              radius={[3, 3, 0, 0]}
            />
          ))}
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ─── SentimentDonut ───────────────────────────────────────────────────────────

export interface SentimentData {
  positive: number;
  negative: number;
  neutral: number;
}

export function SentimentDonut({
  data,
  title = "Phân tích Sentiment",
  height = 240,
}: {
  data: SentimentData;
  title?: string;
  height?: number;
}) {
  const total = data.positive + data.negative + data.neutral;
  if (total === 0) return null;

  const chartData = [
    { name: "Tích cực", value: data.positive, color: SENTIMENT_COLORS.positive },
    { name: "Tiêu cực", value: data.negative, color: SENTIMENT_COLORS.negative },
    { name: "Trung tính", value: data.neutral, color: SENTIMENT_COLORS.neutral },
  ].filter((d) => d.value > 0);

  const pct = (n: number) => Math.round((n / total) * 100);

  return (
    <div className="card p-5 space-y-2">
      <p className="text-sm font-semibold text-slate-700">{title}</p>
      <div className="flex items-center gap-6">
        <ResponsiveContainer width="50%" height={height}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={80}
              paddingAngle={2}
              dataKey="value"
            >
              {chartData.map((entry, i) => (
                <Cell key={i} fill={entry.color} />
              ))}
            </Pie>
            <ReTooltip
              contentStyle={TooltipStyle}
              formatter={(v: number, name: string) => [`${v} (${pct(v)}%)`, name]}
            />
          </PieChart>
        </ResponsiveContainer>

        <div className="flex-1 space-y-3">
          {[
            { key: "positive", label: "Tích cực", value: data.positive, color: "bg-green-500" },
            { key: "negative", label: "Tiêu cực", value: data.negative, color: "bg-red-400" },
            { key: "neutral",  label: "Trung tính", value: data.neutral, color: "bg-slate-300" },
          ].map(({ label, value, color }) => (
            <div key={label}>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-slate-600">{label}</span>
                <span className="font-semibold text-slate-700">{value} ({pct(value)}%)</span>
              </div>
              <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full ${color}`}
                  style={{ width: `${pct(value)}%` }}
                />
              </div>
            </div>
          ))}
          <p className="text-xs text-slate-400 pt-1">Tổng: {total} mẫu</p>
        </div>
      </div>
    </div>
  );
}

// ─── TrendAreaChart ───────────────────────────────────────────────────────────

export interface TrendPoint {
  date: string;
  [key: string]: number | string;
}

export function TrendAreaChart({
  data,
  lines,
  title = "Xu hướng",
  height = 260,
  formatValue,
}: {
  data: TrendPoint[];
  lines: Array<{ key: string; label: string; color: string }>;
  title?: string;
  height?: number;
  formatValue?: (v: number) => string;
}) {
  if (!data.length) return null;

  return (
    <div className="card p-5 space-y-2">
      <p className="text-sm font-semibold text-slate-700">{title}</p>
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={data}>
          <defs>
            {lines.map(({ key, color }) => (
              <linearGradient key={key} id={`grad-${key}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={color} stopOpacity={0.15} />
                <stop offset="95%" stopColor={color} stopOpacity={0} />
              </linearGradient>
            ))}
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: "#94a3b8" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "#94a3b8" }}
            axisLine={false}
            tickLine={false}
            tickFormatter={formatValue}
            width={55}
          />
          <ReTooltip
            contentStyle={TooltipStyle}
            formatter={(v: number, name: string) => [formatValue ? formatValue(v) : v, name]}
          />
          <Legend
            iconType="circle"
            iconSize={8}
            formatter={(value) => <span className="text-xs text-slate-600">{value}</span>}
          />
          {lines.map(({ key, label, color }) => (
            <Area
              key={key}
              type="monotone"
              dataKey={key}
              name={label}
              stroke={color}
              strokeWidth={2}
              fill={`url(#grad-${key})`}
              dot={false}
              activeDot={{ r: 4 }}
            />
          ))}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

// ─── MetricRadarChart ─────────────────────────────────────────────────────────

export interface RadarDataPoint {
  metric: string;
  [platform: string]: number | string;
}

export function MetricRadarChart({
  data,
  platforms,
  title = "Radar Chart",
  height = 280,
}: {
  data: RadarDataPoint[];
  platforms: Array<{ key: string; color: string }>;
  title?: string;
  height?: number;
}) {
  if (!data.length) return null;

  return (
    <div className="card p-5 space-y-2">
      <p className="text-sm font-semibold text-slate-700">{title}</p>
      <ResponsiveContainer width="100%" height={height}>
        <RadarChart data={data} cx="50%" cy="50%">
          <PolarGrid stroke="#e2e8f0" />
          <PolarAngleAxis
            dataKey="metric"
            tick={{ fontSize: 11, fill: "#94a3b8" }}
          />
          <PolarRadiusAxis
            angle={30}
            domain={[0, 100]}
            tick={{ fontSize: 10, fill: "#cbd5e1" }}
          />
          {platforms.map(({ key, color }) => (
            <Radar
              key={key}
              name={key}
              dataKey={key}
              stroke={color}
              fill={color}
              fillOpacity={0.12}
              strokeWidth={2}
            />
          ))}
          <ReTooltip contentStyle={TooltipStyle} />
          <Legend
            iconType="circle"
            iconSize={8}
            formatter={(value) => <span className="text-xs text-slate-600">{value}</span>}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}

// ─── SimpleBarChart ───────────────────────────────────────────────────────────

export function SimpleBarChart({
  data,
  dataKey,
  nameKey = "name",
  color = "#6366f1",
  title,
  height = 220,
  formatValue,
}: {
  data: Array<Record<string, unknown>>;
  dataKey: string;
  nameKey?: string;
  color?: string;
  title?: string;
  height?: number;
  formatValue?: (v: number) => string;
}) {
  if (!data.length) return null;

  return (
    <div className="card p-5 space-y-2">
      {title && <p className="text-sm font-semibold text-slate-700">{title}</p>}
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} layout="vertical" barCategoryGap="25%">
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
          <XAxis
            type="number"
            tick={{ fontSize: 11, fill: "#94a3b8" }}
            axisLine={false}
            tickLine={false}
            tickFormatter={formatValue}
          />
          <YAxis
            type="category"
            dataKey={nameKey}
            tick={{ fontSize: 11, fill: "#64748b" }}
            axisLine={false}
            tickLine={false}
            width={100}
          />
          <ReTooltip
            contentStyle={TooltipStyle}
            formatter={(v: number) => [formatValue ? formatValue(v) : v]}
          />
          <Bar dataKey={dataKey} fill={color} radius={[0, 3, 3, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
