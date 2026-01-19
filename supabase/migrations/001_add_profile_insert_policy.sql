-- Migration: Add INSERT policy for profiles table
-- This allows users to create their own profile if one doesn't exist
-- (handles cases where the trigger didn't fire or user was created before trigger existed)

-- Add INSERT policy for profiles (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE tablename = 'profiles' 
        AND policyname = 'Users can insert own profile'
    ) THEN
        CREATE POLICY "Users can insert own profile" ON profiles
            FOR INSERT WITH CHECK (auth.uid() = id);
    END IF;
END
$$;
