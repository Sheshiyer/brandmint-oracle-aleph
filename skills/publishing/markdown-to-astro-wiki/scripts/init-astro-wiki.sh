#!/bin/bash
# init-astro-wiki.sh - Initialize the brand-native Astro portal scaffold
# Usage: ./init-astro-wiki.sh <project-name>

set -euo pipefail

PROJECT_NAME="${1:?Usage: ./init-astro-wiki.sh <project-name>}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE_DIR="$(cd "$SCRIPT_DIR/../template" && pwd)"
TARGET_DIR="$PWD/$PROJECT_NAME"

if [ ! -d "$TEMPLATE_DIR" ]; then
  echo "Template directory not found: $TEMPLATE_DIR" >&2
  exit 1
fi

echo "🚀 Initializing Astro Wiki: $PROJECT_NAME"
echo ""

rm -rf "$TARGET_DIR"
mkdir -p "$TARGET_DIR"
cp -R "$TEMPLATE_DIR/." "$TARGET_DIR/"

python3 - "$TARGET_DIR" "$PROJECT_NAME" <<'PY'
import json
import re
import sys
from pathlib import Path

target = Path(sys.argv[1])
project_name = sys.argv[2]
package_name = re.sub(r'[^a-z0-9]+', '-', project_name.lower()).strip('-') or 'astro-portal'
package_path = target / 'package.json'
package = json.loads(package_path.read_text())
package['name'] = package_name
package_path.write_text(json.dumps(package, indent=2) + '\n')
PY

echo "📁 Created project structure"
echo "📦 Prepared package.json"
echo "⚙️  Prepared Astro config"
echo "📚 Prepared content collections config"
echo "🎨 Prepared brand-native design system"
echo "🧩 Prepared Astro components"
echo "📐 Prepared layouts"
echo ""
echo "✅ Astro Wiki initialized successfully!"
echo ""
echo "Next steps:"
echo "  cd $PROJECT_NAME"
echo "  bun run dev"
echo ""
echo "Add your markdown files to src/content/docs/"
