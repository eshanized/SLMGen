-- SLMGEN Database Schema
-- Run this in your Supabase SQL Editor

-- ============================================
-- PROFILES TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS profiles (
  id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email TEXT NOT NULL,
  full_name TEXT,
  avatar_url TEXT,
  bio TEXT,
  notifications_enabled BOOLEAN DEFAULT TRUE,
  theme TEXT DEFAULT 'dark',
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Auto-create profile on signup (robust version)
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO profiles (id, email, full_name, avatar_url)
  VALUES (
    NEW.id,
    COALESCE(NEW.email, ''),
    COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.raw_user_meta_data->>'name', ''),
    COALESCE(NEW.raw_user_meta_data->>'avatar_url', NEW.raw_user_meta_data->>'picture', '')
  )
  ON CONFLICT (id) DO UPDATE SET
    email = EXCLUDED.email,
    full_name = COALESCE(EXCLUDED.full_name, profiles.full_name),
    avatar_url = COALESCE(EXCLUDED.avatar_url, profiles.avatar_url),
    updated_at = NOW();
  RETURN NEW;
EXCEPTION WHEN OTHERS THEN
  -- Log but don't fail the signup
  RAISE WARNING 'Failed to create profile for user %: %', NEW.id, SQLERRM;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- ============================================
-- JOBS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  session_id TEXT UNIQUE NOT NULL,
  
  -- Dataset info
  dataset_filename TEXT NOT NULL,
  dataset_path TEXT NOT NULL,
  total_examples INTEGER NOT NULL,
  total_tokens INTEGER NOT NULL,
  quality_score FLOAT NOT NULL,
  
  -- Configuration
  task_type TEXT NOT NULL,
  deployment_target TEXT NOT NULL,
  
  -- Model selection
  selected_model_id TEXT NOT NULL,
  selected_model_name TEXT NOT NULL,
  model_score FLOAT NOT NULL,
  
  -- Training config
  training_config JSONB DEFAULT '{}',
  
  -- Notebook
  notebook_filename TEXT,
  notebook_path TEXT,
  colab_url TEXT,
  
  -- Status
  status TEXT DEFAULT 'created',
  
  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jobs_user_id ON jobs(user_id);
CREATE INDEX IF NOT EXISTS idx_jobs_session_id ON jobs(session_id);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);

-- ============================================
-- DATASETS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS datasets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
  job_id UUID REFERENCES jobs(id) ON DELETE SET NULL,
  
  filename TEXT NOT NULL,
  storage_path TEXT NOT NULL,
  file_size INTEGER NOT NULL,
  
  -- Stats
  total_examples INTEGER,
  total_tokens INTEGER,
  avg_tokens_per_example INTEGER,
  quality_score FLOAT,
  single_turn_pct FLOAT,
  multi_turn_pct FLOAT,
  has_system_prompts BOOLEAN DEFAULT FALSE,
  quality_issues JSONB DEFAULT '[]',
  
  -- Characteristics
  is_multilingual BOOLEAN DEFAULT FALSE,
  looks_like_json BOOLEAN DEFAULT FALSE,
  is_multi_turn BOOLEAN DEFAULT FALSE,
  
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_datasets_user_id ON datasets(user_id);

-- ============================================
-- TRAINING CONFIGS TABLE
-- ============================================
CREATE TABLE IF NOT EXISTS training_configs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id) ON DELETE CASCADE,
  
  name TEXT NOT NULL,
  is_default BOOLEAN DEFAULT FALSE,
  is_system BOOLEAN DEFAULT FALSE,
  
  -- LoRA parameters
  lora_rank INTEGER DEFAULT 16,
  lora_alpha INTEGER DEFAULT 32,
  lora_dropout FLOAT DEFAULT 0.05,
  
  -- Training parameters
  learning_rate FLOAT DEFAULT 2e-4,
  num_epochs INTEGER DEFAULT 3,
  batch_size INTEGER DEFAULT 4,
  gradient_accumulation_steps INTEGER DEFAULT 4,
  warmup_ratio FLOAT DEFAULT 0.03,
  max_seq_length INTEGER DEFAULT 2048,
  
  -- Optimizer
  optimizer TEXT DEFAULT 'adamw_8bit',
  scheduler TEXT DEFAULT 'linear',
  
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Insert system presets
INSERT INTO training_configs (name, is_system, lora_rank, learning_rate, num_epochs) VALUES
  ('Fast', TRUE, 8, 5e-4, 1),
  ('Balanced', TRUE, 16, 2e-4, 3),
  ('Quality', TRUE, 32, 1e-4, 5)
ON CONFLICT DO NOTHING;

-- ============================================
-- ROW LEVEL SECURITY
-- ============================================

-- Enable RLS
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE datasets ENABLE ROW LEVEL SECURITY;
ALTER TABLE training_configs ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can view own profile" ON profiles
  FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can insert own profile" ON profiles
  FOR INSERT WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON profiles
  FOR UPDATE USING (auth.uid() = id);

-- Jobs policies
CREATE POLICY "Users can view own jobs" ON jobs
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own jobs" ON jobs
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own jobs" ON jobs
  FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own jobs" ON jobs
  FOR DELETE USING (auth.uid() = user_id);

-- Datasets policies
CREATE POLICY "Users can view own datasets" ON datasets
  FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own datasets" ON datasets
  FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete own datasets" ON datasets
  FOR DELETE USING (auth.uid() = user_id);

-- Training configs policies
CREATE POLICY "Users can view own and system configs" ON training_configs
  FOR SELECT USING (auth.uid() = user_id OR is_system = TRUE);

CREATE POLICY "Users can insert own configs" ON training_configs
  FOR INSERT WITH CHECK (auth.uid() = user_id AND is_system = FALSE);

CREATE POLICY "Users can update own configs" ON training_configs
  FOR UPDATE USING (auth.uid() = user_id AND is_system = FALSE);

CREATE POLICY "Users can delete own configs" ON training_configs
  FOR DELETE USING (auth.uid() = user_id AND is_system = FALSE);

-- ============================================
-- STORAGE BUCKETS
-- ============================================

-- Create buckets (run in Storage section or via SQL)
INSERT INTO storage.buckets (id, name, public)
VALUES 
  ('datasets', 'datasets', FALSE),
  ('notebooks', 'notebooks', FALSE),
  ('avatars', 'avatars', TRUE)
ON CONFLICT (id) DO NOTHING;

-- Storage policies for datasets
CREATE POLICY "Users can upload own datasets" ON storage.objects
  FOR INSERT WITH CHECK (
    bucket_id = 'datasets' AND
    auth.uid()::text = (storage.foldername(name))[1]
  );

CREATE POLICY "Users can view own datasets" ON storage.objects
  FOR SELECT USING (
    bucket_id = 'datasets' AND
    auth.uid()::text = (storage.foldername(name))[1]
  );

CREATE POLICY "Users can delete own datasets" ON storage.objects
  FOR DELETE USING (
    bucket_id = 'datasets' AND
    auth.uid()::text = (storage.foldername(name))[1]
  );

-- Storage policies for notebooks
CREATE POLICY "Users can upload own notebooks" ON storage.objects
  FOR INSERT WITH CHECK (
    bucket_id = 'notebooks' AND
    auth.uid()::text = (storage.foldername(name))[1]
  );

CREATE POLICY "Users can view own notebooks" ON storage.objects
  FOR SELECT USING (
    bucket_id = 'notebooks' AND
    auth.uid()::text = (storage.foldername(name))[1]
  );

-- Storage policies for avatars
CREATE POLICY "Anyone can view avatars" ON storage.objects
  FOR SELECT USING (bucket_id = 'avatars');

CREATE POLICY "Users can upload avatars" ON storage.objects
  FOR INSERT WITH CHECK (
    bucket_id = 'avatars' AND
    auth.role() = 'authenticated'
  );
