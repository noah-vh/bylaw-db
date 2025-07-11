-- Simple version to make you an admin without creating functions in auth schema

-- Step 1: Update your user metadata directly
UPDATE auth.users 
SET raw_user_meta_data = 
  CASE 
    WHEN raw_user_meta_data IS NULL THEN '{"role": "admin"}'::jsonb
    ELSE raw_user_meta_data || '{"role": "admin"}'::jsonb
  END
WHERE id = '041a2635-d615-4579-9b1f-a7dd49cc2a66';

-- Step 2: Verify it worked
SELECT id, email, raw_user_meta_data->>'role' as role 
FROM auth.users 
WHERE id = '041a2635-d615-4579-9b1f-a7dd49cc2a66';