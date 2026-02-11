#!/usr/bin/env python3
"""
Validate wiki output structure, frontmatter, and internal links.
Run after wiki generation to ensure quality before Astro build.
"""

import os
import sys
import re
import yaml
from pathlib import Path
from typing import List, Dict, Tuple

# Required frontmatter fields
REQUIRED_FIELDS = ['title', 'description', 'category', 'tags']
OPTIONAL_FIELDS = ['sources', 'lastUpdated', 'order', 'icon']

# Valid categories
VALID_CATEGORIES = ['product', 'brand', 'audience', 'marketing', 'project', 'general']

# Expected directory structure
EXPECTED_DIRS = [
    'product',
    'brand', 
    'audience',
    'market',
    'marketing',
    'project',
    'getting-started'
]


class ValidationResult:
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        self.files_checked = 0
        self.files_passed = 0
    
    def add_error(self, msg: str):
        self.errors.append(f"❌ {msg}")
    
    def add_warning(self, msg: str):
        self.warnings.append(f"⚠️  {msg}")
    
    def add_info(self, msg: str):
        self.info.append(f"ℹ️  {msg}")
    
    @property
    def passed(self) -> bool:
        return len(self.errors) == 0


def extract_frontmatter(content: str) -> Tuple[dict, str]:
    """Extract YAML frontmatter from markdown content."""
    if not content.startswith('---'):
        return {}, content
    
    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content
    
    try:
        frontmatter = yaml.safe_load(parts[1])
        body = parts[2]
        return frontmatter or {}, body
    except yaml.YAMLError:
        return {}, content


def validate_frontmatter(filepath: Path, frontmatter: dict, result: ValidationResult):
    """Validate frontmatter fields."""
    rel_path = filepath.name
    
    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in frontmatter:
            result.add_error(f"{rel_path}: Missing required field '{field}'")
        elif not frontmatter[field]:
            result.add_error(f"{rel_path}: Empty required field '{field}'")
    
    # Validate category
    if 'category' in frontmatter:
        cat = frontmatter['category']
        if cat not in VALID_CATEGORIES:
            result.add_warning(f"{rel_path}: Unknown category '{cat}'. Valid: {VALID_CATEGORIES}")
    
    # Validate tags is a list
    if 'tags' in frontmatter:
        if not isinstance(frontmatter['tags'], list):
            result.add_error(f"{rel_path}: 'tags' must be an array")
        elif len(frontmatter['tags']) == 0:
            result.add_warning(f"{rel_path}: 'tags' array is empty")
    
    # Validate description length
    if 'description' in frontmatter and frontmatter['description']:
        desc_len = len(frontmatter['description'])
        if desc_len > 160:
            result.add_warning(f"{rel_path}: Description too long ({desc_len} chars, max 160)")
        elif desc_len < 50:
            result.add_warning(f"{rel_path}: Description very short ({desc_len} chars)")
    
    # Check title matches H1
    if 'title' in frontmatter:
        title = frontmatter['title']
        if not title or len(title) < 3:
            result.add_warning(f"{rel_path}: Title is very short")


def find_internal_links(content: str) -> List[str]:
    """Extract internal markdown links from content."""
    # Match [text](path.md) style links
    link_pattern = r'\[([^\]]+)\]\(([^)]+\.md)\)'
    links = re.findall(link_pattern, content)
    return [link[1] for link in links]


def validate_links(wiki_dir: Path, filepath: Path, body: str, all_files: set, result: ValidationResult):
    """Validate internal links resolve to existing files."""
    links = find_internal_links(body)
    file_dir = filepath.parent
    
    for link in links:
        # Resolve relative path
        if link.startswith('/'):
            target = wiki_dir / link[1:]
        else:
            target = (file_dir / link).resolve()
        
        # Normalize for comparison
        try:
            rel_target = target.relative_to(wiki_dir)
            target_str = str(rel_target)
        except ValueError:
            target_str = str(target)
        
        if target_str not in all_files and not target.exists():
            result.add_error(f"{filepath.name}: Broken link to '{link}'")


def validate_heading_structure(filepath: Path, body: str, result: ValidationResult):
    """Check heading hierarchy."""
    lines = body.split('\n')
    h1_count = 0
    prev_level = 0
    
    for line in lines:
        if line.startswith('#'):
            # Count heading level
            level = len(line) - len(line.lstrip('#'))
            heading_text = line.lstrip('#').strip()
            
            if level == 1:
                h1_count += 1
            
            # Check for skipped levels (e.g., H1 -> H3)
            if prev_level > 0 and level > prev_level + 1:
                result.add_warning(f"{filepath.name}: Skipped heading level (H{prev_level} to H{level})")
            
            prev_level = level
    
    if h1_count == 0:
        result.add_warning(f"{filepath.name}: No H1 heading found")
    elif h1_count > 1:
        result.add_warning(f"{filepath.name}: Multiple H1 headings ({h1_count})")


def validate_file(filepath: Path, wiki_dir: Path, all_files: set, result: ValidationResult):
    """Validate a single markdown file."""
    result.files_checked += 1
    
    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        result.add_error(f"{filepath.name}: Could not read file: {e}")
        return
    
    frontmatter, body = extract_frontmatter(content)
    
    # Validate frontmatter
    if not frontmatter:
        result.add_error(f"{filepath.name}: Missing or invalid frontmatter")
    else:
        validate_frontmatter(filepath, frontmatter, result)
    
    # Validate links
    validate_links(wiki_dir, filepath, body, all_files, result)
    
    # Validate heading structure
    validate_heading_structure(filepath, body, result)
    
    # Check for TODO markers (content gaps)
    if 'TODO' in body or '[TODO' in body:
        result.add_warning(f"{filepath.name}: Contains TODO markers (incomplete content)")
    
    result.files_passed += 1


def validate_structure(wiki_dir: Path, result: ValidationResult):
    """Validate overall wiki structure."""
    
    # Check for index.md
    if not (wiki_dir / 'index.md').exists():
        result.add_error("Missing index.md (homepage)")
    
    # Check for navigation.yaml
    if not (wiki_dir / 'navigation.yaml').exists():
        result.add_warning("Missing navigation.yaml")
    
    # Check expected directories
    for dir_name in EXPECTED_DIRS:
        dir_path = wiki_dir / dir_name
        if dir_path.exists():
            md_files = list(dir_path.glob('*.md'))
            if len(md_files) == 0:
                result.add_warning(f"Directory '{dir_name}/' exists but contains no markdown files")
        else:
            result.add_info(f"Optional directory '{dir_name}/' not present")


def validate_wiki(wiki_dir: str) -> ValidationResult:
    """Main validation function."""
    result = ValidationResult()
    wiki_path = Path(wiki_dir)
    
    if not wiki_path.exists():
        result.add_error(f"Wiki directory not found: {wiki_dir}")
        return result
    
    # Collect all markdown files
    all_files = set()
    md_files = list(wiki_path.rglob('*.md'))
    
    for f in md_files:
        try:
            rel = str(f.relative_to(wiki_path))
            all_files.add(rel)
        except ValueError:
            pass
    
    result.add_info(f"Found {len(md_files)} markdown files")
    
    # Validate structure
    validate_structure(wiki_path, result)
    
    # Validate each file
    for md_file in md_files:
        validate_file(md_file, wiki_path, all_files, result)
    
    return result


def print_results(result: ValidationResult):
    """Print validation results."""
    print("\n" + "="*60)
    print("📋 WIKI VALIDATION REPORT")
    print("="*60)
    
    print(f"\nFiles checked: {result.files_checked}")
    print(f"Files passed: {result.files_passed}")
    
    if result.errors:
        print(f"\n🚨 ERRORS ({len(result.errors)}):")
        for err in result.errors:
            print(f"  {err}")
    
    if result.warnings:
        print(f"\n⚠️  WARNINGS ({len(result.warnings)}):")
        for warn in result.warnings:
            print(f"  {warn}")
    
    if result.info:
        print(f"\nℹ️  INFO:")
        for info in result.info:
            print(f"  {info}")
    
    print("\n" + "="*60)
    if result.passed:
        print("✅ VALIDATION PASSED")
    else:
        print("❌ VALIDATION FAILED - Fix errors before building")
    print("="*60 + "\n")


def main():
    if len(sys.argv) < 2:
        print("Usage: validate-wiki.py <wiki-directory>")
        print("\nValidates wiki markdown files for structure, frontmatter, and links.")
        sys.exit(1)
    
    wiki_dir = sys.argv[1]
    result = validate_wiki(wiki_dir)
    print_results(result)
    
    sys.exit(0 if result.passed else 1)


if __name__ == '__main__':
    main()
