import { render } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import StatusDot from "../StatusDot";

describe("StatusDot", () => {
  it("renders with pulse class when online", () => {
    const { container } = render(<StatusDot online={true} />);
    expect(container.firstChild).toHaveClass("pulse");
  });

  it("renders with danger class when offline", () => {
    const { container } = render(<StatusDot online={false} />);
    expect(container.firstChild).toHaveClass("danger");
  });

  it("always has status-dot base class", () => {
    const { container } = render(<StatusDot online={true} />);
    expect(container.firstChild).toHaveClass("status-dot");
  });

  it("passes through custom className", () => {
    const { container } = render(<StatusDot online={true} className="ml-2" />);
    expect(container.firstChild).toHaveClass("ml-2");
  });
});
