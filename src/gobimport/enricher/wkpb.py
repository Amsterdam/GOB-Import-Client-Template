"""
WKPB enrichment

"""
from gobimport.enricher.enricher import Enricher


class WKPBEnricher(Enricher):

    @classmethod
    def enriches(cls, app_name, catalog_name, collection_name):
        if catalog_name == "wkpb":
            enricher = WKPBEnricher(app_name, catalog_name, collection_name)
            return enricher._enrich_entity is not None

    def __init__(self, app_name, catalog_name, collection_name):

        self.multiple_values_logged = False

        super().__init__(app_name, catalog_name, collection_name, methods={
            "dossiers": self.enrich_dossier,
        })

    def enrich_dossier(self, dossier):
        dossier['heeft_wkpb_brondocument'] = dossier['heeft_wkpb_brondocument'].split(";")
