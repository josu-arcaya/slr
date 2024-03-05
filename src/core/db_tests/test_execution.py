import unittest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from models import (Publisher, Base, IssnImpact, IssnPublisher, EissnPublisher, Document, DoiEurl, Continent,
                    AggregatedPublisher, Manuscript, Journal)  # Importar ./models después del merge
from utils import SqlAlchemyORM  # Importar ./utils después del merge
import data_script


class TestSqlAlchemyORM(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SqlAlchemyORM()
        cls.engine = cls.db.engine
        cls.Session = sessionmaker(bind=cls.engine)

    def test_all(self):

        classes = [Publisher, IssnImpact, IssnPublisher, EissnPublisher, Document, DoiEurl, Continent,
                   AggregatedPublisher, Manuscript, Journal]

        for cls in classes:

            # Crear tabla
            if not inspect(self.engine).has_table(cls.__tablename__):
                Base.metadata.tables[cls.__tablename__].create(bind=self.engine)
            self.assertTrue(inspect(self.engine).has_table(cls.__tablename__), f"Tabla {cls.__tablename__} no creada")

            # Añadir datos
            session = self.Session()
            instance = cls(**data_script.test_data[cls.__name__])
            session.add(instance)
            session.commit()

            # Consultar datos
            queried_instance = session.query(cls).first()
            self.assertIsNotNone(queried_instance, f"No se ha podido hacer una consulta en {cls.__name__}")

            # Eliminar datos
            session.delete(queried_instance)
            session.commit()
            queried_instance = session.query(cls).first()
            self.assertIsNone(queried_instance, f"No se han podido eliminar datos de {cls.__name__}")

            # Eliminar tabla
            Base.metadata.tables[cls.__tablename__].drop(bind=self.engine)
            self.assertFalse(inspect(self.engine).has_table(cls.__tablename__), f"Tabla {cls.__tablename__} no eliminada")


if __name__ == "__main__":
    unittest.main()
