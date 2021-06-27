from dataclasses import dataclass


@dataclass
class Config:
    host: str
    port: int
    keyspace: str
    source_url: str
    waiting_for_connect: int = 600  # default waiting period is 600 seconds
    replication_factor: int = 1  # default replication factor is 1
