-- 02_timescale.sql — TimescaleDB extension: hypertable + policies.
-- Only mount this file when running the timescale/timescaledb image
-- (vanilla Postgres dev setups should skip it; the app works on plain PG too).

CREATE EXTENSION IF NOT EXISTS timescaledb;

DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb') THEN
        -- Auto-partition readings by time
        PERFORM create_hypertable('readings', 'time', if_not_exists => TRUE, migrate_data => TRUE);

        -- Compress chunks older than 7 days (~90% smaller on disk)
        ALTER TABLE readings SET (timescaledb.compress);
        PERFORM add_compression_policy('readings', INTERVAL '7 days');

        -- Keep 12 months of raw data (adjust to taste);
        -- the hourly rollup below is kept forever.
        PERFORM add_retention_policy('readings', INTERVAL '12 months');

        -- Hourly continuous aggregate, auto-refreshed
        CREATE MATERIALIZED VIEW IF NOT EXISTS readings_hourly
        WITH (timescaledb.continuous) AS
        SELECT time_bucket(INTERVAL '1 hour', time) AS bucket,
               sum(pulses)                          AS pulses,
               sum(kwh)                             AS kwh,
               avg(average_watts)                   AS avg_watts
        FROM readings
        GROUP BY bucket
        WITH NO DATA;

        PERFORM add_continuous_aggregate_policy('readings_hourly',
            start_offset      => INTERVAL '3 hours',
            end_offset        => INTERVAL '1 hour',
            schedule_interval => INTERVAL '30 minutes');
    END IF;
END $$;
