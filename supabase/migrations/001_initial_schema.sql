-- =====================================================================
-- Migration: 001_initial_schema.sql
-- Project: Minute AI (Meeting Transcript to Jira Action Item Dashboard)
-- =====================================================================

-- 1. Helper function for automated updated_at timestamp updates
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2. Profiles Table (Extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT,
    email TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Trigger to automatically create a profile row when a new user signs up in auth.users
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, full_name, email, created_at)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email),
        NEW.email,
        NOW()
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 3. Jira Projects Table
CREATE TABLE IF NOT EXISTS jira_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_name TEXT NOT NULL,
    project_key TEXT NOT NULL,
    description TEXT,
    team_name TEXT,
    keywords TEXT[] DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_user_project_key UNIQUE (user_id, project_key)
);

CREATE TRIGGER update_jira_projects_updated_at
    BEFORE UPDATE ON jira_projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 4. Transcripts Table
CREATE TABLE IF NOT EXISTS transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    meeting_name TEXT NOT NULL,
    meeting_date DATE NOT NULL DEFAULT CURRENT_DATE,
    transcript_text TEXT NOT NULL,
    source_type TEXT NOT NULL DEFAULT 'paste' CHECK (source_type IN ('paste', 'txt', 'vtt', 'srt', 'audio')),
    processing_status TEXT NOT NULL DEFAULT 'processed' CHECK (processing_status IN ('pending', 'processed', 'failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER update_transcripts_updated_at
    BEFORE UPDATE ON transcripts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 5. Action Items Table
CREATE TABLE IF NOT EXISTS action_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    transcript_id UUID NOT NULL REFERENCES transcripts(id) ON DELETE CASCADE,
    project_id UUID REFERENCES jira_projects(id) ON DELETE SET NULL,
    action_title TEXT NOT NULL,
    description TEXT NOT NULL,
    assignee TEXT,
    priority TEXT CHECK (priority IN ('Lowest', 'Low', 'Medium', 'High', 'Highest')),
    due_date TEXT,
    action_type TEXT NOT NULL DEFAULT 'task' CHECK (action_type IN ('bug', 'feature', 'investigation', 'follow-up', 'task')),
    source_excerpt TEXT NOT NULL,
    confidence_score NUMERIC(3, 2) NOT NULL DEFAULT 0.85 CHECK (confidence_score >= 0.0 AND confidence_score <= 1.0),
    status TEXT NOT NULL DEFAULT 'Pending Review' CHECK (status IN ('Pending Review', 'Approved', 'Needs Clarification', 'Rejected')),
    clarification_required BOOLEAN NOT NULL DEFAULT FALSE,
    clarification_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER update_action_items_updated_at
    BEFORE UPDATE ON action_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- 6. Indexes for Performance and Filtering
CREATE INDEX IF NOT EXISTS idx_jira_projects_user_id ON jira_projects(user_id);
CREATE INDEX IF NOT EXISTS idx_jira_projects_active ON jira_projects(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_transcripts_user_id ON transcripts(user_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_meeting_date ON transcripts(user_id, meeting_date DESC);
CREATE INDEX IF NOT EXISTS idx_action_items_user_id ON action_items(user_id);
CREATE INDEX IF NOT EXISTS idx_action_items_transcript_id ON action_items(transcript_id);
CREATE INDEX IF NOT EXISTS idx_action_items_project_id ON action_items(project_id);
CREATE INDEX IF NOT EXISTS idx_action_items_status ON action_items(user_id, status);
CREATE INDEX IF NOT EXISTS idx_action_items_priority ON action_items(user_id, priority);
CREATE INDEX IF NOT EXISTS idx_action_items_created_at ON action_items(user_id, created_at DESC);

-- 7. Enable Row Level Security (RLS)
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE jira_projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE transcripts ENABLE ROW LEVEL SECURITY;
ALTER TABLE action_items ENABLE ROW LEVEL SECURITY;

-- 8. RLS Security Policies
-- Profiles: Users can view and update their own profile
CREATE POLICY "Users can view their own profile"
    ON profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY "Users can update their own profile"
    ON profiles FOR UPDATE
    USING (auth.uid() = id);

-- Jira Projects: Users have full access only to their own projects
CREATE POLICY "Users can view their own jira projects"
    ON jira_projects FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own jira projects"
    ON jira_projects FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own jira projects"
    ON jira_projects FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own jira projects"
    ON jira_projects FOR DELETE
    USING (auth.uid() = user_id);

-- Transcripts: Users have full access only to their own transcripts
CREATE POLICY "Users can view their own transcripts"
    ON transcripts FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own transcripts"
    ON transcripts FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own transcripts"
    ON transcripts FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own transcripts"
    ON transcripts FOR DELETE
    USING (auth.uid() = user_id);

-- Action Items: Users have full access only to their own action items
CREATE POLICY "Users can view their own action items"
    ON action_items FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own action items"
    ON action_items FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own action items"
    ON action_items FOR UPDATE
    USING (auth.uid() = user_id);

CREATE POLICY "Users can delete their own action items"
    ON action_items FOR DELETE
    USING (auth.uid() = user_id);
