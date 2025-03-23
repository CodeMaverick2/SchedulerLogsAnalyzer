# Scheduler Log Analyzer

Automated tool to analyze scheduler logs and generate detailed PDF reports with focus on scheduled vs unscheduled task analysis.

## Prerequisites

- Python 3.10
- Access to AWS QuickSight dashboard
- Scheduler logs access

## Installation

### macOS

1. Install Python 3.10 using Homebrew:
```bash
brew install python@3.10
```

2. Create and activate virtual environment:
```bash
python3.10 -m venv venv
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install --upgrade pip
pip install wheel setuptools
pip install numpy==1.24.3  # Required for pandas compatibility
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
playwright install
# For macOS system dependencies
brew install --cask chromium  # For Chromium browser
xattr -d com.apple.quarantine /Applications/Chromium.app  # If needed
```

5. Create required directories:
```bash
mkdir -p reports logs config
```

### Linux/Windows

1. Install Python 3.10:
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev

# Windows: Download from python.org
```

2. Create and activate virtual environment:
```bash
# Linux
python3.10 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install --upgrade pip
pip install wheel setuptools
pip install numpy==1.24.3
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
playwright install
playwright install --with-deps  # For Linux system dependencies
```

## Configuration

1. Copy the example config:
```bash
cp config/config.example.yaml config/config.yaml
```

2. Set up environment variables:

```env
AWS_DASHBOARD_URL=your-dashboard-url
AWS_USERNAME=your-username
AWS_PASSWORD=your-password
```
## Troubleshooting

### macOS Specific
1. If Chromium installation fails:
```bash
brew update && brew upgrade
brew install --cask chromium
```

2. If you get permissions errors:
```bash
sudo chown -R $(whoami) $(brew --prefix)/*
```

3. For PDF generation on macOS:
```bash
pip install reportlab --no-cache-dir
```
