-- =====================================================================
-- Minute AI - Complete Supabase Cloud Database Migration & Seed
-- Project Ref: qklcxzdumitujatjoxqn
-- Instructions:
-- 1. Open Supabase Dashboard: https://supabase.com/dashboard/project/qklcxzdumitujatjoxqn/sql/new
-- 2. Paste this entire SQL file and click "Run" (or Ctrl+Enter)
-- =====================================================================

-- 1. Helper function for automated updated_at timestamps
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2. Profiles Table (Extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name TEXT,
    email TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. Jira Projects Table
CREATE TABLE IF NOT EXISTS public.jira_projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    project_name TEXT NOT NULL,
    project_key TEXT NOT NULL,
    description TEXT,
    team_name TEXT DEFAULT 'General',
    keywords TEXT[] DEFAULT '{}',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_user_project_key UNIQUE (user_id, project_key)
);

CREATE OR REPLACE TRIGGER update_jira_projects_updated_at
    BEFORE UPDATE ON public.jira_projects
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- 4. Transcripts Table
CREATE TABLE IF NOT EXISTS public.transcripts (
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

CREATE OR REPLACE TRIGGER update_transcripts_updated_at
    BEFORE UPDATE ON public.transcripts
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- 5. Action Items Table
CREATE TABLE IF NOT EXISTS public.action_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    transcript_id UUID NOT NULL REFERENCES public.transcripts(id) ON DELETE CASCADE,
    project_id UUID REFERENCES public.jira_projects(id) ON DELETE SET NULL,
    jira_project_key TEXT,
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

CREATE OR REPLACE TRIGGER update_action_items_updated_at
    BEFORE UPDATE ON public.action_items
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

-- 6. Trigger: Automatically provision Profile & Default Jira Projects upon User Sign-Up
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    -- Insert profile
    INSERT INTO public.profiles (id, full_name, email, created_at)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email),
        NEW.email,
        NOW()
    )
    ON CONFLICT (id) DO NOTHING;

    -- Seed 3 default Jira Projects for the new user
    INSERT INTO public.jira_projects (user_id, project_name, project_key, description, team_name, keywords, is_active)
    VALUES 
        (
            NEW.id,
            'Frontend Web App',
            'FRONT',
            'Next.js & React user dashboard, client authentication, and responsive UI components.',
            'Frontend Team',
            ARRAY['ui', 'react', 'nextjs', 'css', 'dashboard', 'button', 'modal', 'frontend'],
            TRUE
        ),
        (
            NEW.id,
            'Core Backend API',
            'CORE',
            'Python FastAPI microservices, database schemas, auth tokens, and business logic.',
            'Backend Team',
            ARRAY['api', 'fastapi', 'backend', 'python', 'database', 'sql', 'endpoint', 'auth'],
            TRUE
        ),
        (
            NEW.id,
            'Cloud Infrastructure',
            'INFRA',
            'AWS, Docker, Kubernetes clusters, CI/CD GitHub Actions pipelines, and monitoring.',
            'DevOps & SRE',
            ARRAY['docker', 'k8s', 'aws', 'ci/cd', 'deployment', 'terraform', 'monitoring'],
            TRUE
        )
    ON CONFLICT (user_id, project_key) DO NOTHING;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- 7. High-Performance Indexes
CREATE INDEX IF NOT EXISTS idx_jira_projects_user_id ON public.jira_projects(user_id);
CREATE INDEX IF NOT EXISTS idx_jira_projects_active ON public.jira_projects(user_id, is_active);
CREATE INDEX IF NOT EXISTS idx_transcripts_user_id ON public.transcripts(user_id);
CREATE INDEX IF NOT EXISTS idx_transcripts_meeting_date ON public.transcripts(user_id, meeting_date DESC);
CREATE INDEX IF NOT EXISTS idx_action_items_user_id ON public.action_items(user_id);
CREATE INDEX IF NOT EXISTS idx_action_items_transcript_id ON public.action_items(transcript_id);
CREATE INDEX IF NOT EXISTS idx_action_items_project_id ON public.action_items(project_id);
CREATE INDEX IF NOT EXISTS idx_action_items_status ON public.action_items(user_id, status);
CREATE INDEX IF NOT EXISTS idx_action_items_priority ON public.action_items(user_id, priority);
CREATE INDEX IF NOT EXISTS idx_action_items_created_at ON public.action_items(user_id, created_at DESC);

-- 8. Grant Table Permissions to Supabase Roles
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO anon;

-- 9. Enable Row Level Security (RLS)
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.jira_projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transcripts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.action_items ENABLE ROW LEVEL SECURITY;

-- 10. RLS Security Policies (Using Postgres Best Practices)
-- Profiles
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
CREATE POLICY "Users can view own profile"
    ON public.profiles FOR SELECT
    TO authenticated
    USING ((SELECT auth.uid()) = id);

DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    TO authenticated
    USING ((SELECT auth.uid()) = id)
    WITH CHECK ((SELECT auth.uid()) = id);

-- Jira Projects
DROP POLICY IF EXISTS "Users can view own projects" ON public.jira_projects;
CREATE POLICY "Users can view own projects"
    ON public.jira_projects FOR SELECT
    TO authenticated
    USING ((SELECT auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can insert own projects" ON public.jira_projects;
CREATE POLICY "Users can insert own projects"
    ON public.jira_projects FOR INSERT
    TO authenticated
    WITH CHECK ((SELECT auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can update own projects" ON public.jira_projects;
CREATE POLICY "Users can update own projects"
    ON public.jira_projects FOR UPDATE
    TO authenticated
    USING ((SELECT auth.uid()) = user_id)
    WITH CHECK ((SELECT auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can delete own projects" ON public.jira_projects;
CREATE POLICY "Users can delete own projects"
    ON public.jira_projects FOR DELETE
    TO authenticated
    USING ((SELECT auth.uid()) = user_id);

-- Transcripts
DROP POLICY IF EXISTS "Users can view own transcripts" ON public.transcripts;
CREATE POLICY "Users can view own transcripts"
    ON public.transcripts FOR SELECT
    TO authenticated
    USING ((SELECT auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can insert own transcripts" ON public.transcripts;
CREATE POLICY "Users can insert own transcripts"
    ON public.transcripts FOR INSERT
    TO authenticated
    WITH CHECK ((SELECT auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can update own transcripts" ON public.transcripts;
CREATE POLICY "Users can update own transcripts"
    ON public.transcripts FOR UPDATE
    TO authenticated
    USING ((SELECT auth.uid()) = user_id)
    WITH CHECK ((SELECT auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can delete own transcripts" ON public.transcripts;
CREATE POLICY "Users can delete own transcripts"
    ON public.transcripts FOR DELETE
    TO authenticated
    USING ((SELECT auth.uid()) = user_id);

-- Action Items
DROP POLICY IF EXISTS "Users can view own action items" ON public.action_items;
CREATE POLICY "Users can view own action items"
    ON public.action_items FOR SELECT
    TO authenticated
    USING ((SELECT auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can insert own action items" ON public.action_items;
CREATE POLICY "Users can insert own action items"
    ON public.action_items FOR INSERT
    TO authenticated
    WITH CHECK ((SELECT auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can update own action items" ON public.action_items;
CREATE POLICY "Users can update own action items"
    ON public.action_items FOR UPDATE
    TO authenticated
    USING ((SELECT auth.uid()) = user_id)
    WITH CHECK ((SELECT auth.uid()) = user_id);

DROP POLICY IF EXISTS "Users can delete own action items" ON public.action_items;
CREATE POLICY "Users can delete own action items"
    ON public.action_items FOR DELETE
    TO authenticated
    USING ((SELECT auth.uid()) = user_id);
