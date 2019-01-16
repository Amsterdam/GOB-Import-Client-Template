import decimal
import unittest
from unittest import mock

from gobimport.enricher.gebieden import _enrich_buurten, _enrich_wijken, CBS_BUURTEN_API, CBS_WIJKEN_API, _add_cbs_code
from gobimport.enricher.gebieden import enrich_ggwgebieden, enrich_ggpgebieden

class MockResponse:

    @property
    def ok(self):
        return True

    def json(self):
        return {'features': [
            {
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [[
                        [0,0],
                        [1,0],
                        [1,1],
                        [0,1],
                        [0,0]
                    ]]
                },
                'properties': {
                    'water': 'NEE',
                    'buurtcode': 'BU03630001',
                    'buurtnaam': 'Buurt'
                },
            },
            {
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [[
                        [0,0],
                        [1,0],
                        [1,1],
                        [0,1],
                        [0,0]
                    ]]
                },
                'properties': {
                    'water': 'NEE',
                    'buurtcode': 'BU03630002',
                    'buurtnaam': 'Buurt dubbel'
                },
            },
            {
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [[
                        [1,1],
                        [2,1],
                        [2,2],
                        [1,2],
                        [1,1]
                    ]]
                },
                'properties': {
                    'water': 'NEE',
                    'buurtcode': 'BU03630003',
                    'buurtnaam': 'Buurt anders'
                },
            },
            {
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': [[
                        [1,1],
                        [2,1],
                        [2,2],
                        [1,2],
                        [1,1]
                    ]]
                },
                'properties': {
                    'water': 'JA',
                    'buurtcode': 'BU03630004',
                    'buurtnaam': 'Buurt water'
                },
            }
        ]}

class TestEnricher(unittest.TestCase):

    def setUp(self):
        self.entities = [
            {
                'identificatie': '1234',
                'naam': 'Buurt',
                'datum_einde_geldigheid': '',
                'geometrie': 'POLYGON((0 0,1 0,1 1,0 1,0 0))'
            },
            {
                'identificatie': '1235',
                'naam': 'Buurt',
                'datum_einde_geldigheid': '',
                'geometrie': 'POLYGON((1 1,2 1,2 2,1 2,1 1))'
            },
            {
                'identificatie': '1236',
                'naam': 'Buurt',
                'datum_einde_geldigheid': '2015-01-01',
                'geometrie': 'POLYGON((2 2,3 2,3 3,2 3,2 2))'
            }
        ]
        self.log = lambda x, y, z: x

    @mock.patch('gobimport.enricher.gebieden._add_cbs_code')
    def test_enrich_buurten(self, mock_add_cbs):
        _enrich_buurten(self.entities, self.log)

        mock_add_cbs.assert_called_with(self.entities, CBS_BUURTEN_API, 'buurt', self.log)

    @mock.patch('gobimport.enricher.gebieden._add_cbs_code')
    def test_enrich_wijken(self, mock_add_cbs):
        _enrich_wijken(self.entities, self.log)

        mock_add_cbs.assert_called_with(self.entities, CBS_WIJKEN_API, 'wijk', self.log)

    @mock.patch('gobimport.enricher.gebieden.requests.get')
    def test_add_cbs_code(self, mock_request):
        mock_request.return_value = MockResponse()
        _add_cbs_code(self.entities, CBS_BUURTEN_API, 'buurt', self.log)

        # Expect cbs codes buurt
        self.assertEqual('BU03630001', self.entities[0]['cbs_code'])

        # Expect an empty string when datum_einde_geldigheid is not empty
        self.assertEqual('', self.entities[2]['cbs_code'])

class TestGGWPEnricher(unittest.TestCase):

    def setUp(self):
        self.entitites = [
            {

            }
        ]

    def test_enrich_ggwgebieden(self):
        ggwgebieden = [
            {
                "GGW_BEGINDATUM": "YYYY-MM-DD HH:MM:SS",
                "GGW_EINDDATUM": "YYYY-MM-DD HH:MM:SS.fff",
                "GGW_DOCUMENTDATUM": "YYYY-MM-DD",
                "WIJKEN": "1, 2, 3",
                "_file_info": {
                    "last_modified": "2020-01-20T12:30:30.12345"
                }
            }
        ]
        enrich_ggwgebieden(ggwgebieden, log=None)
        self.assertEqual(ggwgebieden, [
            {
                "_IDENTIFICATIE": None,
                "_REGISTRATIEDATUM": "2020-01-20T12:30:30.12345",
                "_VOLGNUMMER": 1579519830,
                "GGW_BEGINDATUM": "YYYY-MM-DD",
                "GGW_EINDDATUM": "YYYY-MM-DD",
                "GGW_DOCUMENTDATUM": "YYYY-MM-DD",
                "WIJKEN": ["1", "2", "3"],
                "_file_info": {"last_modified": "2020-01-20T12:30:30.12345"}
            }
        ])

    def test_enrich_ggpgebieden(self):
        ggpgebieden = [
            {
                "GGP_BEGINDATUM": "YYYY-MM-DD HH:MM:SS",
                "GGP_EINDDATUM": "YYYY-MM-DD HH:MM:SS.fff",
                "GGP_DOCUMENTDATUM": None,
                "BUURTEN": "1, 2, 3",
                "_file_info": {
                    "last_modified": "2020-01-20T12:30:30.12345"
                }
            }
        ]
        enrich_ggpgebieden(ggpgebieden, log=None)
        self.assertEqual(ggpgebieden, [
            {
                "_IDENTIFICATIE": None,
                "_REGISTRATIEDATUM": "2020-01-20T12:30:30.12345",
                "_VOLGNUMMER": 1579519830,
                "GGP_BEGINDATUM": "YYYY-MM-DD",
                "GGP_EINDDATUM": "YYYY-MM-DD",
                "GGP_DOCUMENTDATUM": None,
                "BUURTEN": ["1", "2", "3"],
                "_file_info": {"last_modified": "2020-01-20T12:30:30.12345"}
            }
        ])
