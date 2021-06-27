from dataclasses import dataclass


@dataclass
class Config:
    host: str
    port: int
    collection: str
    source_url: str
    api_key: str
    connect_timeout_ms: int = 600000  # connection timeout default value is 10 minutes
