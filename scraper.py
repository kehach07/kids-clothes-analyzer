import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

# ======================
# CONFIG
# ======================
BASE_URL = "https://www.amazon.in/s?k=ethnic+dresses+for+kids+girls&page={}"
BATCH_SIZE = 100
MAX_PAGES = 10   # adjust if needed
OUTPUT_FILE = "amazon_kids_dresses.xlsx"


# ======================
# SETUP DRIVER
# ======================
chrome_options = Options()
chrome_options.add_argument("--start-maximized")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(options=chrome_options)
driver.implicitly_wait(5)


# ======================
# SCROLL FUNCTION
# ======================
def scroll_page():
    last_height = driver.execute_script("return document.body.scrollHeight")
    for _ in range(5):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
    time.sleep(2)


# ======================
# GET PRODUCT LINKS
# ======================
def get_product_links():
    links = set()

    for page in range(1, MAX_PAGES + 1):
        print(f"\nCollecting links from page {page}")
        driver.get(BASE_URL.format(page))
        scroll_page()

        products = driver.find_elements(By.CSS_SELECTOR, "a.a-link-normal.s-no-outline")

        for p in products:
            link = p.get_attribute("href")
            if link and "/dp/" in link:
                links.add(link)

        if len(links) >= BATCH_SIZE:
            break

    print(f"Total links collected: {len(links)}")
    return list(links)[:BATCH_SIZE]


# ======================
# EXTRACT PRODUCT DATA
# ======================
def extract_product_data(url):
    data = {"Product URL": url}

    driver.get(url)
    time.sleep(2)
    scroll_page()

    # Dress Name
    try:
        title = driver.find_element(By.ID, "productTitle").text.strip()
        data["Dress name"] = title
    except:
        data["Dress name"] = ""

    # Image
    try:
        img = driver.find_element(By.ID, "landingImage").get_attribute("src")
        data["Image link"] = img
    except:
        data["Image link"] = ""

    # ======================
    # PRODUCT DETAILS TABLE
    # ======================
    try:
        tables = driver.find_elements(By.CSS_SELECTOR, "#productDetails_techSpec_section_1 tr")
        for row in tables:
            key = row.find_element(By.TAG_NAME, "th").text.strip()
            value = row.find_element(By.TAG_NAME, "td").text.strip()
            data[key] = value
    except:
        pass

    # ======================
    # ADDITIONAL DETAILS
    # ======================
    try:
        tables2 = driver.find_elements(By.CSS_SELECTOR, "#productDetails_detailBullets_sections1 tr")
        for row in tables2:
            key = row.find_element(By.TAG_NAME, "th").text.strip()
            value = row.find_element(By.TAG_NAME, "td").text.strip()
            data[key] = value
    except:
        pass

    # ======================
    # ABOUT THIS ITEM (Bullets)
    # ======================
    try:
        bullets = driver.find_elements(By.CSS_SELECTOR, "#feature-bullets li span")
        about_text = " | ".join([b.text for b in bullets if b.text.strip()])
        data["About this item"] = about_text
    except:
        data["About this item"] = ""

    print("\nExtracted Fields:")
    for k, v in data.items():
        print(f"{k} : {v}")

    return data


# ======================
# SAVE TO EXCEL (BATCH)
# ======================
def save_batch(batch_data):
    df = pd.DataFrame(batch_data)

    try:
        existing = pd.read_excel(OUTPUT_FILE)
        df = pd.concat([existing, df], ignore_index=True)
    except:
        pass

    df.to_excel(OUTPUT_FILE, index=False)
    print(f"\nBatch saved. Total records: {len(df)}")


# ======================
# MAIN
# ======================
def main():
    links = get_product_links()
    batch_data = []

    for i, link in enumerate(links):
        print(f"\nProcessing {i+1}/{len(links)}")
        try:
            data = extract_product_data(link)
            batch_data.append(data)
        except Exception as e:
            print("Error:", e)

        # Save after each batch of 20
        if (i + 1) % 20 == 0:
            save_batch(batch_data)
            batch_data = []
            driver.refresh()
            time.sleep(3)

    # Save remaining
    if batch_data:
        save_batch(batch_data)

    driver.quit()
    print("\nScraping completed.")


if __name__ == "__main__":
    main()
