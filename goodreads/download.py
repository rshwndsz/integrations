import argparse
import logging

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

# Config for root logger
logging.basicConfig(
    format="%(name)-14s :: %(levelname)-8s :: %(asctime)s :: %(message)s in %(filename)s at Line %(lineno)d",
    handlers=[logging.FileHandler("LOG.log", mode="w")],
    level=logging.INFO,
)

# Instantiate local logger
logger = logging.getLogger("download")
logger.setLevel(logging.DEBUG)


def getExport(driver):
    url = "https://www.goodreads.com/review/import"
    driver.get(url)

    wait = WebDriverWait(driver, timeout=10)
    for _ in range(3):
        try:
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "exportBooks")))
        except TimeoutException:
            logger.info(f"TimeoutException while trying {url}. Trying again...")
            driver.refresh()
        else:
            # exportButton = driver.find_element_by
            pass
    return None


def signInPage(driver, username, password):
    driver.get("https://www.goodreads.com/user/sign_in")
    driver.find_element_by_id("user_email").send_keys(username)
    driver.find_element_by_id("password").send_keys(password)


def setupFirefoxDriver(args):
    options = webdriver.FirefoxOptions()

    if args.headless:
        logger.info("Starting Firefox driver in 'headless' mode.")
        options.add_argument("--headless")

    options.set_capability("pageLoadStrategy", "eager")

    driver = webdriver.Firefox(options=options)
    return driver


def main(args):
    driver = setupFirefoxDriver(args)
    pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", dest="headless", action="store_true")
    parser.add_argument("--username")
    parser.add_argument("--password")
    args = parser.parse_args()

    main(args)
