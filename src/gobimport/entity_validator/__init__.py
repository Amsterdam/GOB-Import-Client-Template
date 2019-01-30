""" Entity validation

Validation will take place after the imported data has been converted into the GOBModel.
This is done to be able to perform comparisons between dates in the imported data or
run specific validation for certain collections.
"""
from collections import defaultdict

from gobcore.exceptions import GOBException
from gobcore.model import GOBModel
from gobimport.entity_validator.gebieden import _validate_bouwblokken, _validate_buurten


def entity_validate(catalogue, entity_name, entities, log):
    """
    Validate each entity in the list of entities for a given entity name

    :param catalogue: the name of the catalogue, e.g. meetbouten
    :param entity_name: the name of the entity, e.g. meetbouten
    :param entities: the list of entities
    :param log: log function of the import client
    :return:
    """
    # if model has state, run validations for checks with state
    model = GOBModel()
    states_validated = True
    if model.get_collection(catalogue, entity_name).get('has_states'):
        states_validated = _validate_entity_state(entities, log)

    validators = {
        "bouwblokken": _validate_bouwblokken,
        "buurten": _validate_buurten,
    }

    try:
        validate_entities = validators[entity_name]
    except KeyError:
        return

    # Raise an Exception is a fatal validation has failed
    if not validate_entities(entities, log) or not states_validated:
        raise GOBException(
            f"Quality assurance failed for {entity_name}"
        )


def _validate_entity_state(entities, log):
    """
    Validate entitys with state to see if generic validations for states are correct.

    Checks that are being performed:

    - begin_geldigheid should not be after eind_geldigheid (when filled)
    - volgnummer should be a positive number and unique in the collection

    :param entities: the list of entities
    :param log: log function of the import client
    :return:
    """
    validated = True

    volgnummers = defaultdict(set)

    for entity in entities:
        # begin_geldigheid can not be after eind_geldigheid when filled
        if entity['eind_geldigheid'].to_db and \
           entity['eind_geldigheid'].to_db < entity['begin_geldigheid'].to_db:
            msg = "begin_geldigheid can not be after eind_geldigheid"
            extra_data = {
                'data': {
                    'identificatie': entity['identificatie'],
                    'begin_geldigheid': entity['begin_geldigheid'],
                    'eind_geldigheid': entity['eind_geldigheid'],
                }
            }
            log("error", msg, extra_data)
            validated = False

        # volgnummer should a positive number and unique in the collection
        volgnummer = str(entity['volgnummer'])
        identificatie = str(entity['identificatie'])
        if int(volgnummer) < 1 or volgnummer in volgnummers[identificatie]:
            msg = "volgnummer should be a positive number and unique in the collection"
            extra_data = {
                'data': {
                    'identificatie': entity['identificatie'],
                    'volgnummer': entity['volgnummer'],
                }
            }
            log("error", msg, extra_data)
            validated = False
        # Add the volgnummer to the set for this entity identificatie
        volgnummers[identificatie].add(volgnummer)

    return validated
