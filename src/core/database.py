import logging
import os

from abstract_database import AbstractDatabase
from models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Configure logging
LOGGER = logging.getLogger(__name__)


class Database(AbstractDatabase):
    def __init__(self, db_name="documents.db"):
        """
        Constructor for the Database class.

        Parameters:
        - db_name: (str) Name of the database file. Default is "documents.db".
        """
        self._db_name = db_name
        self._engine = create_engine(f"sqlite:///{self._db_name}")
        self._Session = sessionmaker(bind=self._engine)
        self.create_database()

    def get_session(self):
        """
        Get a new database session.

        Returns:
        - SQLAlchemy session object.
        """
        return self._Session()

    def create_database(self):
        """
        Method for creating the database.

        This method checks if the database already exists in the file system.
        If the database does not exist, it uses the model definitions
        (declared in the Base class) to create all the corresponding tables in
        the database, the models are located in models.py.

        If the database already exists, no additional action is taken
        and an informative message is logged.
        """
        if not os.path.exists(self._db_name):
            Base.metadata.create_all(self._engine)
            LOGGER.info("Database created successfully")
        else:
            LOGGER.info("Database already created")

    @property
    def engine(self):
        """
        Get the SQLAlchemy engine object.

        Returns:
        - SQLAlchemy engine object.
        """
        return self._engine