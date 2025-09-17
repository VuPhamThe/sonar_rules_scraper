import requests
from bs4 import BeautifulSoup
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import time
import os

BASE_URL = "https://rules.sonarsource.com"
LANGUAGES = [
    "java", "csharp", "python", "cpp", "javascript", "typescript",
    "php", "go", "ruby", "kotlin", "swift", "scala", "apex", "plsql",
    "cobol", "vbnet", "rpg", "abap", "xml", "html", "css"
]

FIELDS = ["Key", "Title", "Language", "Type", "AvailableIn"]

def get_rule_links(lang):
    url = f"{BASE_URL}/{lang}"
    r = requests.get(url, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    links = []
    for a in soup.select(f"a[href^='/{lang}/RSPEC-']"):
        links.append(BASE_URL + a["href"])
    return links

def extract_products(soup):
    products = []

    ul = soup.find("ul", class_=lambda c: c and "RuleAvailableInstyles__StyledList" in c)
    if not ul:
        return ""

    for a in ul.select("li > a"):
        href = a.get("href", "").lower()
        img = a.find("img")
        tooltip = a.find("span", class_=lambda c: c and "Tooltip" in (c or ""))
        edition_box = a.find("div", class_=lambda c: c and "EditionBox" in (c or ""))

        # --- product name ---
        product_name = ""
        if "sonarlint" in href:
            product_name = "SonarLint"
        elif "sonarcloud" in href:
            product_name = "SonarCloud"
        elif "community-edition" in href:
            product_name = "SonarQube Community Edition"
        elif "sonarqube" in href:
            product_name = "SonarQube Server"
        elif img and img.get("alt"):
            product_name = img["alt"].strip()

        # --- details (tooltip, edition info) ---
        details = []
        if tooltip:
            details.append(" ".join(tooltip.stripped_strings))
        if edition_box:
            details.append(" ".join(edition_box.stripped_strings))

        if details:
            product_name += f" ({' - '.join(details)})"

        if product_name:
            products.append(product_name)

    return "| ".join(products)

def parse_rule(url, retries=3):
    for attempt in range(retries):
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")

            key = url.split("/")[-2]  # RSPEC-XXXX
            title = soup.select_one("h1").get_text(strip=True) if soup.select_one("h1") else ""

            rule_type, available_in = "", ""

            # --- Rule Type ---
            type_el = soup.find("div", class_=lambda c: c and "StyledType" in c)
            if type_el:
                rule_type = type_el.get_text(strip=True)

            # --- Available In ---
            available_in = extract_products(soup)

            return {
                "Key": key,
                "Title": title,
                "Language": url.split("/")[3],
                "Type": rule_type,
                "AvailableIn": available_in
            }
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
                continue
            print(f"Failed {url}: {e}")
            return None

def process_language(lang):
    try:
        print(f"Fetching rules for {lang}...")
        links = get_rule_links(lang)
        filename = f"rules_{lang}.csv"

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()

            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(parse_rule, url) for url in links]
                for future in tqdm(as_completed(futures), total=len(futures), desc=f"Parsing {lang}"):
                    data = future.result()
                    if data and "Community" not in data["AvailableIn"]:
                        writer.writerow(data)

        return filename
    except Exception as e:
        print(f"Error processing {lang}: {e}")
        return None

def merge_csv(files, output="sonarqube_community_rules.csv"):
    with open(output, "w", newline="", encoding="utf-8") as fout:
        writer = csv.DictWriter(fout, fieldnames=FIELDS)
        writer.writeheader()

        for file in files:
            if file and os.path.exists(file):
                with open(file, newline="", encoding="utf-8") as fin:
                    reader = csv.DictReader(fin)
                    for row in reader:
                        writer.writerow(row)

def main():
    with ThreadPoolExecutor(max_workers=len(LANGUAGES)) as executor:
        futures = [executor.submit(process_language, lang) for lang in LANGUAGES]
        results = [f.result() for f in futures]

    merge_csv(results)
    print("✅ Done! Saved to sonarqube_community_rules.csv")

if __name__ == "__main__":
    main()
