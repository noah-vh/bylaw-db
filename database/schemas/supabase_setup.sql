-- Supabase Database Setup for Bylaw Database
-- Run this in your Supabase SQL Editor

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Municipalities table
CREATE TABLE municipalities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    province VARCHAR(50) NOT NULL,
    website_url TEXT,
    scraping_enabled BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}',
    UNIQUE(name, province)
);

-- Source documents table (for liability protection)
CREATE TABLE source_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    municipality_id UUID REFERENCES municipalities(id) ON DELETE CASCADE,
    document_url TEXT NOT NULL,
    document_type VARCHAR(50) NOT NULL,
    scraped_at TIMESTAMPTZ NOT NULL,
    scraper_version VARCHAR(20) NOT NULL,
    scraper_ip_address INET,
    raw_html_path TEXT,
    pdf_path TEXT,
    screenshot_path TEXT,
    http_headers JSONB,
    response_code INTEGER,
    content_hash VARCHAR(64),
    file_size_bytes BIGINT,
    preservation_status VARCHAR(50) DEFAULT 'pending',
    preservation_error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bylaws table
CREATE TABLE bylaws (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    municipality_id UUID REFERENCES municipalities(id) ON DELETE CASCADE,
    source_document_id UUID REFERENCES source_documents(id),
    bylaw_number VARCHAR(100),
    title TEXT NOT NULL,
    category VARCHAR(100),
    status VARCHAR(50) DEFAULT 'active',
    effective_date DATE,
    amendment_date DATE,
    repeal_date DATE,
    parent_bylaw_id UUID REFERENCES bylaws(id),
    full_text TEXT,
    summary TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Bylaw versions table
CREATE TABLE bylaw_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bylaw_id UUID REFERENCES bylaws(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    content JSONB NOT NULL,
    extracted_requirements JSONB,
    extracted_at TIMESTAMPTZ NOT NULL,
    extraction_method VARCHAR(100),
    confidence_scores JSONB,
    source_document_id UUID REFERENCES source_documents(id),
    source_location JSONB,
    previous_version_id UUID REFERENCES bylaw_versions(id),
    change_type VARCHAR(50),
    change_summary TEXT,
    change_reason TEXT,
    created_by UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    approved_by UUID,
    approved_at TIMESTAMPTZ,
    is_current BOOLEAN DEFAULT false,
    UNIQUE(bylaw_id, version_number)
);

-- ADU Requirements table
CREATE TABLE adu_requirements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bylaw_version_id UUID REFERENCES bylaw_versions(id) ON DELETE CASCADE,
    max_height_m NUMERIC(5,2),
    max_floor_area_sqm NUMERIC(8,2),
    min_lot_size_sqm NUMERIC(10,2),
    front_setback_m NUMERIC(5,2),
    rear_setback_m NUMERIC(5,2),
    side_setback_m NUMERIC(5,2),
    max_units INTEGER,
    parking_spaces_required INTEGER,
    owner_occupancy_required BOOLEAN,
    other_requirements JSONB,
    extraction_confidence NUMERIC(3,2),
    source_text TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Scraping configurations
CREATE TABLE scraping_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    municipality_id UUID REFERENCES municipalities(id) ON DELETE CASCADE,
    target_urls JSONB NOT NULL,
    selectors JSONB,
    schedule_cron VARCHAR(100),
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    scraper_type VARCHAR(50),
    requires_javascript BOOLEAN DEFAULT false,
    custom_headers JSONB,
    is_active BOOLEAN DEFAULT true,
    failure_count INTEGER DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(municipality_id)
);

-- Scraping jobs table
CREATE TABLE scraping_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    municipality_id UUID REFERENCES municipalities(id) ON DELETE CASCADE,
    config_id UUID REFERENCES scraping_configs(id) ON DELETE SET NULL,
    job_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    documents_found INTEGER DEFAULT 0,
    documents_processed INTEGER DEFAULT 0,
    documents_changed INTEGER DEFAULT 0,
    error_message TEXT,
    error_details JSONB,
    triggered_by UUID,
    celery_task_id VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit log table
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    action VARCHAR(50) NOT NULL,
    table_name VARCHAR(100),
    record_id UUID,
    old_values JSONB,
    new_values JSONB,
    changed_fields TEXT[],
    user_id UUID,
    user_email VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    context JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_source_docs_municipality ON source_documents(municipality_id);
CREATE INDEX idx_source_docs_scraped_at ON source_documents(scraped_at);
CREATE INDEX idx_bylaws_municipality ON bylaws(municipality_id);
CREATE INDEX idx_bylaws_number ON bylaws(bylaw_number);
CREATE INDEX idx_bylaws_category ON bylaws(category);
CREATE INDEX idx_bylaws_status ON bylaws(status);
CREATE INDEX idx_versions_bylaw ON bylaw_versions(bylaw_id);
CREATE INDEX idx_versions_current ON bylaw_versions(bylaw_id, is_current);
CREATE INDEX idx_adu_req_version ON adu_requirements(bylaw_version_id);
CREATE INDEX idx_jobs_municipality ON scraping_jobs(municipality_id);
CREATE INDEX idx_jobs_status ON scraping_jobs(status);
CREATE INDEX idx_jobs_created ON scraping_jobs(created_at DESC);
CREATE INDEX idx_audit_timestamp ON audit_log(timestamp DESC);
CREATE INDEX idx_audit_table_record ON audit_log(table_name, record_id);
CREATE INDEX idx_audit_user ON audit_log(user_id);

-- Create update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update triggers
CREATE TRIGGER update_municipalities_updated_at BEFORE UPDATE ON municipalities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bylaws_updated_at BEFORE UPDATE ON bylaws
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_scraping_configs_updated_at BEFORE UPDATE ON scraping_configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert some sample data
INSERT INTO municipalities (name, province, website_url) VALUES
('Toronto', 'Ontario', 'https://www.toronto.ca'),
('Vancouver', 'British Columbia', 'https://vancouver.ca'),
('Montreal', 'Quebec', 'https://ville.montreal.qc.ca');

-- Enable RLS (Row Level Security)
ALTER TABLE municipalities ENABLE ROW LEVEL SECURITY;
ALTER TABLE source_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE bylaws ENABLE ROW LEVEL SECURITY;
ALTER TABLE bylaw_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE adu_requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraping_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraping_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- Create basic policies (allow all for now, can be restricted later)
CREATE POLICY "Enable read access for all users" ON municipalities FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON source_documents FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON bylaws FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON bylaw_versions FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON adu_requirements FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON scraping_configs FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON scraping_jobs FOR SELECT USING (true);
CREATE POLICY "Enable read access for all users" ON audit_log FOR SELECT USING (true);

-- Create storage buckets
INSERT INTO storage.buckets (id, name, public) VALUES 
('source-documents', 'source-documents', false),
('screenshots', 'screenshots', false);

-- Create storage policies
CREATE POLICY "Enable read access for all users" ON storage.objects FOR SELECT USING (true);
CREATE POLICY "Enable insert access for authenticated users" ON storage.objects FOR INSERT WITH CHECK (auth.role() = 'authenticated');