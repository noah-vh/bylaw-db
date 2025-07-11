-- Enable RLS on all tables
ALTER TABLE municipalities ENABLE ROW LEVEL SECURITY;
ALTER TABLE source_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE bylaws ENABLE ROW LEVEL SECURITY;
ALTER TABLE bylaw_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE adu_requirements ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraping_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE scraping_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_log ENABLE ROW LEVEL SECURITY;

-- Create roles
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'viewer') THEN
        CREATE ROLE viewer;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'editor') THEN
        CREATE ROLE editor;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'admin') THEN
        CREATE ROLE admin;
    END IF;
END
$$;

-- Function to check user role
CREATE OR REPLACE FUNCTION auth.user_role()
RETURNS TEXT AS $$
BEGIN
    RETURN current_setting('request.jwt.claims', true)::json->>'role';
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Municipalities policies
CREATE POLICY "Municipalities viewable by all authenticated users" ON municipalities
    FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Municipalities editable by editors and admins" ON municipalities
    FOR ALL
    USING (auth.user_role() IN ('editor', 'admin'));

-- Source documents policies
CREATE POLICY "Source documents viewable by all authenticated users" ON source_documents
    FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Source documents insertable by system" ON source_documents
    FOR INSERT
    WITH CHECK (auth.user_role() IN ('editor', 'admin', 'service_role'));

-- Bylaws policies
CREATE POLICY "Bylaws viewable by all authenticated users" ON bylaws
    FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Bylaws editable by editors and admins" ON bylaws
    FOR ALL
    USING (auth.user_role() IN ('editor', 'admin'));

-- Bylaw versions policies (immutable after creation)
CREATE POLICY "Bylaw versions viewable by all authenticated users" ON bylaw_versions
    FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "Bylaw versions insertable by editors and admins" ON bylaw_versions
    FOR INSERT
    WITH CHECK (auth.user_role() IN ('editor', 'admin'));

-- No update or delete policies for bylaw_versions (immutable)

-- ADU requirements policies
CREATE POLICY "ADU requirements viewable by all authenticated users" ON adu_requirements
    FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY "ADU requirements editable by editors and admins" ON adu_requirements
    FOR ALL
    USING (auth.user_role() IN ('editor', 'admin'));

-- Scraping configs policies (admin only)
CREATE POLICY "Scraping configs viewable by admins" ON scraping_configs
    FOR SELECT
    USING (auth.user_role() = 'admin');

CREATE POLICY "Scraping configs editable by admins" ON scraping_configs
    FOR ALL
    USING (auth.user_role() = 'admin');

-- Scraping jobs policies
CREATE POLICY "Scraping jobs viewable by editors and admins" ON scraping_jobs
    FOR SELECT
    USING (auth.user_role() IN ('editor', 'admin'));

CREATE POLICY "Scraping jobs manageable by admins" ON scraping_jobs
    FOR ALL
    USING (auth.user_role() = 'admin');

-- Audit log policies (view only for all, no modifications allowed)
CREATE POLICY "Audit log viewable by authenticated users" ON audit_log
    FOR SELECT
    USING (auth.role() = 'authenticated');

-- Public access policies for specific use cases
CREATE POLICY "Public bylaw search" ON bylaws
    FOR SELECT
    USING (
        status = 'active' 
        AND auth.role() = 'anon'
        AND current_setting('request.headers', true)::json->>'apikey' IS NOT NULL
    );

-- Function to assign user roles
CREATE OR REPLACE FUNCTION auth.assign_user_role(user_id UUID, new_role TEXT)
RETURNS VOID AS $$
BEGIN
    UPDATE auth.users 
    SET raw_user_meta_data = raw_user_meta_data || jsonb_build_object('role', new_role)
    WHERE id = user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Indexes for performance
CREATE INDEX idx_bylaws_search ON bylaws USING gin(to_tsvector('english', full_text));
CREATE INDEX idx_bylaws_title_search ON bylaws USING gin(to_tsvector('english', title));
CREATE INDEX idx_source_docs_hash ON source_documents(content_hash);
CREATE INDEX idx_audit_context ON audit_log USING gin(context);