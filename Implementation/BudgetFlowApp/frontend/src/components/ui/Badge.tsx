import React from "react";

type Color = "gray" | "green" | "red" | "blue" | "yellow" | "purple";

const colors: Record<Color, string> = {
  gray: "bg-neutral-100 text-neutral-600",
  green: "bg-emerald-50 text-emerald-700",
  red: "bg-red-50 text-red-700",
  blue: "bg-blue-50 text-blue-700",
  yellow: "bg-amber-50 text-amber-700",
  purple: "bg-purple-50 text-purple-700",
};

export default function Badge({ children, color = "gray" }: { children: React.ReactNode; color?: Color }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${colors[color]}`}>
      {children}
    </span>
  );
}
