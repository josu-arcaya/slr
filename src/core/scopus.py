import json
import logging
import os
import time
import urllib
import urllib.request
from datetime import datetime
from http import HTTPStatus

import requests
from ratelimiter import RateLimiter

from core.models import Document, Journal, Manuscript
from core.query import Query
from core.utils import Persistence, Sqlite

LOGGER = logging.getLogger("systematic")

"""
https://dev.elsevier.com/
https://dev.elsevier.com/documentation/ScopusSearchAPI.wadl
https://dev.elsevier.com/documentation/SerialTitleAPI.wadl
"""


class Scopus(Query):
    def __init__(self, persistence: Persistence, search_query: str, date_range: str):
        super().__init__(persistence)

        self._name = "Scopus"

        self._raw_search_query = search_query
        self._search_query = urllib.request.quote(search_query)
        self._date_range = date_range

        # Check API key
        self._api_key = os.environ["ELSEVIER_API_KEY"]

        # Base api query url
        self._base_url = "https://api.elsevier.com/content/search/scopus?"

    def stubborn_url_open(self, url):
        request = urllib.request.Request(url)
        request.add_header("User-Agent", "SurveyRuntime/1.0.0")
        request.add_header("Connection", "keep-alive")
        request.add_header("Accept", "application/json")
        for _ in range(10):
            try:
                response = urllib.request.urlopen(request, timeout=300)
                LOGGER.info(f"{response.getheader('X-RateLimit-Remaining')} " f"requests left.")

                return response
            except TimeoutError as e:
                LOGGER.error(f"Error while opening url, error = {e}")
                time.sleep(60)
            except urllib.error.HTTPError as e:
                LOGGER.error(f"Error while opening url, error = {e}")
                if e.code == HTTPStatus.TOO_MANY_REQUESTS:
                    raise (e)

                time.sleep(60)

    @RateLimiter(max_calls=2, period=3)
    def get_publishers_by_eid(self, eid: str):
        url = f"https://api.elsevier.com/content/abstract/eid/{eid}" f"?apiKey={self._api_key}"

        # Get document information using the eid
        response = self.stubborn_url_open(url=url)

        json_respon = json.loads(response.read())

        authors_list = []

        # Obtain all the authors information from the json response
        try:
            # First type of json response for authors
            for auth in json_respon["abstracts-retrieval-response"]["item"]["bibrecord"]["head"]["author-group"]:
                author_info = {}
                affiliation = auth.get("affiliation")
                if affiliation:
                    country = affiliation.get("country")
                    city = affiliation.get("city")
                    author_info["country"] = country
                    author_info["city"] = city
                else:
                    author_info["country"] = None
                    author_info["city"] = None

                for author in auth.get("author", []):
                    author_info["given_name"] = author.get("ce:given-name")
                    author_info["surname"] = author.get("ce:surname")
                    author_info["auid"] = author.get("@auid")

                    authors_list.append(author_info)

        except Exception:
            try:
                # Second type of json response for authors
                author_group = json_respon["abstracts-retrieval-response"]["item"]["bibrecord"]["head"]["author-group"]
                affiliation = author_group.get("affiliation")
                if affiliation:
                    country = affiliation.get("country")
                    city = affiliation.get("city")
                    author_info["country"] = country
                    author_info["city"] = city
                else:
                    author_info["country"] = None
                    author_info["city"] = None

                for author in author_group.get("author", []):
                    author_info["given_name"] = author.get("ce:given-name")
                    author_info["surname"] = author.get("ce:surname")
                    author_info["auid"] = author.get("@auid")

                    authors_list.append(author_info)

            except Exception as e:
                LOGGER.info(f"There is an error, the error is {e} and json response is {json_respon}")
                authors_list = None

        if authors_list:
            authors_list = self.extend_authors_info(auth_list=authors_list)

        return authors_list

    def get_publisher(self, issn: str, eissn: str, eid: str):
        cache = Sqlite()
        publisher = None
        if issn:
            publisher = cache.get_publisher_by_issn(issn=issn)
        if not publisher and eissn:
            publisher = cache.get_publisher_by_eissn(eissn=eissn)
        if not publisher and eid:
            LOGGER.info(f"Not issn = {issn} nor eissn = {eissn} are yet cached, " f"eid = {eid}")
            publisher = self.get_publisher_by_eid(eid=eid)

            if issn and publisher:
                cache.set_publisher_by_issn(issn=issn, publisher=publisher)
            if eissn and publisher:
                cache.set_publisher_by_eissn(eissn=eissn, publisher=publisher)

        return publisher

    @RateLimiter(max_calls=2, period=1)
    def get_impact_by_issn(self, issn: str):
        url = f"https://api.elsevier.com/content/serial/title/issn/{issn}" f"?apiKey={self._api_key}"

        response = self.stubborn_url_open(url=url)
        json_response = json.loads(response.read())

        try:
            entry = json_response.get("serial-metadata-response").get("entry")[0]

            citeScoreCurrentMetric = entry.get("citeScoreYearInfoList").get("citeScoreCurrentMetric")

            citeScoreCurrentMetricYear = entry.get("citeScoreYearInfoList").get("citeScoreCurrentMetricYear")
            citeScoreTracker = entry.get("citeScoreYearInfoList").get("citeScoreTracker")
            citeScoreTrackerYear = entry.get("citeScoreYearInfoList").get("citeScoreTrackerYear")
            sjrMetric = entry.get("SJRList").get("SJR")[0].get("$")
            sjrYear = entry.get("SJRList").get("SJR")[0].get("@year")
        except AttributeError as e:
            LOGGER.error(f"Error fetching impact for issn = {issn}. Error = {e}")

        j = Journal(
            issn=issn,
            citeScoreCurrentMetric=citeScoreCurrentMetric,
            citeScoreCurrentMetricYear=citeScoreCurrentMetricYear,
            citeScoreTracker=citeScoreTracker,
            citeScoreTrackerYear=citeScoreTrackerYear,
            sjrMetric=sjrMetric,
            sjrYear=sjrYear,
        )
        return j

    def get_impact(self, issn):
        pass

    @RateLimiter(max_calls=1, period=1)
    def next_page(self, url):
        response = self.stubborn_url_open(url=url)
        json_response = json.loads(response.read())

        json_entries = json_response.get("search-results").get("entry")

        entries = []
        if json_entries:
            for e in json_entries:
                m = self.Entry(e, self._raw_search_query, self._name).to_document()
                entries.append(m)

        json_links = json_response.get("search-results").get("link")

        next_link = None
        for link in filter(lambda x: x.get("@ref") == "next", json_links):
            next_link = link.get("@href")

        return entries, next_link

    def fetch_all(self):
        p = self._persistence()

        query = (
            f"query={self._search_query}"
            f"&cursor=*"
            f"&date={self._date_range}"
            f"&view=COMPLETE"
            f"&apiKey={self._api_key}"
        )

        next_link = self._base_url + query

        entries = True
        while entries and next_link:
            entries, next_link = self.next_page(next_link)
            if entries:
                p.save(entries)

    @RateLimiter(max_calls=1, period=1)
    def get_count(self):
        query = (
            f"query={self._search_query}" f"&start=0" f"&count=5" f"&date={self._date_range}" f"&apiKey={self._api_key}"
        )
        url = self._base_url + query

        response = self.stubborn_url_open(url=url)
        json_response = json.loads(response.read())

        return json_response.get("search-results").get("opensearch:totalResults")

    def fill_publishers(self):
        p = self._persistence()

        LOGGER.info("About to populate empty publishers")
        for id_document, eid, issn, eissn in p.get_empty_publisher():
            publisher = self.get_publisher(issn=issn, eissn=eissn, eid=eid)
            if publisher:
                p.set_publisher(publishers=[(id_document, publisher)])

    @RateLimiter(max_calls=2, period=3)
    def extend_authors_info(self, auth_list: list):
        # Once we obtain an author list of the document, we obtain more detail information about each one
        for i in range(len(auth_list)):
            url = f"https://api.elsevier.com/content/author/author_id/{auth_list[i]['auid']}" f"?apiKey={self._api_key}"

            response = self.stubborn_url_open(url=url)

            data = json.loads(response.read())

            author = data["author-retrieval-response"][0]

            auth_list[i]["document_count"] = author["coredata"]["document-count"]
            auth_list[i]["cited_by_count"] = author["coredata"]["cited-by-count"]
            auth_list[i]["citation_count"] = author["coredata"]["citation-count"]
            date_created = author["author-profile"]["date-created"]
            auth_list[i]["creation_date"] = f"{date_created['@day']}-{date_created['@month']}-{date_created['@year']}"
            publication_range = author["author-profile"]["publication-range"]
            start_year = publication_range["@start"]
            end_year = publication_range["@end"]
            auth_list[i]["publication_range"] = f"{start_year}-{end_year}"

        return auth_list

    @RateLimiter(max_calls=2, period=1)
    def get_openaccess(self, eid: str):
        url = f"https://api.elsevier.com/content/abstract/eid/{eid}" f"?apiKey=43b38cab54e0a0e4e42667d2998f51e8"
        headers = {"Accept": "application/json"}
        response = requests.get(url, headers=headers, timeout=10)
        return response.json()["abstracts-retrieval-response"]["coredata"]["openaccess"]

    class Entry:
        def __init__(self, entry, search_query, name):
            self._title = entry.get("dc:title")
            self._abstract = entry.get("dc:description")
            self._keywords = entry.get("authkeywords")
            self._author = entry.get("dc:creator")
            self._published_date = entry.get("prism:coverDate")
            self._eid = entry.get("eid")
            self._doi = entry.get("prism:doi")
            self._publication_name = entry.get("prism:publicationName")
            self._issn = entry.get("prism:issn")
            self._eissn = entry.get("prism:eIssn")
            self._type = entry.get("prism:aggregationType")
            self._sub_type = entry.get("subtypeDescription")
            self._search_query = search_query
            self._source = name
            self._affiliation_country = self._parse_affiliation(entry)
            self._citedby_count = entry.get("citedby-count")

        def _parse_affiliation(self, entry):
            try:
                affiliation_country = entry.get("affiliation")[0].get("affiliation-country")
                return affiliation_country
            except TypeError:
                LOGGER.info(f"The author {self._author} has no affiliation.")

        def to_manuscript(self):
            m = Manuscript(
                title=self._title,
                abstract=self._abstract,
                keywords=self._keywords,
                author=self._author,
                published_date=self._published_date,
                doi=self._doi,
                eid=self._eid,
                publication_name=self._publication_name,
                issn=self._issn,
                eissn=self._eissn,
                type=self._type,
                sub_type=self._sub_type,
                search_query=self._search_query,
                source=self._source,
                affiliation_country=self._affiliation_country,
                citedby_count=self._citedby_count,
            )
            return m

        def to_document(self):
            d = Document(
                title=self._title,
                abstract=self._abstract,
                keywords=self._keywords,
                author=self._author,
                published_date=datetime.strptime(self._published_date, "%Y-%m-%d"),
                doi=self._doi,
                eid=self._eid,
                publication_name=self._publication_name,
                issn=self._issn,
                eissn=self._eissn,
                type=self._type,
                sub_type=self._sub_type,
                search_query=self._search_query,
                source=self._source,
                affiliation_country=self._affiliation_country,
                citedby_count=self._citedby_count,
            )
            return d
