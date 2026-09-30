import json
import requests

from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin


BASE_URL = "https://hcpcsdata.com"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/154.0.0.0 Safari/537.36"
    )
}


def get_code_pages():
    """
    Get all HCPCS code-group pages from /Codes.
    Example: /Codes/A, /Codes/B, /Codes/C...
    """

    url = f"{BASE_URL}/Codes"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    code_pages = []

    for link in soup.find_all("a"):
        href = link.get("href")
        text = link.get_text(" ", strip=True)

        if href and text.endswith("Codes"):
            if href.startswith("/Codes/"):
                full_url = urljoin(BASE_URL, href)

                if full_url not in code_pages:
                    code_pages.append(full_url)

    return code_pages


def scrape_code_page(url):
    """
    Scrape one HCPCS code-group page.
    """

    print(f"\nScraping: {url}")

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table")

    if table is None:
        print("No table found")
        return []

    rows = table.find_all("tr")

    records = []

    for row in rows[1:]:
        cells = row.find_all("td")

        if len(cells) >= 2:

            code = cells[0].get_text(
                " ",
                strip=True
            )

            description = cells[1].get_text(
                " ",
                strip=True
            )

            records.append(
                {
                    "hcpcs_code": code,
                    "long_description": description
                }
            )

    print(f"Records found: {len(records)}")

    return records


def save_raw_data(records, code_group):
    """
    Save extracted data as immutable JSON snapshot.
    """

    raw_folder = Path("raw")

    raw_folder.mkdir(
        exist_ok=True
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    output_file = (
        raw_folder
        / f"hcpcs_{code_group}_{timestamp}.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            records,
            file,
            indent=2,
            ensure_ascii=False
        )

    print(f"Saved: {output_file}")


def main():

    print("Starting HCPCS scraper...")

    code_pages = get_code_pages()

    print(
        f"\nCode pages found: {len(code_pages)}"
    )

    for page in code_pages:

        code_group = page.rstrip("/").split("/")[-1]

        records = scrape_code_page(page)

        if records:
            save_raw_data(
                records,
                code_group
            )


if __name__ == "__main__":
    main()