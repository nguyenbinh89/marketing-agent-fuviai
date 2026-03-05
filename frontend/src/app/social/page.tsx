"use client";

import { useState } from "react";
import { Calendar, Clock, Plus, Trash2, RefreshCw, Send } from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

const PLATFORMS = ["facebook", "tiktok", "zalo", "instagram"];

const PLATFORM_COLORS: Record<string, string> = {
  facebook: "bg-blue-100 text-blue-700 border-blue-200",
  tiktok: "bg-slate-100 text-slate-700 border-slate-200",
  zalo: "bg-sky-100 text-sky-700 border-sky-200",
  instagram: "bg-pink-100 text-pink-700 border-pink-200",
};

interface ScheduledPost {
  id: string;
  platform: string;
  content: string;
  scheduled_time: string;
  status: string;
}

export default function SocialPage() {
  const [platform, setPlatform] = useState("facebook");
  const [content, setContent] = useState("");
  const [scheduledTime, setScheduledTime] = useState("");
  const [posting, setPosting] = useState(false);
  const [scheduling, setScheduling] = useState(false);

  const [schedule, setSchedule] = useState<ScheduledPost[]>([]);
  const [loadingSchedule, setLoadingSchedule] = useState(false);

  const [weeklyLoading, setWeeklyLoading] = useState(false);
  const [weeklyPlan, setWeeklyPlan] = useState("");

  const loadSchedule = async () => {
    setLoadingSchedule(true);
    try {
      const res = await api.getSchedule();
      setSchedule(res.schedule || []);
    } catch {
      setSchedule([]);
    } finally {
      setLoadingSchedule(false);
    }
  };

  const schedulePost = async () => {
    if (!content.trim() || !scheduledTime) return;
    setScheduling(true);
    try {
      await fetch("/api/automation/social/schedule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ platform, content, scheduled_time: scheduledTime }),
      });
      setContent("");
      setScheduledTime("");
      await loadSchedule();
    } catch {
      alert("Lỗi lên lịch. Thử lại sau.");
    } finally {
      setScheduling(false);
    }
  };

  const postNow = async () => {
    if (!content.trim()) return;
    setPosting(true);
    try {
      await fetch("/api/automation/social/post-now", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ platform, content }),
      });
      alert("Đã đăng thành công!");
      setContent("");
    } catch {
      alert("Lỗi đăng bài. Thử lại sau.");
    } finally {
      setPosting(false);
    }
  };

  const generateWeeklyPlan = async () => {
    setWeeklyLoading(true);
    setWeeklyPlan("");
    try {
      const res = await api.weeklyPlan({ product: "FuviAI Marketing Agent" });
      setWeeklyPlan(res.content_plan || res.plan || "");
    } catch (err: unknown) {
      setWeeklyPlan(`❌ ${err instanceof Error ? err.message : "Lỗi"}`);
    } finally {
      setWeeklyLoading(false);
    }
  };

  // Default schedule time = next hour
  const defaultTime = () => {
    const d = new Date();
    d.setHours(d.getHours() + 1, 0, 0, 0);
    return d.toISOString().slice(0, 16);
  };

  return (
    <div className="max-w-5xl space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-800">Lên lịch Social</h1>
        <p className="text-sm text-slate-500 mt-1">Tự động đăng bài Facebook · TikTok · Zalo · Instagram</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Compose */}
        <div className="card p-5 space-y-4">
          <h3 className="font-semibold text-slate-800 flex items-center gap-2">
            <Send size={15} className="text-brand-500" /> Soạn & Đăng bài
          </h3>

          {/* Platform tabs */}
          <div className="flex gap-2 flex-wrap">
            {PLATFORMS.map((p) => (
              <button
                key={p}
                onClick={() => setPlatform(p)}
                className={cn(
                  "px-3 py-1.5 text-xs font-medium rounded-lg border transition-all capitalize",
                  platform === p
                    ? PLATFORM_COLORS[p]
                    : "bg-white border-slate-200 text-slate-500 hover:bg-slate-50"
                )}
              >
                {p.charAt(0).toUpperCase() + p.slice(1)}
              </button>
            ))}
          </div>

          <textarea
            className="textarea h-32"
            placeholder="Nhập nội dung bài đăng..."
            value={content}
            onChange={(e) => setContent(e.target.value)}
          />

          {/* Schedule time */}
          <div>
            <label className="text-sm font-medium text-slate-700 block mb-1.5 flex items-center gap-1.5">
              <Clock size={13} /> Thời gian đăng
            </label>
            <input
              type="datetime-local"
              className="input"
              value={scheduledTime || defaultTime()}
              onChange={(e) => setScheduledTime(e.target.value)}
            />
          </div>

          <div className="flex gap-2">
            <button
              onClick={postNow}
              disabled={!content.trim() || posting}
              className="btn-outline flex-1 text-sm flex items-center justify-center gap-1.5"
            >
              <Send size={13} />
              {posting ? "Đang đăng..." : "Đăng ngay"}
            </button>
            <button
              onClick={schedulePost}
              disabled={!content.trim() || !scheduledTime || scheduling}
              className="btn-primary flex-1 text-sm flex items-center justify-center gap-1.5"
            >
              <Calendar size={13} />
              {scheduling ? "Đang lên lịch..." : "Lên lịch"}
            </button>
          </div>
        </div>

        {/* Weekly Plan */}
        <div className="card p-5 space-y-4">
          <h3 className="font-semibold text-slate-800 flex items-center gap-2">
            <Calendar size={15} className="text-purple-500" /> Kế hoạch tuần
          </h3>
          <p className="text-xs text-slate-500">
            AI tạo lịch đăng bài 7 ngày phù hợp với ngành + thương hiệu
          </p>
          <button
            onClick={generateWeeklyPlan}
            disabled={weeklyLoading}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            <RefreshCw size={14} className={cn(weeklyLoading && "spinner")} />
            {weeklyLoading ? "Đang tạo..." : "Tạo kế hoạch tuần"}
          </button>

          {weeklyPlan && (
            <div className="bg-purple-50 rounded-lg p-3 max-h-64 overflow-y-auto scrollbar-thin">
              <div
                className="prose-ai text-xs"
                dangerouslySetInnerHTML={{
                  __html: weeklyPlan
                    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                    .replace(/\n/g, "<br/>"),
                }}
              />
            </div>
          )}
        </div>
      </div>

      {/* Schedule list */}
      <div className="card p-5">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-slate-800 flex items-center gap-2">
            <Clock size={15} className="text-slate-500" /> Bài đã lên lịch
          </h3>
          <button
            onClick={loadSchedule}
            disabled={loadingSchedule}
            className="btn-outline text-xs flex items-center gap-1.5"
          >
            <RefreshCw size={12} className={cn(loadingSchedule && "spinner")} />
            Tải lại
          </button>
        </div>

        {schedule.length === 0 ? (
          <div className="text-center py-8 text-slate-400 text-sm">
            <Calendar size={32} className="mx-auto mb-2 opacity-30" />
            <p>Chưa có bài nào được lên lịch.</p>
            <button onClick={loadSchedule} className="text-brand-500 hover:underline mt-1 text-xs">
              Tải lịch
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            {schedule.map((post) => (
              <div
                key={post.id}
                className="flex items-start gap-3 p-3 rounded-lg border border-slate-100 hover:bg-slate-50"
              >
                <span
                  className={cn(
                    "px-2 py-0.5 text-xs rounded-full border capitalize flex-shrink-0 mt-0.5",
                    PLATFORM_COLORS[post.platform] || "bg-slate-100 text-slate-600"
                  )}
                >
                  {post.platform}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-700 truncate">{post.content}</p>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {new Date(post.scheduled_time).toLocaleString("vi-VN")}
                  </p>
                </div>
                <span
                  className={cn(
                    "text-xs px-2 py-0.5 rounded-full flex-shrink-0",
                    post.status === "pending" ? "bg-amber-50 text-amber-600" :
                    post.status === "posted" ? "bg-green-50 text-green-600" :
                    "bg-red-50 text-red-600"
                  )}
                >
                  {post.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
