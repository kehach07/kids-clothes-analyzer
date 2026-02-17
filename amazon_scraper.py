import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random

BASE_URL = "https://www.amazon.in/s?k=ethnic+dresses+for+kids+girls&page=1"
TOTAL_PRODUCTS = 10
OUTPUT_FILE = "amazon_kids_features.xlsx"

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-IN,en;q=0.9"
}


# ======================
# TARGET FEATURES
# ======================
TARGET_FIELDS = {
    "Generic Name": "Generic Name",
    "Department": "Department",
    "Colour": "Colour",
    "Color": "Colour",
    "Material composition": "Material Composition",
    "Material type": "Fabric Type",
    "Fabric Type": "Fabric Type",
    "Fit Type": "Fit type",
    "Length": "Length",
    "Collar Style": "Collar style",
    "Waist Style": "Waist style",
    "Occasion": "Occasion type",
    "Sleeve Type": "Sleeve type",
    "Season": "Season",
    "Neck Style": "Neck style",
    "Pattern": "Pattern",
    "Number of Items": "Number of Items",
    "Style": "Style",
    "Style Name": "Style",
    "Closure Type": "Closure type",
    "Care Instructions": "Care instructions",
    "Age Range Description": "Age range description",
    "Design Name": "Design Name",
    "Bottom Style": "Bottom Style",
    "Back Style": "Back Style",
    "Strap Type": "Strap Type"
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
# EXTRACT ALL KEY-VALUE PAIRS
# ======================
def extract_all_features(soup):
    data = {}

    # 1. Product Overview (Top highlights + Style)
    rows = soup.select("#productOverview_feature_div tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) == 2:
            key = clean(cols[0].get_text())
            value = clean(cols[1].get_text())
            data[key] = value

    # 2. Product Details Tables
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

    # 3. Detail bullets (left section)
    items = soup.select("#detailBullets_feature_div li")
    for li in items:
        text = clean(li.get_text(" ", strip=True))
        if ":" in text:
            k, v = text.split(":", 1)
            data[clean(k)] = clean(v)

    return data


# ======================
# MAP TO TARGET SCHEMA
# ======================
def map_to_schema(all_data):
    result = {v: "" for v in TARGET_FIELDS.values()}

    for key, value in all_data.items():
        if key in TARGET_FIELDS:
            result[TARGET_FIELDS[key]] = value

    return result


# ======================
# PRODUCT SCRAPER
# ======================
def extract_product(url):
    print("\nScraping:", url)

    res = requests.get(url, headers=HEADERS)
    soup = BeautifulSoup(res.text, "lxml")

    product = {}

    # Dress name
    title = soup.select_one("#productTitle")
    product["Dress name"] = clean(title.get_text()) if title else ""

    # Image
    img = soup.select_one("#landingImage")
    product["Image link"] = img.get("src") if img else ""

    # Extract all features
    all_features = extract_all_features(soup)

    # Map to fixed schema
    product.update(map_to_schema(all_features))

    print("Extracted filled fields:",
          sum(1 for v in product.values() if v))

    return product


# ======================
# MAIN
# ======================
def main():
    links = get_links()

    data_list = []

    for link in links:
        try:
            data = extract_product(link)
            data_list.append(data)
        except Exception as e:
            print("Error:", e)

        time.sleep(random.uniform(2, 4))

    df = pd.DataFrame(data_list)
    df.to_excel(OUTPUT_FILE, index=False)

    print("\nSaved to:", OUTPUT_FILE)


if __name__ == "__main__":
    main()
