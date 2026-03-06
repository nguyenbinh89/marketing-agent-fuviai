"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard, MessageSquare, Pen, BarChart2,
  Megaphone, Radio, TrendingUp, Users, ShieldCheck,
  Zap, Search, ShoppingBag, MousePointerClick,
  Target, Video, Layers, MessageCircle, Bell, FileText,
} from "lucide-react";

const NAV_GROUPS = [
  {
    label: "Tổng quan",
    items: [
      { label: "Dashboard",        href: "/",             icon: LayoutDashboard },
      { label: "Chat với AI",      href: "/chat",         icon: MessageSquare },
      { label: "Thông báo",        href: "/notifications", icon: Bell },
    ],
  },
  {
    label: "Nội dung & Kênh",
    items: [
      { label: "Tạo Content",      href: "/content",    icon: Pen },
      { label: "Social Scheduling",href: "/social",     icon: Megaphone },
      { label: "Livestream Coach", href: "/livestream", icon: Radio },
      { label: "Zalo OA",          href: "/zalo-oa",    icon: MessageCircle },
    ],
  },
  {
    label: "Quảng cáo",
    items: [
      { label: "Unified Ads",      href: "/ads",          icon: Layers },
      { label: "Google Ads",       href: "/google-ads",   icon: MousePointerClick },
      { label: "Facebook Ads",     href: "/facebook-ads", icon: Target },
      { label: "TikTok Ads",       href: "/tiktok-ads",   icon: Video },
    ],
  },
  {
    label: "Phân tích & Báo cáo",
    items: [
      { label: "Analytics",         href: "/analytics",  icon: TrendingUp },
      { label: "Phân tích Campaign",href: "/campaigns",  icon: BarChart2 },
      { label: "Nghiên cứu & SEO",  href: "/research",   icon: Search },
      { label: "Báo cáo AI",        href: "/reports",    icon: FileText },
    ],
  },
  {
    label: "Thương mại",
    items: [
      { label: "Shopee E-commerce", href: "/shopee",     icon: ShoppingBag },
      { label: "Khách hàng",        href: "/customers",  icon: Users },
    ],
  },
  {
    label: "Nâng cao",
    items: [
      { label: "Campaign Plan AI",  href: "/orchestrate", icon: Zap },
      { label: "Compliance",        href: "/compliance",  icon: ShieldCheck },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-60 bg-white border-r border-slate-200 flex flex-col flex-shrink-0">
      {/* Logo */}
      <div className="h-16 flex items-center px-5 border-b border-slate-200">
        <span className="text-brand-600 font-bold text-xl tracking-tight">Fuvi</span>
        <span className="text-slate-800 font-bold text-xl tracking-tight">AI</span>
        <span className="ml-2 text-xs text-slate-500 font-medium mt-0.5">Marketing</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-3 px-3 overflow-y-auto scrollbar-thin">
        {NAV_GROUPS.map(({ label, items }) => (
          <div key={label} className="mb-4">
            <p className="px-3 mb-1 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
              {label}
            </p>
            <div className="space-y-0.5">
              {items.map(({ label: itemLabel, href, icon: Icon }) => {
                const active = pathname === href;
                return (
                  <Link
                    key={href}
                    href={href}
                    className={cn(
                      "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                      active
                        ? "bg-brand-50 text-brand-600"
                        : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                    )}
                  >
                    <Icon size={16} className={active ? "text-brand-500" : "text-slate-400"} />
                    {itemLabel}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      {/* Footer */}
      <div className="p-4 border-t border-slate-200">
        <p className="text-xs text-slate-400 text-center">
          FuviAI v1.0 • 12 AI Agents
        </p>
      </div>
    </aside>
  );
}
