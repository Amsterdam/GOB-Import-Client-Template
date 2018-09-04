"""Implementation of data input connectors

The following connectors are implemented in this module:
    CSV - Connects to a csv formatted file, using the separator and encoding as specified in the config parameter

"""
import os
import pandas

from gobimportclient.config import LOCAL_DATADIR


def connect_to_file(config):
    """Connect to the datasource

    The pandas library is used to connect to the data source for CSV data files

    :return:
    """
    file_path = os.path.join(LOCAL_DATADIR, config['filename'])
    if config['filetype'] == "CSV":
        return pandas.read_csv(
            filepath_or_buffer=file_path,
            sep=config['separator'],
            encoding=config['encoding'],
            dtype=str)
    else:
        raise NotImplementedError