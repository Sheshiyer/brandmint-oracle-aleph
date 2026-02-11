#!/bin/bash
# process-markdown.sh - Process markdown files and copy to Astro content directory
# Usage: ./process-markdown.sh <source-dir> <dest-dir>

set -e

SOURCE_DIR="${1:?Source directory required}"
DEST_DIR="${2:?Destination directory required}"

echo "📄 Processing markdown files"
echo "   Source: $SOURCE_DIR"
echo "   Destination: $DEST_DIR"
echo ""

# Create destination directory
mkdir -p "$DEST_DIR"

# Counter for processed files
processed=0
skipped=0

# Process each markdown file
find "$SOURCE_DIR" -name "*.md" -type f | while read -r file; do
    # Get relative path from source
    rel_path="${file#$SOURCE_DIR/}"
    dest_file="$DEST_DIR/$rel_path"
    dest_dir="$(dirname "$dest_file")"
    
    # Create destination subdirectory
    mkdir -p "$dest_dir"
    
    # Extract info for frontmatter
    filename="$(basename "$file" .md)"
    category="$(dirname "$rel_path")"
    
    # Clean up category name
    if [ "$category" = "." ]; then
        category="General"
    else
        # Convert path to category name (first directory level)
        category="$(echo "$category" | cut -d'/' -f1 | sed 's/-/ /g' | sed 's/\b\(.\)/\u\1/g')"
    fi
    
    # Extract order from filename prefix (e.g., 01-introduction.md -> 1)
    if [[ "$filename" =~ ^([0-9]+)[-_] ]]; then
        order="${BASH_REMATCH[1]}"
        # Remove leading zeros
        order=$((10#$order))
        # Clean filename
        clean_name="${filename#*[-_]}"
    else
        order=""
        clean_name="$filename"
    fi
    
    # Generate title from filename
    title="$(echo "$clean_name" | sed 's/-/ /g' | sed 's/_/ /g' | sed 's/\b\(.\)/\u\1/g')"
    
    # Check if file already has frontmatter
    first_line="$(head -n 1 "$file")"
    
    if [ "$first_line" = "---" ]; then
        # File has frontmatter, copy as-is but ensure required fields
        echo "  ✓ $rel_path (has frontmatter)"
        cp "$file" "$dest_file"
    else
        # Add frontmatter
        echo "  + $rel_path (adding frontmatter)"
        
        # Extract description from first paragraph
        description="$(awk '/^[^#\[]/ {print; exit}' "$file" | head -c 200)"
        
        # Create frontmatter
        {
            echo "---"
            echo "title: \"$title\""
            if [ -n "$description" ]; then
                # Escape quotes in description
                description="${description//\"/\\\"}"
                echo "description: \"$description\""
            fi
            echo "category: \"$category\""
            if [ -n "$order" ]; then
                echo "order: $order"
            fi
            echo "---"
            echo ""
            cat "$file"
        } > "$dest_file"
    fi
    
    ((processed++)) || true
done

echo ""
echo "✅ Processed $processed markdown files"
echo ""
echo "Your content is ready in $DEST_DIR"
