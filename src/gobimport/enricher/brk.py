"""
BRK enrichment

"""
from gobimport.enricher.enricher import Enricher


class BRKEnricher(Enricher):

    @classmethod
    def enriches(cls, app_name, catalog_name, collection_name):
        if catalog_name == "brk":
            enricher = BRKEnricher(app_name, catalog_name, collection_name)
            return enricher._enrich_entity is not None

    def __init__(self, app_name, catalog_name, collection_name):

        self.multiple_values_logged = False

        super().__init__(app_name, catalog_name, collection_name, methods={
            "gemeentes": self.enrich_gemeentes,
        })

    def enrich_gemeentes(self, gemeente):
        gemeente['code'] = gemeente['properties'].get('code')
        gemeente['gemeentenaam'] = gemeente['properties'].get('gemeentenaam')
