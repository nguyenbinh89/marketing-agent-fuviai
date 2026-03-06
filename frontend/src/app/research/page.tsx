"use client";

import { useState } from "react";
import { Search, TrendingUp, FileText, Globe, Copy, Check, RefreshCw } from "lucide-react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";

type Tab = "search" | "industry" | "keywords" | "seo";

const TABS: { value: Tab; label: string; icon: React.ElementType }[] = [
  { value: "search",   label: "Tìm kiếm thị trường", icon: Search },
  { value: "industry", label: "Nghiên cứu ngành",     icon: TrendingUp },
  { value: "keywords", label: "Từ khoá SEO",           icon: FileText },
  { value: "seo",      label: "Công cụ SEO",           icon: Globe },
];

const SEO_TOOLS = [
  { value: "outline",  label: "Content Outline" },
  { value: "meta",     label: "Meta Tags" },
  { value: "audit",    label: "SEO Audit" },
  { value: "landing",  label: "Landing Page SEO" },
];

function ResultBox({ text, label = "Kết quả" }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false);

  const copy = () => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="card flex flex-col" style={{ minHeight: 240 }}>
      <div className="flex items-center justify-between px-5 py-3 border-b border-slate-100">
        <span className="text-sm font-medium text-slate-700">{label}</span>
        <button
          onClick={copy}
          className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-brand-600 transition-colors"
        >
          {copied ? <Check size={13} className="text-green-500" /> : <Copy size={13} />}
          {copied ? "Đã copy" : "Copy"}
        </button>
      </div>
      <div className="flex-1 p-5 overflow-y-auto scrollbar-thin">
        <div
          className="prose-ai text-sm"
          dangerouslySetInnerHTML={{
            __html: text
              .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
              .replace(/### (.*)/g, "<h3 class='font-semibold text-slate-800 mt-3 mb-1'>$1</h3>")
              .replace(/## (.*)/g, "<h2 class='font-bold text-slate-900 mt-4 mb-2'>$1</h2>")
              .replace(/# (.*)/g, "<h1 class='font-bold text-slate-900 mt-4 mb-2 text-base'>$1</h1>")
              .replace(/---/g, "<hr class='my-3 border-slate-200'/>")
              .replace(/\n/g, "<br/>"),
          }}
        />
      </div>
    </div>
  );
}

// ─── Tab: Market Search ───────────────────────────────────────────────────────

function SearchTab() {
  const [query, setQuery]       = useState("");
  const [days, setDays]         = useState(7);
  const [result, setResult]     = useState("");
  const [loading, setLoading]   = useState(false);

  const run = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setResult("");
    try {
      const res = await api.searchMarket(query, days, 8);
      setResult(res.summary);
    } catch (err: unknown) {
      setResult(`❌ ${err instanceof Error ? err.message : "Lỗi"}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="card p-5 space-y-4">
        <div>
          <label className="text-sm font-medium text-slate-700 block mb-1.5">Từ khoá tìm kiếm</label>
          <input
            className="input"
            placeholder="VD: AI marketing Việt Nam 2026, FMCG trend SME..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && run()}
          />
        </div>
        <div>
          <label className="text-sm font-medium text-slate-700 block mb-1.5">
            Khoảng thời gian: <span className="text-brand-600 font-semibold">{days} ngày</span>
          </label>
          <input
            type="range" min={1} max={30} value={days}
            onChange={(e) => setDays(Number(e.target.value))}
            className="w-full accent-brand-500"
          />
          <div className="flex justify-between text-xs text-slate-400 mt-1">
            <span>1 ngày</span><span>30 ngày</span>
          </div>
        </div>
        <button
          onClick={run}
          disabled={!query.trim() || loading}
          className="btn-primary w-full flex items-center justify-center gap-2"
        >
          {loading
            ? <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full spinner" /> Đang tìm...</>
            : <><Search size={15} /> Tìm kiếm & Phân tích</>}
        </button>
      </div>
      {(loading || result) && (
        loading
          ? <div className="card p-8 flex items-center gap-3 text-slate-400 text-sm">
              <div className="w-4 h-4 border-2 border-brand-400 border-t-transparent rounded-full spinner" />
              AI đang tìm kiếm và tổng hợp thông tin thị trường...
            </div>
          : <ResultBox text={result} label="Kết quả tìm kiếm thị trường" />
      )}
    </div>
  );
}

// ─── Tab: Industry Research ───────────────────────────────────────────────────

const COMMON_ASPECTS = ["xu hướng", "cơ hội", "thách thức", "đối thủ chính", "insight người tiêu dùng", "quy mô thị trường"];

function IndustryTab() {
  const [industry, setIndustry] = useState("");
  const [aspects, setAspects]   = useState<string[]>(["xu hướng", "cơ hội", "thách thức"]);
  const [result, setResult]     = useState("");
  const [loading, setLoading]   = useState(false);

  const toggle = (a: string) =>
    setAspects((prev) => prev.includes(a) ? prev.filter((x) => x !== a) : [...prev, a]);

  const run = async () => {
    if (!industry.trim()) return;
    setLoading(true);
    setResult("");
    try {
      const res = await api.researchIndustry(industry, aspects.length ? aspects : undefined);
      setResult(res.analysis);
    } catch (err: unknown) {
      setResult(`❌ ${err instanceof Error ? err.message : "Lỗi"}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="card p-5 space-y-4">
        <div>
          <label className="text-sm font-medium text-slate-700 block mb-1.5">Ngành / lĩnh vực</label>
          <input
            className="input"
            placeholder="VD: F&B, FMCG, bất động sản, thương mại điện tử..."
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
          />
        </div>
        <div>
          <label className="text-sm font-medium text-slate-700 block mb-2">Khía cạnh phân tích</label>
          <div className="flex flex-wrap gap-2">
            {COMMON_ASPECTS.map((a) => (
              <button
                key={a}
                onClick={() => toggle(a)}
                className={cn(
                  "px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors",
                  aspects.includes(a)
                    ? "bg-brand-50 border-brand-300 text-brand-700"
                    : "bg-white border-slate-200 text-slate-500 hover:bg-slate-50"
                )}
              >
                {a}
              </button>
            ))}
          </div>
        </div>
        <button
          onClick={run}
          disabled={!industry.trim() || loading}
          className="btn-primary w-full flex items-center justify-center gap-2"
        >
          {loading
            ? <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full spinner" /> Đang nghiên cứu...</>
            : <><TrendingUp size={15} /> Nghiên cứu ngành</>}
        </button>
      </div>
      {(loading || result) && (
        loading
          ? <div className="card p-8 flex items-center gap-3 text-slate-400 text-sm">
              <div className="w-4 h-4 border-2 border-brand-400 border-t-transparent rounded-full spinner" />
              AI đang phân tích ngành {industry}...
            </div>
          : <ResultBox text={result} label={`Phân tích ngành: ${industry}`} />
      )}
    </div>
  );
}

// ─── Tab: Keyword Research ────────────────────────────────────────────────────

function KeywordsTab() {
  const [topic, setTopic]       = useState("");
  const [industry, setIndustry] = useState("");
  const [result, setResult]     = useState("");
  const [loading, setLoading]   = useState(false);

  const run = async () => {
    if (!topic.trim()) return;
    setLoading(true);
    setResult("");
    try {
      const res = await api.keywordResearch(topic, industry || undefined);
      setResult(res.keywords);
    } catch (err: unknown) {
      setResult(`❌ ${err instanceof Error ? err.message : "Lỗi"}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="card p-5 space-y-4">
        <div>
          <label className="text-sm font-medium text-slate-700 block mb-1.5">
            Chủ đề / sản phẩm <span className="text-red-500">*</span>
          </label>
          <input
            className="input"
            placeholder="VD: phần mềm quản lý bán hàng, trà sữa, du lịch Đà Lạt..."
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
          />
        </div>
        <div>
          <label className="text-sm font-medium text-slate-700 block mb-1.5">Ngành (tuỳ chọn)</label>
          <input
            className="input"
            placeholder="VD: F&B, SaaS, bất động sản..."
            value={industry}
            onChange={(e) => setIndustry(e.target.value)}
          />
        </div>
        <button
          onClick={run}
          disabled={!topic.trim() || loading}
          className="btn-primary w-full flex items-center justify-center gap-2"
        >
          {loading
            ? <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full spinner" /> Đang nghiên cứu...</>
            : <><FileText size={15} /> Nghiên cứu từ khoá</>}
        </button>
      </div>
      {(loading || result) && (
        loading
          ? <div className="card p-8 flex items-center gap-3 text-slate-400 text-sm">
              <div className="w-4 h-4 border-2 border-brand-400 border-t-transparent rounded-full spinner" />
              AI đang nghiên cứu từ khoá cho "{topic}"...
            </div>
          : <ResultBox text={result} label={`Từ khoá SEO: ${topic}`} />
      )}
    </div>
  );
}

// ─── Tab: SEO Tools ───────────────────────────────────────────────────────────

function SEOTab() {
  const [tool, setTool]         = useState("outline");
  const [result, setResult]     = useState("");
  const [loading, setLoading]   = useState(false);

  // Outline
  const [keyword, setKeyword]       = useState("");
  const [wordCount, setWordCount]   = useState(1500);
  const [contentType, setContentType] = useState("blog");

  // Meta tags
  const [pageTitle, setPageTitle]   = useState("");
  const [pageDesc, setPageDesc]     = useState("");
  const [pageType, setPageType]     = useState("article");

  // Audit
  const [auditContent, setAuditContent]   = useState("");
  const [auditKeyword, setAuditKeyword]   = useState("");

  // Landing page
  const [lpProduct, setLpProduct]   = useState("");
  const [lpKeyword, setLpKeyword]   = useState("");
  const [lpUsp, setLpUsp]           = useState("");

  const run = async () => {
    setLoading(true);
    setResult("");
    try {
      if (tool === "outline") {
        const res = await api.generateContentOutline(keyword, wordCount, contentType);
        setResult(res.outline);
      } else if (tool === "meta") {
        const res = await api.generateMetaTags(pageTitle, pageDesc, undefined, pageType);
        setResult(res.meta_tags);
      } else if (tool === "audit") {
        const res = await api.seoAudit(auditContent, auditKeyword);
        setResult(res.audit);
      } else if (tool === "landing") {
        const res = await api.generateLandingPageSeo(lpProduct, lpKeyword, lpUsp);
        setResult(res.seo_copy);
      }
    } catch (err: unknown) {
      setResult(`❌ ${err instanceof Error ? err.message : "Lỗi"}`);
    } finally {
      setLoading(false);
    }
  };

  const canRun =
    (tool === "outline" && keyword.trim()) ||
    (tool === "meta" && pageTitle.trim() && pageDesc.trim()) ||
    (tool === "audit" && auditContent.trim() && auditKeyword.trim()) ||
    (tool === "landing" && lpProduct.trim() && lpKeyword.trim());

  return (
    <div className="space-y-4">
      {/* Tool selector */}
      <div className="flex gap-2 flex-wrap">
        {SEO_TOOLS.map(({ value, label }) => (
          <button
            key={value}
            onClick={() => { setTool(value); setResult(""); }}
            className={cn(
              "px-4 py-2 rounded-lg border text-sm font-medium transition-colors",
              tool === value
                ? "bg-brand-50 border-brand-300 text-brand-700"
                : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
            )}
          >
            {label}
          </button>
        ))}
      </div>

      <div className="card p-5 space-y-4">
        {tool === "outline" && (
          <>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1.5">Từ khoá mục tiêu <span className="text-red-500">*</span></label>
              <input className="input" placeholder="VD: phần mềm quản lý bán hàng cho SME" value={keyword} onChange={(e) => setKeyword(e.target.value)} />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1.5">Số chữ mục tiêu</label>
                <select className="input" value={wordCount} onChange={(e) => setWordCount(Number(e.target.value))}>
                  {[800, 1200, 1500, 2000, 3000].map((n) => (
                    <option key={n} value={n}>{n.toLocaleString()} chữ</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1.5">Loại content</label>
                <select className="input" value={contentType} onChange={(e) => setContentType(e.target.value)}>
                  {["blog", "landing_page", "product_page", "guide"].map((t) => (
                    <option key={t} value={t}>{t}</option>
                  ))}
                </select>
              </div>
            </div>
          </>
        )}

        {tool === "meta" && (
          <>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1.5">Tiêu đề trang <span className="text-red-500">*</span></label>
              <input className="input" placeholder="VD: FuviAI — AI Marketing Agent cho SME Việt Nam" value={pageTitle} onChange={(e) => setPageTitle(e.target.value)} />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1.5">Mô tả trang <span className="text-red-500">*</span></label>
              <textarea className="textarea h-20" placeholder="Mô tả ngắn về nội dung trang..." value={pageDesc} onChange={(e) => setPageDesc(e.target.value)} />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1.5">Loại trang</label>
              <select className="input" value={pageType} onChange={(e) => setPageType(e.target.value)}>
                {["article", "product", "homepage", "landing_page", "category"].map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
          </>
        )}

        {tool === "audit" && (
          <>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1.5">Từ khoá mục tiêu <span className="text-red-500">*</span></label>
              <input className="input" placeholder="VD: phần mềm quản lý bán hàng" value={auditKeyword} onChange={(e) => setAuditKeyword(e.target.value)} />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1.5">Nội dung cần audit <span className="text-red-500">*</span></label>
              <textarea className="textarea h-36" placeholder="Dán nội dung bài viết / landing page cần kiểm tra SEO..." value={auditContent} onChange={(e) => setAuditContent(e.target.value)} />
            </div>
          </>
        )}

        {tool === "landing" && (
          <>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1.5">Sản phẩm / Dịch vụ <span className="text-red-500">*</span></label>
              <input className="input" placeholder="VD: FuviAI Marketing Agent" value={lpProduct} onChange={(e) => setLpProduct(e.target.value)} />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1.5">Từ khoá mục tiêu <span className="text-red-500">*</span></label>
              <input className="input" placeholder="VD: AI marketing automation Việt Nam" value={lpKeyword} onChange={(e) => setLpKeyword(e.target.value)} />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1.5">USP (Unique Selling Proposition)</label>
              <input className="input" placeholder="VD: ROI 4.2x, tiết kiệm 3h/ngày, 500+ doanh nghiệp tin dùng" value={lpUsp} onChange={(e) => setLpUsp(e.target.value)} />
            </div>
          </>
        )}

        <button
          onClick={run}
          disabled={!canRun || loading}
          className="btn-primary w-full flex items-center justify-center gap-2"
        >
          {loading
            ? <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full spinner" /> Đang tạo...</>
            : <><RefreshCw size={15} /> Tạo với AI</>}
        </button>
      </div>

      {(loading || result) && (
        loading
          ? <div className="card p-8 flex items-center gap-3 text-slate-400 text-sm">
              <div className="w-4 h-4 border-2 border-brand-400 border-t-transparent rounded-full spinner" />
              AI đang xử lý...
            </div>
          : <ResultBox text={result} label={SEO_TOOLS.find((t) => t.value === tool)?.label ?? "Kết quả"} />
      )}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function ResearchPage() {
  const [tab, setTab] = useState<Tab>("search");

  return (
    <div className="max-w-4xl space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-800">Nghiên cứu & SEO</h1>
        <p className="text-sm text-slate-500 mt-1">Tìm kiếm thị trường, phân tích ngành, nghiên cứu từ khoá và tối ưu SEO</p>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 bg-slate-100 p-1 rounded-xl w-fit">
        {TABS.map(({ value, label, icon: Icon }) => (
          <button
            key={value}
            onClick={() => setTab(value)}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all",
              tab === value
                ? "bg-white text-slate-800 shadow-sm"
                : "text-slate-500 hover:text-slate-700"
            )}
          >
            <Icon size={14} />
            {label}
          </button>
        ))}
      </div>

      {tab === "search"   && <SearchTab />}
      {tab === "industry" && <IndustryTab />}
      {tab === "keywords" && <KeywordsTab />}
      {tab === "seo"      && <SEOTab />}
    </div>
  );
}
