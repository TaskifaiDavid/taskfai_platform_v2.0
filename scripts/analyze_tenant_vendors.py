#!/usr/bin/env python3
"""
ABOUTME: Script to analyze tenant-vendor relationships from upload_batches table
ABOUTME: Generates analytics for DRY/YAGNI refactoring planning
"""

import os
import sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import json

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'backend'))

from supabase import create_client


def analyze_demo_tenant():
    """Analyze demo tenant (main Supabase instance)"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_KEY')

    if not url or not key:
        print("ERROR: SUPABASE_URL or SUPABASE_SERVICE_KEY not found in environment")
        return None

    try:
        client = create_client(url, key)

        # Query upload batches
        response = client.table('upload_batches') \
            .select('tenant_id,vendor_name,upload_timestamp,total_records,processing_status') \
            .not_.is_('vendor_name', 'null') \
            .execute()

        return analyze_batches(response.data, 'demo')
    except Exception as e:
        print(f"WARNING: Could not access demo tenant database: {e}")
        return None


def analyze_bibbi_tenant():
    """Analyze BIBBI tenant (separate Supabase instance)"""
    url = os.getenv('BIBBI_SUPABASE_URL')
    key = os.getenv('BIBBI_SUPABASE_SERVICE_KEY')

    if not url or not key:
        print("WARNING: BIBBI credentials not found, skipping BIBBI analysis")
        return None

    try:
        client = create_client(url, key)

        # Query upload batches
        response = client.table('upload_batches') \
            .select('tenant_id,vendor_name,upload_timestamp,total_records,processing_status') \
            .not_.is_('vendor_name', 'null') \
            .execute()

        return analyze_batches(response.data, 'bibbi')
    except Exception as e:
        print(f"WARNING: Could not access BIBBI tenant database: {e}")
        return None


def analyze_batches(batches, tenant_label):
    """Analyze upload batches and extract vendor usage patterns"""
    if not batches:
        print(f"No upload batches found for {tenant_label}")
        return None

    vendor_stats = defaultdict(lambda: {
        'upload_count': 0,
        'total_records': 0,
        'first_upload': None,
        'latest_upload': None,
        'statuses': defaultdict(int)
    })

    tenant_vendor_map = defaultdict(set)

    for batch in batches:
        tenant_id = batch.get('tenant_id', 'unknown')
        vendor = batch.get('vendor_name')
        timestamp = batch.get('upload_timestamp')
        records = batch.get('total_records', 0)
        status = batch.get('processing_status', 'unknown')

        if not vendor:
            continue

        # Track vendor usage
        vendor_stats[vendor]['upload_count'] += 1
        vendor_stats[vendor]['total_records'] += records
        vendor_stats[vendor]['statuses'][status] += 1

        if timestamp:
            if not vendor_stats[vendor]['first_upload'] or timestamp < vendor_stats[vendor]['first_upload']:
                vendor_stats[vendor]['first_upload'] = timestamp
            if not vendor_stats[vendor]['latest_upload'] or timestamp > vendor_stats[vendor]['latest_upload']:
                vendor_stats[vendor]['latest_upload'] = timestamp

        # Track tenant-vendor relationships
        tenant_vendor_map[tenant_id].add(vendor)

    return {
        'tenant_label': tenant_label,
        'vendor_stats': dict(vendor_stats),
        'tenant_vendor_map': {k: list(v) for k, v in tenant_vendor_map.items()},
        'total_batches': len(batches),
        'unique_vendors': len(vendor_stats),
        'unique_tenants': len(tenant_vendor_map)
    }


def generate_report(demo_analysis, bibbi_analysis):
    """Generate markdown report of tenant-vendor analysis"""

    report_lines = [
        "# Tenant-Vendor Relationship Analysis",
        "",
        f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Executive Summary",
        ""
    ]

    # Summary section
    all_vendors = set()
    total_batches = 0

    if demo_analysis:
        all_vendors.update(demo_analysis['vendor_stats'].keys())
        total_batches += demo_analysis['total_batches']
        report_lines.append(f"- **Demo Tenant**: {demo_analysis['unique_vendors']} vendors, {demo_analysis['total_batches']} upload batches")

    if bibbi_analysis:
        all_vendors.update(bibbi_analysis['vendor_stats'].keys())
        total_batches += bibbi_analysis['total_batches']
        report_lines.append(f"- **BIBBI Tenant**: {bibbi_analysis['unique_vendors']} vendors, {bibbi_analysis['total_batches']} upload batches")

    report_lines.extend([
        f"- **Total Unique Vendors**: {len(all_vendors)}",
        f"- **Total Upload Batches**: {total_batches}",
        "",
        "## Vendor Usage by Tenant",
        ""
    ])

    # Demo tenant details
    if demo_analysis:
        report_lines.extend([
            "### Demo Tenant",
            "",
            "| Vendor | Uploads | Total Records | First Upload | Latest Upload | Success Rate |",
            "|--------|---------|---------------|--------------|---------------|--------------|"
        ])

        for vendor, stats in sorted(demo_analysis['vendor_stats'].items(),
                                    key=lambda x: x[1]['upload_count'], reverse=True):
            success_count = stats['statuses'].get('completed', 0)
            total_count = stats['upload_count']
            success_rate = f"{(success_count/total_count*100):.1f}%" if total_count > 0 else "N/A"

            first = stats['first_upload'][:10] if stats['first_upload'] else 'N/A'
            latest = stats['latest_upload'][:10] if stats['latest_upload'] else 'N/A'

            report_lines.append(
                f"| {vendor} | {stats['upload_count']} | {stats['total_records']} | "
                f"{first} | {latest} | {success_rate} |"
            )

        report_lines.extend(["", "**Tenant-Vendor Mapping (Demo)**:", ""])
        for tenant_id, vendors in demo_analysis['tenant_vendor_map'].items():
            report_lines.append(f"- `{tenant_id}`: {', '.join(sorted(vendors))}")
        report_lines.append("")

    # BIBBI tenant details
    if bibbi_analysis:
        report_lines.extend([
            "### BIBBI Tenant",
            "",
            "| Vendor | Uploads | Total Records | First Upload | Latest Upload | Success Rate |",
            "|--------|---------|---------------|--------------|---------------|--------------|"
        ])

        for vendor, stats in sorted(bibbi_analysis['vendor_stats'].items(),
                                    key=lambda x: x[1]['upload_count'], reverse=True):
            success_count = stats['statuses'].get('completed', 0)
            total_count = stats['upload_count']
            success_rate = f"{(success_count/total_count*100):.1f}%" if total_count > 0 else "N/A"

            first = stats['first_upload'][:10] if stats['first_upload'] else 'N/A'
            latest = stats['latest_upload'][:10] if stats['latest_upload'] else 'N/A'

            report_lines.append(
                f"| {vendor} | {stats['upload_count']} | {stats['total_records']} | "
                f"{first} | {latest} | {success_rate} |"
            )

        report_lines.extend(["", "**Tenant-Vendor Mapping (BIBBI)**:", ""])
        for tenant_id, vendors in bibbi_analysis['tenant_vendor_map'].items():
            report_lines.append(f"- `{tenant_id}`: {', '.join(sorted(vendors))}")
        report_lines.append("")

    # All vendors summary
    report_lines.extend([
        "## All Vendors (Across Both Tenants)",
        "",
        f"Total unique vendors identified: **{len(all_vendors)}**",
        "",
        "```",
        "\n".join(sorted(all_vendors)),
        "```",
        "",
        "## Key Insights",
        "",
        f"1. **Vendor Distribution**: {len(all_vendors)} vendors across 2 tenant databases",
        "2. **Usage Pattern**: See table above for vendor-specific upload counts",
        "3. **Success Rates**: Processing success rates vary by vendor",
        "",
        "## Next Steps for Refactoring",
        "",
        "1. **Identify Shared Vendors**: Vendors used by multiple tenants → good candidates for shared base class",
        "2. **Low-Usage Vendors**: Vendors with <5 uploads → consider YAGNI analysis",
        "3. **High-Complexity Vendors**: Review processor code for duplication patterns",
        ""
    ])

    return "\n".join(report_lines)


if __name__ == '__main__':
    # Load environment variables from backend/.env
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / 'backend' / '.env'
    load_dotenv(env_path)

    print("Analyzing tenant-vendor relationships...")

    # Analyze both tenants
    demo_analysis = analyze_demo_tenant()
    bibbi_analysis = analyze_bibbi_tenant()

    if not demo_analysis and not bibbi_analysis:
        print("ERROR: No data collected from any tenant")
        sys.exit(1)

    # Generate report
    report = generate_report(demo_analysis, bibbi_analysis)

    # Write to claudedocs
    output_dir = Path(__file__).parent.parent / 'claudedocs'
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / 'vendor_usage_analysis.md'
    output_file.write_text(report)

    print(f"\n✓ Analysis complete!")
    print(f"  Report saved to: {output_file}")
    print(f"\n{report}")
