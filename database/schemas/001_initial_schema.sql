-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For text search

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
    document_type VARCHAR(50) NOT NULL, -- 'webpage', 'pdf', 'doc', etc.
    scraped_at TIMESTAMPTZ NOT NULL,
    scraper_version VARCHAR(20) NOT NULL,
    scraper_ip_address INET,
    
    -- Storage paths
    raw_html_path TEXT,
    pdf_path TEXT,
    screenshot_path TEXT,
    
    -- Metadata
    http_headers JSONB,
    response_code INTEGER,
    content_hash VARCHAR(64), -- SHA256 hash
    file_size_bytes BIGINT,
    
    -- Preservation metadata
    preservation_status VARCHAR(50) DEFAULT 'pending', -- pending, preserved, failed
    preservation_error TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    INDEX idx_source_docs_municipality (municipality_id),
    INDEX idx_source_docs_scraped_at (scraped_at)
);

-- Bylaws table
CREATE TABLE bylaws (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    municipality_id UUID REFERENCES municipalities(id) ON DELETE CASCADE,
    source_document_id UUID REFERENCES source_documents(id),
    
    bylaw_number VARCHAR(100),
    title TEXT NOT NULL,
    category VARCHAR(100), -- 'zoning', 'adu', 'building_code', etc.
    status VARCHAR(50) DEFAULT 'active', -- active, repealed, amended
    
    effective_date DATE,
    amendment_date DATE,
    repeal_date DATE,
    
    -- For tracking amendments
    parent_bylaw_id UUID REFERENCES bylaws(id),
    
    -- Searchable content
    full_text TEXT,
    summary TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    INDEX idx_bylaws_municipality (municipality_id),
    INDEX idx_bylaws_number (bylaw_number),
    INDEX idx_bylaws_category (category),
    INDEX idx_bylaws_status (status)
);

-- Bylaw versions table (track all changes)
CREATE TABLE bylaw_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bylaw_id UUID REFERENCES bylaws(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    
    -- Content and extracted data
    content JSONB NOT NULL,
    extracted_requirements JSONB,
    
    -- Extraction metadata
    extracted_at TIMESTAMPTZ NOT NULL,
    extraction_method VARCHAR(100), -- 'automated', 'manual', 'hybrid'
    confidence_scores JSONB, -- Confidence for each extracted field
    
    -- Source tracking
    source_document_id UUID REFERENCES source_documents(id),
    source_location JSONB, -- page number, coordinates, etc.
    
    -- Change tracking
    previous_version_id UUID REFERENCES bylaw_versions(id),
    change_type VARCHAR(50), -- 'amendment', 'correction', 'clarification'
    change_summary TEXT,
    change_reason TEXT,
    
    -- Approval workflow
    created_by UUID, -- References Supabase auth.users
    created_at TIMESTAMPTZ DEFAULT NOW(),
    approved_by UUID, -- References Supabase auth.users
    approved_at TIMESTAMPTZ,
    
    -- Make versions immutable
    is_current BOOLEAN DEFAULT false,
    
    INDEX idx_versions_bylaw (bylaw_id),
    INDEX idx_versions_current (bylaw_id, is_current),
    UNIQUE(bylaw_id, version_number)
);

-- ADU Requirements table (standardized extraction)
CREATE TABLE adu_requirements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    bylaw_version_id UUID REFERENCES bylaw_versions(id) ON DELETE CASCADE,
    
    -- Standardized requirements
    max_height_m NUMERIC(5,2),
    max_floor_area_sqm NUMERIC(8,2),
    min_lot_size_sqm NUMERIC(10,2),
    
    -- Setbacks
    front_setback_m NUMERIC(5,2),
    rear_setback_m NUMERIC(5,2),
    side_setback_m NUMERIC(5,2),
    
    -- Other requirements
    max_units INTEGER,
    parking_spaces_required INTEGER,
    owner_occupancy_required BOOLEAN,
    
    -- Raw requirements (for non-standard items)
    other_requirements JSONB,
    
    -- Confidence and source
    extraction_confidence NUMERIC(3,2), -- 0.00 to 1.00
    source_text TEXT, -- Original text this was extracted from
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    INDEX idx_adu_req_version (bylaw_version_id)
);

-- Scraping configurations
CREATE TABLE scraping_configs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    municipality_id UUID REFERENCES municipalities(id) ON DELETE CASCADE,
    
    -- URLs and selectors
    target_urls JSONB NOT NULL, -- Array of URLs to scrape
    selectors JSONB, -- CSS/XPath selectors for different elements
    
    -- Schedule
    schedule_cron VARCHAR(100), -- Cron expression
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    
    -- Configuration
    scraper_type VARCHAR(50), -- 'static', 'dynamic', 'api'
    requires_javascript BOOLEAN DEFAULT false,
    custom_headers JSONB,
    
    -- Status
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
    
    -- Job details
    job_type VARCHAR(50) NOT NULL, -- 'scheduled', 'manual', 'update'
    status VARCHAR(50) NOT NULL, -- 'pending', 'running', 'completed', 'failed'
    
    -- Timing
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    
    -- Results
    documents_found INTEGER DEFAULT 0,
    documents_processed INTEGER DEFAULT 0,
    documents_changed INTEGER DEFAULT 0,
    
    -- Errors
    error_message TEXT,
    error_details JSONB,
    
    -- Metadata
    triggered_by UUID, -- References auth.users
    celery_task_id VARCHAR(255),
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    INDEX idx_jobs_municipality (municipality_id),
    INDEX idx_jobs_status (status),
    INDEX idx_jobs_created (created_at DESC)
);

-- Comprehensive audit log
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- What happened
    action VARCHAR(50) NOT NULL, -- 'INSERT', 'UPDATE', 'DELETE', 'SCRAPE', etc.
    table_name VARCHAR(100),
    record_id UUID,
    
    -- Changes
    old_values JSONB,
    new_values JSONB,
    changed_fields TEXT[],
    
    -- Who and when
    user_id UUID, -- References auth.users
    user_email VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    
    -- Additional context
    context JSONB, -- Any additional context
    
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    
    INDEX idx_audit_timestamp (timestamp DESC),
    INDEX idx_audit_table_record (table_name, record_id),
    INDEX idx_audit_user (user_id)
);

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

-- Audit trigger function
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
DECLARE
    audit_user_id UUID;
    audit_user_email VARCHAR(255);
BEGIN
    -- Get user info from Supabase auth context
    audit_user_id := auth.uid();
    audit_user_email := current_setting('request.jwt.claims', true)::json->>'email';
    
    IF (TG_OP = 'DELETE') THEN
        INSERT INTO audit_log (
            action, table_name, record_id,
            old_values, user_id, user_email
        ) VALUES (
            TG_OP, TG_TABLE_NAME, OLD.id,
            row_to_json(OLD), audit_user_id, audit_user_email
        );
        RETURN OLD;
    ELSIF (TG_OP = 'UPDATE') THEN
        INSERT INTO audit_log (
            action, table_name, record_id,
            old_values, new_values, user_id, user_email
        ) VALUES (
            TG_OP, TG_TABLE_NAME, NEW.id,
            row_to_json(OLD), row_to_json(NEW), audit_user_id, audit_user_email
        );
        RETURN NEW;
    ELSIF (TG_OP = 'INSERT') THEN
        INSERT INTO audit_log (
            action, table_name, record_id,
            new_values, user_id, user_email
        ) VALUES (
            TG_OP, TG_TABLE_NAME, NEW.id,
            row_to_json(NEW), audit_user_id, audit_user_email
        );
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ language 'plpgsql';

-- Apply audit triggers to key tables
CREATE TRIGGER audit_municipalities AFTER INSERT OR UPDATE OR DELETE ON municipalities
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_bylaws AFTER INSERT OR UPDATE OR DELETE ON bylaws
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_bylaw_versions AFTER INSERT OR UPDATE OR DELETE ON bylaw_versions
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();

CREATE TRIGGER audit_adu_requirements AFTER INSERT OR UPDATE OR DELETE ON adu_requirements
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();