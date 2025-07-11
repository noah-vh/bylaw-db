-- Setup Admin User and Roles in Supabase
-- Run this in your Supabase SQL Editor after creating your user account

-- First, add a custom claim to store user roles in the auth.users table
-- This adds a 'role' field to the user metadata

-- Update your user to have admin role (replace YOUR_USER_ID with your actual user ID)
-- You can find your user ID in the Supabase dashboard under Authentication > Users

-- Step 1: Create a function to set user role
CREATE OR REPLACE FUNCTION set_user_role(user_id UUID, role TEXT)
RETURNS void AS $$
BEGIN
  UPDATE auth.users 
  SET raw_user_meta_data = 
    CASE 
      WHEN raw_user_meta_data IS NULL THEN jsonb_build_object('role', role)
      ELSE raw_user_meta_data || jsonb_build_object('role', role)
    END
  WHERE id = user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Step 2: Create a function to get user role
CREATE OR REPLACE FUNCTION auth.user_role()
RETURNS TEXT AS $$
BEGIN
    RETURN COALESCE(
        current_setting('request.jwt.claims', true)::json->>'role',
        (SELECT raw_user_meta_data->>'role' FROM auth.users WHERE id = auth.uid())
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Step 3: Update RLS policies to use roles
-- Drop existing policies first
DROP POLICY IF EXISTS "Enable read access for all users" ON municipalities;
DROP POLICY IF EXISTS "Enable read access for all users" ON bylaws;
DROP POLICY IF EXISTS "Enable read access for all users" ON scraping_configs;
DROP POLICY IF EXISTS "Enable read access for all users" ON scraping_jobs;

-- Create new role-based policies
-- Public read access for municipalities and bylaws
CREATE POLICY "Public read access" ON municipalities FOR SELECT USING (true);
CREATE POLICY "Public read access" ON bylaws FOR SELECT USING (true);

-- Admin-only write access
CREATE POLICY "Admin write access" ON municipalities 
    FOR ALL 
    USING (auth.user_role() = 'admin');

CREATE POLICY "Admin write access" ON bylaws 
    FOR ALL 
    USING (auth.user_role() = 'admin');

-- Admin-only access to scraping configs
CREATE POLICY "Admin only access" ON scraping_configs 
    FOR ALL 
    USING (auth.user_role() = 'admin');

CREATE POLICY "Admin only access" ON scraping_jobs 
    FOR ALL 
    USING (auth.user_role() = 'admin');

-- Step 4: Create a view to see users with roles
CREATE OR REPLACE VIEW public.user_profiles AS
SELECT 
    id,
    email,
    raw_user_meta_data->>'role' as role,
    created_at,
    last_sign_in_at
FROM auth.users;

-- Grant access to the view
GRANT SELECT ON public.user_profiles TO authenticated;

-- Step 5: To make yourself an admin, run this query with your email:
-- First, find your user ID
SELECT id, email FROM auth.users WHERE email = 'YOUR_EMAIL@example.com';

-- Then use the ID from above to set admin role
SELECT set_user_role('YOUR_USER_ID_HERE', 'admin');

-- Example (replace with your actual values):
-- SELECT set_user_role('123e4567-e89b-12d3-a456-426614174000', 'admin');

-- Step 6: Verify your role was set
SELECT id, email, raw_user_meta_data->>'role' as role FROM auth.users WHERE email = 'YOUR_EMAIL@example.com';