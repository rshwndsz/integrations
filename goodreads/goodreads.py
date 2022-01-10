import argparse
import logging
from time import time
from typing import Union
from bs4.element import NavigableString
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
import pandas as pd

from goodreads.tor import getSession, getIp


# Config for the Root Logger
logging.basicConfig(
    format="%(name)s :: %(levelname)-8s :: %(asctime)s :: %(filename)s - L%(lineno)-3d :: %(message)s",
    filename="LOG.log",
    filemode="w",
    level=logging.DEBUG
)

# Instantiate local logger
logger = logging.getLogger("goodreads")
logger.setLevel(logging.DEBUG)


def getGenres(soup: BeautifulSoup) -> Union[None, str]:
    # Adapted from https://github.com/maria-antoniak/goodreads-scraper/blob/b019ff78c7641bba8bcdc36ffa223861a617c7e4/get_books.py#L73-L80
    genres = []
    for node in soup.find_all("div", {"class": "left"}):
        tags = node.find_all("a", {"class": "actionLinkLite bookPageGenreLink"})
        genre = " > ".join([t.text for t in tags]).strip()
        if genre:
            genres.append(genre)

    if not genres:
        return None

    genres = ", ".join(genres)
    return genres


def getCoverImage(soup: BeautifulSoup) -> Union[None, str]:
    image = None
    tags = soup.findAll("meta", attrs={ "property": "og:image" }) or soup.findAll(id="coverImage")
    for tag in tags:
        if tag and not isinstance(tag, NavigableString):
            image = tag.get("content") or tag.get("src")

    return image


def getURLFromBookID(id):
    url = "https://www.goodreads.com/book/show/" + str(id)
    return url


def scrapeURLForHTML(url):
    # https://stackoverflow.com/a/16214510
    try:
        # Update every hit to this function
        scrapeURLForHTML.counter += 1
    except AttributeError:
        # Initialise counter
        scrapeURLForHTML.counter = 0 

    # Rotate IP every 15 requests
    if scrapeURLForHTML.counter % 15 == 0:
        session = getSession(rotateIp=True)
    else:
        session = getSession()
    logger.debug(getIp(session))

    # HTML work
    r = session.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    return soup


def getExtraBookData(id):
    url = getURLFromBookID(id)
    soup = scrapeURLForHTML(url)
    if soup is None:
        return None

    genres = getGenres(soup)
    image = getCoverImage(soup)

    return {
        "soup": soup,
        "Genres": genres,
        "Cover Image": image,
    }


def updateExportedCSV(df):
    # Add new columns
    df["Genres"], df["Cover Image"] = "", ""

    # Track progress
    progress = {"Done": 0, "Failed": 0}
    pbar = tqdm(total=len(df), postfix=progress)

    # Spin up threads
    # TODO Retries
    futureToIndex = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        for index, id in enumerate(df.loc[:, "Book Id"]):
            futureToIndex[executor.submit(getExtraBookData, id)] = index

    # Update DataFrame as threads complete
    for future in as_completed(futureToIndex): 
        index = futureToIndex[future] 
        edata = future.result() 
        descr = f"{df.loc[index, 'Book Id']:>8}: {df.loc[index, 'Title']}"

        if not (edata and edata["Genres"] and edata["Cover Image"]):
            # Failed to get extra data for the book
            logger.warning(f"[Failed] {descr}")
            logger.debug(f"""
                         === Diagnostic Soup START === 
                         {edata['soup'].prettify()}
                         === Diagnostic Soup ENDNG ===
                         """)
            progress["Failed"] += 1
        else:
            # Got extra data! Now update book.
            df.loc[index, "Genres"] = edata["Genres"]
            df.loc[index, "Cover Image"] = edata["Cover Image"]

            logger.info(f"[Updated] {descr}")
            progress["Done"] += 1

        # thank you, next
        pbar.update(1)
        pbar.set_postfix(progress)

    pbar.close()
    return df


def main(args):
    # Read exported CSV
    df = pd.DataFrame(pd.read_csv(args.input))

    # Check validity of arguments
    if args.books > len(df) or args.books == 0 or args.books < -1:
        logger.error(f"Invalid number of books: {args.books}. Aborting...")
        exit()

    # Select a subset of the data, if requested
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
        logger.critical(e, exc_info=True)
    else:
        logger.info(f"Finished successfully in {time() - _start}s.")
