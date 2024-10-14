#!/usr/bin/env python3

import argparse
import itertools
import logging
import os
import tempfile

from omegaconf import OmegaConf

from core.crud import SqlAlchemyORM
from core.database import Database
from core.plotter import Plotter
from core.scopus import Scopus
from core.utils import Editorial, Location, Persistence, Sqlite

LOGGER = logging.getLogger("systematic")

conf = OmegaConf.load("config.yaml")
orm = SqlAlchemyORM()


def init_database():
    Database().create_database()


def fill_openaccess():
    s = Sqlite()
    for eid in list(s.get_empty_openaccess()):
        LOGGER.info(f"Processing document with eid = {eid}.")
        scop = Scopus(persistence=Persistence, search_query="None", date_range=conf.date_range)
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
    terms = conf.search_terms

    search_queries = [
        f"TITLE-ABS-KEY('{a}' AND '{b}' AND '{c}')" for a, b, c in list(itertools.product(terms[0], terms[1], terms[2]))
    ]

    for i, s in enumerate(search_queries):
        LOGGER.info(f"Processing query {i} out of {len(search_queries)}.")
        LOGGER.info(f"Processing {s}")
        q = Scopus(persistence=SqlAlchemyORM, search_query=s, date_range=conf.date_range)
        q.fetch_all()


def count_search_queries():
    terms = conf.search_terms

    search_queries = [
        f"TITLE-ABS-KEY('{a}' AND '{b}' AND '{c}')" for a, b, c in list(itertools.product(terms[0], terms[1], terms[2]))
    ]

    total_queries = len(search_queries)
    LOGGER.info(f"The total amount of search queries are {total_queries}")

    filepath = f"{tempfile.gettempdir()}/search_terms_results.csv"
    if os.path.exists(filepath):
        os.remove(filepath)

    with open(f"{tempfile.gettempdir()}/search_terms_results.csv", "a") as f:
        for i, s in enumerate(search_queries):
            LOGGER.warning(f"Counting elements for query {i} out of {total_queries}.")
            q = Scopus(persistence=Persistence, search_query=s, date_range=conf.date_range)
            total_results = q.get_count()
            LOGGER.info(f"{s} query have {total_results} documents")
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
        "-z",
        "--fill-continent",
        action="store_true",
        help="Fill continent.",
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
        "-pr",
        "--plot-relations",
        action="store_true",
        help="Plot relations diagram",
        required=False,
    )

    parser.add_argument(
        "-i",
        "--init-database",
        action="store_true",
        help="Initialize DataBase.",
        required=False,
    )

    parser.add_argument(
        "-f",
        "--fill-publisher",
        action="store_true",
        help="Fill in the publisher table with the publishers of documents table.",
        required=False,
    )

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)-8s %(message)s")

    if args.count:
        count_search_queries()

    if args.plot_relations:
        search_terms = conf.search_terms
        p = Plotter()
        p.relations_diagram(set_1=search_terms[0], set_2=search_terms[1], set_3=search_terms[2])

    if args.scopus:
        query_scopus()

    if args.fill_publisher:
        scop = Scopus(persistence=Persistence, search_query="None", date_range=conf.date_range)

        eid_list = orm.get_documents_eid()
        for k in range(len(eid_list)):
            LOGGER.info(f"Document {k+1}/{len(eid_list)}")
            authors_list = scop.get_publishers_by_eid(eid_list[k])
            if authors_list:
                for i in range(len(authors_list)):
                    if authors_list[i]["given_name"] is not None and authors_list[i]["surname"] is not None:
                        complete_name = authors_list[i]["given_name"] + " " + authors_list[i]["surname"]
                    elif authors_list[i]["given_name"] is not None:
                        complete_name = authors_list[i]["given_name"]
                    else:
                        complete_name = authors_list[i]["surname"]

                    try:
                        orm.insert_publisher(eid=eid_list[k][0], complete_name=complete_name, author=authors_list[i])
                    except Exception as e:
                        LOGGER.info(f"Error={e} inserting the publisher")

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
