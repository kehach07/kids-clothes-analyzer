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
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-IN,en;q=0.9"
}

# ======================
# REQUIRED FEATURES LIST
# ======================
REQUIRED_FIELDS = [
    "Dress name", "Generic Name", "Department", "Size", "Colour",
    "Material composition", "Weave Type", "Reusability", "Finish type",
    "Material type", "Fit Type", "Length", "Collar style", "Waist style",
    "Occasion", "Sleeve type", "Season", "Neck style", "Embroidery Type",
    "Pattern", "Number of Items", "Theme", "Style Name", "Closure Type",
    "Product Care Instructions", "Age Range Description", "Design Name",
    "Fabric Type", "Bottom Style", "Back Style", "Strap Type", "Image link"
]

# ======================
# CLEAN
# ======================
def clean(text):
    if not text:
        return ""
    return text.replace("\u200f", "").replace("\n", " ").strip()


# ======================
# GET LINKS
# ======================
def get_links():
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

    return links


# ======================
# EXTRACT ALL TABLE DATA
# ======================
def extract_tables(soup):
    data = {}

    tables = soup.select("table.a-normal")
    for table in tables:
        for row in table.select("tr"):
            cols = row.find_all(["th", "td"])
            if len(cols) == 2:
                key = clean(cols[0].get_text())
                value = clean(cols[1].get_text())
                if key:
                    data[key] = value

    return data


# ======================
# PRODUCT DETAILS
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
            data[clean(th.text)] = clean(td.text)

    return data


# ======================
# DETAIL BULLETS
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
# VARIATIONS
# ======================
def extract_variations(soup):
    data = {}

    size = soup.select_one("#variation_size_name .selection")
    if size:
        data["Size"] = clean(size.text)

    color = soup.select_one("#variation_color_name .selection")
    if color:
        data["Colour"] = clean(color.text)

    return data


# ======================
# ABOUT
# ======================
def extract_about(soup):
    data = {}
    bullets = soup.select("#feature-bullets li span")

    texts = []
    for b in bullets:
        text = clean(b.get_text())
        if not text:
            continue

        texts.append(text)

        if ":" in text:
            key, value = text.split(":", 1)
            data[clean(key)] = clean(value)

    data["About"] = " | ".join(texts)
    return data


# ======================
# MAIN PRODUCT SCRAPER
# ======================
def extract_product(url):
    print("\n==============================")
    print("Scraping:", url)

    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "lxml")

    product = {"URL": url}

    # Title
    title = soup.select_one("#productTitle")
    if title:
        product["Dress name"] = clean(title.text)

    # Image
    img = soup.select_one("#landingImage")
    if img:
        product["Image link"] = img.get("src")

    # Merge all sources
    product.update(extract_tables(soup))
    product.update(extract_product_details(soup))
    product.update(extract_detail_bullets(soup))
    product.update(extract_variations(soup))
    product.update(extract_about(soup))

    # ======================
    # DEBUG OUTPUT
    # ======================
    print("\nAll Extracted Fields:")
    for k in product.keys():
        print("-", k)

    print("\nMissing Required Fields:")
    for field in REQUIRED_FIELDS:
        if field not in product:
            print("Missing:", field)

    print("Total extracted:", len(product))

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

        time.sleep(random.uniform(2, 4))

    df = pd.DataFrame(all_data)
    df.to_excel(OUTPUT_FILE, index=False)

    print("\nSaved to:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
