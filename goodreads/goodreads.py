import argparse
import logging
from textwrap import indent
from time import time
from typing import Any, Dict, Union

from tqdm import tqdm
import pandas as pd
from bs4.element import NavigableString
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

from goodreads.tor import getSession, getIp

# Config for root logger
logging.basicConfig(
    format="%(name)s :: %(levelname)-8s :: %(asctime)s :: %(filename)s - L%(lineno)-3d :: %(message)s",
    filename="LOG.log",
    filemode="w",
    level=logging.DEBUG
)

# Instantiate local logger
logger = logging.getLogger("goodreads")
logger.setLevel(logging.DEBUG)


def getGenresFromHTML(soup: BeautifulSoup) -> Union[None, str]:
    # https://github.com/maria-antoniak/goodreads-scraper/blob/b019ff78c7641bba8bcdc36ffa223861a617c7e4/get_books.py#L73-L80
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


def getCoverImageFromHTML(soup: BeautifulSoup) -> Union[None, str]:
    image = None
    tags = soup.findAll("meta", attrs={ "property": "og:image" }) or soup.findAll(id="coverImage")
    for tag in tags:
        if tag and not isinstance(tag, NavigableString):
            image = tag.get("content") or tag.get("src")

    return image


def getURLFromBookID(id: int) -> str:
    url = "https://www.goodreads.com/book/show/" + str(id)
    return url


def getHTMLFromURL(url: str, rotateIpEveryNRequests: int = 15) -> BeautifulSoup:
    # https://stackoverflow.com/a/16214510
    try:
        # Update every hit to this function
        getHTMLFromURL.counter += 1
    except AttributeError:
        # Initialise counter
        getHTMLFromURL.counter = 0

    # Rotate IP every 15 requests, if requested
    if rotateIpEveryNRequests and getHTMLFromURL.counter % rotateIpEveryNRequests == 0:
        session = getSession(rotateIp=True)
    else:
        session = getSession()
    logger.debug(getIp(session))

    # Get HTML
    r = session.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    return soup


def getExtraDataForBook(id: int) -> Union[None, Dict[str, Any]]:
    url = getURLFromBookID(id)
    html = getHTMLFromURL(url)
    if html is None:
        return None

    genres = getGenresFromHTML(html)
    image = getCoverImageFromHTML(html)

    return {
        "HTML": html,
        "Genres": genres,
        "Cover Image": image,
    }


def getUpdatedLibrary(df: pd.DataFrame) -> pd.DataFrame:
    # Add new columns
    df["Genres"], df["Cover Image"] = "", ""

    # Track progress
    progress = {"Done": 0, "Failed": 0}
    pbar = tqdm(total=len(df), postfix=progress)

    # Spin up threads
    futureToIndex = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        for index, id in enumerate(df.loc[:, "Book Id"]):
            futureToIndex[executor.submit(getExtraDataForBook, id)] = index

    # Update DataFrame as threads complete
    for future in as_completed(futureToIndex): 
        index = futureToIndex[future] 
        edata = future.result() 
        descr = f"{df.loc[index, 'Book Id']:>8}: {df.loc[index, 'Title']}"

        if not (edata and edata["Genres"] and edata["Cover Image"]):
            # Failed to get extra data for the book
            logger.warning(f"[Failed] {descr}")
            logger.debug(f"\n=== Diagnostic HTML START ===" +
                         f"\n{indent(edata['HTML'].prettify(), '  ')}" +
                         f"\n=== Diagnostic HTML ENDNG ===")
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


def main(args) -> None:
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
    df = getUpdatedLibrary(df)

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

    main(args)
    logger.info(f"Finished successfully in {time() - _start}s.")
