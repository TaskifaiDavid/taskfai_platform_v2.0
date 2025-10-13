-- ============================================
-- T054: Two-Factor Authentication Support
-- Add MFA fields and tracking tables
-- ============================================

-- Add MFA fields to users table
ALTER TABLE users
  ADD COLUMN IF NOT EXISTS mfa_enabled BOOLEAN DEFAULT FALSE,
  ADD COLUMN IF NOT EXISTS mfa_secret TEXT,
  ADD COLUMN IF NOT EXISTS mfa_enrolled_at TIMESTAMP WITH TIME ZONE,
  ADD COLUMN IF NOT EXISTS backup_codes TEXT[];

-- Create index for MFA lookups
CREATE INDEX IF NOT EXISTS idx_users_mfa_enabled ON users(mfa_enabled) WHERE mfa_enabled = TRUE;

-- Track MFA verification attempts (security monitoring)
CREATE TABLE IF NOT EXISTS mfa_attempts (
  attempt_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
  success BOOLEAN NOT NULL,
  ip_address VARCHAR(45),
  user_agent TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for MFA attempts
CREATE INDEX IF NOT EXISTS idx_mfa_attempts_user ON mfa_attempts(user_id);
CREATE INDEX IF NOT EXISTS idx_mfa_attempts_created ON mfa_attempts(created_at);
CREATE INDEX IF NOT EXISTS idx_mfa_attempts_user_created ON mfa_attempts(user_id, created_at DESC);

-- Enable RLS on mfa_attempts
ALTER TABLE mfa_attempts ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can read own MFA attempts
CREATE POLICY "Users can read own MFA attempts"
  ON mfa_attempts FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

-- RLS Policy: Service can insert MFA attempts (for backend logging)
CREATE POLICY "Service can insert MFA attempts"
  ON mfa_attempts FOR INSERT
  TO authenticated
  WITH CHECK (TRUE);

-- ============================================
-- Comments for documentation
-- ============================================

COMMENT ON COLUMN users.mfa_enabled IS 'Whether TOTP 2FA is enabled for this user';
COMMENT ON COLUMN users.mfa_secret IS 'Encrypted TOTP secret (base32). Decrypt before use.';
COMMENT ON COLUMN users.mfa_enrolled_at IS 'Timestamp when user completed MFA enrollment';
COMMENT ON COLUMN users.backup_codes IS 'Array of encrypted single-use recovery codes';

COMMENT ON TABLE mfa_attempts IS 'Security log of all MFA verification attempts (success and failure)';
COMMENT ON COLUMN mfa_attempts.success IS 'Whether the MFA code was valid';
COMMENT ON COLUMN mfa_attempts.ip_address IS 'Client IP address for security monitoring';
COMMENT ON COLUMN mfa_attempts.user_agent IS 'Client user agent for device tracking';
