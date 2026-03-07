import type { HTMLAttributes, ReactNode } from "react";

interface CardProps extends HTMLAttributes<HTMLElement> {
  children: ReactNode;
  priority?: boolean;
}

export default function Card({ children, priority, className = "", ...rest }: CardProps) {
  return (
    <section className={`content-block${priority ? " priority-block" : ""} ${className}`.trim()} {...rest}>
      {children}
    </section>
  );
}
