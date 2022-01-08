import argparse
import logging
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from time import time

import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
import pandas as pd

# Config for the Root Logger
logging.basicConfig(
    format="%(name)s :: %(levelname)-8s :: %(asctime)s :: %(filename)s - L%(lineno)d :: %(message)s",
    filename="LOG.log",
    filemode="w",
    level=logging.INFO
)

# Instantiate local logger
logger = logging.getLogger("goodreads")
logger.setLevel(logging.DEBUG)


def getGenres(soup):
    genres = []
    for node in soup.find_all("div", {"class": "left"}):
        tags = node.find_all("a", {"class": "actionLinkLite bookPageGenreLink"})
        genre = " > ".join([t.text for t in tags]).strip()
        if genre:
            genres.append(genre)
    return ", ".join(genres)


def getCoverImage(soup):
    tag = soup.find(id="coverImage")
    if tag is None:
        image = None
    else:
        image = tag.get("src")
    return image if image is not None else ""


def getURLFromBookID(id):
    url = "https://www.goodreads.com/book/show/" + str(id) + "?ref=bk_bet_out"
    return url


def scrapeURLForHTML(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    return soup


def getExtraBookData(df, index):
    id = df.loc[index, "Book Id"]
    url = getURLFromBookID(id)

    soup = scrapeURLForHTML(url)
    if soup is None:
        return None

    return {
        "index": index,
        "Genres": getGenres(soup),
        "Cover Image": getCoverImage(soup),
    }


def updateExportedCSV(df):
    df["Genres"], df["Cover Image"] = "", ""

    with tqdm(total=len(df)) as pbar:
        with ThreadPoolExecutor(max_workers=10) as executor:
            futureToIndex = { executor.submit(getExtraBookData, df, index): index for index in range(len(df)) }

        for future in as_completed(futureToIndex):
            index = futureToIndex[future]
            edata = future.result() 

            desc = f"{df.loc[index, 'Book Id']:>8}: {df.loc[index, 'Title']}"

            if edata is None:
                logger.warning(f"[Failed] {desc}: Could not get HTML.")

            elif edata["Genres"] == "":
                logger.error(f"[Failed] {desc}: Could not get Genres.")

            elif edata["Cover Image"] == "":
                logger.error(f"[Failed] {desc}: Could not get Cover Image.")

            else:
                df.loc[index, "Genres"] = edata["Genres"]
                df.loc[index, "Cover Image"] = edata["Cover Image"]
                logger.info(f"[Updated] {desc}")

            pbar.update(1)

    return df


def main(args):
    # Read exported CSV
    df = pd.DataFrame(pd.read_csv(args.input))

    # Select a subset of the data, if requested
    if args.books > len(df) or args.books == 0:
        logger.error(f"Invalid number of books: {args.books}. Aborting...")
        exit()
    if args.books != -1:
        logger.info(f"Using {args.books} books.")
        df = df[:args.books]

    # Update each book's genre & cover image
    df = updateExportedCSV(df)

    # Save updated CSV
    logger.info(f"Saving updated CSV to {args.output}.")
    df.to_csv(args.output, index=False)


if __name__ == "__main__":
    _start = time()

    parser = argparse.ArgumentParser()
    parser.add_argument("--books", type=int, default=-1)
    parser.add_argument("--input", default="./input.csv")
    parser.add_argument("--output", default="./output.csv")
    args = parser.parse_args()

    try:
        main(args)
    except Exception as e:
        logger.error(traceback.format_exc())

    logger.info(f"Finished successfully in {time() - _start}s.")
