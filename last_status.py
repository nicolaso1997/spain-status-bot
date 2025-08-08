import os
import time
import smtplib
from email.message import EmailMessage
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

URL = "https://immi.homeaffairs.gov.au/what-we-do/whm-program/status-of-country-caps"
COUNTRY_NAME = "Spain"

SENDER_EMAIL = os.environ.get("EMAIL_USERNAME")
SENDER_PASSWORD = os.environ.get("EMAIL_PASSWORD")
RECEIVER_EMAIL = SENDER_EMAIL

def send_email(subject, body):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg.set_content(body)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
        smtp.send_message(msg)

def get_spain_status():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get(URL)

    time.sleep(5)

    try:
        tables = driver.find_elements(By.TAG_NAME, "table")
        if not tables:
            return None

        rows = tables[0].find_elements(By.TAG_NAME, "tr")

        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            col_text = [col.text.strip() for col in cols]

            if len(col_text) >= 2 and col_text[0].strip().lower() == COUNTRY_NAME.lower():
                raw_status = col_text[1]
                cleaned_status = raw_status.upper().strip().replace("*", "")
                return cleaned_status

        return None

    except Exception:
        return None
    finally:
        driver.quit()

def main():
    current_status = get_spain_status()

    if current_status:
        subject = f"[Spain Visa Bot] Current status: {current_status}"
        body = f"Spain status: {current_status}\nLast checked: {time.ctime()}"
        send_email(subject, body)
        print(f"Email sent. Spain status is currently: {current_status}")
    else:
        subject = "[Spain Visa Bot] Error checking status"
        body = f"There was an error retrieving Spain's status.\nTime: {time.ctime()}"
        send_email(subject, body)
        print("Spain status not found.")

if __name__ == "__main__":
    main()
