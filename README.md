# Woodgate

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org/downloads/)
[![Selenium](https://img.shields.io/badge/Selenium-4.0%2B-green)](https://www.selenium.dev/)

A Python tool for automating searches and data extraction from the Red Hat Customer Portal using Selenium WebDriver.

## Features

- Automated login to Red Hat Customer Portal
- Configurable search parameters (query, products, document types, pagination)
- Result extraction with configurable sorting options
- Robust cookie popup handling
- Detailed logging and diagnostics

## Requirements

- Python 3.7+
- Chrome/Chromium browser
- Required Python packages (see `requirements.txt`)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/deadjoe/woodgate.git
   cd woodgate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables for secure authentication:
   ```bash
   export REDHAT_USERNAME="your_username"
   export REDHAT_PASSWORD="your_password"
   ```

## Usage

Run the script with Python:

```bash
python redhat_search.py
```

Or use the refactored version with improved code structure:

```bash
python redhat_search_refactored.py
```

### Search Configuration

Modify the `SEARCH_EXAMPLES` list in the script to configure search parameters:

```python
SEARCH_EXAMPLES = [
    {
        "query": "memory leak",
        "products": ["Red Hat Enterprise Linux", "Red Hat OpenShift"],
        "doc_types": ["Solution", "Article"],
        "page": 1,
        "rows": 20,
        "sort_by": "relevant"  # Options: "relevant", "lastModifiedDate desc", "lastModifiedDate asc"
    }
]
```

## Security Notes

- Using environment variables for credentials is strongly recommended
- Default credentials in the script are for example only and should be replaced

## License

This project is licensed under the MIT License - see the LICENSE file for details.