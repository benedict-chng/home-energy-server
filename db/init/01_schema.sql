-- 01_schema.sql — base schema, exactly as specified (2026-10-12):
--   time (timestamptz), pulses (integer), kwh (double), average_watts (double)
-- All fields mandatory. time is the PK -> bridge retries are idempotent.

CREATE TABLE IF NOT EXISTS readings (
    time          TIMESTAMP WITH TIME ZONE NOT NULL,
    pulses        INTEGER NOT NULL CHECK (pulses >= 0),
    kwh           DOUBLE PRECISION NOT NULL CHECK (kwh >= 0),
    average_watts DOUBLE PRECISION NOT NULL CHECK (average_watts >= 0),
    CONSTRAINT readings_pkey PRIMARY KEY (time)
);

-- Solar (Fronius) readings — two fields only (Ben, 18:28), all mandatory,
-- time is the PK -> idempotent retries.

CREATE TABLE IF NOT EXISTS solar_readings (
    time          TIMESTAMP WITH TIME ZONE NOT NULL,
    average_watts DOUBLE PRECISION NOT NULL CHECK (average_watts >= 0),
    CONSTRAINT solar_readings_pkey PRIMARY KEY (time)
);
