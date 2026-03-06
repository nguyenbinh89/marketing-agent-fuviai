/**
 * FuviAI Dashboard — API Client
 * Kết nối với FastAPI backend
 */

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

// ─── Health ─────────────────────────────────────────────────────────────────

export const api = {
  // Health
  health: () => request<{ status: string; version: string; agents: number }>("/health"),

  // ─── Chat ─────────────────────────────────────────────────────────────────
  chat: (sessionId: string, message: string) =>
    request<{ session_id: string; response: string; tokens_used: number }>(
      "/api/agents/chat",
      { method: "POST", body: JSON.stringify({ session_id: sessionId, message }) }
    ),

  getChatHistory: (sessionId: string) =>
    request<{ session_id: string; history: Array<{ role: string; content: string }> }>(
      `/api/agents/sessions/${sessionId}/history`
    ),

  clearSession: (sessionId: string) =>
    request(`/api/agents/sessions/${sessionId}`, { method: "DELETE" }),

  // ─── Content ──────────────────────────────────────────────────────────────
  generateFacebook: (payload: {
    product: string;
    tone?: string;
    target_audience?: string;
    key_benefit?: string;
    cta?: string;
  }) =>
    request<{ platform: string; content: string; tone: string }>(
      "/api/content/generate/facebook",
      { method: "POST", body: JSON.stringify(payload) }
    ),

  generateTikTok: (payload: { product: string; duration?: number; hook_style?: string }) =>
    request<{ platform: string; content: string }>(
      "/api/content/generate/tiktok",
      { method: "POST", body: JSON.stringify(payload) }
    ),

  generateZalo: (payload: { product: string; customer_name?: string; offer?: string; urgency?: string }) =>
    request<{ platform: string; content: string }>(
      "/api/content/generate/zalo",
      { method: "POST", body: JSON.stringify(payload) }
    ),

  generateEmail: (payload: { product: string; target_segment?: string; subject_style?: string }) =>
    request<{ platform: string; content: string }>(
      "/api/content/generate/email",
      { method: "POST", body: JSON.stringify(payload) }
    ),

  generateCampaign: (payload: { product: string; campaign_name: string; platforms: string[] }) =>
    request<{ product: string; campaign_name: string; content: Record<string, string> }>(
      "/api/content/generate/campaign",
      { method: "POST", body: JSON.stringify(payload) }
    ),

  // ─── Insight / Sentiment ──────────────────────────────────────────────────
  analyzeSentiment: (texts: string[]) =>
    request<{
      summary: { positive: number; negative: number; neutral: number; total: number };
      top_positive: string[];
      top_negative: string[];
      ai_insight: string;
    }>("/api/automation/insight/sentiment", {
      method: "POST",
      body: JSON.stringify({ texts }),
    }),

  crisisCheck: (texts: string[]) =>
    request<{
      is_crisis: boolean;
      severity: string;
      negative_ratio: number;
      negative_count: number;
      total: number;
    }>("/api/automation/insight/crisis-check", {
      method: "POST",
      body: JSON.stringify({ texts }),
    }),

  // ─── Campaign ─────────────────────────────────────────────────────────────
  analyzeCampaign: (csvContent: string, platform: string = "facebook") =>
    request<{ platform: string; analysis: string }>(
      "/api/automation/campaign/analyze",
      { method: "POST", body: JSON.stringify({ csv_content: csvContent, platform }) }
    ),

  optimizeBudget: (payload: { current_budget: Record<string, number>; goal?: string; season?: string }) =>
    request<{ goal: string; recommendation: string }>(
      "/api/automation/campaign/optimize-budget",
      { method: "POST", body: JSON.stringify(payload) }
    ),

  // ─── Analytics / Competitor ───────────────────────────────────────────────
  getCompetitorsDashboard: () =>
    request<{ total_competitors: number; competitors: unknown[]; last_scan: string }>(
      "/api/analytics/competitors"
    ),

  addCompetitor: (payload: { name: string; website: string; facebook_page?: string; industry?: string }) =>
    request("/api/analytics/competitors/add", {
      method: "POST",
      body: JSON.stringify(payload),
    }),

  counterStrategy: (payload: { competitor_name: string; trigger_event: string; budget?: number }) =>
    request<{ competitor: string; trigger: string; strategy: string }>(
      "/api/analytics/competitors/counter-strategy",
      { method: "POST", body: JSON.stringify(payload) }
    ),

  scanTrends: (industry: string = "marketing", hoursBack: number = 24) =>
    request<{
      industry: string;
      articles_found: number;
      sentiment: Record<string, number>;
      trend_analysis: string;
      crisis_risk: { is_crisis: boolean; severity: string };
      scan_time: string;
    }>("/api/analytics/listening/scan", {
      method: "POST",
      body: JSON.stringify({ industry, hours_back: hoursBack }),
    }),

  // ─── Research & SEO ───────────────────────────────────────────────────────
  keywordResearch: (topic: string, industry?: string) =>
    request<{ topic: string; keywords: string }>(
      "/api/research/keywords",
      { method: "POST", body: JSON.stringify({ topic, industry }) }
    ),

  searchMarket: (query: string, days: number = 7, maxResults: number = 8) =>
    request<{ query: string; days: number; summary: string }>(
      "/api/research/search",
      { method: "POST", body: JSON.stringify({ query, days, max_results: maxResults }) }
    ),

  researchIndustry: (industry: string, aspects?: string[]) =>
    request<{ industry: string; analysis: string }>(
      "/api/research/industry",
      { method: "POST", body: JSON.stringify({ industry, aspects }) }
    ),

  marketReport: (industry: string = "tổng quan") =>
    request<{ industry: string; report: string }>(
      "/api/research/market-report",
      { method: "POST", body: JSON.stringify({ industry }) }
    ),

  summarizeUrl: (url: string) =>
    request<{ url: string; summary: string }>(
      "/api/research/summarize-url",
      { method: "POST", body: JSON.stringify({ url }) }
    ),

  generateMetaTags: (pageTitle: string, pageDescription: string, keywords?: string[], pageType?: string) =>
    request<{ meta_tags: string }>(
      "/api/research/seo/meta-tags",
      { method: "POST", body: JSON.stringify({ page_title: pageTitle, page_description: pageDescription, keywords, page_type: pageType || "article" }) }
    ),

  generateContentOutline: (keyword: string, wordCount?: number, contentType?: string) =>
    request<{ keyword: string; outline: string }>(
      "/api/research/seo/content-outline",
      { method: "POST", body: JSON.stringify({ keyword, word_count: wordCount || 1500, content_type: contentType || "blog" }) }
    ),

  seoAudit: (content: string, targetKeyword: string) =>
    request<{ keyword: string; audit: string }>(
      "/api/research/seo/audit",
      { method: "POST", body: JSON.stringify({ content, target_keyword: targetKeyword }) }
    ),

  generateLandingPageSeo: (product: string, targetKeyword: string, usp?: string) =>
    request<{ product: string; seo_copy: string }>(
      "/api/research/seo/landing-page",
      { method: "POST", body: JSON.stringify({ product, target_keyword: targetKeyword, usp: usp || "" }) }
    ),

  // ─── Compliance ───────────────────────────────────────────────────────────
  checkCompliance: (content: string, platform: string = "facebook") =>
    request<{ verdict: string; risk_score: number; safe_to_publish: boolean; ai_analysis: string }>(
      "/api/commerce/compliance/check",
      { method: "POST", body: JSON.stringify({ content, platform }) }
    ),

  // ─── Social Scheduling ────────────────────────────────────────────────────
  getSchedule: () =>
    request<{ schedule: Array<{ id: string; platform: string; content: string; scheduled_time: string; status: string }> }>(
      "/api/automation/social/schedule"
    ),

  weeklyPlan: (payload: { product?: string; platforms?: string[]; campaign_theme?: string; industry?: string; brand_name?: string }) =>
    request<{ product: string; content_plan: string; plan?: string }>(
      "/api/automation/social/weekly-plan",
      { method: "POST", body: JSON.stringify(payload) }
    ),

  // ─── Orchestrator ─────────────────────────────────────────────────────────
  campaignPlan: (payload: {
    task: string;
    product: string;
    industry?: string;
    budget?: number;
    season?: string;
  }) =>
    request<{ task: string; completed_nodes: string[]; final_report: string }>(
      "/api/commerce/orchestrate/campaign-plan",
      { method: "POST", body: JSON.stringify(payload) }
    ),

  // ─── Email sending ────────────────────────────────────────────────────────
  sendPersonalizedEmail: (customer: Record<string, unknown>, segment: string, trigger?: string) =>
    request<{ success: boolean; to: string; error?: string }>(
      "/api/commerce/personalize/send-email",
      { method: "POST", body: JSON.stringify({ customer, segment, trigger: trigger || "" }) }
    ),

  sendBirthdayEmail: (customerEmail: string, customerName: string, tier?: string) =>
    request<{ success: boolean; to: string; error?: string }>(
      "/api/commerce/personalize/send-birthday",
      { method: "POST", body: JSON.stringify({ customer_email: customerEmail, customer_name: customerName, tier: tier || "loyal" }) }
    ),

  sendAbandonedCart: (customerEmail: string, customerName: string, cartValue: number, products: string[], steps?: number[]) =>
    request<{ to: string; steps_sent: Record<string, { success: boolean; error?: string }> }>(
      "/api/commerce/personalize/send-abandoned-cart",
      { method: "POST", body: JSON.stringify({ customer_email: customerEmail, customer_name: customerName, cart_value: cartValue, products, steps: steps || [1] }) }
    ),

  sendBulkEmail: (customers: Record<string, unknown>[], baseMessage: string, subject: string) =>
    request<{ sent: number; failed: number; total: number; errors: string[] }>(
      "/api/commerce/personalize/send-bulk",
      { method: "POST", body: JSON.stringify({ customers, base_message: baseMessage, subject }) }
    ),

  // ─── Shopee ───────────────────────────────────────────────────────────────
  shopeeShop: () => request<Record<string, unknown>>("/api/shopee/shop"),
  shopeePerformance: () => request<Record<string, unknown>>("/api/shopee/performance"),
  shopeeRevenue: (days?: number) =>
    request<{ days: number; total_completed_orders: number; total_cancelled_orders: number; cancellation_rate: number }>(
      `/api/shopee/revenue${days ? `?days=${days}` : ""}`
    ),
  shopeeProducts: (pageSize?: number) =>
    request<Array<Record<string, unknown>>>(`/api/shopee/products${pageSize ? `?page_size=${pageSize}` : ""}`),
  shopeeTopProducts: (limit?: number) =>
    request<Array<Record<string, unknown>>>(`/api/shopee/products/top${limit ? `?limit=${limit}` : ""}`),
  shopeeOrders: (days?: number, status?: string) =>
    request<{ days: number; status: string; count: number; orders: Array<Record<string, unknown>> }>(
      `/api/shopee/orders?days=${days || 7}&status=${status || "READY_TO_SHIP"}`
    ),
  shopeeVouchers: (status?: string) =>
    request<{ status: string; count: number; vouchers: Array<Record<string, unknown>> }>(
      `/api/shopee/vouchers?status=${status || "ongoing"}`
    ),
  shopeeCreateVoucher: (payload: { discount_pct: number; min_spend?: number; usage_limit?: number; voucher_name?: string }) =>
    request<{ created: boolean; discount_pct: number }>(
      "/api/shopee/vouchers",
      { method: "POST", body: JSON.stringify(payload) }
    ),
  shopeeAds: () =>
    request<{ count: number; campaigns: Array<Record<string, unknown>> }>("/api/shopee/ads"),
  shopeeUpdateAdsBudget: (campaignId: number, dailyBudget: number) =>
    request<{ updated: boolean }>(
      "/api/shopee/ads/budget",
      { method: "PATCH", body: JSON.stringify({ campaign_id: campaignId, daily_budget: dailyBudget }) }
    ),
  shopeeUpdatePrice: (itemId: number, price: number) =>
    request<{ updated: boolean; item_id: number; new_price: number }>(
      "/api/shopee/products/price",
      { method: "PATCH", body: JSON.stringify({ item_id: itemId, price }) }
    ),

  // ─── Budget ───────────────────────────────────────────────────────────────
  getSeasonCalendar: () =>
    request<{ calendar: Record<string, unknown> }>("/api/commerce/budget/season-calendar"),

  seasonBoost: (baseBudget: number, seasonKey: string, industry: string) =>
    request<{ season: string; recommended_budget: number; cpc_multiplier: number; ai_plan: string }>(
      "/api/commerce/budget/season-boost",
      { method: "POST", body: JSON.stringify({ base_budget: baseBudget, season_key: seasonKey, industry }) }
    ),
};

// ─── Stream helper ────────────────────────────────────────────────────────────

export async function streamCampaignPlan(
  payload: { task: string; product: string; industry?: string; budget?: number; season?: string },
  callbacks: { onChunk: (chunk: unknown) => void; onDone: () => void }
): Promise<void> {
  const { onChunk, onDone } = callbacks;
  const res = await fetch(`${BASE_URL}/api/commerce/orchestrate/campaign-plan/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!res.body) { onDone(); return; }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) { onDone(); break; }
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      try {
        onChunk(JSON.parse(trimmed));
      } catch {
        // non-JSON line, skip
      }
    }
  }
}
