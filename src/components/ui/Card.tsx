import type { ReactNode } from "react";

export default function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`bg-white rounded-3xl shadow-sm border border-gray-100 p-6 ${className}`}>
      {children}
    </div>
  );
}
