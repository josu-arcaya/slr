import abc
import json
import logging
import os
import time
import urllib
import urllib.request

from src.core.utils import Manuscript, Persistence

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
