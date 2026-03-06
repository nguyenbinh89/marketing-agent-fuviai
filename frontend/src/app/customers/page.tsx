"use client";

import { useState } from "react";
import { Users, Upload, Mail, MessageSquare, RefreshCw, Send, CheckCircle, XCircle } from "lucide-react";
import { cn, formatVND } from "@/lib/utils";
import { api } from "@/lib/api";

const SAMPLE_CUSTOMERS = [
  { customer_id: "C001", name: "Nguyễn Văn An", email: "an@example.com", total_spent: 12000000, days_since_last_purchase: 5, purchase_count: 8 },
  { customer_id: "C002", name: "Trần Thị Bích", email: "bich@example.com", total_spent: 4500000, days_since_last_purchase: 20, purchase_count: 3 },
  { customer_id: "C003", name: "Lê Minh Cường", email: "cuong@example.com", total_spent: 800000, days_since_last_purchase: 60, purchase_count: 1 },
  { customer_id: "C004", name: "Phạm Thị Dung", email: "dung@example.com", total_spent: 25000000, days_since_last_purchase: 2, purchase_count: 15 },
  { customer_id: "C005", name: "Hoàng Văn Em", email: "em@example.com", total_spent: 200000, days_since_last_purchase: 120, purchase_count: 1 },
];

const TIER_CONFIG: Record<string, { label: string; color: string; bg: string; desc: string }> = {
  champion:  { label: "Champion",  color: "text-purple-700", bg: "bg-purple-50 border-purple-200", desc: "Mua nhiều, gần đây" },
  loyal:     { label: "Loyal",     color: "text-blue-700",   bg: "bg-blue-50 border-blue-200",     desc: "Trung thành, ổn định" },
  potential: { label: "Potential", color: "text-green-700",  bg: "bg-green-50 border-green-200",   desc: "Tiềm năng tăng trưởng" },
  at_risk:   { label: "At Risk",   color: "text-amber-700",  bg: "bg-amber-50 border-amber-200",   desc: "Nguy cơ rời bỏ" },
  lost:      { label: "Lost",      color: "text-red-700",    bg: "bg-red-50 border-red-200",       desc: "Đã mất" },
  new:       { label: "New",       color: "text-sky-700",    bg: "bg-sky-50 border-sky-200",       desc: "Khách hàng mới" },
};

interface Customer {
  customer_id: string;
  name: string;
  email: string;
  total_spent: number;
  days_since_last_purchase: number;
  purchase_count: number;
}

interface SegmentResult {
  customer_id: string;
  name: string;
  tier: string;
  strategy: string;
}

export default function CustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [segments, setSegments] = useState<SegmentResult[]>([]);
  const [loadingSegment, setLoadingSegment] = useState(false);

  const [selectedSegment, setSelectedSegment] = useState<string | null>(null);
  const [channel, setChannel] = useState<"email" | "zalo">("email");
  const [baseMessage, setBaseMessage] = useState("");
  const [variants, setVariants] = useState<Record<string, string>>({});
  const [loadingVariants, setLoadingVariants] = useState(false);

  const [selectedCustomer, setSelectedCustomer] = useState<SegmentResult | null>(null);
  const [personalMsg, setPersonalMsg] = useState("");
  const [loadingPersonal, setLoadingPersonal] = useState(false);

  const [sendingEmail, setSendingEmail] = useState(false);
  const [sendResult, setSendResult] = useState<{ success: boolean; msg: string } | null>(null);

  const [bulkSubject, setBulkSubject] = useState("");
  const [bulkMsg, setBulkMsg] = useState("");
  const [sendingBulk, setSendingBulk] = useState(false);
  const [bulkResult, setBulkResult] = useState<{ sent: number; failed: number } | null>(null);

  const loadSample = () => setCustomers(SAMPLE_CUSTOMERS);

  const segmentCustomers = async () => {
    if (!customers.length) return;
    setLoadingSegment(true);
    setSegments([]);
    try {
      const res = await fetch("/api/commerce/personalize/segment", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ customers }),
      });
      const data = await res.json();
      setSegments((data.segments as SegmentResult[]) || []);
    } catch {
      alert("Lỗi phân đoạn khách hàng");
    } finally {
      setLoadingSegment(false);
    }
  };

  const createVariants = async () => {
    if (!baseMessage.trim() || !selectedSegment) return;
    setLoadingVariants(true);
    setVariants({});
    try {
      const res = await fetch("/api/commerce/personalize/segment-variants", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          base_message: baseMessage,
          segments: [selectedSegment],
          channel,
        }),
      });
      const data = await res.json();
      setVariants(data.variants || {});
    } catch {
      alert("Lỗi tạo variants");
    } finally {
      setLoadingVariants(false);
    }
  };

  const personalizeMessage = async (customer: SegmentResult) => {
    setSelectedCustomer(customer);
    setLoadingPersonal(true);
    setPersonalMsg("");
    const full = customers.find((c) => c.customer_id === customer.customer_id);
    if (!full) return;
    try {
      const endpoint = channel === "email"
        ? "/api/commerce/personalize/email"
        : "/api/commerce/personalize/zalo";
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          customer: full,
          segment: customer.tier,
          product_context: "Sản phẩm FuviAI",
          trigger: "retention",
        }),
      });
      const data = await res.json();
      // email endpoint returns { email }, zalo returns { message }
      setPersonalMsg(data.email || data.message || data.content || "");
    } catch {
      setPersonalMsg("❌ Lỗi tạo tin nhắn cá nhân hoá");
    } finally {
      setLoadingPersonal(false);
    }
  };

  const sendEmail = async () => {
    if (!selectedCustomer || channel !== "email") return;
    const full = customers.find((c) => c.customer_id === selectedCustomer.customer_id);
    if (!full) return;
    setSendingEmail(true);
    setSendResult(null);
    try {
      const res = await api.sendPersonalizedEmail(
        full as Record<string, unknown>,
        selectedCustomer.tier,
        "nurture",
      );
      setSendResult({ success: res.success, msg: res.success ? `Đã gửi tới ${res.to}` : (res.error || "Lỗi không xác định") });
    } catch (e: unknown) {
      setSendResult({ success: false, msg: e instanceof Error ? e.message : "Lỗi gửi email" });
    } finally {
      setSendingEmail(false);
    }
  };

  const sendBulkEmail = async () => {
    if (!bulkMsg.trim() || !bulkSubject.trim() || !segments.length) return;
    setSendingBulk(true);
    setBulkResult(null);
    const enriched = segments.map((s) => {
      const full = customers.find((c) => c.customer_id === s.customer_id);
      return { ...(full as Record<string, unknown>), clv_tier: s.tier };
    });
    try {
      const res = await api.sendBulkEmail(enriched, bulkMsg, bulkSubject);
      setBulkResult({ sent: res.sent, failed: res.failed });
    } catch (e: unknown) {
      setBulkResult({ sent: 0, failed: segments.length });
    } finally {
      setSendingBulk(false);
    }
  };

  // Group segments by tier
  const tierGroups = segments.reduce<Record<string, SegmentResult[]>>((acc, s) => {
    if (!acc[s.tier]) acc[s.tier] = [];
    acc[s.tier].push(s);
    return acc;
  }, {});

  return (
    <div className="max-w-5xl space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-800 flex items-center gap-2">
          <Users size={20} className="text-brand-500" /> Khách hàng & CLV
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Phân đoạn CLV · Champion / Loyal / At Risk / Lost · Cá nhân hoá tin nhắn
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Data Input */}
        <div className="card p-5 space-y-4">
          <h3 className="font-semibold text-slate-800">Dữ liệu khách hàng</h3>

          <div className="flex gap-2">
            <button onClick={loadSample} className="btn-outline text-xs flex items-center gap-1.5">
              <Upload size={12} /> Dữ liệu mẫu
            </button>
            <span className="text-xs text-slate-400 self-center">
              {customers.length > 0 ? `${customers.length} khách hàng` : "Chưa có dữ liệu"}
            </span>
          </div>

          {customers.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-slate-500 border-b border-slate-100">
                    <th className="text-left py-1.5 pr-3">Tên</th>
                    <th className="text-right pr-3">Chi tiêu</th>
                    <th className="text-right pr-3">SL mua</th>
                    <th className="text-right">Ngày cuối</th>
                  </tr>
                </thead>
                <tbody>
                  {customers.map((c) => (
                    <tr key={c.customer_id} className="border-b border-slate-50">
                      <td className="py-1.5 pr-3 text-slate-700">{c.name}</td>
                      <td className="text-right pr-3 text-slate-600">{formatVND(c.total_spent)}</td>
                      <td className="text-right pr-3 text-slate-600">{c.purchase_count}</td>
                      <td className="text-right text-slate-500">{c.days_since_last_purchase}d</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <button
            onClick={segmentCustomers}
            disabled={!customers.length || loadingSegment}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            <RefreshCw size={14} className={cn(loadingSegment && "spinner")} />
            {loadingSegment ? "Đang phân đoạn..." : "Phân đoạn CLV"}
          </button>
        </div>

        {/* Segment Results */}
        <div className="card p-5 space-y-3">
          <h3 className="font-semibold text-slate-800">Kết quả phân đoạn</h3>

          {segments.length === 0 ? (
            <div className="text-center py-8 text-slate-400 text-sm">
              <Users size={32} className="mx-auto mb-2 opacity-30" />
              <p>Chạy phân đoạn để xem kết quả</p>
            </div>
          ) : (
            <div className="space-y-3">
              {Object.entries(TIER_CONFIG).map(([tier, cfg]) => {
                const group = tierGroups[tier] || [];
                if (!group.length) return null;
                return (
                  <div key={tier} className={cn("rounded-lg border p-3", cfg.bg)}>
                    <div className="flex items-center justify-between mb-2">
                      <span className={cn("text-xs font-bold", cfg.color)}>{cfg.label} ({group.length})</span>
                      <span className="text-xs text-slate-400">{cfg.desc}</span>
                    </div>
                    <div className="space-y-1">
                      {group.map((s) => (
                        <div key={s.customer_id} className="flex items-center justify-between">
                          <span className="text-xs text-slate-700">{s.name}</span>
                          <button
                            onClick={() => personalizeMessage(s)}
                            className="text-xs text-brand-600 hover:underline flex items-center gap-1"
                          >
                            {channel === "email" ? <Mail size={11} /> : <MessageSquare size={11} />}
                            Cá nhân hoá
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Personalized message */}
      {(selectedCustomer || loadingPersonal) && (
        <div className="card p-5 space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-slate-800">
              Tin nhắn cá nhân hoá — {selectedCustomer?.name}
              {selectedCustomer && (
                <span className={cn("ml-2 text-xs px-2 py-0.5 rounded-full font-medium",
                  TIER_CONFIG[selectedCustomer.tier]?.color,
                  TIER_CONFIG[selectedCustomer.tier]?.bg
                )}>
                  {TIER_CONFIG[selectedCustomer.tier]?.label}
                </span>
              )}
            </h3>
            <div className="flex gap-2">
              <button
                onClick={() => setChannel("email")}
                className={cn("text-xs px-2 py-1 rounded-lg border flex items-center gap-1",
                  channel === "email" ? "bg-brand-50 border-brand-300 text-brand-700" : "bg-white border-slate-200 text-slate-500"
                )}
              >
                <Mail size={11} /> Email
              </button>
              <button
                onClick={() => setChannel("zalo")}
                className={cn("text-xs px-2 py-1 rounded-lg border flex items-center gap-1",
                  channel === "zalo" ? "bg-sky-50 border-sky-300 text-sky-700" : "bg-white border-slate-200 text-slate-500"
                )}
              >
                <MessageSquare size={11} /> Zalo
              </button>
            </div>
          </div>

          {loadingPersonal ? (
            <p className="text-sm text-slate-400">AI đang tạo tin nhắn...</p>
          ) : personalMsg ? (
            <div className="space-y-3">
              <div className="bg-slate-50 rounded-lg p-4">
                <div
                  className="prose-ai text-sm"
                  dangerouslySetInnerHTML={{
                    __html: personalMsg
                      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                      .replace(/\n/g, "<br/>"),
                  }}
                />
              </div>
              {channel === "email" && (
                <div className="flex items-center gap-3">
                  <button
                    onClick={sendEmail}
                    disabled={sendingEmail}
                    className="btn-primary text-sm flex items-center gap-2"
                  >
                    <Send size={13} className={cn(sendingEmail && "spinner")} />
                    {sendingEmail ? "Đang gửi..." : "Gửi Email ngay"}
                  </button>
                  {sendResult && (
                    <span className={cn("text-xs flex items-center gap-1", sendResult.success ? "text-green-600" : "text-red-500")}>
                      {sendResult.success ? <CheckCircle size={13} /> : <XCircle size={13} />}
                      {sendResult.msg}
                    </span>
                  )}
                </div>
              )}
            </div>
          ) : null}
        </div>
      )}

      {/* Bulk Email */}
      {segments.length > 0 && (
        <div className="card p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-slate-800 flex items-center gap-2">
              <Send size={16} className="text-brand-500" /> Gửi Email hàng loạt
            </h3>
            <span className="text-xs text-slate-400">{segments.length} khách hàng</span>
          </div>
          <input
            className="input text-sm"
            placeholder="Tiêu đề email..."
            value={bulkSubject}
            onChange={(e) => setBulkSubject(e.target.value)}
          />
          <textarea
            className="textarea h-24 text-sm"
            placeholder="Nội dung gốc — AI tự tạo variant cho từng CLV tier (Champion / Loyal / Potential / At Risk)..."
            value={bulkMsg}
            onChange={(e) => setBulkMsg(e.target.value)}
          />
          <div className="flex items-center gap-3">
            <button
              onClick={sendBulkEmail}
              disabled={sendingBulk || !bulkMsg.trim() || !bulkSubject.trim()}
              className="btn-primary text-sm flex items-center gap-2"
            >
              <Send size={13} className={cn(sendingBulk && "spinner")} />
              {sendingBulk ? "Đang gửi..." : `Gửi tới ${segments.length} khách hàng`}
            </button>
            {bulkResult && (
              <span className={cn("text-xs flex items-center gap-1", bulkResult.failed === 0 ? "text-green-600" : "text-amber-600")}>
                <CheckCircle size={13} />
                Gửi thành công: {bulkResult.sent} · Lỗi: {bulkResult.failed}
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400">
            AI sẽ tạo biến thể nội dung phù hợp cho từng segment trước khi gửi qua SendGrid.
          </p>
        </div>
      )}

      {/* Segment Variants */}
      {segments.length > 0 && (
        <div className="card p-5 space-y-4">
          <h3 className="font-semibold text-slate-800">Tạo variants theo segment</h3>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <select
              className="input text-sm"
              value={selectedSegment || ""}
              onChange={(e) => setSelectedSegment(e.target.value)}
            >
              <option value="">Chọn segment</option>
              {Object.keys(tierGroups).map((tier) => (
                <option key={tier} value={tier}>{TIER_CONFIG[tier]?.label || tier}</option>
              ))}
            </select>
            <select className="input text-sm" value={channel} onChange={(e) => setChannel(e.target.value as "email" | "zalo")}>
              <option value="email">Email</option>
              <option value="zalo">Zalo</option>
            </select>
            <button
              onClick={createVariants}
              disabled={!selectedSegment || !baseMessage.trim() || loadingVariants}
              className="btn-primary text-sm"
            >
              {loadingVariants ? "Đang tạo..." : "Tạo Variants"}
            </button>
          </div>
          <textarea
            className="textarea h-24 text-sm"
            placeholder="Nhập tin nhắn gốc để AI biến thể theo từng segment..."
            value={baseMessage}
            onChange={(e) => setBaseMessage(e.target.value)}
          />

          {Object.keys(variants).length > 0 && (
            <div className="space-y-3">
              {Object.entries(variants).map(([seg, msg]) => (
                <div key={seg} className={cn("rounded-lg border p-3", TIER_CONFIG[seg]?.bg || "bg-slate-50 border-slate-200")}>
                  <p className={cn("text-xs font-bold mb-2", TIER_CONFIG[seg]?.color || "text-slate-600")}>
                    {TIER_CONFIG[seg]?.label || seg}
                  </p>
                  <div
                    className="prose-ai text-xs"
                    dangerouslySetInnerHTML={{
                      __html: msg
                        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                        .replace(/\n/g, "<br/>"),
                    }}
                  />
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
