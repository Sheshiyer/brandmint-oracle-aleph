import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import Card from "../Card";

describe("Card", () => {
  it("renders children", () => {
    render(<Card>Card content</Card>);
    expect(screen.getByText("Card content")).toBeInTheDocument();
  });

  it("applies content-block class", () => {
    const { container } = render(<Card>test</Card>);
    expect(container.firstChild).toHaveClass("content-block");
  });

  it("applies priority-block class when priority is true", () => {
    const { container } = render(<Card priority>important</Card>);
    expect(container.firstChild).toHaveClass("priority-block");
  });

  it("does not apply priority-block class by default", () => {
    const { container } = render(<Card>normal</Card>);
    expect(container.firstChild).not.toHaveClass("priority-block");
  });
});
