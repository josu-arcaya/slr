import abc
import logging

from src.core.utils import Persistence

LOGGER = logging.getLogger("systematic")


class Query:

    def __init__(self, persistence: Persistence):
        self._persistence = persistence

    @abc.abstractmethod
    def next_page(self, url):
        raise NotImplementedError

    @abc.abstractmethod
    def fetch_all(self):
        raise NotImplementedError
