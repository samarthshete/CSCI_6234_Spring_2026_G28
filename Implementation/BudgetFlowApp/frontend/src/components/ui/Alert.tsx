import React from "react";

type Kind = "error" | "success" | "info";
const styles: Record<Kind, string> = {
  error: "bg-red-50 border-red-200 text-red-800",
  success: "bg-emerald-50 border-emerald-200 text-emerald-800",
  info: "bg-blue-50 border-blue-200 text-blue-800",
};

export default function Alert({ kind = "error", children }: { kind?: Kind; children: React.ReactNode }) {
  return (
    <div className={`rounded-lg border px-4 py-3 text-sm ${styles[kind]}`}>
      {children}
    </div>
  );
}
