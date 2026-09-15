-- Supabase database schema for personal assistant bot

-- 1. Conversations table
CREATE TABLE IF NOT EXISTS conversations (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id BIGINT NOT NULL,
  message TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
  topic TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conv_user_time ON conversations(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_conv_topic ON conversations(topic) WHERE topic IS NOT NULL;

-- 2. Topic memories table
CREATE TABLE IF NOT EXISTS topic_memories (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id BIGINT NOT NULL,
  topic TEXT NOT NULL,
  key TEXT NOT NULL,
  value JSONB NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  CONSTRAINT unique_user_topic_key UNIQUE(user_id, topic, key)
);

CREATE INDEX IF NOT EXISTS idx_mem_user_topic ON topic_memories(user_id, topic);
CREATE INDEX IF NOT EXISTS idx_mem_updated ON topic_memories(updated_at DESC);

-- 3. Row Level Security
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE topic_memories ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow all on conversations" ON conversations;
CREATE POLICY "Allow all on conversations" ON conversations FOR ALL USING (true);

DROP POLICY IF EXISTS "Allow all on topic_memories" ON topic_memories;
CREATE POLICY "Allow all on topic_memories" ON topic_memories FOR ALL USING (true);

-- 4. Verification query
SELECT 'Setup complete!' as status,
       (SELECT count(*) FROM information_schema.tables WHERE table_name = 'conversations') as conversations_exists,
       (SELECT count(*) FROM information_schema.tables WHERE table_name = 'topic_memories') as memories_exists;
