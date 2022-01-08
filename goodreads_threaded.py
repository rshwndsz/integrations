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
logger = logging.getLogger("goodreads")
logger.setLevel(logging.DEBUG)


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


def get_url_from_book_id(id):
    url = "https://www.goodreads.com/book/show/" + str(id) + "?ref=bk_bet_out"
    return url


def scrape(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    return soup


def get_extra_data(df, index):
    id = df.loc[index, "Book Id"]
    url = get_url_from_book_id(id)
    soup = scrape(url)

    if soup is None:
        return None

    genres = ", ".join(get_genres(soup))
    image = get_coverimage(soup)

    return {
        "index": index,
        "Genres": genres,
        "Cover Image": image if image is not None else ""
    }


def update_normal(df):
    df["Genres"], df["Cover Image"] = "", ""

    for index in tqdm(range(len(df))):
        desc = f"{df.loc[index, 'Book Id']:>8}: {df.loc[index, 'Title']}"

        edata = get_extra_data(df, index)
        if edata is None:
            logger.warning(f"[Failed] {desc}")
            continue
        else:
            # https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
            df.loc[index, "Genres"] = edata["Genres"]
            df.loc[index, "Cover Image"] = edata["Cover Image"]
            logger.info(f"[Updated] {desc}")

    return df


def update_threaded(df):
    df["Genres"], df["Cover Image"] = "", ""

    with tqdm(total=len(df)) as pbar:
        processes = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            for index in range(len(df)):
                processes.append(executor.submit(get_extra_data, df, index))

        for task in as_completed(processes):
            edata = task.result()
            index = edata["index"]
            desc = f"{df.loc[index, 'Book Id']:>8}: {df.loc[index, 'Title']}"
            logger.info(desc)

            if edata is None:
                logger.warning(f"[Failed] {desc}")
                continue
            else:
                # https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html#returning-a-view-versus-a-copy
                df.loc[index, "Genres"] = edata["Genres"]
                df.loc[index, "Cover Image"] = edata["Cover Image"]
                logger.info(f"[Updated] {desc}")

            pbar.update(1)

    return df


def main(args):
    # Read exported CSV
    df = pd.DataFrame(pd.read_csv(args.input))

    # Select a subset of the data, if requested
    if args.rows > len(df) or args.rows == 0:
        logger.error(f"Invalid number of rows: {args.rows}. Aborting...")
        exit()
    if args.rows != -1:
        logger.info(f"Using {args.rows} rows")
        df = df[:args.rows]

    # For each row, update genre & cover image
    if args.threaded:
        df = update_threaded(df)
    else:
        df = update_normal(df)

    # Save updated CSV
    logger.info(f"Saving updated CSV to {args.output}.")
    df.to_csv(args.output, index=False)


if __name__ == "__main__":
    _start = time()

    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", type=int, default=-1)
    parser.add_argument("--threaded", dest="threaded", action="store_true")
    parser.add_argument("--input", default="./input.csv")
    parser.add_argument("--output", default="./output.csv")
    args = parser.parse_args()

    try:
        main(args)
    except Exception as e:
        logger.error(traceback.format_exc())

    logger.info(f"Finished in {time() - _start}s.")
