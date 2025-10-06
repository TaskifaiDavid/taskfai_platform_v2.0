-- ============================================
-- TaskifAI - Complete Database Schema
-- Sales Data Analytics Platform
-- ============================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- Full-text search
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- JSON indexing

-- ============================================
-- CORE TABLES
-- ============================================

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'analyst' CHECK (role IN ('analyst', 'admin')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Resellers table
CREATE TABLE IF NOT EXISTS resellers (
    reseller_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    country VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    product_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sku VARCHAR(100) UNIQUE NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    product_ean VARCHAR(13), -- Can be NULL for some vendors
    functional_name VARCHAR(255),
    category VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- SALES DATA TABLES
-- ============================================

-- Offline/Wholesale Sales (B2B) - sellout_entries2
CREATE TABLE IF NOT EXISTS sellout_entries2 (
    sale_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(product_id) ON DELETE SET NULL,
    reseller_id UUID REFERENCES resellers(reseller_id) ON DELETE SET NULL,
    upload_batch_id UUID REFERENCES upload_batches(upload_batch_id) ON DELETE CASCADE,

    -- Product info
    functional_name VARCHAR(255) NOT NULL,
    product_ean VARCHAR(13), -- Can be NULL (e.g., Galilu)

    -- Reseller info
    reseller VARCHAR(255) NOT NULL,

    -- Financial data
    sales_eur DECIMAL(12, 2) NOT NULL,
    quantity INTEGER NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'EUR',

    -- Temporal data
    month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    year INTEGER NOT NULL CHECK (year >= 2000 AND year <= 2100),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Online Sales (D2C Ecommerce) - ecommerce_orders
CREATE TABLE IF NOT EXISTS ecommerce_orders (
    order_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    upload_batch_id UUID REFERENCES upload_batches(upload_batch_id) ON DELETE CASCADE,

    -- Product info
    product_ean VARCHAR(13),
    functional_name VARCHAR(255) NOT NULL,
    product_name VARCHAR(255),

    -- Financial data
    sales_eur DECIMAL(12, 2) NOT NULL,
    quantity INTEGER NOT NULL,
    cost_of_goods DECIMAL(12, 2),
    stripe_fee DECIMAL(12, 2),

    -- Temporal data
    order_date DATE NOT NULL,

    -- Geographic data
    country VARCHAR(100),
    city VARCHAR(255),

    -- Marketing attribution
    utm_source VARCHAR(255),
    utm_medium VARCHAR(255),
    utm_campaign VARCHAR(255),
    device_type VARCHAR(50) CHECK (device_type IN ('mobile', 'desktop', 'tablet')),

    -- Metadata
    reseller VARCHAR(255) DEFAULT 'Online',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- UPLOAD & ERROR TRACKING
-- ============================================

-- Upload batches
CREATE TABLE IF NOT EXISTS upload_batches (
    upload_batch_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    uploader_user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    original_filename VARCHAR(500) NOT NULL,
    file_size_bytes BIGINT,
    vendor_name VARCHAR(100), -- Auto-detected vendor
    upload_mode VARCHAR(20) NOT NULL CHECK (upload_mode IN ('append', 'replace')),
    processing_status VARCHAR(50) NOT NULL DEFAULT 'pending'
        CHECK (processing_status IN ('pending', 'processing', 'completed', 'failed')),
    rows_total INTEGER,
    rows_processed INTEGER,
    rows_failed INTEGER,
    total_sales_eur DECIMAL(15, 2),
    upload_timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    error_summary TEXT
);

-- Error reports
CREATE TABLE IF NOT EXISTS error_reports (
    error_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    upload_batch_id UUID NOT NULL REFERENCES upload_batches(upload_batch_id) ON DELETE CASCADE,
    row_number_in_file INTEGER NOT NULL,
    error_type VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    raw_data JSONB, -- Store problematic row data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- AI CHAT SYSTEM
-- ============================================

-- Conversation history
CREATE TABLE IF NOT EXISTS conversation_history (
    conversation_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    session_id VARCHAR(255), -- Optional grouping for multiple threads
    user_message TEXT NOT NULL,
    ai_response TEXT NOT NULL,
    query_intent VARCHAR(100), -- e.g., 'ONLINE_SALES', 'COMPARISON', 'TIME_ANALYSIS'
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- DASHBOARD MANAGEMENT
-- ============================================

-- Dashboard configurations
CREATE TABLE IF NOT EXISTS dashboard_configs (
    config_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    dashboard_name VARCHAR(255) NOT NULL,
    dashboard_type VARCHAR(50) NOT NULL CHECK (dashboard_type IN ('looker', 'tableau', 'powerbi', 'metabase', 'custom')),
    dashboard_url TEXT NOT NULL,
    authentication_method VARCHAR(50) DEFAULT 'none' CHECK (authentication_method IN ('none', 'bearer_token', 'api_key', 'oauth')),
    authentication_config JSONB, -- Encrypted credentials/tokens
    permissions TEXT[], -- Array of user IDs or roles
    is_active BOOLEAN DEFAULT FALSE, -- Primary dashboard flag
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- EMAIL SYSTEM
-- ============================================

-- Email logs
CREATE TABLE IF NOT EXISTS email_logs (
    log_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(user_id) ON DELETE SET NULL,
    email_type VARCHAR(50) NOT NULL CHECK (email_type IN ('success', 'failure', 'scheduled_report')),
    recipient_email VARCHAR(255) NOT NULL,
    subject TEXT NOT NULL,
    sent_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    status VARCHAR(50) NOT NULL DEFAULT 'pending' CHECK (status IN ('sent', 'failed', 'pending')),
    error_message TEXT,
    attachment_count INTEGER DEFAULT 0,
    attachment_size BIGINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

-- Users
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- sellout_entries2
CREATE INDEX IF NOT EXISTS idx_sellout_user_id ON sellout_entries2(user_id);
CREATE INDEX IF NOT EXISTS idx_sellout_year_month ON sellout_entries2(year, month);
CREATE INDEX IF NOT EXISTS idx_sellout_reseller ON sellout_entries2(reseller);
CREATE INDEX IF NOT EXISTS idx_sellout_product_ean ON sellout_entries2(product_ean);
CREATE INDEX IF NOT EXISTS idx_sellout_upload_batch ON sellout_entries2(upload_batch_id);

-- ecommerce_orders
CREATE INDEX IF NOT EXISTS idx_ecommerce_user_id ON ecommerce_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_ecommerce_order_date ON ecommerce_orders(order_date);
CREATE INDEX IF NOT EXISTS idx_ecommerce_country ON ecommerce_orders(country);
CREATE INDEX IF NOT EXISTS idx_ecommerce_utm_source ON ecommerce_orders(utm_source);
CREATE INDEX IF NOT EXISTS idx_ecommerce_upload_batch ON ecommerce_orders(upload_batch_id);

-- upload_batches
CREATE INDEX IF NOT EXISTS idx_upload_batches_user ON upload_batches(uploader_user_id);
CREATE INDEX IF NOT EXISTS idx_upload_batches_status ON upload_batches(processing_status);
CREATE INDEX IF NOT EXISTS idx_upload_batches_timestamp ON upload_batches(upload_timestamp);

-- error_reports
CREATE INDEX IF NOT EXISTS idx_error_reports_upload_batch ON error_reports(upload_batch_id);

-- conversation_history
CREATE INDEX IF NOT EXISTS idx_conversation_user ON conversation_history(user_id);
CREATE INDEX IF NOT EXISTS idx_conversation_session ON conversation_history(session_id);
CREATE INDEX IF NOT EXISTS idx_conversation_timestamp ON conversation_history(timestamp);

-- dashboard_configs
CREATE INDEX IF NOT EXISTS idx_dashboard_user ON dashboard_configs(user_id);

-- email_logs
CREATE INDEX IF NOT EXISTS idx_email_logs_user ON email_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_email_logs_status ON email_logs(status);

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================

-- Enable RLS on all user-specific tables
ALTER TABLE sellout_entries2 ENABLE ROW LEVEL SECURITY;
ALTER TABLE ecommerce_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE upload_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE error_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE dashboard_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE email_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policies for sellout_entries2
CREATE POLICY "Users can read own offline sales data"
    ON sellout_entries2 FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY "Users can insert own offline sales data"
    ON sellout_entries2 FOR INSERT
    TO authenticated
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can delete own offline sales data"
    ON sellout_entries2 FOR DELETE
    TO authenticated
    USING (user_id = auth.uid());

-- RLS Policies for ecommerce_orders
CREATE POLICY "Users can read own online sales data"
    ON ecommerce_orders FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY "Users can insert own online sales data"
    ON ecommerce_orders FOR INSERT
    TO authenticated
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can delete own online sales data"
    ON ecommerce_orders FOR DELETE
    TO authenticated
    USING (user_id = auth.uid());

-- RLS Policies for upload_batches
CREATE POLICY "Users can read own uploads"
    ON upload_batches FOR SELECT
    TO authenticated
    USING (uploader_user_id = auth.uid());

CREATE POLICY "Users can create own uploads"
    ON upload_batches FOR INSERT
    TO authenticated
    WITH CHECK (uploader_user_id = auth.uid());

-- RLS Policies for error_reports (via upload_batches)
CREATE POLICY "Users can read errors for own uploads"
    ON error_reports FOR SELECT
    TO authenticated
    USING (
        upload_batch_id IN (
            SELECT upload_batch_id FROM upload_batches WHERE uploader_user_id = auth.uid()
        )
    );

-- RLS Policies for conversation_history
CREATE POLICY "Users can read own conversations"
    ON conversation_history FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY "Users can create own conversations"
    ON conversation_history FOR INSERT
    TO authenticated
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can delete own conversations"
    ON conversation_history FOR DELETE
    TO authenticated
    USING (user_id = auth.uid());

-- RLS Policies for dashboard_configs
CREATE POLICY "Users can read own dashboards"
    ON dashboard_configs FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY "Users can create own dashboards"
    ON dashboard_configs FOR INSERT
    TO authenticated
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update own dashboards"
    ON dashboard_configs FOR UPDATE
    TO authenticated
    USING (user_id = auth.uid());

CREATE POLICY "Users can delete own dashboards"
    ON dashboard_configs FOR DELETE
    TO authenticated
    USING (user_id = auth.uid());

-- RLS Policies for email_logs
CREATE POLICY "Users can read own email logs"
    ON email_logs FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

-- ============================================
-- TRIGGERS FOR AUTO-UPDATED TIMESTAMPS
-- ============================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_dashboard_configs_updated_at
    BEFORE UPDATE ON dashboard_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- SAMPLE SEED DATA (for development/testing)
-- ============================================

-- Insert sample resellers
INSERT INTO resellers (name, country) VALUES
    ('Galilu', 'Poland'),
    ('Boxnox', 'Europe'),
    ('Skins SA', 'South Africa'),
    ('CDLC', 'Europe'),
    ('Selfridges', 'United Kingdom'),
    ('Liberty', 'United Kingdom'),
    ('Ukraine Distributors', 'Ukraine'),
    ('Continuity Suppliers', 'United Kingdom'),
    ('Skins NL', 'Netherlands'),
    ('Online', 'Global')
ON CONFLICT (name) DO NOTHING;

-- Insert sample products
INSERT INTO products (sku, product_name, product_ean, functional_name, category) VALUES
    ('PROD-001', 'Product A', '1234567890123', 'Product A', 'Category 1'),
    ('PROD-002', 'Product B', '1234567890124', 'Product B', 'Category 1'),
    ('PROD-003', 'Product C', '1234567890125', 'Product C', 'Category 2'),
    ('PROD-004', 'Product D', '1234567890126', 'Product D', 'Category 2'),
    ('PROD-005', 'Product E', '1234567890127', 'Product E', 'Category 3')
ON CONFLICT (sku) DO NOTHING;

-- ============================================
-- VIEWS FOR COMMON QUERIES
-- ============================================

-- Combined sales view (online + offline)
CREATE OR REPLACE VIEW vw_all_sales AS
SELECT
    user_id,
    'offline' AS channel,
    functional_name AS product,
    sales_eur,
    quantity,
    reseller,
    year,
    month,
    NULL::date AS order_date,
    NULL AS country,
    created_at
FROM sellout_entries2
UNION ALL
SELECT
    user_id,
    'online' AS channel,
    functional_name AS product,
    sales_eur,
    quantity,
    reseller,
    EXTRACT(YEAR FROM order_date)::integer AS year,
    EXTRACT(MONTH FROM order_date)::integer AS month,
    order_date,
    country,
    created_at
FROM ecommerce_orders;

-- ============================================
-- COMPLETED
-- ============================================
