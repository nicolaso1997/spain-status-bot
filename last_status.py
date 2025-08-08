import os
import time
import smtplib
import ssl
import schedule
from email.mime.text import MIMEText

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --- Configuration ---
URL = 'https://immi.homeaffairs.gov.au/what-we-do/whm-program/status-of-country-caps'
LAST_STATUS_FILE = 'last_status.txt'

import os

SENDER_EMAIL = os.environ.get("EMAIL_USERNAME")
SENDER_PASSWORD = os.environ.get("EMAIL_PASSWORD")
RECEIVER_EMAIL = SENDER_EMAIL


def get_spain_status():
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless")  # Show browser for debugging; uncomment later to hide
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get(URL)

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "tr"))
        )

        rows = driver.find_elements(By.TAG_NAME, "tr")
        print(f"🔍 Found {len(rows)} table rows")

        for i, row in enumerate(rows):
            cells = row.find_elements(By.TAG_NAME, "td")
            row_text = [cell.text for cell in cells]
            print(f"[{i}] Row: {row_text}")

            if len(cells) >= 3 and "Spain" in cells[0].text:
                raw_status = cells[1].text
                # Clean status: remove asterisks, trim whitespace, convert to uppercase
                cleaned_status = raw_status.strip().upper().replace("*", "")
                print(f"✅ Found Spain. Raw status: {raw_status}, Cleaned: {cleaned_status}")
                return cleaned_status

        print("❌ Spain not found in table.")
        return None

    except Exception as e:
        print("⚠️ Error getting Spain's status:", e)
        return None

    finally:
        driver.quit()


def load_last_status():
    if os.path.exists(LAST_STATUS_FILE):
        with open(LAST_STATUS_FILE, 'r') as f:
            return f.read().strip()
    return None


def save_last_status(status):
    if status:
        with open(LAST_STATUS_FILE, 'w') as f:
            f.write(status)


def send_email(new_status):
    subject = f"✅ WHM Alert: Spain is now '{new_status}'"
    body = f"Spain's WHM application cap status changed to: {new_status}\n\nCheck it here:\n{URL}"

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL

    context = ssl.create_default_context()
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        print("📬 Email sent successfully.")
    except Exception as e:
        print(f"⚠️ Failed to send email: {e}")


def check_for_update():
    try:
        current_status = get_spain_status()

        if current_status is None:
            print("⚠️ Spain status not found.")
            return

        last_status = load_last_status()
        print(f"[{time.ctime()}] Spain status: {current_status} (last: {last_status})")

        if last_status is None:
            save_last_status(current_status)

        elif last_status == "PAUSED" and current_status == "OPEN":
            send_email(current_status)
            save_last_status(current_status)

        elif current_status != last_status:
            save_last_status(current_status)

    except Exception as e:
        print("⚠️ Unexpected error:", e)


# --- Run on start and every 6 hours ---
schedule.every(6).hours.do(check_for_update)
print("🔁 Bot started. Checking every 6 hours...")
check_for_update()

while True:
    schedule.run_pending()
    time.sleep(60)

