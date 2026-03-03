import React from "react";

interface Props extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

export default function Card({ children, className = "", ...rest }: Props) {
  return (
    <div className={`rounded-2xl border border-neutral-200 bg-white p-6 shadow-sm ${className}`} {...rest}>
      {children}
    </div>
  );
}
