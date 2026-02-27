#!/usr/bin/env python3
import hashlib
import os
import re
import sys
import tempfile
import urllib.request

OWNER = os.getenv("BREW_OWNER", "Sheshiyer")
REPO = os.getenv("BREW_REPO", "brandmint-oracle-aleph")
TAG = os.getenv("TAG")

if not TAG:
    print("TAG env var is required", file=sys.stderr)
    sys.exit(1)

url = f"https://github.com/{OWNER}/{REPO}/archive/refs/tags/{TAG}.tar.gz"

with tempfile.NamedTemporaryFile(delete=False) as f:
    with urllib.request.urlopen(url) as r:
        f.write(r.read())
    temp_path = f.name

sha256 = hashlib.sha256(open(temp_path, "rb").read()).hexdigest()

formula = f'''class Brandmint < Formula
  include Language::Python::Virtualenv

  desc "Unified brand creation orchestrator (text + visuals + campaigns)"
  homepage "https://github.com/{OWNER}/{REPO}"
  url "{url}"
  sha256 "{sha256}"
  license "MIT"

  depends_on "python@3.11"

  def install
    venv = virtualenv_create(libexec, "python3.11")
    venv.pip_install buildpath
    venv.pip_install %w[
      click
      annotated-doc
      shellingham
      typing-extensions
      markdown-it-py
      mdurl
      pygments
      typer
      rich
      pydantic
      pyyaml
      python-dotenv
      requests
      fal-client
    ]

    bin.install_symlink libexec/"bin/brandmint"
    bin.install_symlink libexec/"bin/bm"
  end

  test do
    assert_match "Brandmint", shell_output("#{'{'}bin{'}'}/bm --help")
  end
end
'''

out = os.getenv("FORMULA_OUT", "Formula/brandmint.rb")
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w", encoding="utf-8") as fp:
    fp.write(formula)

print(f"Wrote {out} for {TAG}")
print(f"sha256={sha256}")
