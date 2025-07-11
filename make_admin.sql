-- Make user 041a2635-d615-4579-9b1f-a7dd49cc2a66 an admin

-- Step 1: Create the function to set user role
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

-- Step 2: Make YOU an admin
SELECT set_user_role('041a2635-d615-4579-9b1f-a7dd49cc2a66', 'admin');

-- Step 3: Verify it worked
SELECT id, email, raw_user_meta_data->>'role' as role 
FROM auth.users 
WHERE id = '041a2635-d615-4579-9b1f-a7dd49cc2a66';

-- Step 4: Create the function to get user role (needed for policies)
CREATE OR REPLACE FUNCTION auth.user_role()
RETURNS TEXT AS $$
BEGIN
    RETURN COALESCE(
        current_setting('request.jwt.claims', true)::json->>'role',
        (SELECT raw_user_meta_data->>'role' FROM auth.users WHERE id = auth.uid())
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;