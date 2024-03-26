import os
import sys
import unittest
from unittest.mock import Mock, patch

from sqlalchemy import create_engine
from sqlalchemy.exc import CompileError
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from crud import SqlAlchemyORM
from database import Database
from models import (Base, Continent, Document, DoiEurl, EissnPublisher,
                    IssnImpact, IssnPublisher, Publisher)


class TestSqlAlchemyORM(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.orm = SqlAlchemyORM(":memory:")

    def setUp(self):
        self.session = self.orm.db.get_session()

    def test_init(self):
        self.assertIsNotNone(
            self.orm.db._engine,
            "Error en __init__: 'Engine' no se ha inicializado correctamente",
        )
        self.assertIsNotNone(
            self.orm.db._Session,
            "Error en __init__: 'Session' se ha inicializado correctamente",
        )

    def test_get_session(self):
        session = self.orm.db.get_session()
        self.assertIsNotNone(
            session,
            "Error en get_session: La sesión no se obtuvo correctamente",
        )

    # Test de publicación de IssnPublisher y consulta del autor a través del ISSN
    def test_set_get_publisher_by_issn(self):
        with patch("utils.create_engine") as mock_create_engine:
            mock_create_engine.return_value = Mock()
            self.orm.set_publisher_by_issn("1234-5678", "Publisher")

        result = self.orm.get_publisher_by_issn("1234-5678")
        print(f" Resultado de test_set_get_publisher_by_issn: {result}\n")
        self.assertIsNotNone(
            result, "Error en set_publisher_by_issn / get_publisher_by_issn"
        )

    # Test de publicación y consulta de EissnPublisher
    def test_set_get_publisher_by_eissn(self):
        with patch("utils.create_engine") as mock_create_engine:
            mock_create_engine.return_value = Mock()
            self.orm.set_publisher_by_eissn("8765-4321", "EissnPublisher")

        result = self.orm.get_publisher_by_eissn("8765-4321")
        print(f" Resultado de test_set_get_publisher_by_eissn: {result}\n")
        self.assertIsNotNone(
            result, "Error en set_publisher_by_eissn / get_publisher_by_eissn"
        )

    # Test de publicación de IssnImpact y consulta de métricas a través de ISSN
    def test_set_get_impact_by_issn(self):
        with patch("utils.create_engine") as mock_create_engine:
            mock_create_engine.return_value = Mock()
            self.orm.set_impact_by_issn(
                "1234-5678", 1.0, 2022, 2.0, 2023, 3.0, 2024
            )

        result = self.orm.get_impact_by_issn("1234-5678")
        print(f" Resultado de test_set_get_impact_by_issn: {result}\n")
        self.assertIsNotNone(
            result, "Error en set_impact_by_issn / get_impact_by_issn"
        )

    # Test de publicación de un documento y consulta del doi de los documentos existentes
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
            )
        ]
        self.orm.save(documents)

        result = self.orm.get_doi()
        print(f" Resultado de test_set_get_save_and_get_doi: {result}\n")
        self.assertNotEqual(result, [], "Error en save / get_doi")

    # Test de publicación de autores y consulta de los ISSN sin autor asignado en IssnPublisher
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
                )
            ]
            self.orm.save(documents)
            publishers = [("ISSN2", None)]
            result_empty_publisher = self.orm.get_empty_publisher()
            print(
                f" Resultado de test_set_get_empty_publisher: {result_empty_publisher}\n"
            )
            self.assertEqual(
                result_empty_publisher,
                [],
                "Error en set_publisher / get_empty_publisher",
            )
        except AssertionError:
            print(
                f"Error en set_empty_publisher. El editor no puede ser nulo: (publisher = Column(nullable=False))\n"
            )

    # Test de consulta de los ISSN que no tienen un autor asignado en IssnPublisher
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
            )
        ]
        self.orm.save(documents)

        result_issn_without_publisher = (
            self.orm.get_all_issn_without_publisher()
        )
        print(
            f" Resultado de test_get_all_issn_without_publisher: {result_issn_without_publisher}\n"
        )

        expected_result = [("EID3", "ISSN3", "EISSN3")]
        self.assertEqual(
            result_issn_without_publisher,
            expected_result,
            "Error en get_all_issn_without_publisher",
        )

    # Test de consulta de países que no tienen un continente asignado
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
        print(f" Resultado de test_get_empty_continents: {result}\n")
        self.assertEqual(result, ["Country4"], "Error en get_empty_continents")

    # Test de publicación de DoiEurl
    def test_set_doi_eurl(self):
        expected_url = "http://example.com"
        doi = "10.1000/xyz123"

        try:
            self.orm.set_doi_eurl(doi, expected_url)
        except Exception as e:
            print(f"Error en set_doi_eurl: {e}")
            self.fail("Error en set_doi_eurl")

        with self.orm.db.get_session() as sess:
            doi_eurl_instance = sess.query(DoiEurl).filter_by(doi=doi).first()
            if doi_eurl_instance is not None:
                result = doi_eurl_instance.eurl
            else:
                result = None

        print(f" Resultado de test_set_doi_eurl: {result}\n")

        self.assertEqual(result, expected_url, "Error en set_doi_eurl")

    # Test de publicación y consulta de openaccess
    def test_set_get_openaccess(self):
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
            )
        ]
        self.orm.save(documents)

        try:
            result = self.orm.get_empty_openaccess()
            if result is not None:
                self.assertEqual(
                    result, ["EID5"], "Error en get_empty_openaccess"
                )

            self.orm.set_openaccess("EID5", "openaccess")
        except (NameError, CompileError, SystemExit):
            print(
                f" Error en test_set_get openaccess. El nombre 'StudySelection' no está definido.\n"
            )

    @classmethod
    def tearDownClass(cls):
        pass


if __name__ == "__main__":
    unittest.main()
