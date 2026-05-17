-- ============================================================
-- ASPIRE ENGLISH HUB - Complete Database Schema
-- Supabase PostgreSQL
-- ============================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- 1. BRANCHES TABLE
-- ============================================================
CREATE TABLE public.branches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    address TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_branches_active ON public.branches(is_active);

-- ============================================================
-- 2. BATCHES TABLE
-- ============================================================
CREATE TABLE public.batches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    branch_id UUID NOT NULL REFERENCES public.branches(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    schedule VARCHAR(255),
    max_students INT DEFAULT 50,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_batches_branch ON public.batches(branch_id);
CREATE INDEX idx_batches_active ON public.batches(is_active);

-- ============================================================
-- 3. PROFILES TABLE (extends Supabase auth.users)
-- ============================================================
CREATE TABLE public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    full_name VARCHAR(150) NOT NULL,
    display_name VARCHAR(50),
    email VARCHAR(255) UNIQUE NOT NULL,
    role VARCHAR(20) DEFAULT 'student' CHECK (role IN ('student', 'admin', 'super_admin')),
    avatar_url TEXT,
    branch_id UUID REFERENCES public.branches(id) ON DELETE SET NULL,
    batch_id UUID REFERENCES public.batches(id) ON DELETE SET NULL,
    is_online BOOLEAN DEFAULT FALSE,
    last_seen TIMESTAMPTZ DEFAULT NOW(),
    is_banned BOOLEAN DEFAULT FALSE,
    ban_reason TEXT,
    xp_points INT DEFAULT 0,
    current_streak INT DEFAULT 0,
    longest_streak INT DEFAULT 0,
    total_calls INT DEFAULT 0,
    total_ai_sessions INT DEFAULT 0,
    total_speaking_minutes INT DEFAULT 0,
    proficiency_level VARCHAR(20) DEFAULT 'beginner' CHECK (proficiency_level IN ('beginner', 'elementary', 'intermediate', 'upper_intermediate', 'advanced', 'proficient')),
    preferred_language VARCHAR(50) DEFAULT 'English',
    timezone VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_profiles_role ON public.profiles(role);
CREATE INDEX idx_profiles_branch ON public.profiles(branch_id);
CREATE INDEX idx_profiles_batch ON public.profiles(batch_id);
CREATE INDEX idx_profiles_online ON public.profiles(is_online);
CREATE INDEX idx_profiles_xp ON public.profiles(xp_points DESC);

-- ============================================================
-- 4. CALL QUEUE TABLE
-- ============================================================
CREATE TABLE public.call_queue (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    batch_id UUID NOT NULL REFERENCES public.batches(id) ON DELETE CASCADE,
    branch_id UUID NOT NULL REFERENCES public.branches(id) ON DELETE CASCADE,
    status VARCHAR(20) DEFAULT 'waiting' CHECK (status IN ('waiting', 'matched', 'cancelled', 'expired')),
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    matched_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ DEFAULT (NOW() + INTERVAL '10 minutes')
);

CREATE INDEX idx_queue_status ON public.call_queue(status);
CREATE INDEX idx_queue_batch ON public.call_queue(batch_id);
CREATE INDEX idx_queue_user ON public.call_queue(user_id);

-- ============================================================
-- 5. ACTIVE CALLS TABLE
-- ============================================================
CREATE TABLE public.active_calls (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    caller_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    receiver_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    call_type VARCHAR(20) DEFAULT 'peer' CHECK (call_type IN ('peer', 'ai')),
    status VARCHAR(20) DEFAULT 'connecting' CHECK (status IN ('connecting', 'active', 'ended', 'failed')),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    connected_at TIMESTAMPTZ,
    ended_at TIMESTAMPTZ,
    duration_seconds INT DEFAULT 0,
    end_reason VARCHAR(50)
);

CREATE INDEX idx_active_calls_status ON public.active_calls(status);
CREATE INDEX idx_active_calls_caller ON public.active_calls(caller_id);
CREATE INDEX idx_active_calls_receiver ON public.active_calls(receiver_id);

-- ============================================================
-- 6. CALL HISTORY TABLE
-- ============================================================
CREATE TABLE public.call_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    caller_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    receiver_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    call_type VARCHAR(20) DEFAULT 'peer' CHECK (call_type IN ('peer', 'ai')),
    duration_seconds INT DEFAULT 0,
    caller_rating INT CHECK (caller_rating >= 1 AND caller_rating <= 5),
    receiver_rating INT CHECK (receiver_rating >= 1 AND receiver_rating <= 5),
    recording_url TEXT,
    transcript TEXT,
    ai_summary TEXT,
    started_at TIMESTAMPTZ NOT NULL,
    ended_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_call_history_caller ON public.call_history(caller_id);
CREATE INDEX idx_call_history_type ON public.call_history(call_type);
CREATE INDEX idx_call_history_date ON public.call_history(started_at DESC);

-- ============================================================
-- 7. AI SESSIONS TABLE
-- ============================================================
CREATE TABLE public.ai_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    mode VARCHAR(30) DEFAULT 'casual' CHECK (mode IN ('casual', 'interview', 'ielts', 'debate', 'topic_based')),
    topic VARCHAR(255),
    duration_seconds INT DEFAULT 0,
    messages JSONB DEFAULT '[]'::jsonb,
    transcript TEXT,
    ai_feedback JSONB,
    pronunciation_score DECIMAL(5,2),
    grammar_score DECIMAL(5,2),
    fluency_score DECIMAL(5,2),
    vocabulary_score DECIMAL(5,2),
    confidence_score DECIMAL(5,2),
    overall_score DECIMAL(5,2),
    filler_words_count INT DEFAULT 0,
    hesitation_count INT DEFAULT 0,
    words_per_minute DECIMAL(6,2),
    unique_words_count INT DEFAULT 0,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ai_sessions_user ON public.ai_sessions(user_id);
CREATE INDEX idx_ai_sessions_mode ON public.ai_sessions(mode);
CREATE INDEX idx_ai_sessions_date ON public.ai_sessions(started_at DESC);

-- ============================================================
-- 8. SPEAKING SCORES TABLE
-- ============================================================
CREATE TABLE public.speaking_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    session_id UUID REFERENCES public.ai_sessions(id) ON DELETE SET NULL,
    call_id UUID REFERENCES public.call_history(id) ON DELETE SET NULL,
    pronunciation_score DECIMAL(5,2),
    grammar_score DECIMAL(5,2),
    fluency_score DECIMAL(5,2),
    vocabulary_score DECIMAL(5,2),
    confidence_score DECIMAL(5,2),
    accent_score DECIMAL(5,2),
    overall_score DECIMAL(5,2),
    words_per_minute DECIMAL(6,2),
    filler_words JSONB DEFAULT '[]'::jsonb,
    grammar_errors JSONB DEFAULT '[]'::jsonb,
    vocabulary_suggestions JSONB DEFAULT '[]'::jsonb,
    improvement_tips JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_scores_user ON public.speaking_scores(user_id);
CREATE INDEX idx_scores_date ON public.speaking_scores(created_at DESC);

-- ============================================================
-- 9. CHALLENGES TABLE
-- ============================================================
CREATE TABLE public.challenges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    challenge_type VARCHAR(30) DEFAULT 'daily' CHECK (challenge_type IN ('daily', 'weekly', 'special')),
    difficulty VARCHAR(20) DEFAULT 'medium' CHECK (difficulty IN ('easy', 'medium', 'hard', 'expert')),
    xp_reward INT DEFAULT 50,
    requirements JSONB NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    starts_at TIMESTAMPTZ DEFAULT NOW(),
    ends_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_challenges_active ON public.challenges(is_active);
CREATE INDEX idx_challenges_type ON public.challenges(challenge_type);

-- ============================================================
-- 10. USER CHALLENGES TABLE
-- ============================================================
CREATE TABLE public.user_challenges (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    challenge_id UUID NOT NULL REFERENCES public.challenges(id) ON DELETE CASCADE,
    progress DECIMAL(5,2) DEFAULT 0,
    is_completed BOOLEAN DEFAULT FALSE,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, challenge_id)
);

CREATE INDEX idx_user_challenges_user ON public.user_challenges(user_id);

-- ============================================================
-- 11. ACHIEVEMENTS TABLE
-- ============================================================
CREATE TABLE public.achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    icon VARCHAR(50) NOT NULL,
    badge_color VARCHAR(20) DEFAULT '#6C63FF',
    category VARCHAR(30) DEFAULT 'speaking' CHECK (category IN ('speaking', 'streak', 'social', 'ai', 'special')),
    requirement_type VARCHAR(50) NOT NULL,
    requirement_value INT NOT NULL,
    xp_reward INT DEFAULT 100,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 12. USER ACHIEVEMENTS TABLE
-- ============================================================
CREATE TABLE public.user_achievements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    achievement_id UUID NOT NULL REFERENCES public.achievements(id) ON DELETE CASCADE,
    earned_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, achievement_id)
);

CREATE INDEX idx_user_achievements_user ON public.user_achievements(user_id);

-- ============================================================
-- 13. STREAKS TABLE
-- ============================================================
CREATE TABLE public.streaks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    speaking_minutes INT DEFAULT 0,
    calls_made INT DEFAULT 0,
    ai_sessions_count INT DEFAULT 0,
    xp_earned INT DEFAULT 0,
    UNIQUE(user_id, date)
);

CREATE INDEX idx_streaks_user_date ON public.streaks(user_id, date DESC);

-- ============================================================
-- 14. NOTIFICATIONS TABLE
-- ============================================================
CREATE TABLE public.notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(30) DEFAULT 'info' CHECK (type IN ('info', 'success', 'warning', 'error', 'achievement', 'challenge')),
    is_read BOOLEAN DEFAULT FALSE,
    action_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notifications_user ON public.notifications(user_id);
CREATE INDEX idx_notifications_unread ON public.notifications(user_id, is_read) WHERE is_read = FALSE;

-- ============================================================
-- 15. REPORTS TABLE
-- ============================================================
CREATE TABLE public.reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reporter_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    reported_user_id UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    call_id UUID REFERENCES public.call_history(id) ON DELETE SET NULL,
    reason VARCHAR(50) NOT NULL CHECK (reason IN ('toxic_language', 'harassment', 'spam', 'inappropriate', 'other')),
    description TEXT,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'reviewed', 'resolved', 'dismissed')),
    admin_notes TEXT,
    reviewed_by UUID REFERENCES public.profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ
);

CREATE INDEX idx_reports_status ON public.reports(status);

-- ============================================================
-- 16. CONVERSATION TOPICS TABLE
-- ============================================================
CREATE TABLE public.conversation_topics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL,
    difficulty VARCHAR(20) DEFAULT 'medium',
    prompts JSONB DEFAULT '[]'::jsonb,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- FUNCTIONS
-- ============================================================

-- Function: Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER tr_branches_updated_at BEFORE UPDATE ON public.branches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_batches_updated_at BEFORE UPDATE ON public.batches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER tr_profiles_updated_at BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Function: Auto-create profile on signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, full_name, display_name, email)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'full_name', 'Student'),
        COALESCE(NEW.raw_user_meta_data->>'display_name', 'Anonymous'),
        NEW.email
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Function: Smart matching - find partner from different batch
CREATE OR REPLACE FUNCTION find_match(p_user_id UUID, p_batch_id UUID)
RETURNS TABLE(match_id UUID, matched_user_id UUID) AS $$
DECLARE
    v_match RECORD;
BEGIN
    -- Find the oldest waiting user from a DIFFERENT batch
    SELECT cq.id, cq.user_id INTO v_match
    FROM public.call_queue cq
    WHERE cq.status = 'waiting'
      AND cq.batch_id != p_batch_id
      AND cq.user_id != p_user_id
      AND cq.expires_at > NOW()
    ORDER BY cq.joined_at ASC
    LIMIT 1
    FOR UPDATE SKIP LOCKED;

    IF v_match IS NOT NULL THEN
        -- Update the matched user's status
        UPDATE public.call_queue SET status = 'matched', matched_at = NOW()
        WHERE id = v_match.id;

        match_id := v_match.id;
        matched_user_id := v_match.user_id;
        RETURN NEXT;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function: Calculate daily XP
CREATE OR REPLACE FUNCTION calculate_daily_xp(p_user_id UUID)
RETURNS INT AS $$
DECLARE
    v_xp INT := 0;
    v_streak RECORD;
BEGIN
    SELECT * INTO v_streak FROM public.streaks
    WHERE user_id = p_user_id AND date = CURRENT_DATE;

    IF v_streak IS NOT NULL THEN
        v_xp := v_streak.speaking_minutes * 2 + v_streak.calls_made * 10 + v_streak.ai_sessions_count * 15;
    END IF;

    RETURN v_xp;
END;
$$ LANGUAGE plpgsql;

-- Function: Get leaderboard
CREATE OR REPLACE FUNCTION get_leaderboard(p_limit INT DEFAULT 50)
RETURNS TABLE(
    user_id UUID,
    display_name VARCHAR,
    avatar_url TEXT,
    xp_points INT,
    current_streak INT,
    total_calls INT,
    proficiency_level VARCHAR,
    rank BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        p.id,
        p.display_name,
        p.avatar_url,
        p.xp_points,
        p.current_streak,
        p.total_calls,
        p.proficiency_level,
        ROW_NUMBER() OVER (ORDER BY p.xp_points DESC) as rank
    FROM public.profiles p
    WHERE p.role = 'student' AND p.is_banned = FALSE
    ORDER BY p.xp_points DESC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.branches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.call_queue ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.active_calls ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.call_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ai_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.speaking_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.challenges ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_challenges ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.achievements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_achievements ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.streaks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.conversation_topics ENABLE ROW LEVEL SECURITY;

-- Profiles policies
CREATE POLICY "Users can view own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Admins can view all profiles" ON public.profiles
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role IN ('admin', 'super_admin'))
    );
CREATE POLICY "Admins can update all profiles" ON public.profiles
    FOR UPDATE USING (
        EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role IN ('admin', 'super_admin'))
    );

-- Branches policies
CREATE POLICY "Anyone can view branches" ON public.branches
    FOR SELECT USING (TRUE);
CREATE POLICY "Admins can manage branches" ON public.branches
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role IN ('admin', 'super_admin'))
    );

-- Batches policies
CREATE POLICY "Anyone can view batches" ON public.batches
    FOR SELECT USING (TRUE);
CREATE POLICY "Admins can manage batches" ON public.batches
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role IN ('admin', 'super_admin'))
    );

-- Call queue policies
CREATE POLICY "Users can manage own queue entry" ON public.call_queue
    FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Admins can view queue" ON public.call_queue
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role IN ('admin', 'super_admin'))
    );

-- Call history policies
CREATE POLICY "Users can view own calls" ON public.call_history
    FOR SELECT USING (auth.uid() = caller_id OR auth.uid() = receiver_id);
CREATE POLICY "Admins can view all calls" ON public.call_history
    FOR SELECT USING (
        EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role IN ('admin', 'super_admin'))
    );

-- AI sessions policies
CREATE POLICY "Users can manage own ai sessions" ON public.ai_sessions
    FOR ALL USING (auth.uid() = user_id);

-- Speaking scores policies
CREATE POLICY "Users can view own scores" ON public.speaking_scores
    FOR SELECT USING (auth.uid() = user_id);

-- Challenges policies
CREATE POLICY "Anyone can view challenges" ON public.challenges
    FOR SELECT USING (TRUE);
CREATE POLICY "Admins can manage challenges" ON public.challenges
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role IN ('admin', 'super_admin'))
    );

-- User challenges policies
CREATE POLICY "Users can manage own challenges" ON public.user_challenges
    FOR ALL USING (auth.uid() = user_id);

-- Achievements policies
CREATE POLICY "Anyone can view achievements" ON public.achievements
    FOR SELECT USING (TRUE);

-- User achievements policies
CREATE POLICY "Users can view own achievements" ON public.user_achievements
    FOR SELECT USING (auth.uid() = user_id);

-- Streaks policies
CREATE POLICY "Users can manage own streaks" ON public.streaks
    FOR ALL USING (auth.uid() = user_id);

-- Notifications policies
CREATE POLICY "Users can manage own notifications" ON public.notifications
    FOR ALL USING (auth.uid() = user_id);

-- Reports policies
CREATE POLICY "Users can create reports" ON public.reports
    FOR INSERT WITH CHECK (auth.uid() = reporter_id);
CREATE POLICY "Users can view own reports" ON public.reports
    FOR SELECT USING (auth.uid() = reporter_id);
CREATE POLICY "Admins can manage reports" ON public.reports
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role IN ('admin', 'super_admin'))
    );

-- Conversation topics policies
CREATE POLICY "Anyone can view topics" ON public.conversation_topics
    FOR SELECT USING (TRUE);
CREATE POLICY "Admins can manage topics" ON public.conversation_topics
    FOR ALL USING (
        EXISTS (SELECT 1 FROM public.profiles WHERE id = auth.uid() AND role IN ('admin', 'super_admin'))
    );

-- ============================================================
-- SEED DATA
-- ============================================================

-- Default achievements
INSERT INTO public.achievements (name, description, icon, category, requirement_type, requirement_value, xp_reward) VALUES
('First Words', 'Complete your first speaking session', '🎤', 'speaking', 'total_calls', 1, 50),
('Chatterbox', 'Complete 10 speaking sessions', '💬', 'speaking', 'total_calls', 10, 200),
('Silver Tongue', 'Complete 50 speaking sessions', '🗣️', 'speaking', 'total_calls', 50, 500),
('Master Orator', 'Complete 100 speaking sessions', '🏆', 'speaking', 'total_calls', 100, 1000),
('Getting Started', 'Maintain a 3-day streak', '🔥', 'streak', 'current_streak', 3, 100),
('On Fire', 'Maintain a 7-day streak', '⚡', 'streak', 'current_streak', 7, 250),
('Unstoppable', 'Maintain a 30-day streak', '💎', 'streak', 'current_streak', 30, 1000),
('AI Explorer', 'Complete 5 AI practice sessions', '🤖', 'ai', 'total_ai_sessions', 5, 150),
('AI Master', 'Complete 25 AI practice sessions', '🧠', 'ai', 'total_ai_sessions', 25, 500),
('Social Butterfly', 'Speak with 20 different partners', '🦋', 'social', 'unique_partners', 20, 400);

-- Default conversation topics
INSERT INTO public.conversation_topics (title, description, category, difficulty, prompts) VALUES
('Daily Routine', 'Discuss your daily activities and habits', 'general', 'easy', '["What time do you usually wake up?", "What does your morning routine look like?", "How do you spend your evenings?"]'),
('Travel Adventures', 'Share travel experiences and dream destinations', 'general', 'medium', '["Where was your last trip?", "What is your dream destination?", "Do you prefer solo or group travel?"]'),
('Technology Impact', 'Discuss how technology affects our lives', 'general', 'medium', '["How has technology changed your daily life?", "What apps do you use the most?", "What do you think about AI?"]'),
('Career Goals', 'Talk about career aspirations and professional life', 'interview', 'hard', '["Where do you see yourself in 5 years?", "What skills are you currently developing?", "Tell me about your biggest professional achievement."]'),
('Environmental Issues', 'Discuss climate change and sustainability', 'debate', 'hard', '["What can individuals do to help the environment?", "Should companies be forced to be eco-friendly?", "Is climate change the biggest threat we face?"]'),
('Education Systems', 'Compare and discuss education around the world', 'ielts', 'medium', '["How is education in your country?", "What changes would you make to the education system?", "Is online learning as effective as classroom learning?"]');

-- Default daily challenges
INSERT INTO public.challenges (title, description, challenge_type, difficulty, xp_reward, requirements) VALUES
('Daily Speaker', 'Complete at least one speaking session today', 'daily', 'easy', 30, '{"min_calls": 1}'),
('Practice Makes Perfect', 'Speak for at least 15 minutes today', 'daily', 'medium', 50, '{"min_minutes": 15}'),
('AI Conversation', 'Have a conversation with the AI partner', 'daily', 'easy', 25, '{"min_ai_sessions": 1}'),
('Vocabulary Builder', 'Use at least 50 unique words in conversations today', 'daily', 'hard', 75, '{"min_unique_words": 50}'),
('Weekly Marathon', 'Speak for at least 2 hours this week', 'weekly', 'hard', 200, '{"min_minutes": 120}'),
('Social Star', 'Connect with 5 different partners this week', 'weekly', 'medium', 150, '{"min_unique_partners": 5}');
