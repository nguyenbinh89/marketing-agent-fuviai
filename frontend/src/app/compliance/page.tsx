"use client";

import { useState } from "react";
import { ShieldCheck, AlertTriangle, CheckCircle, XCircle, Wrench } from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

const VERDICT_CONFIG = {
  PASS:    { label: "PASS",    icon: CheckCircle,   color: "text-green-600", bg: "bg-green-50 border-green-200" },
  WARNING: { label: "WARNING", icon: AlertTriangle, color: "text-amber-600", bg: "bg-amber-50 border-amber-200" },
  FAIL:    { label: "FAIL",    icon: XCircle,       color: "text-red-600",   bg: "bg-red-50 border-red-200" },
};

const SAMPLE_CONTENT = [
  "FuviAI là phần mềm AI marketing số 1 Việt Nam. Đảm bảo tăng doanh thu 300% sau 30 ngày!",
  "FuviAI giúp bạn tự động hoá marketing, tiết kiệm 3 giờ/ngày. Dùng thử miễn phí 14 ngày.",
  "Chữa bệnh hiệu quả 100%, cam kết hoàn tiền mãi mãi nếu không hài lòng!",
];

export default function CompliancePage() {
  const [content, setContent] = useState("");
  const [platform, setPlatform] = useState("facebook");
  const [result, setResult] = useState<{
    verdict: string;
    risk_score: number;
    safe_to_publish: boolean;
    ai_analysis: string;
  } | null>(null);
  const [loadingCheck, setLoadingCheck] = useState(false);

  const [fixedContent, setFixedContent] = useState("");
  const [loadingFix, setLoadingFix] = useState(false);

  const checkCompliance = async () => {
    if (!content.trim()) return;
    setLoadingCheck(true);
    setResult(null);
    try {
      const res = await api.checkCompliance(content, platform);
      setResult(res);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : "Lỗi");
    } finally {
      setLoadingCheck(false);
    }
  };

  const fixContent = async () => {
    if (!content.trim()) return;
    setLoadingFix(true);
    setFixedContent("");
    try {
      const res = await fetch(`/api/commerce/compliance/fix`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content, platform }),
      });
      const data = await res.json();
      setFixedContent(data.fixed || "");
    } catch {
      setFixedContent("❌ Không sửa được. Thử lại sau.");
    } finally {
      setLoadingFix(false);
    }
  };

  const cfg = result ? VERDICT_CONFIG[result.verdict as keyof typeof VERDICT_CONFIG] : null;

  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-800">Kiểm tra Compliance</h1>
        <p className="text-sm text-slate-500 mt-1">
          Rà soát theo Luật Quảng cáo VN + Nghị định 13/2023/NĐ-CP trước khi đăng
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Input */}
        <div className="card p-5 space-y-4">
          <h3 className="font-semibold text-slate-800 flex items-center gap-2">
            <ShieldCheck size={16} className="text-brand-500" /> Content cần kiểm tra
          </h3>

          <select className="input" value={platform} onChange={(e) => setPlatform(e.target.value)}>
            {["facebook", "tiktok", "zalo", "google", "shopee"].map((p) => (
              <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>
            ))}
          </select>

          <textarea
            className="textarea h-36"
            placeholder="Nhập content cần kiểm tra compliance..."
            value={content}
            onChange={(e) => setContent(e.target.value)}
          />

          {/* Quick samples */}
          <div className="space-y-1">
            <p className="text-xs text-slate-500">Mẫu kiểm tra:</p>
            {SAMPLE_CONTENT.map((s, i) => (
              <button
                key={i}
                onClick={() => setContent(s)}
                className="block w-full text-left text-xs text-slate-600 hover:text-brand-600 truncate py-0.5"
              >
                {i + 1}. {s.slice(0, 60)}...
              </button>
            ))}
          </div>

          <div className="flex gap-2">
            <button
              onClick={checkCompliance}
              disabled={!content.trim() || loadingCheck}
              className="btn-primary flex-1"
            >
              {loadingCheck ? "Đang kiểm tra..." : "Kiểm tra Compliance"}
            </button>
            <button
              onClick={fixContent}
              disabled={!content.trim() || loadingFix}
              className="btn-outline flex items-center gap-1.5"
              title="Tự động sửa"
            >
              <Wrench size={14} />
              Sửa
            </button>
          </div>
        </div>

        {/* Result */}
        <div className="space-y-4">
          {/* Verdict */}
          {cfg && result && (
            <div className={cn("card p-5 border", cfg.bg)}>
              <div className="flex items-center gap-3 mb-3">
                <cfg.icon size={20} className={cfg.color} />
                <div>
                  <p className={cn("font-bold text-lg", cfg.color)}>{cfg.label}</p>
                  <p className="text-xs text-slate-500">
                    Risk score: {result.risk_score}/100 •{" "}
                    {result.safe_to_publish ? "✅ An toàn để đăng" : "❌ Không nên đăng"}
                  </p>
                </div>
              </div>
              {/* Risk bar */}
              <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                <div
                  className={cn("h-full rounded-full transition-all", {
                    "bg-green-500": result.risk_score < 30,
                    "bg-amber-500": result.risk_score >= 30 && result.risk_score < 70,
                    "bg-red-500": result.risk_score >= 70,
                  })}
                  style={{ width: `${result.risk_score}%` }}
                />
              </div>
              {/* AI analysis */}
              {result.ai_analysis && (
                <div className="mt-3 max-h-48 overflow-y-auto scrollbar-thin">
                  <div
                    className="prose-ai text-xs"
                    dangerouslySetInnerHTML={{
                      __html: result.ai_analysis
                        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                        .replace(/\n/g, "<br/>"),
                    }}
                  />
                </div>
              )}
            </div>
          )}

          {/* Fixed content */}
          {(loadingFix || fixedContent) && (
            <div className="card p-5">
              <p className="text-sm font-semibold text-slate-800 mb-2 flex items-center gap-2">
                <Wrench size={14} /> Content đã sửa
              </p>
              {loadingFix ? (
                <p className="text-sm text-slate-400">AI đang sửa...</p>
              ) : (
                <div className="bg-green-50 rounded-lg p-3 max-h-48 overflow-y-auto scrollbar-thin">
                  <div
                    className="prose-ai text-xs"
                    dangerouslySetInnerHTML={{
                      __html: fixedContent
                        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                        .replace(/\n/g, "<br/>"),
                    }}
                  />
                </div>
              )}
            </div>
          )}

          {/* Platform Policies Quick Ref */}
          <div className="card p-5">
            <p className="text-sm font-semibold text-slate-800 mb-3">Policy nhanh</p>
            <div className="space-y-2 text-xs text-slate-600">
              <p><span className="font-medium text-red-600">❌ FAIL ngay:</span> Cờ bạc, vũ khí, ma túy, scam, bôi nhọ</p>
              <p><span className="font-medium text-amber-600">⚠️ WARNING:</span> "Số 1", "đảm bảo 100%", claim y tế, cam kết vĩnh viễn</p>
              <p><span className="font-medium text-blue-600">📋 NĐ 13/2023:</span> Không thu thập CCCD/địa chỉ/y tế khi chưa có consent</p>
              <p><span className="font-medium text-green-600">✅ PASS:</span> Benefit rõ ràng, có disclaimer khi cần, CTA trung thực</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
