-- Initialize DataRack News database
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables for data center tracking
CREATE TABLE IF NOT EXISTS data_centers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) UNIQUE,
    city VARCHAR(100),
    country VARCHAR(100),
    region VARCHAR(100),
    address TEXT,
    electrical_redundancy VARCHAR(50),
    cooling_redundancy VARCHAR(50),
    certifications JSONB,
    amenities JSONB,
    specifications JSONB,
    ibx_highlights TEXT,
    source_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for common searches
CREATE INDEX IF NOT EXISTS idx_data_centers_city ON data_centers(city);
CREATE INDEX IF NOT EXISTS idx_data_centers_country ON data_centers(country);
CREATE INDEX IF NOT EXISTS idx_data_centers_code ON data_centers(code);

-- Create search logs table
CREATE TABLE IF NOT EXISTS search_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query VARCHAR(255),
    results_count INTEGER,
    search_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create facilities tracking table
CREATE TABLE IF NOT EXISTS facility_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    facility_code VARCHAR(50),
    analysis_data JSONB,
    sustainability_score DECIMAL(3,2),
    connectivity_score DECIMAL(3,2),
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);