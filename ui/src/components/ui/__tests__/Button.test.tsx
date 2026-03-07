import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import Button from "../Button";

describe("Button", () => {
  it("renders children text", () => {
    render(<Button>Click me</Button>);
    expect(screen.getByText("Click me")).toBeInTheDocument();
  });

  it("applies primary variant class", () => {
    render(<Button variant="primary">Save</Button>);
    const btn = screen.getByText("Save");
    expect(btn).toHaveClass("btn-primary");
  });

  it("applies danger variant class", () => {
    render(<Button variant="danger">Delete</Button>);
    const btn = screen.getByText("Delete");
    expect(btn).toHaveClass("btn-danger");
  });

  it("defaults to secondary variant", () => {
    render(<Button>Default</Button>);
    const btn = screen.getByText("Default");
    expect(btn).toHaveClass("btn");
    expect(btn).not.toHaveClass("btn-primary");
  });

  it("passes through HTML button attributes", () => {
    render(<Button disabled>Disabled</Button>);
    expect(screen.getByText("Disabled")).toBeDisabled();
  });
});
