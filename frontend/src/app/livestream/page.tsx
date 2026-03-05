"use client";

import { useState } from "react";
import { Radio, Users, Zap, MessageSquare, TrendingDown, PlayCircle, StopCircle } from "lucide-react";
import { cn, formatVND } from "@/lib/utils";

interface Session {
  session_id: string;
  product: string;
  platform: string;
  start_time: string;
  current_viewers: number;
  peak_viewers: number;
  revenue: number;
  phase: string;
}

interface Script {
  script: string;
  phase: string;
  tactic: string;
  urgency_level: string;
  flash_deal?: { name: string; discount: string; duration_minutes: number } | null;
}

const PLATFORMS = ["tiktok", "shopee", "facebook", "youtube"];
const PHASE_COLORS: Record<string, string> = {
  "WARM-UP": "bg-blue-100 text-blue-700",
  "BUILD-UP": "bg-amber-100 text-amber-700",
  "PEAK": "bg-orange-100 text-orange-700",
  "SUSTAIN": "bg-green-100 text-green-700",
  "CLOSE": "bg-red-100 text-red-700",
};

export default function LivestreamPage() {
  const [product, setProduct] = useState("");
  const [platform, setPlatform] = useState("tiktok");
  const [session, setSession] = useState<Session | null>(null);
  const [starting, setStarting] = useState(false);

  // Script generation
  const [currentViewers, setCurrentViewers] = useState("100");
  const [comments, setComments] = useState("");
  const [revenueSegment, setRevenueSegment] = useState("0");
  const [script, setScript] = useState<Script | null>(null);
  const [loadingScript, setLoadingScript] = useState(false);

  // Flash deal
  const [flashDeal, setFlashDeal] = useState<Script | null>(null);
  const [loadingDeal, setLoadingDeal] = useState(false);

  // Comment replies
  const [commentInput, setCommentInput] = useState("");
  const [replies, setReplies] = useState<Record<string, string>>({});
  const [loadingReplies, setLoadingReplies] = useState(false);

  const startSession = async () => {
    if (!product.trim()) return;
    setStarting(true);
    try {
      const res = await fetch("/api/commerce/livestream/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ product, platform }),
      });
      const data = await res.json();
      setSession(data.session || data);
    } catch {
      alert("Lỗi bắt đầu session");
    } finally {
      setStarting(false);
    }
  };

  const endSession = async () => {
    if (!session) return;
    try {
      await fetch(`/api/commerce/livestream/${session.session_id}/end`, { method: "POST" });
      setSession(null);
      setScript(null);
      setFlashDeal(null);
      setReplies({});
    } catch {
      setSession(null);
    }
  };

  const getNextScript = async () => {
    if (!session) return;
    setLoadingScript(true);
    try {
      const res = await fetch(`/api/commerce/livestream/${session.session_id}/next-script`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: session.session_id,
          current_viewers: parseInt(currentViewers) || 100,
          comments: comments.split("\n").filter(Boolean),
          revenue_this_segment: parseFloat(revenueSegment) || 0,
        }),
      });
      const data = await res.json();
      // backend returns { script: {...}, session: {...} }
      setScript(typeof data.script === "object" ? data.script : data);
    } catch {
      alert("Lỗi tạo script");
    } finally {
      setLoadingScript(false);
    }
  };

  const triggerFlashDeal = async () => {
    if (!session) return;
    setLoadingDeal(true);
    try {
      const res = await fetch(`/api/commerce/livestream/${session.session_id}/flash-deal`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: session.session_id,
          discount_percent: 20,
          slots: 10,
          duration_minutes: 10,
        }),
      });
      const data = await res.json();
      setFlashDeal(data);
    } catch {
      alert("Lỗi tạo flash deal");
    } finally {
      setLoadingDeal(false);
    }
  };

  const batchReply = async () => {
    const cmts = commentInput.split("\n").filter(Boolean);
    if (!cmts.length) return;
    setLoadingReplies(true);
    try {
      const res = await fetch("/api/commerce/livestream/batch-reply", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ comments: cmts, product_info: product }),
      });
      const data = await res.json();
      setReplies(data.replies || {});
    } catch {
      alert("Lỗi trả lời comment");
    } finally {
      setLoadingReplies(false);
    }
  };

  return (
    <div className="max-w-5xl space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-800 flex items-center gap-2">
          <Radio size={20} className="text-red-500" /> Livestream Coach
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          AI hỗ trợ realtime — script · flash deal · trả lời comment · phân tích viewer
        </p>
      </div>

      {/* Start / Stop */}
      <div className="card p-5 space-y-4">
        {!session ? (
          <>
            <h3 className="font-semibold text-slate-800">Bắt đầu phiên livestream</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <input
                className="input"
                placeholder="Sản phẩm livestream (VD: Son Kem Lì 3CE)"
                value={product}
                onChange={(e) => setProduct(e.target.value)}
              />
              <select className="input" value={platform} onChange={(e) => setPlatform(e.target.value)}>
                {PLATFORMS.map((p) => (
                  <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
                ))}
              </select>
            </div>
            <button
              onClick={startSession}
              disabled={!product.trim() || starting}
              className="btn-primary flex items-center gap-2"
            >
              <PlayCircle size={15} />
              {starting ? "Đang bắt đầu..." : "Bắt đầu Livestream"}
            </button>
          </>
        ) : (
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5 text-red-600 font-semibold text-sm">
                <Radio size={14} className="animate-pulse" /> LIVE
              </span>
              <span className="text-sm font-medium text-slate-800">{session.product}</span>
              <span className={cn("text-xs px-2 py-0.5 rounded-full font-medium", PHASE_COLORS[session.phase] || "bg-slate-100 text-slate-600")}>
                {session.phase}
              </span>
            </div>
            <div className="flex items-center gap-4 text-sm text-slate-600">
              <span className="flex items-center gap-1"><Users size={13} /> {session.current_viewers}</span>
              <span className="text-green-600 font-medium">{formatVND(session.revenue)}</span>
              <button onClick={endSession} className="btn-outline text-xs flex items-center gap-1.5 text-red-600 border-red-200 hover:bg-red-50">
                <StopCircle size={13} /> Kết thúc
              </button>
            </div>
          </div>
        )}
      </div>

      {session && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Script Generator */}
          <div className="card p-5 space-y-4">
            <h3 className="font-semibold text-slate-800 flex items-center gap-2">
              <MessageSquare size={15} className="text-brand-500" /> Script tiếp theo
            </h3>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-xs text-slate-500 block mb-1">Viewer hiện tại</label>
                <input
                  type="number"
                  className="input text-sm"
                  value={currentViewers}
                  onChange={(e) => setCurrentViewers(e.target.value)}
                />
              </div>
              <div>
                <label className="text-xs text-slate-500 block mb-1">Doanh thu segment (đ)</label>
                <input
                  type="number"
                  className="input text-sm"
                  value={revenueSegment}
                  onChange={(e) => setRevenueSegment(e.target.value)}
                />
              </div>
            </div>
            <div>
              <label className="text-xs text-slate-500 block mb-1">Comments mẫu (mỗi dòng 1 comment)</label>
              <textarea
                className="textarea h-20 text-xs"
                placeholder={"Bao nhiêu tiền?\nCó ship miễn phí không?\nMua được không?"}
                value={comments}
                onChange={(e) => setComments(e.target.value)}
              />
            </div>
            <button onClick={getNextScript} disabled={loadingScript} className="btn-primary w-full">
              {loadingScript ? "Đang tạo script..." : "Tạo Script"}
            </button>

            {script && (
              <div className="space-y-2">
                <div className="flex gap-2">
                  <span className={cn("text-xs px-2 py-0.5 rounded-full font-medium", PHASE_COLORS[script.phase] || "bg-slate-100 text-slate-600")}>
                    {script.phase}
                  </span>
                  <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">{script.tactic}</span>
                  <span className={cn("text-xs px-2 py-0.5 rounded-full",
                    script.urgency_level === "HIGH" ? "bg-red-100 text-red-600" :
                    script.urgency_level === "MEDIUM" ? "bg-amber-100 text-amber-600" :
                    "bg-green-100 text-green-600"
                  )}>
                    Urgency: {script.urgency_level}
                  </span>
                </div>
                <div className="bg-brand-50 rounded-lg p-3">
                  <p className="text-xs text-brand-800 leading-relaxed whitespace-pre-wrap">{script.script}</p>
                </div>
              </div>
            )}
          </div>

          {/* Flash Deal + Comment Reply */}
          <div className="space-y-4">
            {/* Flash Deal */}
            <div className="card p-5 space-y-3">
              <h3 className="font-semibold text-slate-800 flex items-center gap-2">
                <Zap size={15} className="text-amber-500" /> Flash Deal
              </h3>
              <button
                onClick={triggerFlashDeal}
                disabled={loadingDeal}
                className="btn-primary w-full flex items-center justify-center gap-2 bg-amber-500 hover:bg-amber-600"
              >
                <Zap size={14} />
                {loadingDeal ? "Đang tạo..." : "Kích hoạt Flash Deal"}
              </button>

              {flashDeal && (
                <div className="space-y-2">
                  {flashDeal.flash_deal && (
                    <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 text-sm">
                      <p className="font-semibold text-amber-800">{flashDeal.flash_deal.name}</p>
                      <p className="text-amber-700">Giảm {flashDeal.flash_deal.discount} · {flashDeal.flash_deal.duration_minutes} phút</p>
                    </div>
                  )}
                  <div className="bg-orange-50 rounded-lg p-3">
                    <p className="text-xs text-orange-800 leading-relaxed whitespace-pre-wrap">{flashDeal.script}</p>
                  </div>
                </div>
              )}
            </div>

            {/* Batch Reply */}
            <div className="card p-5 space-y-3">
              <h3 className="font-semibold text-slate-800 flex items-center gap-2">
                <TrendingDown size={15} className="text-rose-500" /> Trả lời Comment hàng loạt
              </h3>
              <textarea
                className="textarea h-20 text-xs"
                placeholder={"Giá bao nhiêu?\nCó size L không?\nShip HN mất mấy ngày?"}
                value={commentInput}
                onChange={(e) => setCommentInput(e.target.value)}
              />
              <button onClick={batchReply} disabled={loadingReplies || !commentInput.trim()} className="btn-outline w-full text-sm">
                {loadingReplies ? "Đang tạo..." : "Tạo reply hàng loạt"}
              </button>
              {Object.keys(replies).length > 0 && (
                <div className="space-y-2 max-h-48 overflow-y-auto scrollbar-thin">
                  {Object.entries(replies).map(([comment, reply]) => (
                    <div key={comment} className="text-xs border border-slate-100 rounded-lg p-2">
                      <p className="text-slate-500 mb-1">💬 {comment}</p>
                      <p className="text-slate-800">↩ {reply}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
