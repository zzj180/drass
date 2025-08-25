-- Database initialization script for Dify platform
-- Based on official Dify documentation and extended for Drass applications

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Create schema for Dify platform
CREATE SCHEMA IF NOT EXISTS public;

-- Set search path
SET search_path TO public;

-- Note: Dify will create its own tables automatically
-- This script adds our custom data after Dify initialization

-- Create custom tables for Drass applications
CREATE TABLE IF NOT EXISTS drass_applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(50) NOT NULL DEFAULT '1.0.0',
    category VARCHAR(100),
    tags TEXT[],
    config JSONB NOT NULL,
    dify_app_id VARCHAR(255),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_drass_applications_name ON drass_applications(name);
CREATE INDEX IF NOT EXISTS idx_drass_applications_category ON drass_applications(category);
CREATE INDEX IF NOT EXISTS idx_drass_applications_dify_app_id ON drass_applications(dify_app_id);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_drass_applications_updated_at BEFORE UPDATE ON drass_applications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample Drass applications
INSERT INTO drass_applications (name, description, category, tags, config, dify_app_id) VALUES
    ('Data Regulation Assistant', 'AI-powered assistant for data regulation compliance and guidance', 'compliance', 
     ARRAY['data-regulation', 'compliance', 'legal', 'ai-assistant'], 
     '{"version": "1.0.0", "settings": {"language": "en", "timezone": "UTC", "default_model": "gpt-4", "max_tokens": 4000, "temperature": 0.7}, "workflow": {"name": "Data Regulation Compliance Workflow", "description": "Main workflow for handling data regulation queries", "steps": ["query_analysis", "regulation_lookup", "compliance_check", "recommendation_generation"]}, "knowledge_base": {"name": "Data Regulation Knowledge Base", "description": "Comprehensive knowledge base for data regulations", "sources": ["gdpr", "ccpa", "hipaa", "sox", "industry_standards"]}, "api": {"endpoints": [{"path": "/query", "method": "POST", "description": "Submit data regulation query"}, {"path": "/compliance-check", "method": "POST", "description": "Check compliance for specific scenario"}, {"path": "/regulations", "method": "GET", "description": "List available regulations"}]}, "security": {"data_retention_days": 90, "audit_logging": true, "encryption": true, "access_control": [{"role": "user", "permissions": ["query", "read"]}, {"role": "admin", "permissions": ["query", "read", "write", "delete"]}]}}',
     NULL),
    ('Legal Document Analyzer', 'AI-powered legal document analysis and compliance checking', 'legal', 
     ARRAY['legal', 'document-analysis', 'compliance', 'ai'], 
     '{"version": "1.0.0", "settings": {"language": "en", "timezone": "UTC", "default_model": "gpt-4", "max_tokens": 6000, "temperature": 0.3}, "workflow": {"name": "Legal Document Analysis Workflow", "description": "Workflow for analyzing legal documents and contracts", "steps": ["document_upload", "text_extraction", "legal_analysis", "compliance_check", "risk_assessment"]}, "knowledge_base": {"name": "Legal Framework Knowledge Base", "description": "Comprehensive legal framework and regulation knowledge", "sources": ["contract_law", "regulatory_frameworks", "case_precedents", "industry_standards"]}, "api": {"endpoints": [{"path": "/analyze", "method": "POST", "description": "Analyze legal document"}, {"path": "/compliance", "method": "POST", "description": "Check document compliance"}, {"path": "/risk-assessment", "method": "POST", "description": "Assess legal risks"}]}, "security": {"data_retention_days": 180, "audit_logging": true, "encryption": true, "access_control": [{"role": "user", "permissions": ["analyze", "read"]}, {"role": "lawyer", "permissions": ["analyze", "read", "write"]}, {"role": "admin", "permissions": ["analyze", "read", "write", "delete"]}]}}',
     NULL)
ON CONFLICT DO NOTHING;

-- Grant permissions to Dify user
GRANT USAGE ON SCHEMA public TO dify;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO dify;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO dify;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO dify;

-- Grant permissions on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO dify;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO dify;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT EXECUTE ON FUNCTIONS TO dify;
