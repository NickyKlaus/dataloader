CREATE KEYSPACE IF NOT EXISTS nasa WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

CREATE TABLE IF NOT EXISTS nasa.item(
    id uuid,
    href text,
    description text,
    title text,
    media_type text,
    date_created timestamp,
    PRIMARY KEY ((id), date_created, title)
) WITH comment = 'NASA data';
