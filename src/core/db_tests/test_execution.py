import unittest
from unittest.mock import Mock, patch
from ..utils import SqlAlchemyORM


class TestSqlAlchemyORM(unittest.TestCase):

    def setUp(self):
        self.orm = SqlAlchemyORM()

    def test_init(self):
        self.assertTrue(os.path.exists(self.orm._db_name), "Error en __init__: La base de datos no se ha creado")
        self.assertIsNotNone(self.orm._engine, "Error en __init__: El motor no se ha inicializado correctamente")
        self.assertIsNotNone(self.orm._Session, "Error en __init__: La sesión se ha inicializado correctamente")

    def test_get_session(self):
        # Verifica que el método get_session devuelve una sesión válida
        session = self.orm.get_session()
        self.assertIsNotNone(session, "Error en get_session: La sesión no se obtuvo correctamente")

    def test_get_impact_by_issn(self):
        result = self.orm.get_impact_by_issn('1234-5678')
        self.assertIsNone(result, "Error en get_impact_by_issn")

    def test_set_impact_by_issn(self):
        with patch('your_module.utils.create_engine') as mock_create_engine:
            mock_create_engine.return_value = Mock()
            self.orm.set_impact_by_issn('1234-5678', 1.0, 2022,
                                        2.0, 2023, 3.0, 2024)

        result = self.orm.get_impact_by_issn('1234-5678')
        self.assertIsNotNone(result, "Error en set_impact_by_issn")

    def test_get_publisher_by_issn(self):
        result = self.orm.get_publisher_by_issn('1234-5678')
        self.assertIsNone(result, "Error en get_publisher_by_issn")

    def test_set_publisher_by_issn(self):
        with patch('your_module.utils.create_engine') as mock_create_engine:
            mock_create_engine.return_value = Mock()
            self.orm.set_publisher_by_issn('1234-5678', 'Publisher')

        result = self.orm.get_publisher_by_issn('1234-5678')
        self.assertIsNotNone(result, "Error en set_publisher_by_issn")

    def test_get_publisher_by_eissn(self):
        result = self.orm.get_publisher_by_eissn('8765-4321')
        self.assertIsNone(result, "Error en get_publisher_by_eissn")

    def test_set_publisher_by_eissn(self):
        with patch('your_module.utils.create_engine') as mock_create_engine:
            mock_create_engine.return_value = Mock()
            self.orm.set_publisher_by_eissn('8765-4321', 'EissnPublisher')

        result = self.orm.get_publisher_by_eissn('8765-4321')
        self.assertIsNotNone(result, "Error en set_publisher_by_eissn")

    def test_save(self):
        documents = [('Title1', 'Abstract1', 'Keyword1', 'Author1', '2022-01-01', 'DOI1', 'EID1',
                      'Publication1', 'ISSN1', 'EISSN1', 'Type1', 'SubType1', 'Query1', 'Source1',
                      'Country1', 10)]
        self.orm.save(documents)

        # Verifica que los documentos se hayan insertado correctamente
        result = self.orm.get_impact_by_issn('ISSN1')
        self.assertIsNotNone(result, "Error en save")

    def test_get_all_issn_without_publisher(self):
        result = self.orm.get_all_issn_without_publisher()
        self.assertEqual(result, [], "Error en get_all_issn_without_publisher")

    def test_get_all_eissn_without_publisher(self):
        result = self.orm.get_all_eissn_without_publisher()
        self.assertEqual(result, [], "Error en get_all_eissn_without_publisher")

    def test_get_empty_publisher(self):
        result = self.orm.get_empty_publisher()
        self.assertEqual(result, [], "Error en get_empty_publisher")

    def test_set_publisher(self):
        publishers = [('ISSN1', 'Publisher1'), ('ISSN2', 'Publisher2')]
        self.orm.set_publisher(publishers)

        result = self.orm.get_publisher_by_issn('ISSN1')
        self.assertIsNotNone(result, "Error en set_publisher")

    def test_get_empty_continents(self):
        result = self.orm.get_empty_continents()
        self.assertEqual(result, [], "Error en get_empty_continents")

    def test_set_continent(self):
        continents = [('Country1', 'Continent1'), ('Country2', 'Continent2')]
        self.orm.set_continent(continents)

        result = self.orm.get_empty_continents()
        self.assertEqual(result, [], "Error en set_continent")

    def test_get_doi(self):
        result = self.orm.get_doi()
        self.assertEqual(result, [], "Error en get_doi")

    def test_set_doi_eurl(self):
        self.orm.set_doi_eurl('DOI1', 'EURL1')

        result = self.orm.get_doi()
        self.assertEqual(result, [('DOI1',)], "Error en set_doi_eurl")

    def test_get_empty_openaccess(self):
        result = self.orm.get_empty_openaccess()
        self.assertEqual(result, [], "Error en get_empty_openaccess")

    def tearDown(self):
        pass


if __name__ == '__main__':
    unittest.main()
