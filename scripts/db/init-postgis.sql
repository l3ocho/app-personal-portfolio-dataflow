-- Initialize PostGIS extension
-- This script runs automatically on first container start

-- Enable PostGIS extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- Verify installation
SELECT PostGIS_Version();
