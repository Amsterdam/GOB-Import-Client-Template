from datetime import datetime
import requests

from gobcore.logging.logger import logger

from shapely.geometry import shape
from shapely.wkt import loads


CBS_BUURTEN_API = 'https://geodata.nationaalgeoregister.nl/wijkenbuurten2018/wfs' \
                 '?SERVICE=WFS&VERSION=1.0.0&REQUEST=GetFeature&TYPENAME=wijkenbuurten2018:cbs_buurten_2018' \
                 '&SRSNAME=EPSG:28992&outputFormat=application/json' \
                 '&FILTER=<ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">' \
                 '<ogc:PropertyIsEqualTo><ogc:PropertyName>gemeentenaam</ogc:PropertyName>'\
                 '<ogc:Literal>Amsterdam</ogc:Literal></ogc:PropertyIsEqualTo></ogc:Filter>'


CBS_WIJKEN_API = 'https://geodata.nationaalgeoregister.nl/wijkenbuurten2018/wfs' \
                 '?SERVICE=WFS&VERSION=1.0.0&REQUEST=GetFeature&TYPENAME=wijkenbuurten2018:cbs_wijken_2018' \
                 '&SRSNAME=EPSG:28992&outputFormat=application/json' \
                 '&FILTER=<ogc:Filter xmlns:ogc="http://www.opengis.net/ogc">' \
                 '<ogc:PropertyIsEqualTo><ogc:PropertyName>gemeentenaam</ogc:PropertyName>'\
                 '<ogc:Literal>Amsterdam</ogc:Literal></ogc:PropertyIsEqualTo></ogc:Filter>'


def _enrich_buurten(entities):
    # Add the CBS Code
    entities = _add_cbs_code(entities, CBS_BUURTEN_API, 'buurt')

    return entities


def _enrich_wijken(entities):
    # Add the CBS Code
    entities = _add_cbs_code(entities, CBS_WIJKEN_API, 'wijk')
    return entities


def _volgnummer_from_date(date_str, date_format):
    """Generate a volgnummer from a date

    :param date_str: date string to derive volgnummer from
    :param date_format: format of date string
    :return: a volgnummer that is higher for recent dates and lower for oldest dates
    """
    return int(datetime.strptime(date_str, date_format).timestamp())


def enrich_ggw_ggp_gebieden(entities, prefix):
    """Enrich GGW or GGP Gebieden

    Add:
    - Missing identificatie
    - Set registratiedatum to the date of the file
    - Set volgnummer to a number that corresponds to the registratiedatum
    - Interpret BUURTEN as a comma separated list of codes
    - Convert Excel DateTime values to date strings in YYYY-MM-DD format

    :param entities: a list of entities
    :param prefix: GGW or GGP
    :return: None
    """
    for entity in entities:
        entity["BUURTEN"] = entity["BUURTEN"].split(", ")
        entity["_IDENTIFICATIE"] = None
        entity["registratiedatum"] = entity["_file_info"]["last_modified"]
        entity["volgnummer"] = _volgnummer_from_date(entity["registratiedatum"], "%Y-%m-%dT%H:%M:%S.%f")
        for date in [f"{prefix}_{date}" for date in ["BEGINDATUM", "EINDDATUM", "DOCUMENTDATUM"]]:
            if entity[date] is not None:
                entity[date] = str(entity[date])[:10]   # len "YYYY-MM-DD" = 10


def enrich_ggwgebieden(entities):
    """Enrich GGW Gebieden

    Add:
    - Missing identificatie
    - Interpret BUURTEN as a comma separated list of buurt codes
    - Convert Excel DateTime values to dates

    :param entities: a list of entities
    :return: None
    """
    enrich_ggw_ggp_gebieden(entities, "GGW")


def enrich_ggpgebieden(entities):
    """Enrich GGP Gebieden

    Add:
    - Missing identificatie
    - Interpret BUURTEN as a comma separated list of buurt codes
    - Convert Excel DateTime values to dates

    :param entities: a list of entities
    :return: None
    """
    enrich_ggw_ggp_gebieden(entities, "GGP")


def _add_cbs_code(entities, url, type):
    """
    Gets the CBS codes and tries to match them based on the inside
    point of the geometry. Returns the entities enriched with CBS Code.

    :param entities: a list of entities ready for enrichment
    :param url: the url to the cbs code API
    :param type: the type of entity, needed to get the correct values from the API
    :return: the entities enriched with CBS Code
    """
    features = _get_cbs_features(url, type)

    for entity in entities:
        # Leave entities without datum_einde_geldigheid empty
        if entity['datum_einde_geldigheid']:
            entity['cbs_code'] = ''
            continue

        # Check which CBS feature lays within the geometry
        match = _match_cbs_features(entity, features)

        entity['cbs_code'] = match['code'] if match else ''

        # Show a warning if the names do not match with CBS
        if match and entity['naam'] != match['naam']:
            msg = "Naam and CBS naam don't match"
            extra_data = {
                'id': msg,
                'data': {
                    'identificatie': entity['identificatie'],
                    'naam': entity['naam'],
                    'cbs_naam': match['naam'],
                }
            }
            logger.warning(msg, extra_data)

    return entities


def _match_cbs_features(entity, features):
    """
    Match the geometry of an entity to the CBS inside point

    :param entity: the entity to match to
    :param features: the cbs features
    :return: the matched cbs feature or none
    """
    geom = loads(entity['geometrie'])
    match = None

    for feature in features:
        if geom.contains(feature['geometrie']) and not match:
            match = feature
        elif geom.contains(feature['geometrie']) and match:
            msg = "Entity already had a match"
            extra_data = {
                'data': {
                    'id': msg,
                    'naam': entity['naam'],
                    'match': match['naam'],
                    'cbs_naam': feature['naam'],
                }
            }
            logger.warning(msg, extra_data)

    return match


def _get_cbs_features(url, type):
    """
    Gets the CBS codes from the API and returns a list of dicts with the naam,
    code and geometrie of the feature (wijk or buurt)

    :param url: the url to the cbs code API
    :param type: the type of entity, needed to get the correct values from the API
    :return: a list of dicts with CBS Code, CBS naam and geometry
    """
    response = requests.get(url)
    assert response.ok
    cbs_result = response.json()

    features = []
    for feature in cbs_result['features']:
        # Skip features if they exist only of water
        if feature['properties']['water'] == 'JA':
            continue

        # Include the naam, code and representative point of the feature
        cleaned_feature = {
            'geometrie': shape(feature['geometry']).representative_point(),
            'code': feature['properties'][f'{type}code'],
            'naam': feature['properties'][f'{type}naam'],
        }
        features.append(cleaned_feature)
    return features
