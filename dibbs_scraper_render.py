# dibbs_scraper_render.py
from datetime import datetime, timedelta
import os
import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# === Configuration ===
today = datetime.today()
issued_from = (today - timedelta(days=1)).strftime("%Y-%m-%d")
next_month = today.replace(day=28) + timedelta(days=4)
issued_to = next_month.replace(day=1) + timedelta(days=31)
issued_to = issued_to.replace(day=1) - timedelta(days=1)
issued_to = issued_to.strftime("%Y-%m-%d")
min_qty = 5

search_fsc_codes = [
    "1015", "1055", "1450", "1560", "1620", "1680", "2090", "2540", "2590",
    "3120", "3419", "3441", "3442", "3445", "3446", "4720", "4730", "5305", "5306",
    "5310", "5320", "5325", "5330", "5331", "5340", "5342", "6650", "8145", "9320", "9390"
]

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--window-size=1920x1080")

prefs = {"download.default_directory": "/tmp"}
chrome_options.add_experimental_option("prefs", prefs)

solicitations = []

# === Upload to Google Drive ===
def upload_to_drive(file_path):
    SCOPES = ['https://www.googleapis.com/auth/drive']
    SERVICE_ACCOUNT_FILE = 'service_account.json'

    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    service = build('drive', 'v3', credentials=creds)

    file_metadata = {
        'name': os.path.basename(file_path),
        'mimeType': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    }
    media = MediaFileUpload(file_path, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    print(f"Uploaded to Google Drive with ID: {file.get('id')}")

# === Main Process ===
def scrape():
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver.get("https://www.dibbs.bsm.dla.mil/RFQ/RfqFsc.aspx")

    try:
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "butAgree")))
        driver.find_element(By.ID, "butAgree").click()
        time.sleep(1)
    except:
        pass

    for fsc_code in search_fsc_codes:
        try:
            driver.get("https://www.dibbs.bsm.dla.mil/RFQ/RfqFsc.aspx")
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "ctl00_cph1_lstValue")))
            select_element = Select(driver.find_element(By.ID, "ctl00_cph1_lstValue"))
            for option in select_element.options:
                if option.text.strip().startswith(fsc_code):
                    select_element.select_by_visible_text(option.text.strip())
                    break
            driver.find_element(By.ID, "ctl00_cph1_but1").click()

            try:
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "ctl00_cph1_grdRfqSearch"))
                )
            except:
                continue

            try:
                sort_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "#ctl00_cph1_grdRfqSearch > tbody > tr.AwdRecs > th:nth-child(9) > a"))
                )
                sort_btn.click()
                time.sleep(0.6)
                sort_btn.click()
                time.sleep(0.6)
            except:
                pass

            for page_count in range(1, 6):
                try:
                    table = driver.find_element(By.ID, "ctl00_cph1_grdRfqSearch")
                    rows = table.find_elements(By.XPATH, ".//tr[td]")
                    for row in rows:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if len(cells) != 9 or not cells[4].text.strip().startswith("SPE"):
                            continue
                        try:
                            issued = datetime.strptime(cells[7].text.strip(), "%m-%d-%Y").date()
                            if not (datetime.strptime(issued_from, "%Y-%m-%d").date() <= issued <= datetime.strptime(issued_to, "%Y-%m-%d").date()):
                                continue
                        except:
                            continue

                        pr_text = cells[6].text.strip().replace('\n', ' ')
                        quantity = ""
                        if "QTY" in pr_text.upper():
                            parts = pr_text.upper().split("QTY")
                            if len(parts) > 1:
                                quantity = ''.join(filter(str.isdigit, parts[1]))

                        if quantity and int(quantity) < min_qty:
                            continue

                        solicitations.append({
                            "FSC": fsc_code,
                            "NSN_Part": cells[1].text.strip().replace('\n', ' '),
                            "Nomenclature": cells[2].text.strip().replace('\n', ' '),
                            "TechDocs": cells[3].text.strip().replace('\n', ' '),
                            "Solicitation": cells[4].text.strip().split("\n")[0].replace("-", ""),
                            "Status": cells[5].text.strip().replace('\n', ' '),
                            "PurchaseRequest": ''.join(filter(str.isdigit, cells[6].text)),
                            "Quantity": quantity,
                            "IssuedDate": cells[7].text.strip(),
                            "ReturnByDate": cells[8].text.strip()
                        })

                    next_link = driver.find_elements(By.XPATH, f"//a[text()='{page_count + 1}']")
                    if next_link:
                        next_link[0].click()
                        time.sleep(1.5)
                    else:
                        break
                except:
                    break
        except Exception as e:
            print(f"Error with FSC {fsc_code}: {e}")

    driver.quit()

    if solicitations:
        df = pd.DataFrame(solicitations)
        output_path = f"/tmp/DIBBS_Solicitations_{datetime.today().strftime('%Y-%m-%d')}.xlsx"
        df.to_excel(output_path, index=False)
        print(f"Saved to: {output_path}")
        upload_to_drive(output_path)
    else:
        print("No solicitations found.")

if __name__ == "__main__":
    scrape()
