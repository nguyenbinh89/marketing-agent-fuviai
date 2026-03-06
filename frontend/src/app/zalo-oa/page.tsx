"use client";

import { useState, useEffect, useCallback } from "react";
import {
  MessageCircle, Users, Megaphone, Tag, Clock,
  RefreshCw, AlertTriangle, Send, Check,
} from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

type Tab = "overview" | "chats" | "message" | "broadcast" | "tags";

const TABS: { value: Tab; label: string; icon: React.ElementType }[] = [
  { value: "overview",   label: "Tổng quan",    icon: MessageCircle },
  { value: "chats",      label: "Hội thoại",    icon: Clock },
  { value: "message",    label: "Gửi tin nhắn", icon: Send },
  { value: "broadcast",  label: "Broadcast",    icon: Megaphone },
  { value: "tags",       label: "Tags",         icon: Tag },
];

function NotConfiguredBanner() {
  return (
    <div className="card p-6 flex items-start gap-4 bg-amber-50 border-amber-200">
      <AlertTriangle size={20} className="text-amber-500 flex-shrink-0 mt-0.5" />
      <div>
        <p className="font-semibold text-amber-800 text-sm">Zalo OA chưa được cấu hình</p>
        <p className="text-amber-700 text-xs mt-1 leading-relaxed">
          Thêm <code className="bg-amber-100 px-1 rounded">ZALO_OA_ACCESS_TOKEN</code> và{" "}
          <code className="bg-amber-100 px-1 rounded">ZALO_OA_SECRET</code> vào file{" "}
          <code className="bg-amber-100 px-1 rounded">.env</code>.{" "}
          Lấy token tại{" "}
          <span className="font-medium">developers.zalo.me → Official Account API</span>.
        </p>
      </div>
    </div>
  );
}

// ─── Overview Tab ─────────────────────────────────────────────────────────────

function OverviewTab() {
  const [info, setInfo]       = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);
  const [notConfigured, setNotConfigured] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setNotConfigured(false);
    try {
      const res = await api.zaloOAInfo();
      if ((res as Record<string, unknown>).error) {
        setNotConfigured(true);
      } else {
        setInfo(res as Record<string, unknown>);
      }
    } catch {
      setNotConfigured(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (notConfigured) return <NotConfiguredBanner />;

  return (
    <div className="space-y-5">
      <div className="flex justify-end">
        <button onClick={load} className="text-slate-400 hover:text-brand-500">
          <RefreshCw size={15} className={loading ? "spinner" : ""} />
        </button>
      </div>

      {loading ? (
        <div className="card p-8 animate-pulse space-y-4">
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-full bg-slate-200" />
            <div className="space-y-2">
              <div className="h-5 bg-slate-200 rounded w-40" />
              <div className="h-3 bg-slate-200 rounded w-24" />
            </div>
          </div>
        </div>
      ) : info ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
          {/* OA Profile card */}
          <div className="card p-5 col-span-1 space-y-4">
            <div className="flex items-center gap-3">
              {info.avatar ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={String(info.avatar)} alt="OA avatar" className="w-14 h-14 rounded-full object-cover" />
              ) : (
                <div className="w-14 h-14 rounded-full bg-brand-100 flex items-center justify-center">
                  <MessageCircle size={24} className="text-brand-500" />
                </div>
              )}
              <div>
                <p className="font-bold text-slate-800">{String(info.name || "Zalo OA")}</p>
                <p className="text-xs text-slate-500 mt-0.5">ID: {String(info.oa_id || "—")}</p>
                {info.is_verified && (
                  <span className="text-xs bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded-full font-medium mt-1 inline-block">
                    Đã xác minh
                  </span>
                )}
              </div>
            </div>
            {info.description && (
              <p className="text-xs text-slate-500 leading-relaxed">{String(info.description)}</p>
            )}
          </div>

          {/* Stats */}
          <div className="card p-5 col-span-1 lg:col-span-2">
            <p className="text-xs font-semibold text-slate-500 mb-4 uppercase tracking-wide">Thống kê</p>
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <p className="text-3xl font-bold text-brand-600">
                  {Number(info.num_follower || 0).toLocaleString()}
                </p>
                <p className="text-xs text-slate-500 mt-1 flex items-center justify-center gap-1">
                  <Users size={12} /> Followers
                </p>
              </div>
              <div className="text-center">
                <p className="text-3xl font-bold text-slate-700">
                  {info.oa_type === 1 ? "Enterprise" : info.oa_type === 0 ? "Business" : "—"}
                </p>
                <p className="text-xs text-slate-500 mt-1">Loại tài khoản</p>
              </div>
            </div>
          </div>
        </div>
      ) : null}

      {/* Followers quick list */}
      <FollowersList />
    </div>
  );
}

function FollowersList() {
  const [data, setData]       = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        setData(await api.zaloFollowers(0, 20));
      } catch {
        setData(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const followers: string[] = Array.isArray((data as Record<string, unknown>)?.data?.followers)
    ? ((data as Record<string, unknown>)?.data as Record<string, unknown>)?.followers as string[]
    : [];

  if (!data || loading) return null;

  return (
    <div className="card p-5 space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-sm font-semibold text-slate-700 flex items-center gap-2">
          <Users size={14} /> Followers gần đây
        </p>
        <p className="text-xs text-slate-400">
          Hiển thị {followers.length} / {String((data as Record<string, unknown>)?.data && ((data as Record<string, unknown>)?.data as Record<string, unknown>)?.total || 0)}
        </p>
      </div>
      {followers.length === 0 ? (
        <p className="text-xs text-slate-400 text-center py-4">Không có follower nào</p>
      ) : (
        <div className="space-y-1">
          {followers.slice(0, 10).map((uid, i) => (
            <div key={i} className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-slate-50">
              <div className="w-7 h-7 rounded-full bg-slate-200 flex items-center justify-center flex-shrink-0">
                <Users size={12} className="text-slate-400" />
              </div>
              <p className="text-xs text-slate-600 font-mono">{uid}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Chats Tab ────────────────────────────────────────────────────────────────

function ChatsTab() {
  const [chats, setChats]     = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading] = useState(false);
  const [notConfigured, setNotConfigured] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setNotConfigured(false);
    try {
      const res = await api.zaloChats(20);
      setChats(res.chats || []);
      if (res.chats.length === 0) setNotConfigured(true);
    } catch {
      setNotConfigured(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button onClick={load} className="text-slate-400 hover:text-brand-500">
          <RefreshCw size={15} className={loading ? "spinner" : ""} />
        </button>
      </div>

      {notConfigured ? <NotConfiguredBanner /> : loading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="card p-4 animate-pulse flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-slate-200 flex-shrink-0" />
              <div className="flex-1 space-y-2">
                <div className="h-3 bg-slate-200 rounded w-32" />
                <div className="h-3 bg-slate-200 rounded w-48" />
              </div>
            </div>
          ))}
        </div>
      ) : chats.length === 0 ? (
        <div className="card p-8 text-center text-slate-400 text-sm">Chưa có hội thoại nào</div>
      ) : (
        <div className="space-y-2">
          {chats.map((c, i) => (
            <div key={i} className="card p-4 flex items-center gap-3 hover:bg-slate-50/50 transition-colors">
              {c.avatar ? (
                // eslint-disable-next-line @next/next/no-img-element
                <img src={String(c.avatar)} alt="" className="w-10 h-10 rounded-full object-cover flex-shrink-0" />
              ) : (
                <div className="w-10 h-10 rounded-full bg-brand-100 flex items-center justify-center flex-shrink-0">
                  <Users size={16} className="text-brand-500" />
                </div>
              )}
              <div className="flex-1 min-w-0">
                <p className="font-medium text-slate-800 text-sm truncate">
                  {String(c.display_name || c.user_id || "Unknown")}
                </p>
                <p className="text-xs text-slate-500 truncate mt-0.5">
                  {String(c.last_message || "—")}
                </p>
              </div>
              {c.time && (
                <p className="text-xs text-slate-400 flex-shrink-0">
                  {new Date(Number(c.time)).toLocaleTimeString("vi-VN", { hour: "2-digit", minute: "2-digit" })}
                </p>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Message Tab ──────────────────────────────────────────────────────────────

function MessageTab() {
  const [userId, setUserId]   = useState("");
  const [message, setMessage] = useState("");
  const [mode, setMode]       = useState<"text" | "button">("text");
  const [buttons, setButtons] = useState([{ title: "", payload: "" }]);
  const [sending, setSending] = useState(false);
  const [result, setResult]   = useState<{ ok: boolean; text: string } | null>(null);

  const addButton = () => {
    if (buttons.length < 5) setButtons([...buttons, { title: "", payload: "" }]);
  };
  const removeButton = (i: number) => setButtons(buttons.filter((_, idx) => idx !== i));
  const updateButton = (i: number, field: "title" | "payload", val: string) =>
    setButtons(buttons.map((b, idx) => idx === i ? { ...b, [field]: val } : b));

  const send = async () => {
    if (!userId.trim() || !message.trim()) return;
    setSending(true);
    setResult(null);
    try {
      if (mode === "text") {
        await api.zaloSendText(userId, message);
      } else {
        const validButtons = buttons.filter((b) => b.title.trim());
        if (validButtons.length === 0) { setSending(false); return; }
        await api.zaloSendButton(userId, message, validButtons);
      }
      setResult({ ok: true, text: "Tin nhắn đã được gửi thành công!" });
      setMessage("");
    } catch (err: unknown) {
      setResult({ ok: false, text: err instanceof Error ? err.message : "Lỗi gửi tin nhắn" });
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="max-w-2xl space-y-5">
      <div className="card p-5 space-y-4">
        <h3 className="font-semibold text-slate-800 text-sm flex items-center gap-2">
          <Send size={14} /> Gửi tin nhắn 1:1
        </h3>

        <div>
          <label className="text-sm font-medium text-slate-700 block mb-1.5">User ID Zalo</label>
          <input
            className="input"
            placeholder="VD: 3746458011527527430"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
          />
          <p className="text-xs text-slate-400 mt-1">ID follower lấy từ webhook hoặc danh sách followers</p>
        </div>

        {/* Message type */}
        <div className="flex gap-2">
          {(["text", "button"] as const).map((m) => (
            <button key={m} onClick={() => setMode(m)}
              className={cn("px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors",
                mode === m ? "bg-brand-50 border-brand-300 text-brand-700" : "bg-white border-slate-200 text-slate-600"
              )}>
              {m === "text" ? "Văn bản" : "Có nút bấm"}
            </button>
          ))}
        </div>

        <div>
          <label className="text-sm font-medium text-slate-700 block mb-1.5">
            {mode === "button" ? "Tiêu đề / nội dung" : "Nội dung tin nhắn"}
            <span className="text-slate-400 font-normal ml-1">({message.length}/2000)</span>
          </label>
          <textarea
            className="input min-h-[100px] resize-none"
            placeholder={mode === "text" ? "Xin chào anh/chị! FuviAI thông báo..." : "Chọn một trong các tuỳ chọn sau:"}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            maxLength={2000}
          />
        </div>

        {/* Buttons */}
        {mode === "button" && (
          <div className="space-y-2">
            <p className="text-sm font-medium text-slate-700">Nút bấm (tối đa 5)</p>
            {buttons.map((b, i) => (
              <div key={i} className="flex gap-2 items-center">
                <input
                  className="input flex-1"
                  placeholder={`Nút ${i + 1}: tiêu đề`}
                  value={b.title}
                  onChange={(e) => updateButton(i, "title", e.target.value)}
                />
                <input
                  className="input w-32"
                  placeholder="Payload (tuỳ chọn)"
                  value={b.payload}
                  onChange={(e) => updateButton(i, "payload", e.target.value)}
                />
                {buttons.length > 1 && (
                  <button onClick={() => removeButton(i)} className="text-slate-400 hover:text-red-500">
                    ✕
                  </button>
                )}
              </div>
            ))}
            {buttons.length < 5 && (
              <button onClick={addButton} className="text-xs text-brand-500 hover:text-brand-700 font-medium">
                + Thêm nút
              </button>
            )}
          </div>
        )}

        <button
          onClick={send}
          disabled={sending || !userId.trim() || !message.trim()}
          className="btn-primary flex items-center gap-2"
        >
          {sending
            ? <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full spinner" /> Đang gửi...</>
            : <><Send size={14} /> Gửi tin nhắn</>
          }
        </button>

        {result && (
          <div className={cn("text-sm p-3 rounded-lg flex items-center gap-2",
            result.ok ? "bg-green-50 text-green-700" : "bg-red-50 text-red-600"
          )}>
            {result.ok ? <Check size={14} /> : <AlertTriangle size={14} />}
            {result.text}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Broadcast Tab ────────────────────────────────────────────────────────────

function BroadcastTab() {
  const [message, setMessage] = useState("");
  const [tagName, setTagName] = useState("");
  const [tags, setTags]       = useState<Array<{ name: string; total: number }>>([]);
  const [sending, setSending] = useState(false);
  const [result, setResult]   = useState<{ ok: boolean; text: string } | null>(null);

  useEffect(() => {
    api.zaloTags().then((res) => setTags(res.tags || [])).catch(() => {});
  }, []);

  const send = async () => {
    if (!message.trim()) return;
    setSending(true);
    setResult(null);
    try {
      const res = await api.zaloBroadcast(message, tagName || undefined);
      setResult({ ok: true, text: `Broadcast thành công đến ${res.target === "all" ? "tất cả followers" : `tag "${res.target}"`}!` });
      setMessage("");
    } catch (err: unknown) {
      setResult({ ok: false, text: err instanceof Error ? err.message : "Lỗi broadcast" });
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="max-w-2xl space-y-5">
      <div className="card p-5 space-y-4">
        <h3 className="font-semibold text-slate-800 text-sm flex items-center gap-2">
          <Megaphone size={14} /> Broadcast tin nhắn hàng loạt
        </h3>

        <div>
          <label className="text-sm font-medium text-slate-700 block mb-1.5">Gửi đến</label>
          <select
            className="input"
            value={tagName}
            onChange={(e) => setTagName(e.target.value)}
          >
            <option value="">Tất cả followers</option>
            {tags.map((t) => (
              <option key={t.name} value={t.name}>
                Tag: {t.name} ({t.total.toLocaleString()} người)
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-sm font-medium text-slate-700 block mb-1.5">
            Nội dung broadcast
            <span className="text-slate-400 font-normal ml-1">({message.length}/2000)</span>
          </label>
          <textarea
            className="input min-h-[120px] resize-none"
            placeholder="📢 Thông báo từ [Tên OA]: Chương trình khuyến mãi đặc biệt tháng 3..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            maxLength={2000}
          />
        </div>

        {/* Preview */}
        {message && (
          <div className="bg-slate-50 rounded-lg p-3 border border-slate-200">
            <p className="text-xs font-medium text-slate-500 mb-1">Preview:</p>
            <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">{message}</p>
          </div>
        )}

        <button
          onClick={send}
          disabled={sending || !message.trim()}
          className="btn-primary flex items-center gap-2"
        >
          {sending
            ? <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full spinner" /> Đang gửi...</>
            : <><Megaphone size={14} /> Broadcast</>
          }
        </button>

        {result && (
          <div className={cn("text-sm p-3 rounded-lg flex items-center gap-2",
            result.ok ? "bg-green-50 text-green-700" : "bg-red-50 text-red-600"
          )}>
            {result.ok ? <Check size={14} /> : <AlertTriangle size={14} />}
            {result.text}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Tags Tab ─────────────────────────────────────────────────────────────────

function TagsTab() {
  const [tags, setTags]       = useState<Array<{ name: string; total: number }>>([]);
  const [loading, setLoading] = useState(false);
  const [notConfigured, setNotConfigured] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setNotConfigured(false);
    try {
      const res = await api.zaloTags();
      setTags(res.tags || []);
      if (res.tags.length === 0) setNotConfigured(true);
    } catch {
      setNotConfigured(true);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const total = tags.reduce((s, t) => s + t.total, 0);

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button onClick={load} className="text-slate-400 hover:text-brand-500">
          <RefreshCw size={15} className={loading ? "spinner" : ""} />
        </button>
      </div>

      {notConfigured ? <NotConfiguredBanner /> : loading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="card p-4 animate-pulse">
              <div className="h-3 bg-slate-200 rounded w-20 mb-2" />
              <div className="h-5 bg-slate-200 rounded w-12" />
            </div>
          ))}
        </div>
      ) : tags.length === 0 ? (
        <div className="card p-8 text-center text-slate-400 text-sm">
          Chưa có tag nào. Tạo tag trong Zalo OA Manager.
        </div>
      ) : (
        <div className="space-y-4">
          <p className="text-sm text-slate-600">
            <span className="font-semibold text-slate-800">{tags.length}</span> tags,{" "}
            tổng <span className="font-semibold text-slate-800">{total.toLocaleString()}</span> followers có tag
          </p>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {tags.map((t) => (
              <div key={t.name} className="card p-4 space-y-2">
                <div className="flex items-center gap-1.5">
                  <Tag size={12} className="text-brand-400 flex-shrink-0" />
                  <p className="text-sm font-semibold text-slate-800 truncate">{t.name}</p>
                </div>
                <p className="text-xl font-bold text-brand-600">{t.total.toLocaleString()}</p>
                <p className="text-xs text-slate-400">followers</p>
                {/* Proportion bar */}
                <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-brand-400 rounded-full"
                    style={{ width: total > 0 ? `${Math.round(t.total / total * 100)}%` : "0%" }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function ZaloOAPage() {
  const [tab, setTab] = useState<Tab>("overview");

  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-800 flex items-center gap-2">
          <MessageCircle size={20} className="text-brand-500" />
          Zalo Official Account
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Quản lý OA, gửi tin nhắn cá nhân hoá, broadcast theo tag và theo dõi hội thoại
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
      {tab === "chats"     && <ChatsTab />}
      {tab === "message"   && <MessageTab />}
      {tab === "broadcast" && <BroadcastTab />}
      {tab === "tags"      && <TagsTab />}
    </div>
  );
}
