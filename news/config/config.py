from dataclasses import dataclass


@dataclass
class Config:
    host: str
    port: int
    collection: str
    source_url: str
    api_key: str
    days_ago: int = 1  # period for publication of news in days, default value is 1 day
    connect_timeout_ms: int = 600000  # connection timeout default value is 10 minutes
