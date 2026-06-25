"use client";

import { clsx } from "clsx";

type Variant = "primary" | "secondary" | "danger" | "ghost" | "outline";

export function Button({
  children,
  variant = "primary",
  className,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  const variants: Record<Variant, string> = {
    primary: "bg-accent text-white hover:bg-accent-hover",
    secondary: "bg-surface text-text hover:bg-border border border-border",
    outline: "bg-white text-text border border-border hover:bg-surface",
    danger: "bg-danger text-white hover:bg-red-700",
    ghost: "text-text-secondary hover:bg-surface hover:text-text",
  };
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center gap-1.5 rounded-md px-3.5 py-2 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-50",
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}
