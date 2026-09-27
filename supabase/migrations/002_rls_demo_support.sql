-- =====================================================================
-- Migration: 002_rls_demo_support.sql
-- Project: Minute AI
-- Description: Expand RLS policies and table grants so that demo data
--              (user_id = '00000000-0000-0000-0000-000000000001') can be
--              accessed in demo mode by anon role, while preserving multi-tenant
--              isolation for authenticated users.
-- =====================================================================

-- 1. Grant table permissions to anon role
GRANT USAGE ON SCHEMA public TO anon, authenticated, service_role;
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO anon;

-- 2. Profiles Policies
DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
CREATE POLICY "Users can view own profile"
    ON public.profiles FOR SELECT
    TO authenticated, anon
    USING ((SELECT auth.uid()) = id OR id = '00000000-0000-0000-0000-000000000001');

DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
CREATE POLICY "Users can update own profile"
    ON public.profiles FOR UPDATE
    TO authenticated, anon
    USING ((SELECT auth.uid()) = id OR id = '00000000-0000-0000-0000-000000000001')
    WITH CHECK ((SELECT auth.uid()) = id OR id = '00000000-0000-0000-0000-000000000001');

-- 3. Jira Projects Policies
DROP POLICY IF EXISTS "Users can view own projects" ON public.jira_projects;
CREATE POLICY "Users can view own projects"
    ON public.jira_projects FOR SELECT
    TO authenticated, anon
    USING ((SELECT auth.uid()) = user_id OR user_id = '00000000-0000-0000-0000-000000000001');

DROP POLICY IF EXISTS "Users can insert own projects" ON public.jira_projects;
CREATE POLICY "Users can insert own projects"
    ON public.jira_projects FOR INSERT
    TO authenticated, anon
    WITH CHECK ((SELECT auth.uid()) = user_id OR user_id = '00000000-0000-0000-0000-000000000001');

DROP POLICY IF EXISTS "Users can update own projects" ON public.jira_projects;
CREATE POLICY "Users can update own projects"
    ON public.jira_projects FOR UPDATE
    TO authenticated, anon
    USING ((SELECT auth.uid()) = user_id OR user_id = '00000000-0000-0000-0000-000000000001')
    WITH CHECK ((SELECT auth.uid()) = user_id OR user_id = '00000000-0000-0000-0000-000000000001');

DROP POLICY IF EXISTS "Users can delete own projects" ON public.jira_projects;
CREATE POLICY "Users can delete own projects"
    ON public.jira_projects FOR DELETE
    TO authenticated, anon
    USING ((SELECT auth.uid()) = user_id OR user_id = '00000000-0000-0000-0000-000000000001');

-- 4. Transcripts Policies
DROP POLICY IF EXISTS "Users can view own transcripts" ON public.transcripts;
CREATE POLICY "Users can view own transcripts"
    ON public.transcripts FOR SELECT
    TO authenticated, anon
    USING ((SELECT auth.uid()) = user_id OR user_id = '00000000-0000-0000-0000-000000000001');

DROP POLICY IF EXISTS "Users can insert own transcripts" ON public.transcripts;
CREATE POLICY "Users can insert own transcripts"
    ON public.transcripts FOR INSERT
    TO authenticated, anon
    WITH CHECK ((SELECT auth.uid()) = user_id OR user_id = '00000000-0000-0000-0000-000000000001');

DROP POLICY IF EXISTS "Users can update own transcripts" ON public.transcripts;
CREATE POLICY "Users can update own transcripts"
    ON public.transcripts FOR UPDATE
    TO authenticated, anon
    USING ((SELECT auth.uid()) = user_id OR user_id = '00000000-0000-0000-0000-000000000001')
    WITH CHECK ((SELECT auth.uid()) = user_id OR user_id = '00000000-0000-0000-0000-000000000001');

DROP POLICY IF EXISTS "Users can delete own transcripts" ON public.transcripts;
CREATE POLICY "Users can delete own transcripts"
    ON public.transcripts FOR DELETE
    TO authenticated, anon
    USING ((SELECT auth.uid()) = user_id OR user_id = '00000000-0000-0000-0000-000000000001');

-- 5. Action Items Policies
DROP POLICY IF EXISTS "Users can view own action items" ON public.action_items;
CREATE POLICY "Users can view own action items"
    ON public.action_items FOR SELECT
    TO authenticated, anon
    USING ((SELECT auth.uid()) = user_id OR user_id = '00000000-0000-0000-0000-000000000001');

DROP POLICY IF EXISTS "Users can insert own action items" ON public.action_items;
CREATE POLICY "Users can insert own action items"
    ON public.action_items FOR INSERT
    TO authenticated, anon
    WITH CHECK ((SELECT auth.uid()) = user_id OR user_id = '00000000-0000-0000-0000-000000000001');

DROP POLICY IF EXISTS "Users can update own action items" ON public.action_items;
CREATE POLICY "Users can update own action items"
    ON public.action_items FOR UPDATE
    TO authenticated, anon
    USING ((SELECT auth.uid()) = user_id OR user_id = '00000000-0000-0000-0000-000000000001')
    WITH CHECK ((SELECT auth.uid()) = user_id OR user_id = '00000000-0000-0000-0000-000000000001');

DROP POLICY IF EXISTS "Users can delete own action items" ON public.action_items;
CREATE POLICY "Users can delete own action items"
    ON public.action_items FOR DELETE
    TO authenticated, anon
    USING ((SELECT auth.uid()) = user_id OR user_id = '00000000-0000-0000-0000-000000000001');
