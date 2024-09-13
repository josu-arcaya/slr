#!/usr/bin/env python3

import argparse
import itertools
import logging
import os

from src.core.utils import Editorial, Location, Persistence, Sqlite
from src.core.plotter import Plotter
from src.core.scopus import Scopus
from src.core.database import Database

LOGGER = logging.getLogger("systematic")

def init_database():
    Database().create_database()

def fill_openaccess():
    s = Sqlite()
    for eid in list(s.get_empty_openaccess()):
        LOGGER.info(f"Processing document with eid = {eid}.")
        scop = Scopus(persistence=Persistence, search_query="None")
        openaccess = scop.get_openaccess(eid=eid)
        s.set_openaccess(eid=eid, openaccess=openaccess)


def fill_editorial():
    s = Sqlite()
    e = Editorial()
    for index, doi in reversed(list(enumerate(s.get_doi()))):
        try:
            LOGGER.info(f"Processing document {index} with doi = {doi}.")
            final_url = e.get_editorial(doi=doi)
            s.set_doi_eurl(doi=doi, eurl=final_url)
        except Exception:
            LOGGER.exception(f"Exception handling document {doi}.")


def query_scopus():
    with open("search_terms.csv", "r") as f:
        lines = f.read().splitlines()

    terms = [lines[0].split(","), lines[1].split(","), lines[2].split(",")]

    search_queries = [
        f"TITLE-ABS-KEY('{a}' AND '{b}' AND '{c}')" for a, b, c in list(itertools.product(terms[0], terms[1], terms[2]))
    ]

    for i, s in enumerate(search_queries):
        LOGGER.info(f"Processing query {i} out of {len(search_queries)}.")
        LOGGER.info(f"Processing {s}")
        q = Scopus(persistence=Sqlite, search_query=s)
        q.fetch_all()


def count_search_queries():
    with open("search_terms.csv", "r") as f:
        lines = f.read().splitlines()

    terms = [lines[0].split(","), lines[1].split(","), lines[2].split(",")]

    search_queries = [
        f"TITLE-ABS-KEY('{a}' AND '{b}' AND '{c}')" for a, b, c in list(itertools.product(terms[0], terms[1], terms[2]))
    ]

    total_queries = len(search_queries)

    filepath = "/tmp/search_terms_results.csv"
    if os.path.exists(filepath):
        os.remove(filepath)

    with open("/tmp/search_terms_results.csv", "a") as f:
        for i, s in enumerate(search_queries):
            LOGGER.warning(f"Counting elements for query {i} out of {total_queries}.")
            q = Scopus(persistence=Persistence, search_query=s)
            total_results = q.get_count()
            f.write(str(i) + "," + s + "," + total_results + "\n")


def main():
    text = "This application queries different academic engines."
    parser = argparse.ArgumentParser(description=text)
    parser.add_argument(
        "-s",
        "--scopus",
        action="store_true",
        help="Query Scopus.",
        required=False,
    )
    parser.add_argument(
        "-c",
        "--count",
        action="store_true",
        help="Count the documents for each search query.",
        required=False,
    )
    parser.add_argument(
        "-f",
        "--fill-publisher",
        action="store_true",
        help="Fill publisher.",
        required=False,
    )
    parser.add_argument(
        "-z",
        "--fill-continent",
        action="store_true",
        help="Fill continent.",
        required=False,
    )

    parser.add_argument(
        "-p",
        "--plot",
        action="store_true",
        help="Plot Data.",
        required=False,
    )
    parser.add_argument(
        "-e",
        "--fill-editorial",
        action="store_true",
        help="Fill editorial.",
        required=False,
    )
    parser.add_argument(
        "-o",
        "--fill-openaccess",
        action="store_true",
        help="Fill openaccess.",
        required=False,
    )
    parser.add_argument(
        "-i",
        "--init-database",
        action="store_true",
        help="Initialize DataBase.",
        required=False,
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(message)s")

    if args.plot:
        p = Plotter()
        # p.plot_continent()
        # p.plot_geo_continent()
        # p.plot_type()
        p.plot_publisher()
        # p.plot_keywords()
        # p.plot_waffle_type()

    if args.scopus:
        query_scopus()

    if args.fill_publisher:
        pass
        # Scopus(persistence=Sqlite, search_query="None").fill_publishers()

    if args.fill_continent:
        LOGGER.info("About to populate empty continents")
        s = Sqlite()
        loc = Location()
        for affiliation_country in s.get_empty_continents():
            try:
                continent = loc.country_to_continent(affiliation_country)
                tuples = [(affiliation_country, continent)]
                s.set_continent(tuples=tuples)
            except KeyError:
                LOGGER.error(f"Cannot get continent for {affiliation_country}")

    if args.fill_editorial:
        fill_editorial()

    if args.fill_openaccess:
        fill_openaccess()

    if args.init_database:
        init_database()


if __name__ == "__main__":
    main()
