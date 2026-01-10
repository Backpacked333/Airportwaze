-- AirportWaze Database Initialization Script
-- Run this after creating the database to set up TimescaleDB and initial data

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

-- Enable PostGIS for geospatial queries (optional, for future features)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Create hypertables after tables are created by SQLAlchemy
-- Run these separately after first `Base.metadata.create_all()`:

-- Convert telemetry_batches to hypertable (partitioned by uploaded_at)
-- SELECT create_hypertable('telemetry_batches', 'uploaded_at', if_not_exists => TRUE);

-- Convert zone_dwell_events to hypertable (partitioned by enter_time)
-- SELECT create_hypertable('zone_dwell_events', 'enter_time', if_not_exists => TRUE);

-- Convert wait_time_observations to hypertable (partitioned by observed_at)
-- SELECT create_hypertable('wait_time_observations', 'observed_at', if_not_exists => TRUE);

-- Create additional indexes for performance

-- Spatial indexes (if using PostGIS)
-- CREATE INDEX idx_checkpoint_location ON checkpoints USING GIST(ST_SetSRID(ST_MakePoint(lng, lat), 4326));

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_wait_obs_recent ON wait_time_observations(checkpoint_id, observed_at DESC);
CREATE INDEX IF NOT EXISTS idx_telemetry_recent ON telemetry_batches(airport_code, uploaded_at DESC);
CREATE INDEX IF NOT EXISTS idx_flight_upcoming ON flight_schedules(airport_code, departure_time) WHERE departure_time > NOW();

-- Create materialized view for checkpoint statistics (refreshed periodically)
CREATE MATERIALIZED VIEW IF NOT EXISTS checkpoint_stats AS
SELECT
    c.id AS checkpoint_id,
    c.airport_code,
    c.name,
    c.type,
    c.terminal,
    COUNT(o.observation_id) AS total_observations,
    AVG(o.wait_minutes) AS avg_wait_minutes,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY o.wait_minutes) AS median_wait_minutes,
    PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY o.wait_minutes) AS p90_wait_minutes,
    MAX(o.observed_at) AS last_observation_at
FROM checkpoints c
LEFT JOIN wait_time_observations o ON c.id = o.checkpoint_id
WHERE o.observed_at > NOW() - INTERVAL '30 days'
GROUP BY c.id, c.airport_code, c.name, c.type, c.terminal;

-- Create index on materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_checkpoint_stats_id ON checkpoint_stats(checkpoint_id);

-- Function to refresh checkpoint_stats (call this periodically)
CREATE OR REPLACE FUNCTION refresh_checkpoint_stats()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY checkpoint_stats;
END;
$$ LANGUAGE plpgsql;

-- Set up automatic compression for old time-series data (TimescaleDB feature)
-- Compress data older than 7 days
-- SELECT add_compression_policy('telemetry_batches', INTERVAL '7 days');
-- SELECT add_compression_policy('zone_dwell_events', INTERVAL '7 days');
-- SELECT add_compression_policy('wait_time_observations', INTERVAL '7 days');

-- Set up automatic data retention policies
-- Keep telemetry data for 90 days, then drop
-- SELECT add_retention_policy('telemetry_batches', INTERVAL '90 days');

-- Keep wait time observations for 1 year
-- SELECT add_retention_policy('wait_time_observations', INTERVAL '365 days');

-- Comments on tables
COMMENT ON TABLE airports IS 'Airport master data with coordinates and terminals';
COMMENT ON TABLE checkpoints IS 'Security checkpoints, bag check, and passport control locations';
COMMENT ON TABLE telemetry_batches IS 'User telemetry data batches (TimescaleDB hypertable)';
COMMENT ON TABLE zone_dwell_events IS 'Processed zone dwell events from telemetry (TimescaleDB hypertable)';
COMMENT ON TABLE wait_time_observations IS 'Wait time observations from all sources (TimescaleDB hypertable)';
COMMENT ON TABLE checkpoint_distributions IS 'Learned distribution parameters for Bayesian model';
COMMENT ON TABLE flight_schedules IS 'Flight schedules for demand forecasting';
COMMENT ON TABLE trip_events IS 'User-confirmed trip events (1-tap prompts)';

-- Grant permissions (adjust user as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO airportwaze;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO airportwaze;
