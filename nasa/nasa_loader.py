from cassandra.cqlengine.management import sync_table, create_keyspace_simple
from cassandra.cluster import Cluster
from cassandra.cqlengine.connection import set_default_connection, register_connection
from os import getenv, environ as env
from datetime import datetime
from uuid import uuid4
import logging
from typing import Iterator, Any, Dict
import requests
from config.config import Config
from model.item import Item


logger = logging.getLogger("nasa_data_loader")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('%(asctime)s [%(name)-12s] %(levelname)-8s %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


if getenv('CQLENG_ALLOW_SCHEMA_MANAGEMENT') is None:
    env['CQLENG_ALLOW_SCHEMA_MANAGEMENT'] = '1'


def get_config() -> Config:
    """
    Loads configuration from environment variables
    """
    if {
        'NASA_DB_HOST',
        'NASA_DB_PORT',
        'NASA_DB_KEYSPACE',
        'NASA_SOURCE_URL'
    }.issubset(env.keys()):
        return Config(
            host=env['NASA_DB_HOST'],
            port=int(env['NASA_DB_PORT']),
            keyspace=env['NASA_DB_KEYSPACE'],
            source_url=env['NASA_SOURCE_URL'],
            waiting_for_connect=int(getenv('WAITING_TO_CONNECT_PERIOD_SEC', 600)),
            replication_factor=int(getenv('NASA_DB_REPLICATION_FACTOR', 1))
        )
    else:
        raise Exception("Configuration initialization fault because no valid configuration found.")


def get_raw_data(config: Config) -> Iterator[Dict[str, Any]]:
    def try_get_data():
        try:
            response = requests.get(config.source_url)
            logger.info(f"Getting raw data from source [{config.source_url}]: {response.status_code}")
            if response.status_code == 200:
                for item in response.json()['collection']['items']:
                    if item:
                        yield item
        except requests.HTTPError as http_error:
            logging.error(f"Connection to Nasa raw data fault: {http_error}")
            raise
        except Exception as error:
            logging.error(f"Error: {error}")
            raise
    yield from try_get_data()


def _insert_items(raw_items: Iterator[Dict[str, Any]], config=None) -> None:
    for raw_item in raw_items:
        for data in raw_item['data']:
            Item.with_keyspace(config.keyspace).create(
                id=uuid4(),
                date_created=int(datetime.strptime(data['date_created'], '%Y-%m-%dT%H:%M:%SZ').timestamp()),
                title=data['title'],
                description=data['description'],
                media_type=data['media_type'],
                href=raw_item['href'],
            )
    logger.info("Items inserted")


def connect(hosts, port):
    cluster = Cluster(hosts, port=port)
    session = cluster.connect()
    return session


def sync_schema(config: Config = None):
    try:
        create_keyspace_simple(
            name=config.keyspace,
            replication_factor=config.replication_factor
        )
        sync_table(model=Item, keyspaces=[config.keyspace])
    except Exception as sync_err:
        logger.error(f"DB error: {sync_err}")
        raise


def save_items(config: Config):
    try:
        _insert_items(get_raw_data(config), config=config)
        logger.info("Done")
    except Exception as save_err:
        logger.error(f"Saving items fault: {save_err}")
        raise


if __name__ == '__main__':
    configuration: Config = get_config()
    logger.info(f"CONF:{configuration}")

    _session = None
    import time
    _waiting_connection_period = configuration.waiting_for_connect
    while _waiting_connection_period >= 0:
        try:
            _session = connect(hosts=[configuration.host], port=configuration.port)
            if _session:
                break
        except Exception as conn_err:
            logger.info(f"Connection to db is still not available: {conn_err}")
        time.sleep(10)
        _waiting_connection_period -= 10

    try:
        if _session and _waiting_connection_period >= 0:
            register_connection(name=str(_session), session=_session)
            set_default_connection(str(_session))
            sync_schema(configuration)
            save_items(configuration)
        else:
            logger.fatal(f"DB connection fault. Please check config: {configuration}")
            raise Exception(f"DB connection fault. Please check config: {configuration}")
    except Exception as e:
        logger.fatal(f"Nasa loader service fault: {e}")
