"""
Downloads Organizer Script

A script to organize files in the Downloads folder into categorized subdirectories.
Generates JSON and HTML reports with statistics and file metadata.

DISCLAIMER: This script is provided "AS IS" without warranties of any kind. 
Use at your own risk. Always test with --dry-run first and back up your data.
"""

import os
import shutil
import hashlib
import json
from pathlib import Path
import argparse
from datetime import datetime
from collections import defaultdict
import jinja2

# --------------------------
# Configuration Section
# --------------------------

# Define file categories and their associated extensions
FILE_CATEGORIES = {
    "Documents": [".pdf", ".docx", ".txt", ".rtf", ".xlsx", ".pptx", ".md"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".svg", ".bmp", ".webp"],
    "Music": [".mp3", ".wav", ".flac", ".aac", ".ogg"],
    "Videos": [".mp4", ".mov", ".avi", ".mkv", ".flv", ".webm"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Executables": [".exe", ".msi", ".dmg", ".pkg", ".deb"],
    "Scripts": [".py", ".js", ".sh", ".bat", ".ps1"]
}

# Default category for unrecognized file types
DEFAULT_CATEGORY = "Miscellaneous"

# Path configuration (Note: Adjust these paths according to your system)
# WARNING: Hardcoded path might need modification for different environments
DOWNLOADS_PATH = Path.home() / "Downloads"

# Path to the Organized folder
ORGANIZED_PATH = DOWNLOADS_PATH / "Organized"

# --------------------------
# Core Functions
# --------------------------

# Function to get the category of a file based on its extension
def get_file_category(file_extension):
    for category, extensions in FILE_CATEGORIES.items():
        if file_extension.lower() in extensions:
            return category
    return DEFAULT_CATEGORY

# Function to get the hash of a file
def get_file_hash(file_path):
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

# Function to generate an HTML report
def generate_html_report(report_data, output_path):
    template_str = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Downloads Organization Report</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: Arial, sans-serif; margin: 2rem; }
            .chart-container { margin: 2rem 0; max-width: 800px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
            tr:hover { background-color: #f5f5f5; }
        </style>
    </head>
    <body>
        <h1>Organization Report</h1>
        
        <div class="chart-container">
            <h2>File Type Distribution</h2>
            <canvas id="typeChart"></canvas>
        </div>

        <div class="chart-container">
            <h2>File Type History</h2>
            <canvas id="historyChart"></canvas>
        </div>

        <h2>Largest Files (Top 10)</h2>
        <table>
            <tr><th>File</th><th>Size (MB)</th><th>Type</th><th>Path</th></tr>
            {% for file in largest_files %}
            <tr>
                <td>{{ file.name }}</td>
                <td>{{ "%.2f"|format(file.size_mb) }}</td>
                <td>{{ file.category }}</td>
                <td>{{ file.new_path }}</td>
            </tr>
            {% endfor %}
        </table>

        <h2>Oldest Files (Top 10)</h2>
        <table>
            <tr><th>File</th><th>Last Modified</th><th>Type</th><th>Path</th></tr>
            {% for file in oldest_files %}
            <tr>
                <td>{{ file.name }}</td>
                <td>{{ file.modified[:10] }}</td>
                <td>{{ file.category }}</td>
                <td>{{ file.new_path }}</td>
            </tr>
            {% endfor %}
        </table>

        <script>
            // Pie Chart
            new Chart(document.getElementById('typeChart'), {
                type: 'pie',
                data: {
                    labels: {{ categories|tojson }},
                    datasets: [{
                        data: {{ counts|tojson }},
                        backgroundColor: [
                            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0',
                            '#9966FF', '#FF9F40', '#E7E9ED'
                        ]
                    }]
                }
            });

            // History Chart
            const historyData = {{ file_history|tojson }};
            new Chart(document.getElementById('historyChart'), {
                type: 'line',
                data: {
                    labels: historyData.dates,
                    datasets: Object.entries(historyData.types).map(([type, counts]) => ({
                        label: type,
                        data: counts,
                        borderWidth: 2,
                        fill: false
                    }))
                },
                options: {
                    responsive: true,
                    scales: { y: { beginAtZero: true } }
                }
            });
        </script>
    </body>
    </html>
    """

    # Prepare chart data
    categories = list(report_data['category_stats'].keys())
    counts = list(report_data['category_stats'].values())
    
    # Generate file type history
    file_history = defaultdict(lambda: {'dates': set(), 'types': defaultdict(int)})
    for file in report_data['all_files']:
        month = file['modified'][:7]
        file_history['dates'].add(month)
        file_history['types'][file['category']] += 1

    dates = sorted(file_history['dates'])
    type_data = defaultdict(list)
    for date in dates:
        for cat in categories:
            type_data[cat].append(file_history['types'][cat].get(date, 0))

    template = jinja2.Template(template_str)
    html = template.render(
        categories=categories,
        counts=counts,
        largest_files=report_data['largest_files'][:10],
        oldest_files=report_data['oldest_files'][:10],
        file_history={'dates': dates, 'types': type_data}
    )

    with open(output_path, 'w') as f:
        f.write(html)

# Function to organize files
def organize_files(organize_by_date=False, dry_run=False):
    stats = defaultdict(int)
    all_files = []
    duplicates = 0
    total_size = 0
    start_time = datetime.now()

    if not dry_run and not ORGANIZED_PATH.exists():
        ORGANIZED_PATH.mkdir()

    for item in DOWNLOADS_PATH.iterdir():
        if item.is_dir() or item == ORGANIZED_PATH:
            continue

        ext = item.suffix
        category = get_file_category(ext)
        modified_date = datetime.fromtimestamp(item.stat().st_mtime)
        
        if organize_by_date:
            date_folder = modified_date.strftime("%Y-%m")
            dest_folder = ORGANIZED_PATH / category / date_folder
        else:
            dest_folder = ORGANIZED_PATH / category

        if not dry_run and not dest_folder.exists():
            dest_folder.mkdir(parents=True)

        dest_path = dest_folder / item.name
        if dest_path.exists():
            file_hash = get_file_hash(item)
            dest_hash = get_file_hash(dest_path)
            
            if file_hash == dest_hash:
                duplicates += 1
                if not dry_run:
                    item.unlink()
                continue
            else:
                counter = 1
                while dest_path.exists():
                    dest_path = dest_folder / f"{item.stem}_{counter}{ext}"
                    counter += 1

        file_info = {
            'name': item.name,
            'category': category,
            'size_mb': round(item.stat().st_size / (1024 * 1024), 2),
            'modified': modified_date.isoformat(),
            'new_path': str(dest_path.relative_to(ORGANIZED_PATH))
        }
        all_files.append(file_info)

        stats[category] += 1
        total_size += item.stat().st_size

        if not dry_run:
            try:
                shutil.move(str(item), str(dest_path))
            except Exception as e:
                print(f"Error moving {item.name}: {str(e)}")

    # Prepare report data
    all_files_sorted = sorted(all_files, key=lambda x: x['modified'])
    largest_files = sorted(all_files, key=lambda x: x['size_mb'], reverse=True)

    # Generate reports
    report_data = {
        'metadata': {
            'timestamp': start_time.isoformat(),
            'duration_seconds': round((datetime.now() - start_time).total_seconds(), 2),
            'source_folder': str(DOWNLOADS_PATH),
            'target_folder': str(ORGANIZED_PATH),
            'total_files_processed': sum(stats.values()),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'duplicates_found': duplicates
        },
        'category_stats': dict(stats),
        'all_files': all_files,
        'largest_files': largest_files,
        'oldest_files': all_files_sorted
    }

    # Generate reports
    if not dry_run:
        # JSON report
        json_report_path = ORGANIZED_PATH / f"report_{start_time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        # HTML report
        html_report_path = ORGANIZED_PATH / f"report_{start_time.strftime('%Y%m%d_%H%M%S')}.html"
        generate_html_report(report_data, html_report_path)

    # Console output
    print("\n=== Organization Summary ===")
    print(f"Total files processed: {sum(stats.values())}")
    print(f"Duplicates found/removed: {duplicates}")
    print(f"Total space used: {report_data['metadata']['total_size_mb']} MB")
    print("\nFile Type Breakdown:")
    for category, count in stats.items():
        print(f"- {category}: {count} files")
    
    if not dry_run:
        print(f"\nReports generated:")
        print(f"- JSON: {json_report_path}")
        print(f"- HTML: {html_report_path}")

# --------------------------
# Main Execution
# --------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Organize Downloads folder with reports")
    parser.add_argument("--dry-run", action="store_true", help="Simulate without moving files")
    parser.add_argument("--organize-by-date", action="store_true", help="Create date-based subfolders")
    args = parser.parse_args()

    print("=== Downloads Organizer ===")
    print(f"Source: {DOWNLOADS_PATH}")
    print(f"Destination: {ORGANIZED_PATH}")
    
    organize_files(
        organize_by_date=args.organize_by_date,
        dry_run=args.dry_run
    )
