-- Initialize database for Trending Intelligence System

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables for analytics data
CREATE TABLE IF NOT EXISTS trending_posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    post_id VARCHAR(255) UNIQUE NOT NULL,
    content TEXT NOT NULL,
    author VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,
    engagement_score DECIMAL(5,2),
    viral_score DECIMAL(5,2),
    processed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    batch_id VARCHAR(255),
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS analysis_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    batch_id VARCHAR(255) NOT NULL,
    engine_name VARCHAR(100) NOT NULL,
    analysis_type VARCHAR(100) NOT NULL,
    results JSONB NOT NULL,
    execution_time DECIMAL(8,3),
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS system_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    metric_unit VARCHAR(50),
    tags JSONB,
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_trending_posts_batch_id ON trending_posts(batch_id);
CREATE INDEX IF NOT EXISTS idx_trending_posts_created_at ON trending_posts(created_at);
CREATE INDEX IF NOT EXISTS idx_analysis_results_batch_id ON analysis_results(batch_id);
CREATE INDEX IF NOT EXISTS idx_analysis_results_engine_name ON analysis_results(engine_name);
CREATE INDEX IF NOT EXISTS idx_system_metrics_metric_name ON system_metrics(metric_name);
CREATE INDEX IF NOT EXISTS idx_system_metrics_recorded_at ON system_metrics(recorded_at);

-- Create views for common queries
CREATE OR REPLACE VIEW recent_analysis AS
SELECT 
    batch_id,
    engine_name,
    analysis_type,
    success,
    execution_time,
    created_at
FROM analysis_results
WHERE created_at >= NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;

CREATE OR REPLACE VIEW trending_summary AS
SELECT 
    DATE(created_at) as analysis_date,
    COUNT(*) as total_posts,
    AVG(engagement_score) as avg_engagement,
    AVG(viral_score) as avg_viral_score,
    COUNT(DISTINCT batch_id) as total_batches
FROM trending_posts
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY analysis_date DESC;