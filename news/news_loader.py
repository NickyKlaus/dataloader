from pymongo import MongoClient, InsertOne
import logging
from typing import Iterator, Any, Dict
import requests
from os import environ as env, getenv
from datetime import date, timedelta
from dataclasses import asdict
from model.article import Article, Source
from config.config import Config

logger = logging.getLogger("mongo_db")
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter('%(asctime)s [%(name)-12s] %(levelname)-8s %(message)s')
)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)


def get_config() -> Config:
    """
    Loads configuration from environment variables
    """
    if {
        'NEWS_DB_HOST',
        'NEWS_DB_PORT',
        'NEWS_DB_COLLECTION_NAME',
        'NEWS_SOURCE_URL',
        'NEWS_API_KEY'
    }.issubset(env.keys()):
        return Config(
            host=env['NEWS_DB_HOST'],
            port=int(env['NEWS_DB_PORT']),
            collection=env['NEWS_DB_COLLECTION_NAME'],
            source_url=env['NEWS_SOURCE_URL'],
            api_key=env['NEWS_API_KEY'],
            days_ago=int(getenv('NEWS_DAYS_AGO', 1)),
            connect_timeout_ms=int(getenv('NEWS_CONNECT_TIMEOUT_MS', 600000))
        )
    else:
        logger.fatal(f"Configuration initialization fault because no valid configuration found.")
        raise


def get_raw_data(source_url) -> Iterator[Dict[str, Any]]:
    def try_get_data():
        try:
            response = requests.get(source_url)
            logger.info(f"Getting raw data from source [{source_url}]: {response.status_code}")
            if response.status_code == 200:
                for item in response.json()['articles']:
                    if item:
                        yield item
        except requests.HTTPError as http_error:
            logging.error(f"Http error: {http_error}")
            raise
        except Exception as error:
            logging.error(f"Error: {error}")
            raise
    yield from try_get_data()


def articles(raw_data: Iterator[Dict[str, Any]]) -> Iterator[Article]:
    for raw_article in raw_data:
        yield Article(
            Source(raw_article['source']['id'], raw_article['source']['name']),
            raw_article['author'],
            raw_article['title'],
            raw_article['description'],
            raw_article['url'],
            raw_article['urlToImage'],
            raw_article['publishedAt'],
            raw_article['content']
        )


def _days_range(start: date, stop: date, step: int = 1) -> Iterator[date]:
    """
    days_range(stop) -> date object
    days_range(start, stop[, step]) -> date object

    Returns date object generated from the sequence of days. Default sequence iteration step is a day.
    """
    if start == stop:
        raise ValueError(f"days_range() argument <start> must not be equal to argument <stop>")
    if step == 0:
        raise ValueError(f"days_range() argument <step> must not be zero")

    _is_asc = step > 0
    _day = start
    while (_is_asc and _day < stop) or (not _is_asc and _day > stop):
        yield _day
        _day += timedelta(days=step)


def save_news(mongo: MongoClient = None, config: Config = None):
    try:
        news_db = mongo[config.collection]
        today = date.today()
        days_ago = today - timedelta(days=config.days_ago)
        for day in _days_range(today, days_ago, -1):
            raw_articles = get_raw_data(str.format(config.source_url, *(day, day + timedelta(days=-1), config.api_key)))
            bulk_operations = (InsertOne(asdict(article)) for article in articles(raw_articles))
            saved_news = news_db['article'].bulk_write(requests=list(bulk_operations)).inserted_count
            logger.info(f"Bulk insert result: {saved_news}")
        logger.info("Done")
    except Exception as err:
        logger.error(f"DB error: {err}")
        raise


if __name__ == '__main__':
    configuration = get_config()
    logger.info(f"CONF:{configuration}")
    try:
        with MongoClient(
                host=f"mongodb://{configuration.host}",
                port=configuration.port,
                connectTimeoutMS=configuration.connect_timeout_ms
        ) as mongo:
            save_news(mongo=mongo, config=configuration)
    except Exception as e:
        logger.fatal(f"News loader service fault: {e}")
