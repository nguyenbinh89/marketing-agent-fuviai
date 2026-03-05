import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center h-64 gap-4">
      <p className="text-6xl font-bold text-slate-200">404</p>
      <p className="text-slate-500 text-sm">Trang không tồn tại</p>
      <Link href="/" className="btn-primary text-sm">
        Về Dashboard
      </Link>
    </div>
  );
}
