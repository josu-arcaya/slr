import abc
import logging
import os
import sqlite3 as sl
from io import BytesIO

import psycopg2 as ps
import pycountry_convert as pc
import pycurl
from core.models import Journal
from ratelimiter import RateLimiter

LOGGER = logging.getLogger("systematic")


class Persistence:
    def __init__(self, database="test"):
        self._database = database

    @abc.abstractmethod
    def save(self, documents):
        pass

    @abc.abstractmethod
    def get_title(self):
        pass

    @abc.abstractmethod
    def get_publisher_by_issn(self, issn: str):
        return None

    @abc.abstractmethod
    def set_publisher_by_issn(self, issn: str, publisher: str):
        pass


class Postgres(Persistence):
    def __init__(self, database="prod"):
        Persistence.__init__(self, database)

        if os.getenv("DB_USER") is None or os.getenv("DB_HOST") is None or os.getenv("DB_PASS") is None:
            logging.error("Please define DB_USER, DB_HOST and DB_PASS environment " "variables.")
            exit(-1)
        self._user = os.getenv("DB_USER")
        self._host = os.getenv("DB_HOST")
        self._password = os.getenv("DB_PASS")

    def save(self, documents):
        connection = None
        try:
            connection = ps.connect(
                user=self._user,
                password=self._password,
                host=self._host,
                port="5432",
                database=self._database,
            )
            cursor = connection.cursor()
            sql = """ INSERT INTO documents (title, abstract, keywords, author,
             published_date, doi, eid, publication_name, issn, eissn, type,
              sub_type, search_query, source) VALUES
              (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
              ON CONFLICT DO NOTHING;"""
            cursor.executemany(sql, documents)
            connection.commit()
            LOGGER.info("Record inserted successfully")
        except Exception as error:
            LOGGER.error(f"Failed to insert record, {error}.")
            exit(-1)
        finally:
            if connection is not None:
                connection.close()


class Sqlite(Persistence):
    def __init__(self, database="prod"):
        super().__init__(database=database)
        # self._db_name = f"publishers_{database}.db"
        self._db_name = "documents.db"
        # self.__create_database()
        self._con = sl.connect(self._db_name)

    def __create_database(self):
        if not os.path.isfile(self._db_name):
            conn = sl.connect(self._db_name)
            with conn:
                sql = """CREATE TABLE publisher (id_document
                INTEGER PRIMARY KEY, publisher TEXT NOT NULL);"""
                conn.execute(sql)
            with conn:
                sql = """CREATE TABLE issn_publisher (issn TEXT NOT NULL
                PRIMARY KEY, publisher TEXT NOT NULL);"""
                conn.execute(sql)
            with conn:
                sql = """CREATE TABLE eissn_publisher (eissn TEXT NOT NULL
                PRIMARY KEY, publisher TEXT NOT NULL);"""
                conn.execute(sql)
            with conn:
                sql = """CREATE TABLE issn_impact (issn TEXT NOT NULL PRIMARY
                KEY, citeScoreCurrentMetric REAL NOT
                NULL, citeScoreCurrentMetricYear INT NOT NULL,
                citeScoreTracker REAL NOT NULL, citeScoreTrackerYear
                INT NOT NULL, sjrMetric REAL NOT NULL,
                sjrYear INT NOT NULL);"""
                conn.execute(sql)
            with conn:
                sql = """CREATE TABLE documents (id_document INTEGER PRIMARY
                KEY AUTOINCREMENT,title TEXT,abstract
                TEXT, keywords TEXT,author TEXT,published_date DATE,doi TEXT
                UNIQUE,eid TEXT UNIQUE,publication_name
                TEXT, issn TEXT,eissn TEXT,type TEXT,sub_type TEXT,
                search_query TEXT,source TEXT, affiliation_country
                TEXT, citedby_count INT);"""
                conn.execute(sql)
            with conn:
                sql = """CREATE TABLE IF NOT EXISTS doi_eurl
                (doi TEXT NOT NULL, eurl TEXT NOT NULL);"""
                conn.execute(sql)
            with conn:
                sql = """CREATE TABLE IF NOT EXISTS continents
                (affiliation_country TEXT PRIMARY KEY, continent TEXT
                NOT NULL);"""
                conn.execute(sql)
        conn = sl.connect(self._db_name)
        with conn:
            sql = """CREATE TABLE IF NOT EXISTS aggregated_publisher
            (publisher TEXT NOT NULL, aggregated_publisher
            TEXT NOT NULL);"""
            conn.execute(sql)

    def get_impact_by_issn(self, issn: str):
        with self._con:
            data = self._con.execute(
                "SELECT citeScoreCurrentMetric, citeScoreCurrentMetricYear, "
                "citeScoreTracker, citeScoreTrackerYear, "
                "sjrMetric, sjrYear FROM issn_impact WHERE issn=?",
                (issn,),
            )
            for row in data:
                j = Journal(
                    issn=issn,
                    citeScoreCurrentMetric=row[0],
                    citeScoreCurrentMetricYear=row[1],
                    citeScoreTracker=row[2],
                    citeScoreTrackerYear=row[3],
                    sjrMetric=row[4],
                    sjrYear=row[5],
                )
                return j

    def set_impact_by_issn(
        self,
        issn: str,
        citeScoreCurrentMetric: float,
        citeScoreCurrentMetricYear: int,
        citeScoreTracker: float,
        citeScoreTrackerYear: int,
        sjrMetric: float,
        sjrYear: int,
    ):
        with self._con:
            data = (
                issn,
                citeScoreCurrentMetric,
                citeScoreCurrentMetricYear,
                citeScoreTracker,
                citeScoreTrackerYear,
                sjrMetric,
                sjrYear,
            )
            sql = """INSERT OR IGNORE INTO issn_impact
            (issn, citeScoreCurrentMetric, citeScoreCurrentMetricYear,
            citeScoreTracker, citeScoreTrackerYear, sjrMetric, sjrYear)
            VALUES (?, ?, ?, ?, ?, ?, ?)"""
            self._con.execute(sql, data)

    def get_publisher_by_issn(self, issn: str):
        with self._con:
            data = self._con.execute("SELECT publisher FROM issn_publisher WHERE issn=?", (issn,))
            for row in data:
                return row[0]

    def set_publisher_by_issn(self, issn: str, publisher: str):
        with self._con:
            data = (issn, publisher)
            self._con.execute(
                "INSERT OR IGNORE INTO issn_publisher " "(issn, publisher) VALUES (?, ?)",
                data,
            )

    def get_publisher_by_eissn(self, eissn: str):
        with self._con:
            data = self._con.execute("SELECT publisher FROM eissn_publisher WHERE eissn=?", (eissn,))
            for row in data:
                return row[0]

    def set_publisher_by_eissn(self, eissn: str, publisher: str):
        with self._con:
            data = (eissn, publisher)
            self._con.execute(
                "INSERT OR IGNORE INTO eissn_publisher " "(eissn, publisher) VALUES (?, ?)",
                data,
            )

    def save(self, documents):
        with self._con:
            try:
                sql = """INSERT OR IGNORE INTO documents
                (title, abstract, keywords, author, published_date, doi,
                eid, publication_name, issn, eissn,
                type, sub_type, search_query, source, affiliation_country,
                citedby_count) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);"""
                self._con.executemany(sql, documents)

                LOGGER.info("Document inserted successfully")
            except Exception as error:
                LOGGER.error(f"Failed to insert document, {error}.")
                exit(-1)

    def get_all_issn_without_publisher(self):
        with self._con:
            sql = """
                SELECT d.eid, d.issn, d.eissn FROM documents d
                LEFT JOIN issn_publisher p ON d.issn = p.issn
                WHERE p.publisher IS NULL AND d.issn IS NOT NULL
                """
            data = self._con.execute(sql)
            for row in data:
                yield (row[0], row[1], row[2])

    def get_all_eissn_without_publisher(self):
        with self._con:
            sql = """
                SELECT d.eid, d.issn, d.eissn FROM documents d
                LEFT JOIN eissn_publisher p ON d.eissn = p.eissn
                WHERE p.publisher IS NULL AND d.eissn IS NOT NULL
                """
            data = self._con.execute(sql)
            for row in data:
                yield (row[0], row[1], row[2])

    def get_empty_publisher(self):
        with self._con:
            sql = """
                SELECT d.id_document, d.eid, d.issn, d.eissn FROM documents d
                LEFT JOIN publisher p ON d.id_document = p.id_document
                WHERE p.publisher IS NULL
                """
            data = self._con.execute(sql)
            for row in data:
                yield (row[0], row[1], row[2], row[3])

    def set_publisher(self, publishers):
        with self._con:
            try:
                sql = """
                    INSERT OR IGNORE INTO publisher (id_document, publisher)
                    VALUES (?, ?)
                    """
                self._con.executemany(sql, publishers)
                LOGGER.info("Publisher inserted successfully")
            except Exception as error:
                LOGGER.error(f"Failed to insert publisher, {error}.")
                exit(-1)

    def get_empty_continents(self):
        with self._con:
            sql = """
                SELECT DISTINCT d.affiliation_country FROM documents d
                LEFT JOIN continents c ON d.affiliation_country =
                 c.affiliation_country WHERE c.continent IS NULL AND
                 d.affiliation_country IS NOT NULL
                """
            data = self._con.execute(sql)
            for row in data:
                yield row[0]

    def set_continent(self, tuples):
        with self._con:
            try:
                sql = """
                    INSERT OR IGNORE INTO continents
                    (affiliation_country, continent) VALUES (?, ?)
                    """
                self._con.executemany(sql, tuples)
                LOGGER.info("Continent inserted successfully")
            except Exception as error:
                LOGGER.error(f"Failed to insert continent, {error}.")
                exit(-1)

    def get_doi(self):
        with self._con:
            sql = """
                SELECT d.doi FROM documents d
                LEFT OUTER JOIN doi_eurl de ON d.doi = de.doi
                WHERE d.doi IS NOT NULL
                AND de.eurl IS NULL
                """
            data = self._con.execute(sql)
            for row in data:
                yield row[0]

    def set_doi_eurl(self, doi: str, eurl: str):
        with self._con:
            data = (doi, eurl)
            self._con.execute(
                "INSERT INTO doi_eurl (doi, eurl) VALUES (?, ?)",
                data,
            )

    def get_empty_openaccess(self):
        with self._con:
            sql = """
                SELECT d.eid
                FROM study_selection ss
                INNER JOIN documents d ON d.id_document = ss.id_document
                WHERE  d.openaccess IS NULL
                AND ss.status = 3
                """
            data = self._con.execute(sql)
            for row in data:
                yield row[0]

    def set_openaccess(self, eid: str, openaccess: str):
        data = (openaccess, eid)
        with self._con:
            try:
                sql = """
                    UPDATE documents
                    SET openaccess = (?)
                    WHERE eid = (?);
                    """
                self._con.executemany(sql, [data])
                LOGGER.info("Field openaccess updated successfully")
            except Exception as error:
                LOGGER.error(f"Failed to update openaccess, {error}.")
                exit(-1)


class Location:
    def country_to_continent(self, country_name):
        country_alpha2 = pc.country_name_to_country_alpha2(country_name)
        country_continent_code = pc.country_alpha2_to_continent_code(country_alpha2)
        country_continent_name = pc.convert_continent_code_to_continent_name(country_continent_code)
        return country_continent_name


class Editorial:
    def return_publisher(self, effective_url: str):
        return effective_url.split("/")[2]

    @RateLimiter(max_calls=2, period=1)
    def get_editorial(self, doi: str):
        try:
            buffer = BytesIO()
            c = pycurl.Curl()
            c.setopt(c.URL, "http://www.doi.org/" + doi)
            c.setopt(pycurl.FOLLOWLOCATION, 1)
            c.setopt(c.WRITEDATA, buffer)
            c.setopt(pycurl.CONNECTTIMEOUT, 30)
            c.setopt(pycurl.TIMEOUT, 30)
            c.perform()
            effective_url = c.getinfo(pycurl.EFFECTIVE_URL)
            final_url = self.return_publisher(effective_url=effective_url)
            return final_url
        except pycurl.error:
            raise
