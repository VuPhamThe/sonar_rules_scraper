# SonarQube Community Rules Scraper

This script scrapes [rules.sonarsource.com](https://rules.sonarsource.com) to collect all rules are not available in **Community Edition** and exports them into a CSV file.

## Requirements

-   OS linux or wsl on window
-   Python 3.9+
-   pip (inside venv recommended)

## Setup

``` bash
sudo apt update
sudo apt install -y python3-venv
python3 -m venv venv
source venv/bin/activate
pip install requests beautifulsoup4 tqdm
```

## Run

``` bash
python sonar_rules_scraper.py
```

or use Codespaces of github

## Output

-   `sonarqube_community_rules.csv` containing:
    -   Key
    -   Title
    -   Language
    -   Type
    -   AvailableIn
