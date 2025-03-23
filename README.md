# Downloads Organizer

![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)

A script to automatically organize your Downloads folder into categorized subdirectories and generate detailed reports.

**Disclaimer**: This software is provided "AS IS" without any warranties. Use at your own risk. The author takes no responsibility for any data loss or system issues. Always test with `--dry-run` first and ensure you have proper backups.

## Features

- 📂 Automatic file categorization by type
- 📊 Generates HTML & JSON reports with:
  - File type distribution charts
  - Historical file additions graph
  - Largest files list
  - Oldest files list
- 🔍 Duplicate file detection using MD5 hashing
- 📅 Optional date-based organization (YYYY-MM subfolders)
- 🧪 Dry-run mode for safe testing

## Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/downloads-organizer.git
```


3. Install dependencies:
```
pip install jinja2
```

5. Usage:
```
python main.py [OPTIONS]
```

Options:
--dry-run: Test the script without making changes
--organize-by-date: Create monthly subfolders within categories

Example:
```
python main.py --organize-by-date
```

## Configuration
Modify these variables in main.py:

```
# Path to your Downloads folder
DOWNLOADS_PATH = Path.home() / "Downloads"  # Update this path
FILE_CATEGORIES = {  # Add/remove categories as needed
    # ... existing categories ...
}
```

## Important Notes
 - Always run with --dry-run first to preview changes
 - The script skips the 'Organized' directory if present
 - Duplicate files are automatically deleted after verification
 - Reports are saved in the Organized folder with timestamps
