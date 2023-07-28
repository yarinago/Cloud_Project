-- init.sql

CREATE TABLE IF NOT EXISTS candidates (
    id BIGSERIAL PRIMARY KEY CHECK (id > 0),
    first_name VARCHAR(256) NOT NULL,
    last_name VARCHAR(256) NOT NULL,
    email VARCHAR(256) NOT NULL,
    job_id BIGINT CHECK (job_id > 0)
);