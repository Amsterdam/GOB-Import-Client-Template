""" Validator

Basic validation logic

The first version implements only the most basic validation logic
In order to prepare a more generic validation approach the validation has been set up by means of regular expressions.

"""
import re

from gobcore.exceptions import GOBException
from gobcore.model import GOBModel
from gobcore.model.metadata import FIELD
from gobcore.logging.logger import logger

from gobcore.quality.issue import QA_CHECK, QA_LEVEL, Issue, log_issue


# Log message formats
MISSING_ATTR_FMT = "{attr} missing in entity: {entity}"
QA_CHECK_FAILURE_FMT = "{msg}. Value was: {value}"


ENTITY_CHECKS = {
    "test_entity": {},
    "meetbouten": {
        "identificatie": [
            {
                **QA_CHECK.Format_N8,
                "level": QA_LEVEL.FATAL,
            },
        ],
        "status_id": [
            {
                **QA_CHECK.Value_1_2_3,
                "level": QA_LEVEL.WARNING,
            },
        ],
        "windrichting": [
            {
                **QA_CHECK.Value_wind_direction_NOZW,
                "allow_null": True,
                "level": QA_LEVEL.WARNING,
            }
        ],
        "publiceerbaar": [
            {
                **QA_CHECK.Value_1_0,
                "allow_null": True,
                "level": QA_LEVEL.WARNING,
            },
        ],
    },
    "metingen": {
        "identificatie": [
            {
                **QA_CHECK.Format_numeric,
                "level": QA_LEVEL.FATAL,
            },
        ],
        "hoort_bij_meetbout": [
            {
                **QA_CHECK.Format_N8,
                "level": QA_LEVEL.FATAL,
            },
        ],
        "publiceerbaar": [
            {
                **QA_CHECK.Value_1_0,
                "allow_null": True,
                "level": QA_LEVEL.WARNING,
            },
        ],
    },
    "referentiepunten": {
        "publiceerbaar": [
            {
                **QA_CHECK.Value_J_N,
                "allow_null": True,
                "level": QA_LEVEL.FATAL,
            },
        ],
    },
    "rollagen": {
        "name": [
            {
                **QA_CHECK.Format_AAN_AANN,
                "level": QA_LEVEL.FATAL,
            },
        ],
    },
    "peilmerken": {
        "identificatie": [
            {
                **QA_CHECK.Format_N8,
                "level": QA_LEVEL.FATAL,
            },
        ],
        "hoogte_tov_nap": [
            {
                **QA_CHECK.Value_height_6_15,
                "level": QA_LEVEL.WARNING,
            },
        ],
        "geometrie": [
            {
                **QA_CHECK.Value_geometry_in_NL,
                "level": QA_LEVEL.FATAL,
            },
        ],
        "publiceerbaar": [
            {
                **QA_CHECK.Value_J_N,
                "allow_null": True,
                "level": QA_LEVEL.FATAL,
            },
        ]
    },
    "bouwblokken": {
        "source_id": [
            {
                "source_app": "DGDialog",
                **QA_CHECK.Format_4_2_2_2_6_HEX,
                "level": QA_LEVEL.WARNING
            }
        ],
        "code": [
            {
                **QA_CHECK.Format_AANN,
                "level": QA_LEVEL.FATAL
            }
        ],
    },
    "buurten": {
        "geometrie": [
            {
                **QA_CHECK.Value_geometry_in_NL,
                "level": QA_LEVEL.FATAL,
            },
        ],
        "naam": [
            {
                **QA_CHECK.Value_not_empty,
                "level": QA_LEVEL.WARNING
            }
        ],
    },
    "wijken": {
        "code": [
            {
                **QA_CHECK.Format_ANN,
                "level": QA_LEVEL.FATAL
            }
        ],
        "documentnummer": [
            {
                **QA_CHECK.Value_not_empty,
                "level": QA_LEVEL.WARNING,
            },
        ],
    },
    "ggpgebieden": {
        "GGP_NAAM": [
            {
                **QA_CHECK.Format_alfabetic,
                "level": QA_LEVEL.WARNING,
            },
        ],
    },
    "ggwgebieden": {
        "GGW_NAAM": [
            {
                **QA_CHECK.Format_alfabetic,
                "level": QA_LEVEL.WARNING,
            },
        ],
    },
    "stadsdelen": {
        "naam": [
            {
                **QA_CHECK.Format_alfabetic,
                "level": QA_LEVEL.WARNING,
            },
        ],
    }
}


class Validator:

    def __init__(self, source_app, entity_name, source_id, input_spec):
        self.source_app = source_app
        self.entity_name = entity_name
        self.source_id = source_id
        self.input_spec = input_spec

        checks = ENTITY_CHECKS.get(entity_name, {})
        self.collection_qa = {f"num_invalid_{attr}": 0 for attr in checks.keys()}
        self.fatal = False

        self.primary_keys = set()
        self.duplicates = set()

    def result(self):
        if self.fatal:
            raise GOBException(
                f"Quality assurance failed for {self.entity_name}"
            )

        if self.duplicates:
            raise GOBException(f"Duplicate primary key(s) found in source: "
                               f"[{', '.join([str(dup) for dup in self.duplicates])}]")

        logger.info("Quality assurance passed")

    def validate(self, entity):
        """
        Validate a single entity

        :param self:
        :return:
        """
        # Validate uniqueness of primary key
        self._validate_primary_key(entity)

        # Run quality checks on the collection and individual entities
        self._validate_quality(entity)

    def _validate_primary_key(self, entity):
        """
        Validate a primary key, this should be unique for source_id + seqnr if the collection has states

        :param entity:
        :return:
        """

        entity_has_states = GOBModel().has_states(self.input_spec['catalogue'], self.input_spec['entity'])

        if entity_has_states:
            # Volgnummer could be a different field in the source entity than FIELD.SEQNR
            try:
                seqnr_field = self.input_spec['gob_mapping'][FIELD.SEQNR]['source_mapping']
            except KeyError:
                seqnr_field = FIELD.SEQNR

        id = f"{entity[self.source_id]}.{entity[seqnr_field]}" if entity_has_states else entity[self.source_id]
        if id is not None:
            # Only add ids that are not None, None id's can occur for imports of collections without ids
            if id not in self.primary_keys:
                self.primary_keys.add(id)
            else:
                self.duplicates.add(id)

    def _validate_entity(self, entity):
        """
        Validate a single entity.

        Fails on any fatal validation check
        Warns on any warning validation check
        All info validation checks are counted

        :param entity_name: the entity name
        :param entity: a single entity
        :return: Result of the qa checks
        """
        qa_checks = ENTITY_CHECKS.get(self.entity_name, {})

        invalid_attrs = set()

        for attr, entity_checks in qa_checks.items():
            for check in entity_checks:
                if check.get("source_app", self.source_app) != self.source_app:
                    # Checks can be made app specific by setting the source_app attribute
                    continue
                # Check if the attribute is available
                if not self._attr_check(check, attr, entity):
                    # Add the attribute to the set of non-valid attributes for count
                    invalid_attrs.add(attr)
                    continue

                if not self._qa_check(check, attr, entity):
                    # Add the attribute to the set of non-valid attributes for count
                    invalid_attrs.add(attr)

        return invalid_attrs

    def _attr_check(self, check, attr, entity):
        level = check["level"]
        # Check if attr is available in entity
        if attr not in entity:
            # If a fatal check has failed, mark the validation as fatal
            if level == QA_LEVEL.FATAL:
                self.fatal = True

            log_issue(logger, level, Issue(QA_CHECK.Attribute_exists, entity, self.source_id, attr))
            return False

        return True

    # TODO: fix too complex
    def _qa_check(self, check, attr, entity):   # noqa: C901
        level = check["level"]
        value = entity[attr]
        if 'pattern' in check:
            is_correct = self._regex_check(check, value)
        elif 'between' in check:
            is_correct = self._between_check(check['between'], value)
        elif 'geometry' in check:
            is_correct = self._geometry_check(check['geometry'], value)

        # If the value doesn't pass the qa check, handle the correct way
        if not is_correct:
            # If a fatal check has failed, mark the validation as fatal
            if level == QA_LEVEL.FATAL:
                self.fatal = True

            log_issue(logger, level, Issue(check, entity, self.source_id, attr))
            return False

        return True

    def _regex_check(self, check, value):
        # Check if Null values are allowed
        allow_null = check.get('allow_null')
        if allow_null and value is None:
            return True
        elif not allow_null and value is None:
            return False
        return re.compile(check['pattern']).match(str(value))

    def _between_check(self, between, value):
        return value >= between[0] and value <= between[1] if value is not None else False

    def _geometry_check(self, between, value):
        coords = re.findall('([0-9]+\.[0-9]+)', value)
        # Loop through all coords and check if they fill within the supplied range
        # Even coords are x values, uneven are y values
        coord_types = ['x', 'y']
        for count, coord in enumerate(coords):
            # Get the coord type
            coord_type = coord_types[count % 2]
            # If the coord is outside of the boundaries, retun false
            if not(between[coord_type]['min'] <= float(coord) <= between[coord_type]['max']):
                return False
        return True

    def _validate_quality(self, entity):
        """
        Validate an entity.

        Fails on any fatal validation check
        Warns on any warning validation check
        All info validation checks are counted

        :param entity_name: the entity name
        :param entity: a single entity
        :param source_id: the column defining the unique identifier
        :return: Result of the qa checks, and a boolean if fatal errors have been found
        """
        # Validate on individual entities
        invalid_attrs = self._validate_entity(entity)
        for attr in invalid_attrs:
            self.collection_qa[f"num_invalid_{attr}"] += 1
