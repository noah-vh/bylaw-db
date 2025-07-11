-- Simple authentication policies - all authenticated users have full access
-- Run this in your Supabase SQL Editor

-- Drop any existing policies that might conflict
DROP POLICY IF EXISTS "Enable read access for all users" ON municipalities;
DROP POLICY IF EXISTS "Enable read access for all users" ON bylaws;
DROP POLICY IF EXISTS "Enable read access for all users" ON source_documents;
DROP POLICY IF EXISTS "Enable read access for all users" ON bylaw_versions;
DROP POLICY IF EXISTS "Enable read access for all users" ON adu_requirements;
DROP POLICY IF EXISTS "Enable read access for all users" ON scraping_configs;
DROP POLICY IF EXISTS "Enable read access for all users" ON scraping_jobs;
DROP POLICY IF EXISTS "Enable read access for all users" ON audit_log;

DROP POLICY IF EXISTS "Public read access" ON municipalities;
DROP POLICY IF EXISTS "Public read access" ON bylaws;
DROP POLICY IF EXISTS "Admin write access" ON municipalities;
DROP POLICY IF EXISTS "Admin write access" ON bylaws;
DROP POLICY IF EXISTS "Admin only access" ON scraping_configs;
DROP POLICY IF EXISTS "Admin only access" ON scraping_jobs;

-- Create simple policies - authenticated users have full access
CREATE POLICY "Authenticated users have full access" ON municipalities
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users have full access" ON source_documents
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users have full access" ON bylaws
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users have full access" ON bylaw_versions
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users have full access" ON adu_requirements
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users have full access" ON scraping_configs
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users have full access" ON scraping_jobs
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Authenticated users have full access" ON audit_log
    FOR ALL USING (auth.role() = 'authenticated');

-- Optional: Allow public read access to bylaws and municipalities
CREATE POLICY "Public can read municipalities" ON municipalities
    FOR SELECT USING (true);

CREATE POLICY "Public can read bylaws" ON bylaws
    FOR SELECT USING (true);