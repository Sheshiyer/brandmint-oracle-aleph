#!/bin/bash
# process-markdown.sh - Process markdown files and copy to Astro content directory
# Usage: ./process-markdown.sh <source-dir> <dest-dir> [--images <images-dir>]

set -e

SOURCE_DIR="${1:?Source directory required}"
DEST_DIR="${2:?Destination directory required}"

# Parse optional --images flag
IMAGES_DIR=""
shift 2
while [[ $# -gt 0 ]]; do
    case "$1" in
        --images)
            IMAGES_DIR="${2:?--images requires a directory path}"
            shift 2
            ;;
        *)
            echo "Unknown option: $1" >&2
            exit 1
            ;;
    esac
done

echo "📄 Processing markdown files"
echo "   Source: $SOURCE_DIR"
echo "   Destination: $DEST_DIR"
if [ -n "$IMAGES_DIR" ]; then
    echo "   Images: $IMAGES_DIR"
fi
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

# Copy images if --images flag was provided
if [ -n "$IMAGES_DIR" ]; then
    if [ -d "$IMAGES_DIR" ]; then
        # Resolve public/images relative to dest-dir (dest is src/content/docs, public is ../../public)
        PUBLIC_IMAGES="$(cd "$DEST_DIR" && cd ../../.. && pwd)/public/images"
        mkdir -p "$PUBLIC_IMAGES"

        image_count=0
        for ext in png jpg jpeg webp svg; do
            for img in "$IMAGES_DIR"/*."$ext"; do
                [ -f "$img" ] || continue
                cp "$img" "$PUBLIC_IMAGES/"
                ((image_count++)) || true
            done
        done

        echo "🖼️  Copied $image_count images to $PUBLIC_IMAGES"
    else
        echo "⚠️  Images directory not found: $IMAGES_DIR" >&2
    fi
fi

echo ""
echo "Your content is ready in $DEST_DIR"
