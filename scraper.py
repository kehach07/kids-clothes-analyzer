import time
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options

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


# ==============================
# Setup Chrome Driver
# ==============================
# driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

# Open Amazon search page
search_url = "https://www.amazon.in/s?k=ethnic+dresses+for+kids+girls"
driver.get(search_url)

# Wait for page to load
time.sleep(5)


# ==============================
# Step 1: Collect Product Links
# ==============================
product_links = []

products = driver.find_elements(By.CSS_SELECTOR, "a.a-link-normal.s-no-outline")

for product in products[:5]:   # Limit to first 20 products (safe)
    link = product.get_attribute("href")
    if link:
        product_links.append(link)

print("Collected links:", len(product_links))


# ==============================
# Step 2: Visit Each Product
# ==============================
data = []

for index, link in enumerate(product_links):
    print("Processing:", index + 1)

    try:
        driver.set_page_load_timeout(30)
        driver.get(link)
    except:
        print("Page timeout. Retrying...")
        try:
            driver.get(link)
        except:
            print("Skipping:", link)
            continue

    time.sleep(5)



    # --------------------------
    # Basic Details
    # --------------------------
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

    # --------------------------
    # Product Details Table
    # --------------------------
    details = {}

    # Table 1
    rows = driver.find_elements(By.CSS_SELECTOR, "#productDetails_techSpec_section_1 tr")
    for row in rows:
        try:
            key = row.find_element(By.TAG_NAME, "th").text.strip()
            value = row.find_element(By.TAG_NAME, "td").text.strip()
            details[key] = value
        except:
            pass

    # Table 2 (some products use this)
    rows2 = driver.find_elements(By.CSS_SELECTOR, "#productDetails_detailBullets_sections1 tr")
    for row in rows2:
        try:
            key = row.find_element(By.TAG_NAME, "th").text.strip()
            value = row.find_element(By.TAG_NAME, "td").text.strip()
            details[key] = value
        except:
            pass

    # --------------------------
    # Save Required Fields
    # --------------------------
    data.append({
        "Dress Name": title,
        "Brand": brand,
        "Price": price,
        "Gender": details.get("Department", ""),
        "Fabric Type": details.get("Material composition", ""),
        "Material Type": details.get("Material", ""),
        "Closure type": details.get("Closure type", ""),
        "Care instructions": details.get("Care instructions", ""),
        "Age range description": details.get("Age range description", ""),
        "Fit type": details.get("Fit type", ""),
        "Sleeve type": details.get("Sleeve type", ""),
        "Neck style": details.get("Neck style", ""),
        "Pattern": details.get("Pattern", ""),
        "Theme": details.get("Theme", ""),
        "Style": details.get("Style", ""),
        "Bottom Style": details.get("Bottom style", ""),
        "Product URL": link,
        "Image URL": image
    })

    # Small delay to avoid blocking
    time.sleep(2)


# ==============================
# Step 3: Close Browser
# ==============================
driver.quit()


# ==============================
# Step 4: Save to Excel
# ==============================
df = pd.DataFrame(data)
df.to_excel("amazon_kids_clothes.xlsx", index=False)

print("Excel file saved: amazon_kids_clothes.xlsx")
