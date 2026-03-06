"use client";

import { useState, useEffect, useCallback } from "react";
import {
  ShoppingBag, Package, Tag, Megaphone,
  RefreshCw, TrendingUp, AlertTriangle, Check, X,
} from "lucide-react";
import { api } from "@/lib/api";
import { cn, formatVND } from "@/lib/utils";

type Tab = "overview" | "products" | "orders" | "vouchers" | "ads";

const TABS: { value: Tab; label: string; icon: React.ElementType }[] = [
  { value: "overview",  label: "Tổng quan",  icon: TrendingUp },
  { value: "products",  label: "Sản phẩm",   icon: Package },
  { value: "orders",    label: "Đơn hàng",   icon: ShoppingBag },
  { value: "vouchers",  label: "Voucher",     icon: Tag },
  { value: "ads",       label: "Quảng cáo",  icon: Megaphone },
];

const ORDER_STATUSES = [
  { value: "READY_TO_SHIP", label: "Chờ giao" },
  { value: "SHIPPED",       label: "Đang giao" },
  { value: "COMPLETED",     label: "Hoàn thành" },
  { value: "UNPAID",        label: "Chưa thanh toán" },
  { value: "CANCELLED",     label: "Đã huỷ" },
];

function NotConfiguredBanner() {
  return (
    <div className="card p-6 flex items-start gap-4 bg-amber-50 border-amber-200">
      <AlertTriangle size={20} className="text-amber-500 flex-shrink-0 mt-0.5" />
      <div>
        <p className="font-semibold text-amber-800 text-sm">Shopee chưa được cấu hình</p>
        <p className="text-amber-700 text-xs mt-1">
          Thêm <code className="bg-amber-100 px-1 rounded">SHOPEE_PARTNER_ID</code>,{" "}
          <code className="bg-amber-100 px-1 rounded">SHOPEE_PARTNER_KEY</code>,{" "}
          <code className="bg-amber-100 px-1 rounded">SHOPEE_ACCESS_TOKEN</code> và{" "}
          <code className="bg-amber-100 px-1 rounded">SHOPEE_SHOP_ID</code> vào file{" "}
          <code className="bg-amber-100 px-1 rounded">.env</code> để kết nối shop.
        </p>
      </div>
    </div>
  );
}

// ─── Overview Tab ─────────────────────────────────────────────────────────────

function OverviewTab() {
  const [revenue, setRevenue]   = useState<Record<string, unknown> | null>(null);
  const [loading, setLoading]   = useState(false);
  const [days, setDays]         = useState(30);
  const [notConfigured, setNotConfigured] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.shopeeRevenue(days);
      setRevenue(res as unknown as Record<string, unknown>);
      if ((res as unknown as Record<string, unknown>).error) setNotConfigured(true);
    } catch {
      setNotConfigured(true);
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => { load(); }, [load]);

  if (notConfigured) return <NotConfiguredBanner />;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <label className="text-sm text-slate-600">Khoảng thời gian:</label>
        {[7, 14, 30, 90].map((d) => (
          <button
            key={d}
            onClick={() => setDays(d)}
            className={cn(
              "px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors",
              days === d
                ? "bg-brand-50 border-brand-300 text-brand-700"
                : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
            )}
          >
            {d} ngày
          </button>
        ))}
        <button onClick={load} className="ml-auto text-slate-400 hover:text-brand-500 transition-colors">
          <RefreshCw size={15} className={loading ? "spinner" : ""} />
        </button>
      </div>

      {loading ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="card p-5 animate-pulse">
              <div className="h-3 bg-slate-200 rounded w-24 mb-3" />
              <div className="h-6 bg-slate-200 rounded w-16" />
            </div>
          ))}
        </div>
      ) : revenue ? (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="card p-5">
            <p className="text-xs text-slate-500 mb-1">Đơn hoàn thành</p>
            <p className="text-2xl font-bold text-green-600">{String(revenue.total_completed_orders ?? 0)}</p>
            <p className="text-xs text-slate-400 mt-1">{days} ngày qua</p>
          </div>
          <div className="card p-5">
            <p className="text-xs text-slate-500 mb-1">Đơn huỷ</p>
            <p className="text-2xl font-bold text-red-500">{String(revenue.total_cancelled_orders ?? 0)}</p>
            <p className="text-xs text-slate-400 mt-1">Cancellation rate: {String(revenue.cancellation_rate ?? 0)}%</p>
          </div>
          <div className="card p-5 col-span-2">
            <p className="text-xs text-slate-500 mb-1">Ghi chú</p>
            <p className="text-sm text-slate-600 leading-relaxed">{String(revenue.note ?? "")}</p>
          </div>
        </div>
      ) : null}
    </div>
  );
}

// ─── Products Tab ─────────────────────────────────────────────────────────────

function ProductsTab() {
  const [products, setProducts] = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading]   = useState(false);
  const [topOnly, setTopOnly]   = useState(false);

  // Edit price
  const [editId, setEditId]     = useState<number | null>(null);
  const [newPrice, setNewPrice] = useState("");
  const [saving, setSaving]     = useState(false);
  const [saved, setSaved]       = useState<number | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const res = topOnly ? await api.shopeeTopProducts(10) : await api.shopeeProducts(20);
      setProducts(Array.isArray(res) ? res : []);
    } catch {
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [topOnly]); // eslint-disable-line react-hooks/exhaustive-deps

  const savePrice = async (itemId: number) => {
    const price = parseFloat(newPrice);
    if (!price || price <= 0) return;
    setSaving(true);
    try {
      await api.shopeeUpdatePrice(itemId, price);
      setSaved(itemId);
      setEditId(null);
      setTimeout(() => setSaved(null), 3000);
      load();
    } catch {
      // ignore
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <button
          onClick={() => setTopOnly(false)}
          className={cn("px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors",
            !topOnly ? "bg-brand-50 border-brand-300 text-brand-700" : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
          )}
        >Tất cả sản phẩm</button>
        <button
          onClick={() => setTopOnly(true)}
          className={cn("px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors",
            topOnly ? "bg-brand-50 border-brand-300 text-brand-700" : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
          )}
        >Top bán chạy</button>
        <button onClick={load} className="ml-auto text-slate-400 hover:text-brand-500">
          <RefreshCw size={15} className={loading ? "spinner" : ""} />
        </button>
      </div>

      {loading ? (
        <div className="card p-5 text-slate-400 text-sm text-center py-12">Đang tải sản phẩm...</div>
      ) : products.length === 0 ? (
        <NotConfiguredBanner />
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50">
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">Sản phẩm</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Đã bán</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Giá</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Hành động</th>
              </tr>
            </thead>
            <tbody>
              {products.map((p) => {
                const id = Number(p.item_id || p.id || 0);
                const name = String(p.item_name || p.name || "—");
                const sold = Number(p.sold || 0);
                const price = Number(p.price || p.original_price || 0);
                return (
                  <tr key={id} className="border-b border-slate-50 hover:bg-slate-50/50 transition-colors">
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-800 truncate max-w-xs">{name}</p>
                      <p className="text-xs text-slate-400 mt-0.5">ID: {id}</p>
                    </td>
                    <td className="px-4 py-3 text-right text-slate-600">{sold.toLocaleString()}</td>
                    <td className="px-4 py-3 text-right">
                      {saved === id ? (
                        <span className="text-green-600 flex items-center justify-end gap-1 text-xs">
                          <Check size={12} /> Đã lưu
                        </span>
                      ) : editId === id ? (
                        <div className="flex items-center gap-1 justify-end">
                          <input
                            type="number"
                            value={newPrice}
                            onChange={(e) => setNewPrice(e.target.value)}
                            className="input w-28 text-right text-xs py-1"
                            placeholder="Giá mới"
                          />
                          <button onClick={() => savePrice(id)} disabled={saving} className="text-green-600 hover:text-green-700">
                            <Check size={14} />
                          </button>
                          <button onClick={() => setEditId(null)} className="text-slate-400 hover:text-slate-600">
                            <X size={14} />
                          </button>
                        </div>
                      ) : (
                        <span className="font-medium text-slate-800">{price > 0 ? formatVND(price) : "—"}</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {editId !== id && (
                        <button
                          onClick={() => { setEditId(id); setNewPrice(price > 0 ? String(price) : ""); }}
                          className="text-xs text-brand-500 hover:text-brand-700 font-medium"
                        >
                          Sửa giá
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── Orders Tab ───────────────────────────────────────────────────────────────

function OrdersTab() {
  const [status, setStatus]   = useState("READY_TO_SHIP");
  const [days, setDays]       = useState(7);
  const [data, setData]       = useState<{ count: number; orders: Array<Record<string, unknown>> } | null>(null);
  const [loading, setLoading] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.shopeeOrders(days, status);
      setData(res);
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [status, days]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="space-y-4">
      <div className="card p-4 flex flex-wrap items-center gap-3">
        <div className="flex gap-1">
          {ORDER_STATUSES.map(({ value, label }) => (
            <button
              key={value}
              onClick={() => setStatus(value)}
              className={cn(
                "px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors",
                status === value
                  ? "bg-brand-50 border-brand-300 text-brand-700"
                  : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
              )}
            >
              {label}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-2 ml-auto">
          <select
            className="input text-xs py-1 w-28"
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
          >
            {[7, 14, 30, 60].map((d) => <option key={d} value={d}>{d} ngày</option>)}
          </select>
          <button onClick={load} className="text-slate-400 hover:text-brand-500">
            <RefreshCw size={15} className={loading ? "spinner" : ""} />
          </button>
        </div>
      </div>

      {loading ? (
        <div className="card p-12 text-center text-slate-400 text-sm">Đang tải đơn hàng...</div>
      ) : !data ? (
        <NotConfiguredBanner />
      ) : (
        <div className="space-y-3">
          <p className="text-sm text-slate-600">
            Tìm thấy <span className="font-semibold text-slate-800">{data.count}</span> đơn hàng — trạng thái: <span className="font-semibold">{ORDER_STATUSES.find((s) => s.value === status)?.label}</span>
          </p>
          {data.orders.length === 0 ? (
            <div className="card p-8 text-center text-slate-400 text-sm">Không có đơn hàng nào</div>
          ) : (
            <div className="card overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50">
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">Order SN</th>
                    <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">Trạng thái</th>
                    <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Thời gian tạo</th>
                  </tr>
                </thead>
                <tbody>
                  {data.orders.slice(0, 50).map((o, idx) => (
                    <tr key={idx} className="border-b border-slate-50 hover:bg-slate-50/50">
                      <td className="px-4 py-3 font-mono text-xs text-slate-700">{String(o.order_sn || "—")}</td>
                      <td className="px-4 py-3">
                        <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">
                          {String(o.order_status || status)}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-right text-xs text-slate-400">
                        {o.create_time
                          ? new Date(Number(o.create_time) * 1000).toLocaleDateString("vi-VN")
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Voucher Tab ──────────────────────────────────────────────────────────────

function VouchersTab() {
  const [vouchers, setVouchers] = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading]   = useState(false);
  const [vStatus, setVStatus]   = useState("ongoing");

  // Create form
  const [discountPct, setDiscountPct]   = useState(10);
  const [minSpend, setMinSpend]         = useState(0);
  const [usageLimit, setUsageLimit]     = useState(100);
  const [voucherName, setVoucherName]   = useState("");
  const [creating, setCreating]         = useState(false);
  const [createMsg, setCreateMsg]       = useState<{ ok: boolean; text: string } | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.shopeeVouchers(vStatus);
      setVouchers(res.vouchers || []);
    } catch {
      setVouchers([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [vStatus]); // eslint-disable-line react-hooks/exhaustive-deps

  const createVoucher = async () => {
    setCreating(true);
    setCreateMsg(null);
    try {
      await api.shopeeCreateVoucher({ discount_pct: discountPct, min_spend: minSpend, usage_limit: usageLimit, voucher_name: voucherName || undefined });
      setCreateMsg({ ok: true, text: `Đã tạo voucher giảm ${discountPct}% thành công!` });
      load();
    } catch (err: unknown) {
      setCreateMsg({ ok: false, text: err instanceof Error ? err.message : "Lỗi tạo voucher" });
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Create voucher */}
      <div className="card p-5 space-y-4">
        <h3 className="font-semibold text-slate-800 flex items-center gap-2"><Tag size={15} /> Tạo Voucher mới</h3>
        <div>
          <label className="text-sm font-medium text-slate-700 block mb-1.5">Tên voucher (tuỳ chọn)</label>
          <input className="input" placeholder="VD: Flash Sale T3" value={voucherName} onChange={(e) => setVoucherName(e.target.value)} />
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="text-sm font-medium text-slate-700 block mb-1.5">
              Giảm giá: <span className="text-brand-600 font-bold">{discountPct}%</span>
            </label>
            <input type="range" min={1} max={90} value={discountPct} onChange={(e) => setDiscountPct(Number(e.target.value))} className="w-full accent-brand-500" />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700 block mb-1.5">Lượt dùng tối đa</label>
            <input type="number" className="input" min={1} value={usageLimit} onChange={(e) => setUsageLimit(Number(e.target.value))} />
          </div>
        </div>
        <div>
          <label className="text-sm font-medium text-slate-700 block mb-1.5">Đơn tối thiểu (VNĐ, 0 = không giới hạn)</label>
          <input type="number" className="input" min={0} step={10000} value={minSpend} onChange={(e) => setMinSpend(Number(e.target.value))} />
        </div>
        <button onClick={createVoucher} disabled={creating} className="btn-primary w-full flex items-center justify-center gap-2">
          {creating ? <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full spinner" /> Đang tạo...</> : <><Tag size={15} /> Tạo Voucher</>}
        </button>
        {createMsg && (
          <div className={cn("text-sm p-3 rounded-lg flex items-center gap-2", createMsg.ok ? "bg-green-50 text-green-700" : "bg-red-50 text-red-600")}>
            {createMsg.ok ? <Check size={14} /> : <X size={14} />} {createMsg.text}
          </div>
        )}
      </div>

      {/* Voucher list */}
      <div className="space-y-3">
        <div className="flex gap-2">
          {["upcoming", "ongoing", "expired"].map((s) => (
            <button key={s} onClick={() => setVStatus(s)}
              className={cn("px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors",
                vStatus === s ? "bg-brand-50 border-brand-300 text-brand-700" : "bg-white border-slate-200 text-slate-600"
              )}>
              {s === "upcoming" ? "Sắp diễn ra" : s === "ongoing" ? "Đang chạy" : "Đã hết hạn"}
            </button>
          ))}
          <button onClick={load} className="ml-auto text-slate-400 hover:text-brand-500">
            <RefreshCw size={15} className={loading ? "spinner" : ""} />
          </button>
        </div>
        {loading ? (
          <div className="card p-8 text-center text-slate-400 text-sm">Đang tải...</div>
        ) : vouchers.length === 0 ? (
          <div className="card p-8 text-center text-slate-400 text-sm">Không có voucher nào</div>
        ) : (
          <div className="space-y-2">
            {vouchers.map((v, i) => (
              <div key={i} className="card p-4 flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-800 text-sm">{String(v.voucher_name || v.voucher_code || "Voucher")}</p>
                  <p className="text-xs text-slate-500 mt-0.5">Code: {String(v.voucher_code || "—")}</p>
                </div>
                <div className="text-right">
                  <p className="font-bold text-brand-600">{String(v.discount_amount || 0)}%</p>
                  <p className="text-xs text-slate-400">x{String(v.usage_quantity || 0)} lượt</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Ads Tab ──────────────────────────────────────────────────────────────────

function AdsTab() {
  const [campaigns, setCampaigns] = useState<Array<Record<string, unknown>>>([]);
  const [loading, setLoading]     = useState(false);
  const [editBudget, setEditBudget] = useState<number | null>(null);
  const [budgetVal, setBudgetVal]   = useState("");
  const [saving, setSaving]         = useState(false);
  const [savedId, setSavedId]       = useState<number | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.shopeeAds();
      setCampaigns(res.campaigns || []);
    } catch {
      setCampaigns([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const saveBudget = async (campaignId: number) => {
    const budget = parseFloat(budgetVal);
    if (!budget || budget <= 0) return;
    setSaving(true);
    try {
      await api.shopeeUpdateAdsBudget(campaignId, budget);
      setSavedId(campaignId);
      setEditBudget(null);
      setTimeout(() => setSavedId(null), 3000);
      load();
    } catch { /* ignore */ } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-slate-600">Quản lý Shopee Ads campaigns — điều chỉnh ngân sách tự động</p>
        <button onClick={load} className="text-slate-400 hover:text-brand-500">
          <RefreshCw size={15} className={loading ? "spinner" : ""} />
        </button>
      </div>

      {loading ? (
        <div className="card p-12 text-center text-slate-400 text-sm">Đang tải campaigns...</div>
      ) : campaigns.length === 0 ? (
        <NotConfiguredBanner />
      ) : (
        <div className="card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-100 bg-slate-50">
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">Campaign</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500">Trạng thái</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Ngân sách/ngày</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-slate-500">Hành động</th>
              </tr>
            </thead>
            <tbody>
              {campaigns.map((c) => {
                const id = Number(c.campaign_id || c.id || 0);
                const name = String(c.campaign_name || c.name || "Campaign");
                const status = String(c.state || c.status || "active");
                const budget = Number(c.daily_budget || 0);
                return (
                  <tr key={id} className="border-b border-slate-50 hover:bg-slate-50/50">
                    <td className="px-4 py-3">
                      <p className="font-medium text-slate-800">{name}</p>
                      <p className="text-xs text-slate-400">ID: {id}</p>
                    </td>
                    <td className="px-4 py-3">
                      <span className={cn(
                        "text-xs px-2 py-0.5 rounded-full font-medium",
                        status === "active" || status === "ON"
                          ? "bg-green-50 text-green-700"
                          : "bg-slate-100 text-slate-600"
                      )}>
                        {status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      {savedId === id ? (
                        <span className="text-green-600 flex items-center justify-end gap-1 text-xs"><Check size={12} /> Đã lưu</span>
                      ) : editBudget === id ? (
                        <div className="flex items-center gap-1 justify-end">
                          <input
                            type="number"
                            value={budgetVal}
                            onChange={(e) => setBudgetVal(e.target.value)}
                            className="input w-28 text-right text-xs py-1"
                            placeholder="Budget mới"
                          />
                          <button onClick={() => saveBudget(id)} disabled={saving} className="text-green-600 hover:text-green-700">
                            <Check size={14} />
                          </button>
                          <button onClick={() => setEditBudget(null)} className="text-slate-400 hover:text-slate-600">
                            <X size={14} />
                          </button>
                        </div>
                      ) : (
                        <span className="font-medium text-slate-800">{budget > 0 ? formatVND(budget) : "—"}</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {editBudget !== id && (
                        <button
                          onClick={() => { setEditBudget(id); setBudgetVal(budget > 0 ? String(budget) : ""); }}
                          className="text-xs text-brand-500 hover:text-brand-700 font-medium"
                        >
                          Sửa budget
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function ShopeePage() {
  const [tab, setTab] = useState<Tab>("overview");

  return (
    <div className="max-w-5xl space-y-6">
      <div>
        <h1 className="text-xl font-bold text-slate-800">Shopee E-commerce</h1>
        <p className="text-sm text-slate-500 mt-1">Quản lý shop, sản phẩm, đơn hàng, voucher và quảng cáo Shopee</p>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 bg-slate-100 p-1 rounded-xl w-fit flex-wrap">
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

      {tab === "overview"  && <OverviewTab />}
      {tab === "products"  && <ProductsTab />}
      {tab === "orders"    && <OrdersTab />}
      {tab === "vouchers"  && <VouchersTab />}
      {tab === "ads"       && <AdsTab />}
    </div>
  );
}
