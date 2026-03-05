"use client";

import { useEffect } from "react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex flex-col items-center justify-center h-64 gap-4">
      <p className="text-4xl font-bold text-red-200">⚠️</p>
      <p className="text-slate-700 font-medium">Đã xảy ra lỗi</p>
      <p className="text-sm text-slate-500 max-w-sm text-center">{error.message}</p>
      <button onClick={reset} className="btn-primary text-sm">
        Thử lại
      </button>
    </div>
  );
}
