# import unittest
# from unittest.mock import Mock, patch

from datetime import date

import pytest

from core.crud import SqlAlchemyORM
from core.models import Document

# from src.core.models import DoiEurl

# logging.basicConfig(level=logging.INFO)
# LOGGER = logging.getLogger(__name__)
# LOGGER.setLevel(logging.ERROR)


@pytest.fixture
def get_db():
    orm = SqlAlchemyORM(":memory:")
    orm.db.create_database()
    return orm


def test_get_session(get_db):
    session = get_db.db.get_session()
    assert session is not None


def test_save(get_db):
    documents = [
        Document(
            title="Title3",
            abstract="Abstract3",
            keywords="Keyword3",
            author="Author3",
            published_date=date(2022, 1, 3),
            doi="DOI3",
            eid="EID3",
            publication_name="Publication3",
            issn="ISSN3",
            eissn="EISSN3",
            type="Type3",
            sub_type="SubType3",
            search_query="Query3",
            source="Source3",
            affiliation_country="Country3",
            citedby_count=10,
            openaccess="Access3",
        )
    ]
    get_db.save(documents)


def test_get_documents_country(get_db):
    get_db.get_documents_country()


"""
class TestSqlAlchemyORM(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.orm = SqlAlchemyORM(":memory:")

    def setUp(self):
        self.session = self.orm.db.get_session()

    def test_init(self):
        self.assertIsNotNone(
            self.orm.db._engine,
            "Error in __init__: " "'Engine' has not been correctly " "initialized",
        )
        self.assertIsNotNone(
            self.orm.db._Session,
            "Error in __init__: " "'Session' has not been correctly " "initialized",
        )

    def test_get_session(self):
        session = self.orm.db.get_session()
        self.assertIsNotNone(
            session,
            "Error in get_session: Session was " "not obtained " "correctly",
        )

    # IssnPublisher publishing test and Publisher query through ISSN
    def test_set_get_publisher_by_issn(self):
        with patch("sqlalchemy.create_engine") as mock_create_engine:
            mock_create_engine.return_value = Mock()
            self.orm.set_publisher_by_issn("1234-5678", "Publisher")

        result = self.orm.get_publisher_by_issn("1234-5678")
        self.assertIsNotNone(result, "Error in set_publisher_by_issn / " "get_publisher_by_issn")

    # EissnPublisher publishing and query test
    def test_set_get_publisher_by_eissn(self):
        with patch("sqlalchemy.create_engine") as mock_create_engine:
            mock_create_engine.return_value = Mock()
            self.orm.set_publisher_by_eissn("8765-4321", "EissnPublisher")

        result = self.orm.get_publisher_by_eissn("8765-4321")
        self.assertIsNotNone(
            result,
            "Error in set_publisher_by_eissn / " "get_publisher_by_eissn",
        )

    # IssnImpact publishing test and query consult through ISSN
    def test_set_get_impact_by_issn(self):
        with patch("sqlalchemy.create_engine") as mock_create_engine:
            mock_create_engine.return_value = Mock()
            self.orm.set_impact_by_issn("1234-5678", 1.0, 2022, 2.0, 2023, 3.0, 2024)

        result = self.orm.get_impact_by_issn("1234-5678")
        self.assertIsNotNone(result, "Error in set_impact_by_issn / " "get_impact_by_issn")

    # Document publishing test and doi query in existing documents
    def test_save_and_get_doi(self):
        documents = [
            (
                "Title1",
                "Abstract1",
                "Keyword1",
                "Author1",
                "2022-01-01",
                "DOI1",
                "EID1",
                "Publication1",
                "ISSN1",
                "EISSN1",
                "Type1",
                "SubType1",
                "Query1",
                "Source1",
                "Country1",
                10,
                "Access1",
            )
        ]
        self.orm.save(documents)

        result = self.orm.get_doi()
        self.assertNotEqual(result, [], "Error in save / get_doi")

    # Author publishing test and ISSN consult test without assigned publisher
    # in IssnPublisher
    def test_set_publisher_get_empty_publisher(self):
        try:
            documents = [
                (
                    "Title2",
                    "Abstract2",
                    "Keyword2",
                    "Author2",
                    "2022-01-02",
                    "DOI2",
                    "EID2",
                    "Publication2",
                    "ISSN2",
                    "EISSN2",
                    "Type2",
                    "SubType2",
                    "Query2",
                    "Source2",
                    "Country2",
                    10,
                    "Access2",
                )
            ]
            self.orm.save(documents)
            result_empty_publisher = self.orm.get_empty_publisher()
            self.assertEqual(
                result_empty_publisher,
                [],
                "Error in " "set_publisher / get_empty_publisher",
            )
        except AssertionError:
            LOGGER.error("Error in set_empty_publisher. The editor can't be null: (publisher = Column(nullable=False))")

    # Test of ISSN query of publishers without an assigned value in
    # IssnPublisher
    def test_get_all_issn_without_publisher(self):
        documents = [
            (
                "Title3",
                "Abstract3",
                "Keyword3",
                "Author3",
                "2022-01-03",
                "DOI3",
                "EID3",
                "Publication3",
                "ISSN3",
                "EISSN3",
                "Type3",
                "SubType3",
                "Query3",
                "Source3",
                "Country3",
                10,
                "Access3",
            )
        ]
        self.orm.save(documents)

        result_issn_without_publisher = self.orm.get_all_issn_without_publisher()
        expected_result = [("EID3", "ISSN3", "EISSN3")]
        self.assertEqual(
            result_issn_without_publisher,
            expected_result,
            "Error in get_all_issn_without_publisher",
        )

    # Query test of countries without an assigned continent
    def test_get_empty_continents(self):
        documents = [
            (
                "Title4",
                "Abstract4",
                "Keyword4",
                "Author4",
                "2022-01-04",
                "DOI4",
                "EID4",
                "Publication4",
                "ISSN4",
                "EISSN4",
                "Type4",
                "SubType4",
                "Query4",
                "Source4",
                "Country4",
                10,
                "Access4",
            )
        ]

        self.orm.save(documents)
        continents = [
            ("Country1", "Continent1"),
            ("Country2", "Continent2"),
            ("Country3", "Continent3"),
            ("Country5", "Continent5"),
        ]
        self.orm.set_continent(continents)

        result = list(self.orm.get_empty_continents())
        self.assertEqual(result, ["Country4"], "Error in " "get_empty_continents")

    # DoiEurl publication test
    def test_set_doi_eurl(self):
        expected_url = "http://example.com"
        doi = "10.1000/xyz123"

        try:
            self.orm.set_doi_eurl(doi, expected_url)
        except Exception as e:
            self.fail(f"Error in set_doi_eurl: {e}")

        with self.orm.db.get_session() as sess:
            doi_eurl_instance = sess.query(DoiEurl).filter_by(doi=doi).first()
            if doi_eurl_instance is not None:
                result = doi_eurl_instance.eurl
            else:
                result = None

        self.assertEqual(result, expected_url, "Error in set_doi_eurl")

    # Openaccess publishing and query test
    def test_set_get_empty_openaccess_status(self):
        documents = [
            (
                "Title5",
                "Abstract5",
                "Keyword5",
                "Author5",
                "2022-01-05",
                "DOI5",
                "EID5",
                "Publication5",
                "ISSN5",
                "EISSN5",
                "Type5",
                "SubType5",
                "Query5",
                "Source5",
                "Country5",
                10,
                None,
            )
        ]
        self.orm.save(documents)

        try:
            self.orm.set_status_studyselection(1, 3)

            result_before_update = self.orm.get_empty_openaccess()

            self.assertIn(
                "EID5",
                result_before_update,
                "Error in get_empty_openaccess after update",
            )

            self.orm.set_openaccess("EID5", "openaccess")

            result_after_update = self.orm.get_empty_openaccess()
            self.assertNotIn(
                "EID5",
                result_after_update,
                "Error in get_empty_openaccess after openaccess update",
            )

        except Exception as error:
            LOGGER.error(f"Error in test_set_get_empty_openaccess_status. {error}\n")

    @classmethod
    def tearDownClass(cls):
        pass


if __name__ == "__main__":
    unittest.main()

"""
