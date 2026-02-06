import { motion } from "framer-motion";
import type { ButtonHTMLAttributes, ReactNode } from "react";

interface Props extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "ghost";
  children: ReactNode;
}

export default function Button({ variant = "primary", children, className = "", ...props }: Props) {
  const base = "inline-flex items-center justify-center gap-2 rounded-xl px-5 py-2.5 font-semibold text-sm transition-colors focus:outline-none focus:ring-2 focus:ring-electric/40 disabled:opacity-50";
  const variants = {
    primary: "bg-electric text-white hover:bg-electric-light",
    secondary: "bg-pink/10 text-electric hover:bg-pink/20",
    ghost: "text-gray-600 hover:bg-gray-100",
  };

  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      className={`${base} ${variants[variant]} ${className}`}
      {...(props as any)}
    >
      {children}
    </motion.button>
  );
}
