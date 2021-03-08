"""
Abstract base class for any enrichment class

"""
from abc import ABC, abstractmethod


class Enricher(ABC):

    @classmethod
    @abstractmethod
    def enriches(cls, app_name, catalog_name, collection_name):
        """
        Tells wether this class enriches the given catalog - collection
        :param catalog_name:
        :param collection_name:
        :return:
        """
        pass

    def __init__(self, app_name, catalog_name, collection_name, methods):
        """
        Given the methods and collection name, the enrich_entity method is set

        :param methods:
        :param entity_name:
        """
        self.app_name = app_name
        self.catalog_name = catalog_name
        self.collection_name = collection_name
        self._enrich_entity = methods.get(collection_name)

    def enrich(self, entity):
        """
        Enrich a single entity

        :param entity:
        :return:
        """
        if self._enrich_entity:
            self._enrich_entity(entity)
