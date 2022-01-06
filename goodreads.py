import argparse
import logging

import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


def get_genres(soup):
    genres = []
    for node in soup.find_all("div", {"class": "left"}):
        tags = node.find_all("a", {"class": "actionLinkLite bookPageGenreLink"})
        genre = " > ".join([t.text for t in tags]).strip()
        if genre:
            genres.append(genre)
    return genres


def get_coverimage(soup):
    tag = soup.find(id="coverImage")
    return tag.get("src")


def scrape(id, driver):
    url = "https://www.goodreads.com/book/show/" + id + "?ref=bk_bet_out"
    driver.get(url)

    wait = WebDriverWait(driver, timeout=10)
    for retry in range(3):
        try:
            wait.until(EC.presence_of_element_located((By.ID, "coverImage")))
            soup = BeautifulSoup(driver.page_source, "html.parser")
            return soup
        except TimeoutException:
            logging.info(f"TimeoutException while trying {url}. Trying again...")
            driver.refresh()

    return None


def update_export(args):
    # Read exported CSV
    df = pd.read_csv(args.input)

    # Debug mode: Use just 6 rows
    if args.debug:
        logging.info("Using only 6 rows in 'debug' mode.")
        df = df[:6]

    # Create new columns for Genre & Cover Image
    df["Genres"] = ""
    df["Cover Image"] = ""

    # Setup Firefox Driver
    options = webdriver.FirefoxOptions()
    if args.headless:
        logging.info("Starting Firefox driver in 'headless' mode.")
        options.add_argument("--headless")
    options.set_capability("pageLoadStrategy", "eager")
    driver = webdriver.Firefox(options=options)

    # For each row, update genre & cover image
    for index, row in tqdm(df.iterrows(), total=len(df)):
        soup = scrape(str(row["Book Id"]), driver)
        if soup is None:
            logging.warning(f"Could not update {row['Book Id']}: {row['Title']}. Skipping...")
            continue

        genres = get_genres(soup)
        df["Genres"] = ", ".join(genres)

        image = get_coverimage(soup)
        if image is None:
            logging.warning(f"Could not get cover image for {row['Book Id']}: {row['title']}.")
        df["Cover Image"] = image if image is not None else ""

    driver.quit()
    df.to_csv(args.output, index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", dest="headless", action="store_true")
    parser.add_argument("--debug", dest="debug", action="store_true")
    parser.add_argument("--input", default="./input.csv")
    parser.add_argument("--output", default="./output.csv")
    args = parser.parse_args()

    # Config for the Root Logger
    logging.basicConfig(
        format="[%(levelname)s] :: %(asctime)s :: %(message)s in %(pathname)s at (lineno)d",
        filename="LOG.log",
        filemode="a",
        level=logging.DEBUG if args.debug else logging.INFO,
    )

    update_export(args)
