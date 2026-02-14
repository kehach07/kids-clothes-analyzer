import time
import random
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# =====================================
# Chrome Setup
# =====================================
options = Options()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

wait = WebDriverWait(driver, 15)


# =====================================
# Config (Test Mode)
# =====================================
BASE_URL = "https://www.amazon.in/s?k=ethnic+dresses+for+kids+girls&page={}"
MAX_PRODUCTS = 10
OUTPUT_FILE = "amazon_kids_clothes_fixed.xlsx"

data = []


# =====================================
# Helper function (flexible key match)
# =====================================
def get_value(details, keywords):
    for key in details:
        for k in keywords:
            if k.lower() in key.lower():
                return details[key]
    return ""


# =====================================
# Step 1: Open Search Page
# =====================================
driver.get(BASE_URL.format(1))
time.sleep(5)

products = driver.find_elements(By.CSS_SELECTOR, "a.a-link-normal.s-no-outline")

links = []
for p in products:
    link = p.get_attribute("href")
    if link and "/dp/" in link:
        links.append(link)

print("Collected links:", len(links))


# =====================================
# Step 2: Visit Products
# =====================================
for i, link in enumerate(links):

    if len(data) >= MAX_PRODUCTS:
        break

    print("\nProcessing product:", i + 1)

    driver.get(link)

    # Wait for page load
    try:
        wait.until(EC.presence_of_element_located((By.ID, "productTitle")))
    except:
        print("Page load failed")
        continue

    time.sleep(2)

    # Scroll to load dynamic sections
    driver.execute_script("window.scrollTo(0, 800);")
    time.sleep(2)

    # ---------------- Basic Info ----------------
    try:
        title = driver.find_element(By.ID, "productTitle").text.strip()
    except:
        title = ""

    try:
        brand = driver.find_element(By.ID, "bylineInfo").text
        brand = brand.replace("Visit the ", "").replace(" Store", "")
    except:
        brand = ""

    try:
        price = driver.find_element(By.CSS_SELECTOR, ".a-price .a-offscreen").text
    except:
        price = ""

    try:
        image = driver.find_element(By.ID, "imgTagWrapperId") \
            .find_element(By.TAG_NAME, "img") \
            .get_attribute("src")
    except:
        image = ""

    # =====================================
    # Collect ALL Details
    # =====================================
    details = {}

    # ---------- Layout 1: Top Highlights (NEW) ----------
    try:
        overview = driver.find_element(By.ID, "productOverview_feature_div")
        rows = overview.find_elements(By.TAG_NAME, "tr")

        for row in rows:
            try:
                key = row.find_element(By.CSS_SELECTOR, "td.a-span3").text.strip()
                value = row.find_element(By.CSS_SELECTOR, "td.a-span9").text.strip()
                details[key] = value
            except:
                pass
    except:
        pass

    # ---------- Layout 2: Bullet Details ----------
    bullets = driver.find_elements(By.CSS_SELECTOR, "#detailBullets_feature_div li")
    for b in bullets:
        text = b.text
        if ":" in text:
            k, v = text.split(":", 1)
            details[k.strip()] = v.strip()

    # ---------- Layout 3: Technical Table ----------
    rows = driver.find_elements(By.CSS_SELECTOR, "#productDetails_techSpec_section_1 tr")
    for row in rows:
        try:
            k = row.find_element(By.TAG_NAME, "th").text.strip()
            v = row.find_element(By.TAG_NAME, "td").text.strip()
            details[k] = v
        except:
            pass

    # ---------- Layout 4: Alternate Table ----------
    rows2 = driver.find_elements(By.CSS_SELECTOR, "#productDetails_detailBullets_sections1 tr")
    for row in rows2:
        try:
            k = row.find_element(By.TAG_NAME, "th").text.strip()
            v = row.find_element(By.TAG_NAME, "td").text.strip()
            details[k] = v
        except:
            pass

    # Debug: see what Amazon actually provided
    print("Extracted keys:", list(details.keys()))

    # =====================================
    # Save Row
    # =====================================
    data.append({
        "Dress Name": title,
        "Brand": brand,
        "Price": price,
        "Gender": get_value(details, ["Department"]),
        "Fabric Type": get_value(details, ["Material composition", "Fabric"]),
        "Material Type": get_value(details, ["Material type"]),
        "Closure type": get_value(details, ["Closure type"]),
        "Care instructions": get_value(details, ["Care instructions"]),
        "Age range description": get_value(details, ["Age range"]),
        "Fit type": get_value(details, ["Fit type"]),
        "Sleeve type": get_value(details, ["Sleeve"]),
        "Neck style": get_value(details, ["Neck"]),
        "Pattern": get_value(details, ["Pattern"]),
        "Theme": get_value(details, ["Theme"]),
        "Style": get_value(details, ["Style"]),
        "Length": get_value(details, ["Length"]),
        "Bottom Style": get_value(details, ["Bottom"]),
        "Country of Origin": get_value(details, ["Country"]),
        "Product URL": link,
        "Image URL": image
    })

    print("Collected:", len(data), "/", MAX_PRODUCTS)
    time.sleep(random.randint(2, 4))


# =====================================
# Save Excel
# =====================================
pd.DataFrame(data).to_excel(OUTPUT_FILE, index=False)

driver.quit()

print("\nScraping completed")
print("Saved file:", OUTPUT_FILE)
