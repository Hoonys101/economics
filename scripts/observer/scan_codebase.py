import os
import re
import argparse
from typing import Dict, List, Tuple
from collections import defaultdict
import datetime

# Configuration
TARGET_EXTENSIONS = ['.py', '.tsx', '.ts', '.md']
IGNORE_DIRS = ['venv', '__pycache__', '.git', 'node_modules', '.gemini', 'reports']
TAGS_TO_SCAN = ['TODO', 'FIXME', 'HACK', 'REVIEW', 'NOTE', 'XXX']

def scan_file(filepath: str) -> Dict:
    metrics = {
        'lines': 0,
        'tags': defaultdict(list),
        'imports': []
    }
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            metrics['lines'] = len(lines)
            
            for i, line in enumerate(lines):
                # Tag Scanning
                for tag in TAGS_TO_SCAN:
                    if tag in line:
                        clean_line = line.strip()[:100]  # Truncate for display
                        metrics['tags'][tag].append((i + 1, clean_line))
                
                # Import Scanning (Python Only for now)
                if filepath.endswith('.py'):
                    if line.strip().startswith('import ') or line.strip().startswith('from '):
                        metrics['imports'].append(line.strip())
                        
    except Exception as e:
        print(f"Error scanning {filepath}: {e}")
        
    return metrics

def scan_directory(root_dir: str) -> Dict[str, Dict]:
    results = {}
    
    for root, dirs, files in os.walk(root_dir):
        # Filter directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        # Exclude observer script directory to avoid self-flagging
        if "scripts\\observer" in root or "scripts/observer" in root:
            continue
        
        for file in files:
            if any(file.endswith(ext) for ext in TARGET_EXTENSIONS):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, root_dir)
                results[rel_path] = scan_file(filepath)
                
    return results

def generate_report(results: Dict[str, Dict], output_format: str = 'markdown') -> str:
    total_files = len(results)
    total_lines = sum(r['lines'] for r in results.values())
    total_tags = defaultdict(int)
    tag_locations = defaultdict(list)
    
    # Complexity Analysis
    complex_files = sorted(
        [(k, v['lines']) for k, v in results.items()], 
        key=lambda x: x[1], 
        reverse=True
    )[:10]
    
    # Tag Aggregation
    for fpath, data in results.items():
        for tag, items in data['tags'].items():
            total_tags[tag] += len(items)
            for lineno, content in items:
                tag_locations[tag].append((fpath, lineno, content))

    report = []
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report.append(f"# 🕵️ Observer Scan Report")
    report.append(f"**Date:** {timestamp}")
    report.append(f"**Total Files:** {total_files}")
    report.append(f"**Total Lines:** {total_lines}")
    report.append("")
    
    report.append("## 1. 🏗️ Complexity Watchlist (Top 10 Big Files)")
    report.append("| File | Lines | Status |")
    report.append("|---|---|---|")
    for fpath, lines in complex_files:
        status = "🔴 Critical" if lines > 800 else "🟡 Warning" if lines > 400 else "🟢 Safe"
        report.append(f"| `{fpath}` | {lines} | {status} |")
    report.append("")
    
    report.append("## 2. 🏷️ Tech Debt Tags")
    report.append("| Tag | Count | Description |")
    report.append("|---|---|---|")
    for tag in TAGS_TO_SCAN:
        count = total_tags[tag]
        desc = "Action Required" if tag in ['FIXME', 'XXX'] else "Review Needed"
        report.append(f"| **{tag}** | {count} | {desc} |")
    report.append("")
    
    report.append("### Critical Fixes (FIXME/XXX)")
    critical_tags = tag_locations.get('FIXME', []) + tag_locations.get('XXX', [])
    if not critical_tags:
        report.append("No critical tags found. Great job! 🎉")
    else:
        for fpath, lineno, content in critical_tags[:20]: # Limit to 20
            report.append(f"- [ ] `{fpath}:{lineno}` - {content}")
    
    if len(critical_tags) > 20:
        report.append(f"... and {len(critical_tags) - 20} more.")
        
    return "\n".join(report)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Observer Codebase Scanner")
    parser.add_argument("--root", default=".", help="Root directory to scan")
    parser.add_argument("--output", default="reports/observer_scan.md", help="Output report file")
    
    args = parser.parse_args()
    
    print(f"Scanning codebase at {args.root}...")
    scan_results = scan_directory(args.root)
    report_content = generate_report(scan_results)
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"Scan complete. Report generated at {args.output}")
