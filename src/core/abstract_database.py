from abc import ABC, abstractmethod


class AbstractDatabase(ABC):
    @abstractmethod
    def get_session(self):
        pass

    @abstractmethod
    def create_database(self):
        pass

    @property
    @abstractmethod
    def engine(self):
        pass

from abc import ABC, abstractmethod


class AbstractDatabase(ABC):
    @abstractmethod
    def get_session(self):
        pass

    @abstractmethod
    def create_database(self):
        pass

    @property
    @abstractmethod
    def engine(self):
        pass