#!/usr/bin/env python
"""
HTML Report Generator for Enhanced Parser Validation
Creates interactive HTML reports with charts and visualizations

WORKSTREAM 3: Enhanced Parser Validation - HTML Reporting

Usage:
    # Generate from existing JSON report
    python tests/generate_html_report.py docs/enhanced_parser_validation_report.json
    
    # Specify output location
    python tests/generate_html_report.py report.json --output reports/validation.html
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

def generate_html_report(json_path: Path, output_path: Path):
    """
    Generate HTML report from JSON validation results.
    
    Args:
        json_path: Path to JSON validation report
        output_path: Path for output HTML file
    """
    # Load JSON data
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Extract key metrics
    summary = data.get('summary', {})
    agg_metrics = data.get('aggregate_metrics', {})
    quality_score = data.get('overall_quality_score', 0)
    test_results = data.get('test_results', [])
    
    # Determine status color
    if quality_score >= 90:
        status_color = "#4CAF50"  # Green
        status_label = "EXCELLENT"
    elif quality_score >= 75:
        status_color = "#FFC107"  # Amber
        status_label = "GOOD"
    elif quality_score >= 60:
        status_color = "#FF9800"  # Orange
        status_label = "ACCEPTABLE"
    else:
        status_color = "#F44336"  # Red
        status_label = "NEEDS IMPROVEMENT"
    
    # Generate HTML
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Enhanced Parser Validation Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .header .date {{
            opacity: 0.9;
            font-size: 0.9em;
        }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f9f9f9;
        }}
        
        .metric {{
            text-align: center;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        }}
        
        .metric .value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }}
        
        .metric .label {{
            font-size: 0.9em;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .quality-score {{
            text-align: center;
            padding: 40px;
            background: {status_color};
            color: white;
        }}
        
        .quality-score .score {{
            font-size: 4em;
            font-weight: bold;
            margin: 20px 0;
        }}
        
        .quality-score .status {{
            font-size: 1.5em;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}
        
        .section {{
            padding: 40px;
        }}
        
        .section h2 {{
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        
        .test-results {{
            display: grid;
            gap: 20px;
        }}
        
        .test-card {{
            background: #f9f9f9;
            border-left: 4px solid #667eea;
            padding: 20px;
            border-radius: 4px;
            transition: transform 0.2s;
        }}
        
        .test-card:hover {{
            transform: translateX(5px);
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
        }}
        
        .test-card.failed {{
            border-left-color: #F44336;
        }}
        
        .test-card .name {{
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .test-card .status {{
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            margin-bottom: 15px;
        }}
        
        .status.pass {{
            background: #4CAF50;
            color: white;
        }}
        
        .status.fail {{
            background: #F44336;
            color: white;
        }}
        
        .test-card .metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        
        .test-card .metric-item {{
            font-size: 0.9em;
        }}
        
        .test-card .metric-item .label {{
            color: #666;
            font-size: 0.85em;
        }}
        
        .test-card .metric-item .value {{
            font-weight: bold;
            color: #333;
            font-size: 1.1em;
        }}
        
        .progress-bar {{
            width: 100%;
            height: 30px;
            background: #e0e0e0;
            border-radius: 15px;
            overflow: hidden;
            margin: 20px 0;
        }}
        
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }}
        
        .issues {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        
        .issues.critical {{
            background: #f8d7da;
            border-left-color: #f44336;
        }}
        
        .issues h3 {{
            margin-bottom: 10px;
            color: #856404;
        }}
        
        .issues.critical h3 {{
            color: #721c24;
        }}
        
        .issues ul {{
            list-style-position: inside;
            margin-left: 10px;
        }}
        
        footer {{
            text-align: center;
            padding: 20px;
            background: #f9f9f9;
            color: #666;
            font-size: 0.9em;
        }}
        
        @media print {{
            body {{
                background: white;
            }}
            
            .container {{
                box-shadow: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>📊 Enhanced Parser Validation Report</h1>
            <p class="date">Generated: {data.get('report_date', 'N/A')}</p>
        </div>
        
        <!-- Quality Score -->
        <div class="quality-score">
            <div class="status">{status_label}</div>
            <div class="score">{quality_score:.1f}/100</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {quality_score}%;">
                    {quality_score:.0f}%
                </div>
            </div>
        </div>
        
        <!-- Summary Metrics -->
        <div class="summary">
            <div class="metric">
                <div class="label">Total Scenarios</div>
                <div class="value">{summary.get('total_scenarios', 0)}</div>
            </div>
            <div class="metric">
                <div class="label">Successful</div>
                <div class="value" style="color: #4CAF50">{summary.get('successful_scenarios', 0)}</div>
            </div>
            <div class="metric">
                <div class="label">Failed</div>
                <div class="value" style="color: #F44336">{summary.get('failed_scenarios', 0)}</div>
            </div>
            <div class="metric">
                <div class="label">Success Rate</div>
                <div class="value">{summary.get('success_rate', '0%')}</div>
            </div>
            <div class="metric">
                <div class="label">Avg EBITDA Risk</div>
                <div class="value">{agg_metrics.get('avg_ebitda_risk_score', 0):.1f}/10</div>
            </div>
            <div class="metric">
                <div class="label">Avg LME Risk</div>
                <div class="value">{agg_metrics.get('avg_lme_risk_score', 0):.1f}/10</div>
            </div>
            <div class="metric">
                <div class="label">Total LME Risks</div>
                <div class="value">{agg_metrics.get('total_lme_risks_found', 0)}</div>
            </div>
            <div class="metric">
                <div class="label">EBITDA Detection</div>
                <div class="value">{agg_metrics.get('ebitda_detection_rate', '0%')}</div>
            </div>
        </div>
        
        <!-- Issues & Warnings -->
        <div class="section">
"""
    
    # Add critical issues
    critical_issues = data.get('critical_issues', [])
    if critical_issues:
        html += """
            <div class="issues critical">
                <h3>⚠️ Critical Issues</h3>
                <ul>
"""
        for issue in critical_issues:
            html += f"                    <li>{issue}</li>\n"
        html += """
                </ul>
            </div>
"""
    
    # Add warnings
    warnings = data.get('warnings', [])
    if warnings:
        html += """
            <div class="issues">
                <h3>⚡ Warnings</h3>
                <ul>
"""
        for warning in warnings:
            html += f"                    <li>{warning}</li>\n"
        html += """
                </ul>
            </div>
"""
    
    html += """
        </div>
        
        <!-- Test Results -->
        <div class="section">
            <h2>📋 Detailed Test Results</h2>
            <div class="test-results">
"""
    
    # Add test cards
    for i, result in enumerate(test_results, 1):
        status_class = "pass" if result.get('success') else "fail"
        card_class = "test-card" if result.get('success') else "test-card failed"
        status_emoji = "✅" if result.get('success') else "❌"
        
        html += f"""
                <div class="{card_class}">
                    <div class="name">{i}. {result.get('scenario_name', 'Unknown')}</div>
                    <span class="status {status_class}">{status_emoji} {'PASS' if result.get('success') else 'FAIL'}</span>
                    <div style="color: #666; margin: 10px 0;">
                        <strong>Type:</strong> {result.get('document_type', 'N/A')}
                    </div>
"""
        
        if result.get('success'):
            html += """
                    <div class="metrics">
"""
            if result.get('ebitda_found'):
                html += f"""
                        <div class="metric-item">
                            <div class="label">EBITDA Risk</div>
                            <div class="value">{result.get('ebitda_risk_score', 0):.1f}/10.0</div>
                        </div>
"""
            if result.get('lme_risks_found', 0) > 0:
                html += f"""
                        <div class="metric-item">
                            <div class="label">LME Risks</div>
                            <div class="value">{result.get('lme_risks_found', 0)}</div>
                        </div>
                        <div class="metric-item">
                            <div class="label">Max LME Risk</div>
                            <div class="value">{result.get('max_lme_risk_score', 0):.1f}/10.0</div>
                        </div>
"""
            if result.get('debt_tranches_found', 0) > 0:
                html += f"""
                        <div class="metric-item">
                            <div class="label">Tranches Found</div>
                            <div class="value">{result.get('debt_tranches_found', 0)}</div>
                        </div>
"""
            
            html += f"""
                        <div class="metric-item">
                            <div class="label">Extraction Time</div>
                            <div class="value">{result.get('extraction_time_ms', 0):.1f}ms</div>
                        </div>
"""
            html += """
                    </div>
"""
        else:
            html += f"""
                    <div style="color: #F44336; margin-top: 10px;">
                        <strong>Error:</strong> {result.get('error_message', 'Unknown error')}
                    </div>
"""
        
        html += """
                </div>
"""
    
    html += """
            </div>
        </div>
        
        <!-- Footer -->
        <footer>
            <p>Enhanced Parser Validation Report | Signal-Triage Workstream 3</p>
            <p>Generated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
        </footer>
    </div>
</body>
</html>
"""
    
    # Write HTML file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ HTML report generated: {output_path}")
    print(f"   Open in browser: file://{output_path.resolve()}")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate HTML report from validation JSON"
    )
    
    parser.add_argument(
        'json_file',
        type=Path,
        help='Path to JSON validation report'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=None,
        help='Output HTML file path (default: same location as JSON with .html extension)'
    )
    
    args = parser.parse_args()
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        output_path = args.json_file.with_suffix('.html')
    
    # Generate report
    try:
        generate_html_report(args.json_file, output_path)
        return 0
    except FileNotFoundError:
        print(f"❌ Error: JSON file not found: {args.json_file}")
        return 1
    except json.JSONDecodeError:
        print(f"❌ Error: Invalid JSON in file: {args.json_file}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
