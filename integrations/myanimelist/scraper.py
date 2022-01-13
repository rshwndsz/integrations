from argparse import ArgumentParser
import json
import pandas as pd

from integrations.common import sessions as S
from integrations.common import log as L

logger = L.getLogger(
    __name__,
    localLevel="DEBUG",
    rootLevel="DEBUG",
    logFile="LOG.log",
    console=False
)


def formatAnimeList(animelist):
    for i, anime in enumerate(animelist):
        # Studios
        studios = [s["name"] for s in anime["studios"]]
        animelist[i]["studios"] = ", ".join(studios)

        # Genres
        genres = [g["name"] for g in anime["genres"]]
        animelist[i]["genres"] = ", ".join(genres)

        # Demographics
        dems = [d["name"] for d in anime["demographics"]]
        animelist[i]["demographics"] = ", ".join(dems)

        # Licensors
        lics = [l["name"] for l in anime["licensors"]]
        animelist[i]["licensors"] = ", ".join(lics)

    return animelist


def getAnimeListOfUser(username, session=None):
    BASE_URL = "https://api.jikan.moe/v3"

    if not session:
        session = S.getSession(
            useFakeUserAgent=True,
            useTor=False,
            maxRetries=3
        )

    animelist = []
    for i in range(1, 20):
        # https://jikan.docs.apiary.io/#reference/0/user
        r = session.get(f"{BASE_URL}/user/{username}/animelist/all/{i}")
        r.raise_for_status()

        anime = r.json().get("anime")
        if anime:
            animelist.extend(anime)
        else:
            break

    logger.info(f"Found {animelist.__len__()} anime.")
    return animelist


def main(args):
    if not args.username:
        raise ValueError("Enter a valid username.")
    animelist = getAnimeListOfUser(args.username)

    if args.formatForNotion:
        animelist = formatAnimeList(animelist)

    if args.outputFile and args.outputFormat == "csv":
        df = pd.DataFrame(animelist)
        df.to_csv(args.outputFile, index=False)
    elif args.outputFile and args.outputFormat == "json":
        with open(args.outputFile, "w") as f:
            json.dump(animelist, f)
    else:
        logger.info(animelist)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--username", default="")
    parser.add_argument(
        "--formatForNotion", dest="formatForNotion", action="store_true"
    )
    parser.add_argument("--outputFile", default="animelist.json")
    parser.add_argument("--outputFormat", default="json")  # `json` or `csv`
    args = parser.parse_args()

    logger.info(args)
    main(args)
