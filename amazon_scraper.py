import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

# ======================
# CONFIG
# ======================
BASE_URL = "https://www.amazon.in/s?k=ethnic+dresses+for+kids+girls&page=1"
TOTAL_PRODUCTS = 10
OUTPUT_FILE = "amazon_kids_full_features.xlsx"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Accept-Language": "en-IN,en;q=0.9"
}


# ======================
# CLEAN TEXT
# ======================
def clean(text):
    if not text:
        return ""
    return text.replace("\u200f", "").replace("\n", " ").strip()


# ======================
# GET PRODUCT LINKS
# ======================
def get_links():
    print("Collecting product links...")
    res = requests.get(BASE_URL, headers=HEADERS)
    soup = BeautifulSoup(res.text, "lxml")

    links = []

    for a in soup.select("a.a-link-normal.s-no-outline"):
        href = a.get("href")

        if href and "/dp/" in href and "aax" not in href:
            link = "https://www.amazon.in" + href.split("?")[0]

            if link not in links:
                links.append(link)

        if len(links) >= TOTAL_PRODUCTS:
            break

    print("Collected:", len(links))
    return links


# ======================
# SECTION 1: TOP HIGHLIGHTS / STYLE
# ======================
def extract_product_overview(soup):
    data = {}

    rows = soup.select("#productOverview_feature_div tr")

    for row in rows:
        cols = row.find_all("td")
        if len(cols) == 2:
            key = clean(cols[0].get_text())
            value = clean(cols[1].get_text())
            data[key] = value

    return data


# ======================
# SECTION 2: PRODUCT DETAILS TABLES
# ======================
def extract_product_details(soup):
    data = {}

    rows = soup.select(
        "#productDetails_techSpec_section_1 tr, "
        "#productDetails_detailBullets_sections1 tr"
    )

    for row in rows:
        th = row.find("th")
        td = row.find("td")

        if th and td:
            key = clean(th.get_text())
            value = clean(td.get_text())
            data[key] = value

    return data


# ======================
# SECTION 3: DETAIL BULLETS
# ======================
def extract_detail_bullets(soup):
    data = {}

    items = soup.select("#detailBullets_feature_div li")

    for li in items:
        text = clean(li.get_text(" ", strip=True))

        if ":" in text:
            key, value = text.split(":", 1)
            data[clean(key)] = clean(value)

    return data


# ======================
# SECTION 4: EXTRA TABLES (Style / Materials & Care)
# ======================
def extract_extra_tables(soup):
    data = {}

    tables = soup.select("table.a-normal")

    for table in tables:
        rows = table.select("tr")
        for row in rows:
            cols = row.find_all(["th", "td"])
            if len(cols) == 2:
                key = clean(cols[0].get_text())
                value = clean(cols[1].get_text())

                if key and value:
                    data[key] = value

    return data


# ======================
# SECTION 5: SIZE / COLOUR (Variation)
# ======================
def extract_variations(soup):
    data = {}

    size_selected = soup.select_one("#variation_size_name .selection")
    if size_selected:
        data["Size"] = clean(size_selected.get_text())

    color_selected = soup.select_one("#variation_color_name .selection")
    if color_selected:
        data["Colour"] = clean(color_selected.get_text())

    return data


# ======================
# SECTION 6: ABOUT
# ======================
def extract_about(soup):
    bullets = soup.select("#feature-bullets li span")
    texts = [clean(b.get_text()) for b in bullets if clean(b.get_text())]
    return " | ".join(texts)


# ======================
# PRODUCT SCRAPER
# ======================
def extract_product(url):
    print("\nScraping:", url)

    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "lxml")

    product = {"URL": url}

    # Title
    title = soup.select_one("#productTitle")
    if title:
        product["Dress name"] = clean(title.get_text())

    # Image
    img = soup.select_one("#landingImage")
    if img:
        product["Image link"] = img.get("src")

    # Extract from all sections
    product.update(extract_product_overview(soup))
    product.update(extract_product_details(soup))
    product.update(extract_detail_bullets(soup))
    product.update(extract_extra_tables(soup))
    product.update(extract_variations(soup))
    product["About"] = extract_about(soup)

    # ======================
    # PRINT IMPORTANT FEATURES
    # ======================
    important_fields = [
        "Size", "Colour", "Pattern", "Sleeve Type", "Sleeve type",
        "Neck style", "Material composition", "Material type",
        "Closure Type", "Bottom Style", "Fabric Type",
        "Occasion", "Length", "Style Name"
    ]

    print("Important extracted:")
    for f in important_fields:
        if f in product:
            print(f, ":", product[f])

    print("Total fields:", len(product))

    return product


# ======================
# MAIN
# ======================
def main():
    links = get_links()

    all_data = []

    for link in links:
        try:
            data = extract_product(link)
            all_data.append(data)
        except Exception as e:
            print("Error:", e)

        time.sleep(random.uniform(2, 4))  # avoid blocking

    df = pd.DataFrame(all_data)
    df.to_excel(OUTPUT_FILE, index=False)

    print("\nSaved to:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
