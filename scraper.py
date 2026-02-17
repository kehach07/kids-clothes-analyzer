import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

BASE_URL = "https://www.amazon.in/s?k=ethnic+dresses+for+kids+girls&page=1"
TOTAL_PRODUCTS = 10
OUTPUT_FILE = "amazon_kids_dresses.xlsx"


# ======================
# DRIVER
# ======================
def get_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


driver = get_driver()


def human_delay(a=2, b=4):
    time.sleep(random.uniform(a, b))


# ======================
# DEEP SCROLL
# ======================
def deep_scroll():
    print("Scrolling page...")
    height = driver.execute_script("return document.body.scrollHeight")

    for i in range(0, height, 400):
        driver.execute_script(f"window.scrollTo(0, {i});")
        time.sleep(0.5)

    time.sleep(2)


# ======================
# CLICK TOGGLE BY TEXT
# ======================
def click_if_exists(text):
    try:
        el = driver.find_element(By.XPATH, f"//span[contains(text(),'{text}')]")
        driver.execute_script("arguments[0].click();", el)
        time.sleep(1)
        print(f"Opened: {text}")
    except:
        pass


# ======================
# EXPAND ABOUT
# ======================
def expand_about():
    try:
        btn = driver.find_element(By.XPATH, "//a[contains(text(),'See more')]")
        driver.execute_script("arguments[0].click();", btn)
        time.sleep(1)
        print("Expanded About")
    except:
        pass


# ======================
# EXTRACT KEY-VALUE TABLES
# ======================
def extract_tables():
    data = {}
    rows = driver.find_elements(By.XPATH, "//tr")

    for row in rows:
        try:
            key = row.find_element(By.XPATH, ".//th").text.strip()
            value = row.find_element(By.XPATH, ".//td").text.strip()
            if key:
                data[key] = value
        except:
            pass

    return data


# ======================
# TOP HIGHLIGHTS
# ======================
def extract_highlights():
    data = {}
    rows = driver.find_elements(By.CSS_SELECTOR, "#productOverview_feature_div tr")
    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")
        if len(cols) == 2:
            key = cols[0].text.strip()
            value = cols[1].text.strip()
            data[key] = value
    return data


# ======================
# ABOUT BULLETS
# ======================
def extract_about():
    texts = []
    bullets = driver.find_elements(By.CSS_SELECTOR, "#feature-bullets li span")
    for b in bullets:
        t = b.text.strip()
        if t:
            texts.append(t)
    return " | ".join(texts)


# ======================
# GET PRODUCT LINKS
# ======================
def get_links():
    driver.get(BASE_URL)
    time.sleep(3)

    links = []
    items = driver.find_elements(By.CSS_SELECTOR, "a.a-link-normal.s-no-outline")

    for i in items:
        href = i.get_attribute("href")
        if href and "/dp/" in href:
            links.append(href)
        if len(links) >= TOTAL_PRODUCTS:
            break

    return links


# ======================
# EXTRACT PRODUCT
# ======================
def extract_product(url):
    print("\nOpening:", url)
    driver.get(url)
    time.sleep(3)

    deep_scroll()

    # Expand sections
    expand_about()
    click_if_exists("Top highlights")
    click_if_exists("Style")
    click_if_exists("Materials & Care")
    click_if_exists("Product details")

    product = {}
    product["URL"] = url

    # Title
    try:
        product["Dress Name"] = driver.find_element(By.ID, "productTitle").text.strip()
    except:
        pass

    # Image
    try:
        product["Image link"] = driver.find_element(By.ID, "landingImage").get_attribute("src")
    except:
        pass

    # Extract data
    product.update(extract_highlights())
    product.update(extract_tables())
    product["About"] = extract_about()

    print("\nExtracted Fields:")
    for k, v in product.items():
        print(k, ":", v)

    return product


# ======================
# MAIN
# ======================
def main():
    driver.get("https://www.amazon.in/")
    input("Login if needed and press ENTER...")

    links = get_links()
    print("Collected:", len(links))

    all_data = []

    for i, link in enumerate(links):
        print(f"\nProcessing {i+1}/{len(links)}")
        data = extract_product(link)
        all_data.append(data)
        human_delay(4, 8)

    pd.DataFrame(all_data).to_excel(OUTPUT_FILE, index=False)
    print("\nSaved to", OUTPUT_FILE)

    driver.quit()


if __name__ == "__main__":
    main()
