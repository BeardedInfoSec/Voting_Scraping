import time
import re
import random
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from concurrent.futures import ThreadPoolExecutor
import threading
import os

options = Options()
options.headless = True  # Run in headless mode
options.add_argument('--headless=new')
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})  # Disable images

servers = [
    "us-atlanta", "us-west-virginia", "us-alabama", "us-tennessee", "us-mississippi",
    "us-south-carolina", "us-texas", "us-east-streaming-optimized", "us-washington-dc",
    "us-kentucky", "us-arkansas", "us-virginia", "us-chicago", "us-idaho", "us-nebraska",
    "us-houston", "us-east", "us-kansas", "us-missouri", "us-florida", "us-north-dakota",
    "us-denver", "us-iowa", "us-new-mexico", "us-wisconsin", "us-wyoming", "us-alaska",
    "us-montana", "us-massachusetts", "us-ohio", "us-vermont", "us-maine", "us-oklahoma",
    "us-south-dakota", "us-indiana", "us-michigan", "us-oregon", "us-california", "us-minnesota",
    "us-new-york", "us-connecticut", "us-new-hampshire", "us-pennsylvania", "us-west",
    "us-rhode-island", "us-silicon-valley", "us-las-vegas", "us-seattle", "us-west-streaming-optimized",
    "us-baltimore", "us-honolulu", "us-salt-lake-city", "us-wilmington", "us-louisiana", "us-north-carolina"
]

vote_counter = 0
vote_counter_lock = threading.Lock()


def switch_vpn():
    new_server = random.choice(servers)
    print(f"Switching to server: {new_server}")
    try:
        piactl_path = r"C:\Program Files\Private Internet Access\piactl.exe"
        result = subprocess.run([piactl_path, "set", "region", new_server], check=True, capture_output=True, text=True)
        print(result.stdout)
        result = subprocess.run([piactl_path, "connect"], check=True, capture_output=True, text=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error switching VPN server: {e}")
        print(e.stdout)
        print(e.stderr)


def vote():
    global vote_counter
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(
            "https://www.commercialappeal.com/story/sports/high-school/2024/05/13/tssaa-vote-for-campbell-clinic-girls-high-school-athlete-of-the-week-may-6-11/73663018007/")
        driver.set_window_size(1728, 980)
        print("Page loaded successfully.")

        try:
            WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button.close, .gnt_mol_xb'))
            ).click()
            print("Popup closed successfully.")
        except TimeoutException:
            print("No popup found or error closing popup.")

        driver.execute_script("window.scrollTo(0, 167)")
        driver.execute_script("window.scrollTo(0, 630)")
        driver.execute_script("window.scrollTo(0, 1099)")

        # Find the <aside> element containing the iframe
        aside = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'aside.gnt_em.gnt_em_pd.gnt_em__lp'))
        )
        iframe = aside.find_element(By.TAG_NAME, 'iframe')

        if not iframe:
            print("Expected iframe not found.")
            driver.quit()
            return

        driver.switch_to.frame(iframe)
        print("Switched to voting iframe.")

        try:
            container = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "PDI_container13756604"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", container)
            print("Scrolled to voting container.")
        except TimeoutException:
            print("Voting container not found.")
            driver.quit()
            return

        try:
            radio_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "PDI_answer61394150"))  # Example radio button ID
            )
            radio_button.click()
            print("Radio button selected.")

            vote_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.ID, "pd-vote-button13756604"))
            )
            vote_button.click()
            print("Vote submitted.")
            with vote_counter_lock:
                vote_counter += 1
        except (TimeoutException, NoSuchElementException):
            print("Error during voting.")
            driver.quit()
            return

        try:
            math_problem = WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "#captcha_13756604 p"))
            ).text
            numbers = re.findall(r'\d+', math_problem)
            if numbers:
                result = sum(map(int, numbers))  # Simple summation of numbers
                driver.find_element(By.ID, "answer_13756604").send_keys(str(result))
                print("Captcha solved.")

                vote_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.ID, "pd-vote-button13756604"))
                )
                vote_button.click()
                print("Vote submitted after solving captcha.")
                with vote_counter_lock:
                    vote_counter += 1
            else:
                print("No numbers found in math problem.")
        except (TimeoutException, NoSuchElementException):
            print("Error solving captcha and voting.")
    finally:
        driver.quit()


def close_chrome_processes():
    try:
        os.system("taskkill /F /IM chrome.exe /T")
        print("Closed all Chrome processes.")
    except subprocess.CalledProcessError as e:
        print(f"Error closing Chrome processes: {e}")


def main():
    global vote_counter
    max_threads = 5
    with ThreadPoolExecutor(max_threads) as executor:
        for _ in range(20000):  # Example loop count
            if vote_counter >= 5:
                close_chrome_processes()
                switch_vpn()
                with vote_counter_lock:
                    vote_counter = 0
            executor.submit(vote)
            time.sleep(1)  # Small delay between votes to avoid detection


if __name__ == "__main__":
    main()
