type BadgeVariant = "idle" | "running" | "done" | "error" | "attention" | "info";

interface BadgeProps {
  variant?: BadgeVariant;
  children: React.ReactNode;
  className?: string;
}

const variantClass: Record<BadgeVariant, string> = {
  idle: "",
  running: "ok",
  done: "ok",
  error: "warn",
  attention: "warn",
  info: "",
};

export default function Badge({ variant = "idle", children, className = "" }: BadgeProps) {
  return (
    <span className={`status-pill ${variantClass[variant]} ${className}`.trim()}>
      {children}
    </span>
  );
}
