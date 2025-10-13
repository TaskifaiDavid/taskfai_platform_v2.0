/**
 * MFA API Client
 *
 * API endpoints for Two-Factor Authentication (TOTP) management
 */
import { apiClient } from '@/lib/api'

export interface MFAEnrollResponse {
  qr_code: string
  secret: string
  backup_codes: string[]
  message: string
}

export interface MFAStatusResponse {
  mfa_enabled: boolean
  enrolled_at: string | null
  backup_codes_remaining: number
}

export interface MFALoginResponse {
  requires_mfa?: boolean
  temp_token?: string
  message?: string
  user?: any
  access_token?: string
}

export const mfaApi = {
  /**
   * Enroll in 2FA - returns QR code and backup codes
   */
  async enrollMFA(password: string): Promise<MFAEnrollResponse> {
    const { data } = await apiClient.post('/auth/mfa/enroll', { password })
    return data
  },

  /**
   * Verify TOTP code to complete enrollment
   */
  async verifyEnrollment(code: string): Promise<{ message: string }> {
    const { data } = await apiClient.post('/auth/mfa/verify-enrollment', { code })
    return data
  },

  /**
   * Disable 2FA (requires password + current TOTP code)
   */
  async disableMFA(password: string, code: string): Promise<{ message: string }> {
    const { data } = await apiClient.post('/auth/mfa/disable', { password, code })
    return data
  },

  /**
   * Get current MFA status
   */
  async getStatus(): Promise<MFAStatusResponse> {
    const { data } = await apiClient.get('/auth/mfa/status')
    return data
  },

  /**
   * Complete MFA-protected login with TOTP code
   */
  async verifyLoginMFA(tempToken: string, mfaCode: string): Promise<MFALoginResponse> {
    const { data } = await apiClient.post('/auth/login/mfa-verify', {
      temp_token: tempToken,
      mfa_code: mfaCode
    })
    return data
  }
}
