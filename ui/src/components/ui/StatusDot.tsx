interface StatusDotProps {
  online: boolean;
  className?: string;
}

export default function StatusDot({ online, className = "" }: StatusDotProps) {
  return (
    <span className={`status-dot ${online ? "pulse" : "danger"} ${className}`.trim()} />
  );
}
