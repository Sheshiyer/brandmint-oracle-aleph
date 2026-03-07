import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import Badge from "../Badge";

describe("Badge", () => {
  it("renders children text", () => {
    render(<Badge>running</Badge>);
    expect(screen.getByText("running")).toBeInTheDocument();
  });

  it("applies variant class for running", () => {
    const { container } = render(<Badge variant="running">active</Badge>);
    expect(container.firstChild).toHaveClass("ok");
  });

  it("applies idle variant with no extra class", () => {
    const { container } = render(<Badge variant="idle">idle</Badge>);
    expect(container.firstChild).toHaveClass("status-pill");
  });

  it("passes through custom className", () => {
    const { container } = render(<Badge className="extra">test</Badge>);
    expect(container.firstChild).toHaveClass("extra");
  });
});
