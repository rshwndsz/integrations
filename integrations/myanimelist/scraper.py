from argparse import ArgumentParser
import requests
import pandas as pd

from integrations.common import sessions as S
from integrations.common import log as L

logger = L.getLogger(__name__, localLevel="DEBUG", rootLevel="DEBUG", console=True)


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
    if not session:
        session = S.getSession(useFakeUserAgent=True, useTor=False, maxRetries=3)

    animelist = []
    for i in range(1, 20):
        res = session.get(f"https://api.jikan.moe/v3/user/{username}/animelist/all/{i}")
        res.raise_for_status()

        anime = res.json().get("anime")
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
    animelist = formatAnimeList(animelist)

    if args.output:
        df = pd.DataFrame(animelist)
        df.to_csv("animelist.csv", index=False)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--username", default="")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    main(args)
