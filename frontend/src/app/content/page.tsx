"use client";

import { useState } from "react";
import { Copy, RefreshCw, Check } from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

type Platform = "facebook" | "tiktok" | "zalo" | "email" | "campaign";

const TONES = [
  { value: "than_thien", label: "Thân thiện" },
  { value: "chuyen_nghiep", label: "Chuyên nghiệp" },
  { value: "genz", label: "Gen Z" },
];

const PLATFORMS: { value: Platform; label: string; color: string }[] = [
  { value: "facebook", label: "Facebook", color: "bg-blue-50 border-blue-300 text-blue-700" },
  { value: "tiktok", label: "TikTok", color: "bg-slate-50 border-slate-300 text-slate-700" },
  { value: "zalo", label: "Zalo OA", color: "bg-sky-50 border-sky-300 text-sky-700" },
  { value: "email", label: "Email", color: "bg-amber-50 border-amber-300 text-amber-700" },
  { value: "campaign", label: "Multi-platform", color: "bg-purple-50 border-purple-300 text-purple-700" },
];

export default function ContentPage() {
  const [platform, setPlatform] = useState<Platform>("facebook");
  const [product, setProduct] = useState("");
  const [tone, setTone] = useState("than_thien");
  const [extra, setExtra] = useState("");
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);

  const generate = async () => {
    if (!product.trim()) return;
    setLoading(true);
    setResult("");
    try {
      let content = "";
      if (platform === "facebook") {
        const res = await api.generateFacebook({ product, tone, key_benefit: extra });
        content = res.content;
      } else if (platform === "tiktok") {
        const res = await api.generateTikTok({ product, hook_style: extra || undefined });
        content = res.content;
      } else if (platform === "zalo") {
        const res = await api.generateZalo({ product, offer: extra || undefined });
        content = res.content;
      } else if (platform === "email") {
        const res = await api.generateEmail({ product, target_segment: extra || undefined });
        content = res.content;
      } else {
        const res = await api.generateCampaign({
          product,
          campaign_name: extra || "Campaign 2027",
          platforms: ["facebook", "zalo", "tiktok"],
        });
        content = Object.entries(res.content)
          .map(([p, c]) => `### ${p.toUpperCase()}\n${c}`)
          .join("\n\n---\n\n");
      }
      setResult(content);
    } catch (err: unknown) {
      setResult(`❌ Lỗi: ${err instanceof Error ? err.message : "Không xác định"}`);
    } finally {
      setLoading(false);
    }
  };

  const copyResult = () => {
    navigator.clipboard.writeText(result);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-800">Tạo Content</h1>
        <p className="text-sm text-slate-500 mt-1">AI viết content chuẩn bản ngữ cho từng nền tảng</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Form */}
        <div className="card p-5 space-y-4">
          {/* Platform selector */}
          <div>
            <label className="text-sm font-medium text-slate-700 block mb-2">Nền tảng</label>
            <div className="flex flex-wrap gap-2">
              {PLATFORMS.map(({ value, label, color }) => (
                <button
                  key={value}
                  onClick={() => setPlatform(value)}
                  className={cn(
                    "px-3 py-1.5 text-xs font-medium rounded-lg border transition-all",
                    platform === value ? color : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
                  )}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* Product */}
          <div>
            <label className="text-sm font-medium text-slate-700 block mb-1.5">
              Sản phẩm / Dịch vụ <span className="text-red-500">*</span>
            </label>
            <input
              className="input"
              placeholder="VD: FuviAI Marketing Agent — AI tự động hoá marketing"
              value={product}
              onChange={(e) => setProduct(e.target.value)}
            />
          </div>

          {/* Tone (only for Facebook) */}
          {platform === "facebook" && (
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1.5">Tone</label>
              <select className="input" value={tone} onChange={(e) => setTone(e.target.value)}>
                {TONES.map(({ value, label }) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>
            </div>
          )}

          {/* Extra context */}
          <div>
            <label className="text-sm font-medium text-slate-700 block mb-1.5">
              {platform === "facebook" ? "Lợi ích chính" :
               platform === "tiktok" ? "Hook style" :
               platform === "zalo" ? "Offer / Ưu đãi" :
               platform === "email" ? "Target segment" :
               "Tên chiến dịch"}
            </label>
            <input
              className="input"
              placeholder={
                platform === "facebook" ? "VD: Tiết kiệm 3 giờ/ngày" :
                platform === "tiktok" ? "VD: câu hỏi gây tò mò" :
                platform === "zalo" ? "VD: Giảm 30% trong tháng 3" :
                platform === "email" ? "VD: giám đốc marketing SME" :
                "VD: Ra mắt tháng 3/2027"
              }
              value={extra}
              onChange={(e) => setExtra(e.target.value)}
            />
          </div>

          <button
            onClick={generate}
            disabled={!product.trim() || loading}
            className="btn-primary w-full flex items-center justify-center gap-2"
          >
            {loading ? (
              <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full spinner" /> Đang tạo...</>
            ) : (
              <><RefreshCw size={15} /> Tạo Content</>
            )}
          </button>
        </div>

        {/* Result */}
        <div className="card flex flex-col" style={{ minHeight: 320 }}>
          <div className="flex items-center justify-between px-5 py-3 border-b border-slate-100">
            <span className="text-sm font-medium text-slate-700">Kết quả</span>
            {result && (
              <button
                onClick={copyResult}
                className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-brand-600 transition-colors"
              >
                {copied ? <Check size={13} className="text-green-500" /> : <Copy size={13} />}
                {copied ? "Đã copy" : "Copy"}
              </button>
            )}
          </div>
          <div className="flex-1 p-5 overflow-y-auto scrollbar-thin">
            {loading && (
              <div className="flex items-center gap-2 text-slate-400 text-sm">
                <div className="w-4 h-4 border-2 border-brand-400 border-t-transparent rounded-full spinner" />
                AI đang viết content...
              </div>
            )}
            {!loading && !result && (
              <p className="text-slate-400 text-sm">Content sẽ hiển thị ở đây sau khi tạo.</p>
            )}
            {!loading && result && (
              <div
                className="prose-ai text-sm"
                dangerouslySetInnerHTML={{
                  __html: result
                    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                    .replace(/### (.*)/g, "<h2>$1</h2>")
                    .replace(/---/g, "<hr/>")
                    .replace(/\n/g, "<br/>"),
                }}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
