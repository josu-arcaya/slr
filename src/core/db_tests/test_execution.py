import unittest
import data_script
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, inspect

from ..utils import SqlAlchemyORM
from ..models import (Base, Publisher, IssnImpact, IssnPublisher, EissnPublisher, Document, DoiEurl, Continent,
                      AggregatedPublisher, Manuscript, Journal)


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
            self.assertTrue(inspect(self.engine).has_table(cls.__tablename__), f"Tabla {cls.__name__} no creada")

            # Añadir datos
            session = self.Session()
            try:
                instance = cls(**data_script.test_data[cls.__name__])
                session.add(instance)
                session.commit()
                queried_instance = session.query(cls).first()
                self.assertIsNotNone(queried_instance, f"No se han podido añadir datos a {cls.__name__}")
            except Exception as e:
                print(f"Error al añadir datos a la tabla {cls.__name__}: {e}")

            # Consultar datos
            queried_instance = session.query(cls).first()
            self.assertIsNotNone(queried_instance, f"No se ha podido hacer una consulta en {cls.__name__}")

            # Eliminar datos
            session.delete(queried_instance)
            session.commit()
            queried_instance = session.query(cls).first()
            self.assertIsNone(queried_instance, f"No se han podido eliminar los datos de {cls.__name__}")

            # Eliminar tabla
            Base.metadata.tables[cls.__tablename__].drop(bind=self.engine)
            self.assertFalse(inspect(self.engine).has_table(cls.__tablename__), f"Tabla {cls.__name__} no eliminada")

            print(f"Todas las operaciones para la tabla {cls.__name__} se han realizado correctamente.")


if __name__ == "__main__":
    unittest.main()
