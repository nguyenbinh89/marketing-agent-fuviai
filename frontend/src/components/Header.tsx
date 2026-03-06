"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Bell, Settings } from "lucide-react";

import { api } from "@/lib/api";

export default function Header() {
  const [counts, setCounts] = useState<{ critical: number; warning: number } | null>(null);

  useEffect(() => {
    api.notificationCount()
      .then((d) => setCounts({ critical: d.critical, warning: d.warning }))
      .catch(() => {/* backend offline — hide badge */});
  }, []);

  const urgentCount = (counts?.critical ?? 0) + (counts?.warning ?? 0);

  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6 flex-shrink-0">
      <div>
        <p className="text-sm text-slate-500">Xin chào,</p>
        <p className="font-semibold text-slate-800 -mt-0.5">Marketing Manager</p>
      </div>
      <div className="flex items-center gap-3">
        <Link
          href="/notifications"
          className="relative p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
        >
          <Bell size={18} />
          {urgentCount > 0 && (
            <span className="absolute top-1 right-1 min-w-[16px] h-4 bg-red-500 rounded-full flex items-center justify-center text-white text-[9px] font-bold px-0.5">
              {urgentCount > 9 ? "9+" : urgentCount}
            </span>
          )}
        </Link>
        <Link
          href="/settings"
          className="p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors"
        >
          <Settings size={18} />
        </Link>
        <div className="w-8 h-8 rounded-full bg-brand-500 flex items-center justify-center text-white text-sm font-semibold">
          F
        </div>
      </div>
    </header>
  );
}
