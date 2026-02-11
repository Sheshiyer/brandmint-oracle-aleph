#!/usr/bin/env python3
"""
Inventory and classify source documents for wiki generation.
Scans a directory for campaign outputs and business documents,
classifies them by type, and outputs an inventory for parallel agent dispatch.
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

# Document type patterns - keywords that identify each document type
DOCUMENT_PATTERNS = {
    'mds': {
        'keywords': ['messaging', 'direction', 'summary', 'mds', 'product pitch', 'value prop'],
        'skill': 'mds-messaging-direction-summary',
        'wiki_section': 'product',
        'priority': 1
    },
    'buyer_persona': {
        'keywords': ['persona', 'buyer', 'avatar', 'customer profile', 'target audience'],
        'skill': 'buyer-persona-generator',
        'wiki_section': 'audience',
        'priority': 1
    },
    'positioning': {
        'keywords': ['positioning', 'cbbe', 'brand equity', 'salience', 'resonance'],
        'skill': 'product-positioning-summary',
        'wiki_section': 'product',
        'priority': 1
    },
    'voice_tone': {
        'keywords': ['voice', 'tone', 'brand voice', 'writing style', 'persona definition'],
        'skill': 'voice-and-tone',
        'wiki_section': 'brand',
        'priority': 1
    },
    'competitor': {
        'keywords': ['competitor', 'competitive', 'market analysis', 'comparison'],
        'skill': 'competitor-analysis',
        'wiki_section': 'audience',
        'priority': 2
    },
    'product_description': {
        'keywords': ['product description', 'features', 'specifications', 'detailed product'],
        'skill': 'detailed-product-description',
        'wiki_section': 'product',
        'priority': 2
    },
    'campaign_copy': {
        'keywords': ['campaign', 'page copy', 'landing page', 'kickstarter', 'indiegogo'],
        'skill': 'campaign-page-copy',
        'wiki_section': 'marketing',
        'priority': 2
    },
    'email_welcome': {
        'keywords': ['welcome email', 'vip welcome', 'subscriber'],
        'skill': 'welcome-email-sequence',
        'wiki_section': 'marketing',
        'priority': 3
    },
    'email_prelaunch': {
        'keywords': ['pre-launch email', 'prelaunch', 'countdown'],
        'skill': 'pre-launch-email-sequence',
        'wiki_section': 'marketing',
        'priority': 3
    },
    'email_launch': {
        'keywords': ['launch email', 'launch sequence', 'live now'],
        'skill': 'launch-email-sequence',
        'wiki_section': 'marketing',
        'priority': 3
    },
    'ads_prelaunch': {
        'keywords': ['pre-launch ads', 'prelaunch ads', 'awareness ads'],
        'skill': 'pre-launch-ads',
        'wiki_section': 'marketing',
        'priority': 3
    },
    'ads_live': {
        'keywords': ['live ads', 'campaign ads', 'conversion ads'],
        'skill': 'live-campaign-ads',
        'wiki_section': 'marketing',
        'priority': 3
    },
    'proposal': {
        'keywords': ['proposal', 'development proposal', 'technical architecture', 'investment'],
        'skill': 'thoughtseed-proposal-generator',
        'wiki_section': 'project',
        'priority': 2
    },
    'contract': {
        'keywords': ['contract', 'agreement', 'service agreement', 'terms'],
        'skill': 'thoughtseed-contract-generator',
        'wiki_section': 'project',
        'priority': 2
    },
    'visual_identity': {
        'keywords': ['visual identity', 'brand guide', 'color palette', 'typography', 'logo'],
        'skill': 'visual-identity-core',
        'wiki_section': 'brand',
        'priority': 2
    }
}

# Agent groupings for parallel dispatch
AGENT_GROUPS = {
    'foundation': ['mds', 'positioning', 'product_description'],
    'brand': ['voice_tone', 'visual_identity'],
    'persona': ['buyer_persona', 'competitor'],
    'marketing': ['campaign_copy', 'email_welcome', 'email_prelaunch', 'email_launch', 'ads_prelaunch', 'ads_live'],
    'project': ['proposal', 'contract']
}


def read_file_sample(filepath: Path, max_chars: int = 2000) -> str:
    """Read first N characters of a file for classification."""
    try:
        if filepath.suffix.lower() in ['.md', '.txt']:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read(max_chars).lower()
        elif filepath.suffix.lower() == '.docx':
            # For DOCX, just use filename for now
            return filepath.stem.lower()
    except Exception as e:
        print(f"Warning: Could not read {filepath}: {e}", file=sys.stderr)
    return filepath.stem.lower()


def classify_document(filepath: Path) -> dict:
    """Classify a document by matching content against patterns."""
    content = read_file_sample(filepath)
    filename_lower = filepath.stem.lower()
    
    scores = {}
    for doc_type, pattern_info in DOCUMENT_PATTERNS.items():
        score = 0
        for keyword in pattern_info['keywords']:
            if keyword in content:
                score += 2
            if keyword in filename_lower:
                score += 3  # Filename matches are stronger signals
        scores[doc_type] = score
    
    # Get best match
    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]
    
    if best_score == 0:
        return {
            'type': 'unknown',
            'confidence': 'low',
            'wiki_section': 'general',
            'skill': None
        }
    
    pattern_info = DOCUMENT_PATTERNS[best_type]
    return {
        'type': best_type,
        'confidence': 'high' if best_score >= 4 else 'medium',
        'wiki_section': pattern_info['wiki_section'],
        'skill': pattern_info['skill'],
        'priority': pattern_info['priority']
    }


def scan_directory(source_dir: str) -> dict:
    """Scan directory and classify all documents."""
    source_path = Path(source_dir)
    
    if not source_path.exists():
        print(f"Error: Directory not found: {source_dir}", file=sys.stderr)
        sys.exit(1)
    
    inventory = {
        'scan_date': datetime.now().isoformat(),
        'source_directory': str(source_path.absolute()),
        'documents': [],
        'by_type': {},
        'by_section': {},
        'agent_dispatch': {}
    }
    
    # Scan for documents
    extensions = ['.md', '.txt', '.docx']
    for ext in extensions:
        for filepath in source_path.rglob(f'*{ext}'):
            classification = classify_document(filepath)
            
            doc_entry = {
                'path': str(filepath.absolute()),
                'filename': filepath.name,
                'relative_path': str(filepath.relative_to(source_path)),
                **classification
            }
            
            inventory['documents'].append(doc_entry)
            
            # Group by type
            doc_type = classification['type']
            if doc_type not in inventory['by_type']:
                inventory['by_type'][doc_type] = []
            inventory['by_type'][doc_type].append(doc_entry)
            
            # Group by wiki section
            section = classification['wiki_section']
            if section not in inventory['by_section']:
                inventory['by_section'][section] = []
            inventory['by_section'][section].append(doc_entry)
    
    # Build agent dispatch plan
    for agent_name, doc_types in AGENT_GROUPS.items():
        agent_docs = []
        for doc_type in doc_types:
            if doc_type in inventory['by_type']:
                agent_docs.extend(inventory['by_type'][doc_type])
        
        if agent_docs:
            inventory['agent_dispatch'][agent_name] = {
                'document_count': len(agent_docs),
                'documents': [d['relative_path'] for d in agent_docs],
                'wiki_sections': list(set(d['wiki_section'] for d in agent_docs))
            }
    
    return inventory


def print_summary(inventory: dict):
    """Print human-readable summary."""
    print("\n" + "="*60)
    print("📁 WIKI SOURCE INVENTORY")
    print("="*60)
    print(f"\nSource: {inventory['source_directory']}")
    print(f"Scanned: {inventory['scan_date']}")
    print(f"Total documents: {len(inventory['documents'])}")
    
    print("\n📊 BY DOCUMENT TYPE:")
    for doc_type, docs in sorted(inventory['by_type'].items()):
        print(f"  • {doc_type}: {len(docs)} file(s)")
    
    print("\n📂 BY WIKI SECTION:")
    for section, docs in sorted(inventory['by_section'].items()):
        print(f"  • {section}: {len(docs)} file(s)")
    
    print("\n🤖 AGENT DISPATCH PLAN:")
    for agent, info in inventory['agent_dispatch'].items():
        print(f"\n  Agent: {agent.upper()}")
        print(f"    Documents: {info['document_count']}")
        print(f"    Wiki sections: {', '.join(info['wiki_sections'])}")
        for doc in info['documents'][:3]:
            print(f"      - {doc}")
        if len(info['documents']) > 3:
            print(f"      ... and {len(info['documents']) - 3} more")
    
    print("\n" + "="*60)


def main():
    if len(sys.argv) < 2:
        print("Usage: inventory-sources.py <source-directory> [--json]")
        print("\nScans a directory for campaign outputs and classifies them for wiki generation.")
        sys.exit(1)
    
    source_dir = sys.argv[1]
    output_json = '--json' in sys.argv
    
    inventory = scan_directory(source_dir)
    
    if output_json:
        print(json.dumps(inventory, indent=2))
    else:
        print_summary(inventory)
        
        # Also save JSON for programmatic use
        output_path = Path(source_dir) / 'wiki-inventory.json'
        with open(output_path, 'w') as f:
            json.dump(inventory, f, indent=2)
        print(f"\n💾 Full inventory saved to: {output_path}")


if __name__ == '__main__':
    main()
