#!/usr/bin/env python3
"""
ABOUTME: Analyze codebase structure for DRY/YAGNI refactoring planning
ABOUTME: Focuses on vendor processors, code complexity, and duplication patterns
"""

import os
import re
from pathlib import Path
from collections import defaultdict
import ast


def analyze_vendor_processors(backend_dir):
    """Analyze vendor processor files for structure and patterns"""
    processors_dir = backend_dir / 'app' / 'services' / 'vendors'

    if not processors_dir.exists():
        processors_dir = backend_dir / 'app' / 'services' / 'bibbi' / 'processors'

    if not processors_dir.exists():
        print(f"ERROR: Could not find vendor processors directory")
        return None

    processors = []

    for processor_file in processors_dir.glob('*_processor.py'):
        try:
            content = processor_file.read_text()
            tree = ast.parse(content)

            # Extract methods from classes
            methods = []
            classes = []

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                    for item in node.body:
                        if isinstance(node, ast.FunctionDef):
                            methods.append(item.name)

            # Count lines and complexity
            lines = content.split('\n')
            code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]

            # Count imports
            imports = [l for l in lines if 'import ' in l]

            # Find common patterns
            patterns = {
                'has_process_method': 'def process(' in content,
                'uses_pandas': 'import pandas' in content or 'from pandas' in content,
                'uses_openpyxl': 'import openpyxl' in content or 'from openpyxl' in content,
                'has_normalize': 'normalize' in content.lower(),
                'has_validation': 'validate' in content.lower(),
                'has_error_handling': 'try:' in content and 'except' in content,
                'uses_logger': 'logger.' in content or 'logging.' in content
            }

            processors.append({
                'file': processor_file.name,
                'path': str(processor_file.relative_to(backend_dir)),
                'classes': classes,
                'methods': methods,
                'total_lines': len(lines),
                'code_lines': len(code_lines),
                'imports_count': len(imports),
                'patterns': patterns
            })

        except Exception as e:
            print(f"WARNING: Could not parse {processor_file.name}: {e}")

    return processors


def analyze_api_routes(backend_dir):
    """Analyze API routes for complexity and patterns"""
    api_dir = backend_dir / 'app' / 'api'

    if not api_dir.exists():
        print("WARNING: API directory not found")
        return None

    routes = []

    for api_file in api_dir.glob('*.py'):
        if api_file.name == '__init__.py':
            continue

        try:
            content = api_file.read_text()

            # Count endpoints
            endpoint_count = content.count('@router.')

            # Count dependencies
            dep_count = content.count('Depends(')

            # Lines of code
            lines = content.split('\n')
            code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]

            routes.append({
                'file': api_file.name,
                'path': str(api_file.relative_to(backend_dir)),
                'total_lines': len(lines),
                'code_lines': len(code_lines),
                'endpoints': endpoint_count,
                'dependencies': dep_count
            })

        except Exception as e:
            print(f"WARNING: Could not analyze {api_file.name}: {e}")

    return routes


def find_duplicated_code(backend_dir):
    """Find potential code duplication patterns"""
    # Simple heuristic: find similar function names across files
    function_signatures = defaultdict(list)

    for py_file in backend_dir.rglob('*.py'):
        if 'venv' in str(py_file) or '__pycache__' in str(py_file):
            continue

        try:
            content = py_file.read_text()
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Create signature based on name and arg count
                    sig = f"{node.name}({len(node.args.args)} args)"
                    function_signatures[sig].append(str(py_file.relative_to(backend_dir)))

        except:
            pass

    # Find duplicates (same signature in multiple files)
    duplicates = {sig: files for sig, files in function_signatures.items() if len(files) > 1}

    return duplicates


def generate_structure_report(processors, routes, duplicates, backend_dir):
    """Generate markdown report of code structure analysis"""

    report_lines = [
        "# Code Structure Analysis",
        "",
        "## Vendor Processors Analysis",
        "",
        f"**Total Processors Found**: {len(processors)}",
        "",
        "| File | Lines | Code Lines | Classes | Patterns |",
        "|------|-------|------------|---------|----------|"
    ]

    # Sort by code lines descending
    for proc in sorted(processors, key=lambda x: x['code_lines'], reverse=True):
        pattern_summary = ', '.join([k.replace('has_', '').replace('uses_', '')
                                    for k, v in proc['patterns'].items() if v])

        report_lines.append(
            f"| {proc['file']} | {proc['total_lines']} | {proc['code_lines']} | "
            f"{', '.join(proc['classes'])} | {pattern_summary} |"
        )

    # Common patterns
    report_lines.extend([
        "",
        "### Common Patterns Across Processors",
        ""
    ])

    # Count pattern frequency
    pattern_counts = defaultdict(int)
    for proc in processors:
        for pattern, present in proc['patterns'].items():
            if present:
                pattern_counts[pattern] += 1

    for pattern, count in sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(processors)) * 100
        report_lines.append(f"- **{pattern}**: {count}/{len(processors)} ({percentage:.0f}%)")

    # API Routes
    if routes:
        report_lines.extend([
            "",
            "## API Routes Analysis",
            "",
            f"**Total Route Files**: {len(routes)}",
            "",
            "| File | Lines | Endpoints | Dependencies |",
            "|------|-------|-----------|--------------|"
        ])

        for route in sorted(routes, key=lambda x: x['endpoints'], reverse=True):
            report_lines.append(
                f"| {route['file']} | {route['code_lines']} | {route['endpoints']} | {route['dependencies']} |"
            )

    # Duplication
    report_lines.extend([
        "",
        "## Potential Code Duplication",
        "",
        f"**Functions with same signature in multiple files**: {len(duplicates)}",
        ""
    ])

    # Show top duplicates
    top_duplicates = sorted(duplicates.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    for sig, files in top_duplicates:
        report_lines.append(f"### `{sig}`")
        report_lines.append(f"Found in {len(files)} files:")
        for f in files:
            report_lines.append(f"- {f}")
        report_lines.append("")

    # Recommendations
    report_lines.extend([
        "## DRY/YAGNI Refactoring Opportunities",
        "",
        "### High Priority (DRY Violations)",
        ""
    ])

    # Find processors with common patterns
    common_pattern_files = []
    for proc in processors:
        if all(proc['patterns'].get(p, False) for p in ['has_process_method', 'uses_pandas']):
            common_pattern_files.append(proc['file'])

    if common_pattern_files:
        report_lines.append(f"1. **Extract Common Processor Base Class**: {len(common_pattern_files)} processors share common patterns")
        report_lines.append(f"   - Files: {', '.join(common_pattern_files)}")
        report_lines.append("")

    # Find duplicated functions
    if len(duplicates) > 0:
        report_lines.append(f"2. **Consolidate Duplicated Functions**: {len(duplicates)} function signatures appear in multiple files")
        report_lines.append("")

    return "\n".join(report_lines)


if __name__ == '__main__':
    backend_dir = Path(__file__).parent.parent / 'backend'

    print("Analyzing codebase structure...")

    processors = analyze_vendor_processors(backend_dir)
    routes = analyze_api_routes(backend_dir)
    duplicates = find_duplicated_code(backend_dir)

    if not processors:
        print("ERROR: No processors found")
        exit(1)

    # Generate report
    report = generate_structure_report(processors, routes, duplicates, backend_dir)

    # Write to claudedocs
    output_dir = Path(__file__).parent.parent / 'claudedocs'
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / 'code_structure_analysis.md'
    output_file.write_text(report)

    print(f"\n✓ Code structure analysis complete!")
    print(f"  Report saved to: {output_file}")
    print(f"\nSummary:")
    print(f"  - {len(processors)} vendor processors")
    print(f"  - {len(routes) if routes else 0} API route files")
    print(f"  - {len(duplicates)} potentially duplicated functions")
