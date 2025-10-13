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
    return await apiClient.post<MFAEnrollResponse>('/auth/mfa/enroll', { password })
  },

  /**
   * Verify TOTP code to complete enrollment
   */
  async verifyEnrollment(code: string): Promise<{ message: string }> {
    return await apiClient.post<{ message: string }>('/auth/mfa/verify-enrollment', { code })
  },

  /**
   * Disable 2FA (requires password + current TOTP code)
   */
  async disableMFA(password: string, code: string): Promise<{ message: string }> {
    return await apiClient.post<{ message: string }>('/auth/mfa/disable', { password, code })
  },

  /**
   * Get current MFA status
   */
  async getStatus(): Promise<MFAStatusResponse> {
    return await apiClient.get<MFAStatusResponse>('/auth/mfa/status')
  },

  /**
   * Complete MFA-protected login with TOTP code
   */
  async verifyLoginMFA(tempToken: string, mfaCode: string): Promise<MFALoginResponse> {
    return await apiClient.post<MFALoginResponse>('/auth/login/mfa-verify', {
      temp_token: tempToken,
      mfa_code: mfaCode
    })
  }
}
