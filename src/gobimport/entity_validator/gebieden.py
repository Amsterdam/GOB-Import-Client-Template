""" Gebieden specific validation

Validations which need to happen after converting the data to GOBModel.
"""

import datetime

from gobcore.logging.logger import logger


def _validate_bouwblokken(entities, source_id):
    """
    Validate bouwblokken

    Checks that are being performed:

    - begin_geldigheid can not be in the future (fatal)

    :param entities: the list of entities
    :return:
    """
    validated = True

    for entity in entities:
        # begin_geldigheid can not be in the future
        identificatie = str(entity[source_id])
        if entity['begin_geldigheid'] > datetime.datetime.utcnow():
            msg = "begin_geldigheid can not be in the future"
            extra_data = {
                'id': msg,
                'data': {
                    'identificatie': identificatie,
                    'begin_geldigheid': entity['begin_geldigheid'].isoformat(),
                }
            }
            logger.error(msg, extra_data)
            validated = False

    return validated


def _validate_buurten(entities, source_id):
    """
    Validate buurten

    Checks that are being performed:

    - documentdatum can not be after eind_geldigheid (warning)

    :param entities: the list of entities
    :return:
    """
    validated = True

    for entity in entities:
        # get eind_geldigheid or use current date
        eind_geldigheid = entity['eind_geldigheid'] if entity['eind_geldigheid'] \
            else datetime.datetime.utcnow().date()

        documentdatum = entity['documentdatum']
        # documentdatum should not be after eind_geldigheid
        if documentdatum and documentdatum > eind_geldigheid:
            log_date_comparison(entity, 'documentdatum', 'eind_geldigheid', source_id)

        registratiedatum = entity['registratiedatum']
        # registratiedatum should not be after eind_geldigheid
        if registratiedatum and registratiedatum.date() > eind_geldigheid:
            log_date_comparison(entity, 'registratiedatum', 'eind_geldigheid', source_id)

    return validated


def log_date_comparison(entity, date_field, compare_date_field, source_id):
    """
    Log date comparison

    Logs the a warning for a date comparison between 2 fields

    :param entity: the entity which is compared
    :param date_field: field name of the date
    :param compare_date_field: field name of the compared date
    :param source_id: the functional source id
    :return:
    """
    identificatie = str(entity[source_id])
    msg = f"{date_field} can not be after {compare_date_field}"
    extra_data = {
        'id': msg,
        'data': {
            'identificatie': identificatie,
            '{date_field}': entity[date_field].isoformat(),
            '{compare_date_field}': entity[compare_date_field].isoformat(),
        }
    }
    logger.warning(msg, extra_data)
