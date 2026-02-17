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
# Config
# =====================================
BASE_URL = "https://www.amazon.in/s?k=ethnic+dresses+for+kids+girls&page=1"
MAX_PRODUCTS = 10
OUTPUT_FILE = "amazon_test.xlsx"

data = []


# =====================================
# Helper: Slow scroll (important)
# =====================================
def scroll_full_page():
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollBy(0, 500)")
        time.sleep(1)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height


# =====================================
# Helper: Extract all key-value pairs
# =====================================
def extract_details():
    details = {}

    # --- Top Highlights (MAIN TARGET) ---
    rows = driver.find_elements(By.CSS_SELECTOR, "#productOverview_feature_div tr")
    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")
        if len(cols) >= 2:
            key = cols[0].text.strip()
            value = cols[1].text.strip()
            details[key] = value

    # --- Item details bullets ---
    bullets = driver.find_elements(By.CSS_SELECTOR, "#detailBullets_feature_div li")
    for b in bullets:
        text = b.text
        if ":" in text:
            k, v = text.split(":", 1)
            details[k.strip()] = v.strip()

    # --- Product information table ---
    rows2 = driver.find_elements(By.CSS_SELECTOR, "#productDetails_techSpec_section_1 tr")
    for r in rows2:
        try:
            k = r.find_element(By.TAG_NAME, "th").text.strip()
            v = r.find_element(By.TAG_NAME, "td").text.strip()
            details[k] = v
        except:
            pass

    return details


# =====================================
# Step 1: Open search page
# =====================================
driver.get(BASE_URL)
time.sleep(4)

links = []
products = driver.find_elements(By.CSS_SELECTOR, "a.a-link-normal.s-no-outline")

for p in products:
    link = p.get_attribute("href")
    if link and "/dp/" in link:
        links.append(link)

print("Collected links:", len(links))


# =====================================
# Step 2: Visit products
# =====================================
for i, link in enumerate(links[:MAX_PRODUCTS]):

    print(f"\nProcessing product: {i+1}")
    driver.get(link)

    # Wait for title
    try:
        wait.until(EC.presence_of_element_located((By.ID, "productTitle")))
    except:
        print("Title not loaded")
        continue

    # Scroll to load dynamic sections
    scroll_full_page()

    # Small wait after scroll
    time.sleep(2)

    # Basic Info
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

    # Extract all details
    details = extract_details()

    print("Extracted keys:", list(details.keys()))

    # Save selected fields
    data.append({
        "Dress Name": title,
        "Brand": brand,
        "Price": price,
        "Material composition": details.get("Material composition", ""),
        "Material type": details.get("Material type", ""),
        "Sleeve type": details.get("Sleeve type", ""),
        "Neck style": details.get("Neck style", ""),
        "Style": details.get("Style", ""),
        "Length": details.get("Length", ""),
        "Country of Origin": details.get("Country of Origin", ""),
        "Department": details.get("Department", ""),
        "Product URL": link,
        "Image URL": image
    })

    print(f"Collected: {len(data)} / {MAX_PRODUCTS}")

    time.sleep(random.randint(2, 4))


# =====================================
# Save to Excel
# =====================================
df = pd.DataFrame(data)
df.to_excel(OUTPUT_FILE, index=False)

driver.quit()

print("\nDone!")
print("Saved:", OUTPUT_FILE)
