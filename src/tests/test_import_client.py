from unittest import TestCase
from unittest.mock import MagicMock, patch, call

from gobcore.model import GOBModel
from gobimport.import_client import ImportClient
from tests import fixtures

from gobcore.enum import ImportMode


@patch('gobimport.converter.GOBModel', MagicMock(spec=GOBModel))
@patch.object(GOBModel, 'has_states', MagicMock())
@patch.object(GOBModel, 'get_collection', MagicMock())
class TestImportClient(TestCase):

    import_client = None

    def setUp(self):
        self.mock_dataset = {
            'source': {
                'entity_id': fixtures.random_string(),
                'application': fixtures.random_string(),
                'name': fixtures.random_string(),
                'type': 'file',
                'config': {},
                'query': fixtures.random_string(),
            },
            'version': 0.1,
            'catalogue': fixtures.random_string(),
            'entity': fixtures.random_string(),
            'gob_mapping': {}
        }

        self.mock_msg = {
            'header': {}
        }

    def test_init(self):
        logger = MagicMock()
        self.import_client = ImportClient(self.mock_dataset, self.mock_msg, logger)

        logger.info.assert_called()

    def test_publish(self):
        logger = MagicMock()
        self.import_client = ImportClient(self.mock_dataset, self.mock_msg, logger)
        self.import_client.n_rows = 10
        self.import_client.filename = "filename"
        msg = self.import_client.get_result_msg()
        self.assertEqual(msg['contents_ref'], 'filename')
        self.assertEqual(msg['summary']['num_records'], 10)
        self.assertEqual(msg['header']['version'], 0.1)

    @patch('gobimport.import_client.Reader')
    def test_import_rows(self, mock_Reader):
        mock_reader = MagicMock()
        mock_Reader.return_value = mock_reader
        rows = ((1, 2), (3, 4))
        mock_reader.read.return_value = rows

        progress = MagicMock()
        write = MagicMock()

        _self = MagicMock()
        _self.logger = MagicMock()
        _self.injector.inject = MagicMock()
        _self.merger = MagicMock()
        _self.converter = MagicMock()
        entity = 'Entity'
        _self.converter.convert.return_value = entity
        _self.validator = MagicMock()
        ImportClient.import_rows(_self, write, progress)
        _self.logger.info.assert_called()
        self.assertEquals(_self.injector.inject.call_args_list, [call(c) for c in rows])
        self.assertEquals(_self.merger.merge.call_args_list, [call(c, write) for c in rows])
        self.assertEquals(_self.converter.convert.call_args_list, [call(c) for c in rows])
        self.assertEquals(_self.validator.validate.call_args_list, [call(entity) for c in rows])
        self.assertEquals(write.call_args_list, [call(entity) for c in rows])

        _self.validator.result.called_once_with()
        self.assertEquals(len(_self.logger.info.call_args_list), 3)

    @patch('gobimport.import_client.Reader')
    def test_import_row_too_few_records(self, mock_Reader):
        reader = MagicMock()
        mock_Reader.return_value = reader
        rows = set()
        reader.read.return_value = rows

        progress = MagicMock()
        write = MagicMock()

        _self = MagicMock()
        _self.mode = ImportMode.FULL
        _self.dataset = {}
        ImportClient.import_rows(_self, write, progress)

        _self.validator.result.assert_called_once_with()
        self.assertEquals(len(_self.logger.info.call_args_list), 3)
        self.assertEquals(len(_self.logger.error.call_args_list), 1)

    @patch('gobimport.import_client.ContentsWriter')
    @patch('gobimport.import_client.ProgressTicker')
    def test_import_dataset(self, mock_ProgressTicker, mock_ContentsWriter):
        _self = MagicMock()
        _self.get_result_msg.return_value = 'res'
        writer = MagicMock()
        mock_ContentsWriter.return_value.__enter__.return_value = writer
        filename = 'fname'
        writer.filename = filename
        writer.write = 'write'
        progress = MagicMock()
        mock_ProgressTicker.return_value.__enter__.return_value = progress

        res = ImportClient.import_dataset(_self)

        self.assertEquals(res, 'res')
        mock_ProgressTicker.called_once()
        _self.merger.prepare.assert_called_once_with(progress)
        self.assertEquals(_self.filename, filename)
        _self.import_rows.assert_called_once_with('write', progress)
        _self.merger.finish.assert_called_once_with('write')
        _self.entity_validator.result.assert_called_once()

    @patch('gobimport.import_client.ContentsWriter')
    @patch('gobimport.import_client.ProgressTicker')
    @patch('gobimport.import_client.traceback')
    def test_import_dataset_exception(self, mock_traceback, mock_ProgressTicker, mock_ContentsWriter):
        _self = MagicMock()
        _self.get_result_msg.return_value = 'res'
        writer = MagicMock()
        writer.side_effect = Exception('Boom')
        mock_ContentsWriter.return_value.__enter__ = writer

        res = ImportClient.import_dataset(_self)

        self.assertEquals(res, 'res')
        self.assertEquals(len(_self.logger.error.call_args_list), 2)
        mock_traceback.format_exc.assert_called_once_with(limit=-5)
