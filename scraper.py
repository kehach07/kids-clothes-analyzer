import time
import random
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


# =====================================
# Chrome Setup (Linux safe)
# =====================================
options = Options()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument(
    "user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

driver.set_page_load_timeout(30)


# =====================================
# Config
# =====================================
BASE_URL = "https://www.amazon.in/s?k=ethnic+dresses+for+kids+girls&page={}"
TOTAL_PAGES = 50
MAX_PRODUCTS = 200
OUTPUT_FILE = "amazon_kids_clothes.xlsx"

data = []


# Helper: get value from multiple possible keys
def get_value(details, keys):
    for k in keys:
        if k in details:
            return details[k]
    return ""


# =====================================
# Start Scraping
# =====================================
for page in range(1, TOTAL_PAGES + 1):

    if len(data) >= MAX_PRODUCTS:
        break

    print(f"\n===== Processing Page {page} =====")

    try:
        driver.get(BASE_URL.format(page))
    except:
        print("Page load failed")
        continue

    time.sleep(5)

    products = driver.find_elements(By.CSS_SELECTOR, "a.a-link-normal.s-no-outline")
    product_links = []

    for p in products:
        link = p.get_attribute("href")
        if link and "/dp/" in link:
            product_links.append(link)

    print("Links found:", len(product_links))

    # =====================================
    # Visit Products
    # =====================================
    for idx, link in enumerate(product_links):

        if len(data) >= MAX_PRODUCTS:
            print("\nReached max product limit!")
            break

        print(f"Product {idx+1} on page {page}")

        try:
            driver.get(link)
        except:
            print("Timeout, skipping")
            continue

        time.sleep(random.randint(4, 7))

        # -------- Basic Info --------
        try:
            title = driver.find_element(By.ID, "productTitle").text.strip()
        except:
            title = ""

        try:
            price = driver.find_element(By.CSS_SELECTOR, ".a-price .a-offscreen").text
        except:
            price = ""

        try:
            brand = driver.find_element(By.ID, "bylineInfo").text
        except:
            brand = ""

        try:
            image = driver.find_element(By.ID, "imgTagWrapperId") \
                .find_element(By.TAG_NAME, "img") \
                .get_attribute("src")
        except:
            image = ""

        # =====================================
        # Collect ALL product details
        # =====================================
        details = {}

        # 1. Technical table
        rows = driver.find_elements(By.CSS_SELECTOR, "#productDetails_techSpec_section_1 tr")
        for row in rows:
            try:
                key = row.find_element(By.TAG_NAME, "th").text.strip()
                value = row.find_element(By.TAG_NAME, "td").text.strip()
                details[key] = value
            except:
                pass

        # 2. Detail bullets table
        rows2 = driver.find_elements(By.CSS_SELECTOR, "#productDetails_detailBullets_sections1 tr")
        for row in rows2:
            try:
                key = row.find_element(By.TAG_NAME, "th").text.strip()
                value = row.find_element(By.TAG_NAME, "td").text.strip()
                details[key] = value
            except:
                pass

        # 3. Bullet section
        bullets = driver.find_elements(By.CSS_SELECTOR, "#detailBullets_feature_div li")
        for bullet in bullets:
            text = bullet.text
            if ":" in text:
                parts = text.split(":", 1)
                details[parts[0].strip()] = parts[1].strip()

        # 4. Top Highlights (NEW layout)
        overview_rows = driver.find_elements(By.CSS_SELECTOR, "#productOverview_feature_div tr")
        for row in overview_rows:
            try:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 2:
                    key = cols[0].text.strip()
                    value = cols[1].text.strip()
                    details[key] = value
            except:
                pass

        # Alternate layout
        overview_alt = driver.find_elements(By.CSS_SELECTOR, "#poExpander tr")
        for row in overview_alt:
            try:
                cols = row.find_elements(By.TAG_NAME, "td")
                if len(cols) >= 2:
                    key = cols[0].text.strip()
                    value = cols[1].text.strip()
                    details[key] = value
            except:
                pass

        # Debug (optional)
        # print(details)

        # =====================================
        # Save Row (flexible mapping)
        # =====================================
        data.append({
            "Dress Name": title,
            "Brand": brand,
            "Price": price,
            "Gender": get_value(details, ["Department"]),
            "Fabric Type": get_value(details, ["Material composition", "Fabric", "Fabric type"]),
            "Material Type": get_value(details, ["Material type", "Material"]),
            "Closure type": get_value(details, ["Closure type"]),
            "Care instructions": get_value(details, ["Care instructions"]),
            "Age range description": get_value(details, ["Age range description"]),
            "Fit type": get_value(details, ["Fit type"]),
            "Sleeve type": get_value(details, ["Sleeve type"]),
            "Neck style": get_value(details, ["Neck style"]),
            "Pattern": get_value(details, ["Pattern"]),
            "Theme": get_value(details, ["Theme"]),
            "Style": get_value(details, ["Style"]),
            "Length": get_value(details, ["Length"]),
            "Bottom Style": get_value(details, ["Bottom style"]),
            "Product URL": link,
            "Image URL": image
        })

        print(f"Collected: {len(data)} / {MAX_PRODUCTS}")
        time.sleep(random.randint(2, 4))

    # =====================================
    # Batch Save
    # =====================================
    df = pd.DataFrame(data)
    df.to_excel(OUTPUT_FILE, index=False)
    print(f"Saved after page {page} | Total: {len(data)}")


# =====================================
# Close
# =====================================
driver.quit()

print("\nScraping completed!")
print("Total collected:", len(data))
print("File saved:", OUTPUT_FILE)
