from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from sqlalchemy.ext.declarative import declarative_base
from abstract_database import AbstractDatabase
from models import Base


class Database(AbstractDatabase):
    def __init__(self, db_name="documents.db"):
        """
        Constructor para la clase Database.

        Parámetros:
        - db_name: (str) Nombre del archivo de la base de datos. Por defecto es "documents.db".
        """
        self._db_name = db_name
        self._engine = create_engine(f'sqlite:///{self._db_name}')
        self._Session = sessionmaker(bind=self._engine)
        self.create_database()

    def get_session(self):
        """
        Obtener una nueva sesión de la base de datos.

        Retorna:
        - Objeto de sesión de SQLAlchemy.
        """
        return self._Session()

    def create_database(self):
        """
               Método para la creación de la base de datos.

               Este método se encarga de verificar si la base de datos ya existe en el sistema de archivos.
               En caso de que la base de datos no exista, se utilizan las definiciones de modelo
               (declaradas en la clase Base) para crear todas las tablas correspondientes en la base de datos,
               los modelos se encuentran en models.py.

               Si la base de datos ya existe, no se realiza ninguna acción adicional y se imprime un mensaje informativo.
        """
        if not os.path.exists(self._db_name):
            Base.metadata.create_all(self._engine)
            print("Database created successfully")
        else:
            print("Database already created")

    @property
    def engine(self):
        """
        Obtener el objeto de motor de SQLAlchemy.

        Retorna:
        - Objeto de motor de SQLAlchemy.
        """
        return self._engine