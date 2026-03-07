import type { ButtonHTMLAttributes } from "react";

type Variant = "primary" | "secondary" | "danger";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
}

const variantClass: Record<Variant, string> = {
  primary: "btn btn-primary",
  secondary: "btn",
  danger: "btn btn-danger",
};

export default function Button({
  variant = "secondary",
  className = "",
  children,
  ...rest
}: ButtonProps) {
  return (
    <button className={`${variantClass[variant]} ${className}`.trim()} {...rest}>
      {children}
    </button>
  );
}
