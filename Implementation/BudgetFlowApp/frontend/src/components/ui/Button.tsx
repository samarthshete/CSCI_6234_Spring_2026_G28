"use client";
import React from "react";

type Variant = "primary" | "secondary" | "danger" | "ghost";

interface Props extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  loading?: boolean;
}

const base = "inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none";
const variants: Record<Variant, string> = {
  primary: "bg-neutral-900 text-white hover:bg-neutral-800 focus:ring-neutral-600",
  secondary: "border border-neutral-300 bg-white text-neutral-700 hover:bg-neutral-50 focus:ring-neutral-400",
  danger: "bg-red-600 text-white hover:bg-red-700 focus:ring-red-500",
  ghost: "text-neutral-600 hover:bg-neutral-100 focus:ring-neutral-400",
};

export default function Button({ variant = "primary", loading, children, className = "", ...rest }: Props) {
  return (
    <button className={`${base} ${variants[variant]} ${className}`} disabled={loading || rest.disabled} {...rest}>
      {loading && <span className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-current border-t-transparent" />}
      {children}
    </button>
  );
}
