import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { mfaApi, type MFAEnrollResponse } from '@/api/mfa'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useUIStore } from '@/stores/ui'
import { Shield, Download, AlertCircle, CheckCircle2, Loader2 } from 'lucide-react'

type EnrollmentStep = 'status' | 'enroll' | 'verify'

export function MFASettings() {
  const [step, setStep] = useState<EnrollmentStep>('status')
  const [enrollData, setEnrollData] = useState<MFAEnrollResponse | null>(null)
  const [password, setPassword] = useState('')
  const [verifyCode, setVerifyCode] = useState('')
  const [disablePassword, setDisablePassword] = useState('')
  const [disableCode, setDisableCode] = useState('')

  const queryClient = useQueryClient()
  const addNotification = useUIStore((state) => state.addNotification)

  // Query MFA status
  const { data: status, isLoading } = useQuery({
    queryKey: ['mfa-status'],
    queryFn: mfaApi.getStatus,
  })

  // Enrollment mutation
  const enrollMutation = useMutation({
    mutationFn: (password: string) => mfaApi.enrollMFA(password),
    onSuccess: (data) => {
      setEnrollData(data)
      setStep('verify')
      addNotification({
        type: 'success',
        title: 'QR Code Generated',
        message: 'Scan the QR code with your authenticator app',
      })
    },
    onError: (error: any) => {
      addNotification({
        type: 'error',
        title: 'Enrollment Failed',
        message: error?.response?.data?.detail || 'Failed to start enrollment',
      })
    },
  })

  // Verify enrollment mutation
  const verifyMutation = useMutation({
    mutationFn: (code: string) => mfaApi.verifyEnrollment(code),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mfa-status'] })
      setStep('status')
      setPassword('')
      setVerifyCode('')
      setEnrollData(null)
      addNotification({
        type: 'success',
        title: '2FA Enabled',
        message: 'Your account is now protected with two-factor authentication',
      })
    },
    onError: (error: any) => {
      addNotification({
        type: 'error',
        title: 'Verification Failed',
        message: error?.response?.data?.detail || 'Invalid code',
      })
    },
  })

  // Disable MFA mutation
  const disableMutation = useMutation({
    mutationFn: ({ password, code }: { password: string; code: string }) =>
      mfaApi.disableMFA(password, code),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['mfa-status'] })
      setDisablePassword('')
      setDisableCode('')
      addNotification({
        type: 'info',
        title: '2FA Disabled',
        message: 'Two-factor authentication has been disabled',
      })
    },
    onError: (error: any) => {
      addNotification({
        type: 'error',
        title: 'Failed to Disable',
        message: error?.response?.data?.detail || 'Could not disable 2FA',
      })
    },
  })

  const handleEnroll = (e: React.FormEvent) => {
    e.preventDefault()
    if (!password) return
    enrollMutation.mutate(password)
  }

  const handleVerify = (e: React.FormEvent) => {
    e.preventDefault()
    if (verifyCode.length !== 6) return
    verifyMutation.mutate(verifyCode)
  }

  const handleDisable = (e: React.FormEvent) => {
    e.preventDefault()
    if (!disablePassword || disableCode.length !== 6) return
    disableMutation.mutate({ password: disablePassword, code: disableCode })
  }

  const downloadBackupCodes = () => {
    if (!enrollData?.backup_codes) return
    const text = enrollData.backup_codes.join('\n')
    const blob = new Blob([text], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'taskifai-backup-codes.txt'
    a.click()
    URL.revokeObjectURL(url)
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center">
          <Shield className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-foreground">Two-Factor Authentication</h1>
          <p className="text-sm text-muted-foreground">
            Secure your account with TOTP authentication
          </p>
        </div>
      </div>

      {/* Status View */}
      {step === 'status' && (
        <div className="space-y-6">
          {/* Current Status Card */}
          <div className="p-6 bg-card border border-border rounded-lg space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {status?.mfa_enabled ? (
                  <CheckCircle2 className="h-5 w-5 text-green-500" />
                ) : (
                  <AlertCircle className="h-5 w-5 text-yellow-500" />
                )}
                <div>
                  <p className="font-medium text-foreground">
                    Status: {status?.mfa_enabled ? 'Enabled' : 'Disabled'}
                  </p>
                  {status?.mfa_enabled && status?.enrolled_at && (
                    <p className="text-sm text-muted-foreground">
                      Enabled on {new Date(status.enrolled_at).toLocaleDateString()}
                    </p>
                  )}
                </div>
              </div>
            </div>

            {status?.mfa_enabled && (
              <div className="pt-4 border-t border-border">
                <p className="text-sm text-muted-foreground">
                  Backup codes remaining: <span className="font-medium">{status.backup_codes_remaining}</span>
                </p>
              </div>
            )}
          </div>

          {/* Info Box */}
          <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
            <p className="text-sm text-blue-900 dark:text-blue-100">
              Two-factor authentication adds an extra layer of security by requiring a code from your
              authenticator app in addition to your password.
            </p>
          </div>

          {/* Action Buttons */}
          {!status?.mfa_enabled ? (
            <Button onClick={() => setStep('enroll')} className="w-full">
              <Shield className="mr-2 h-4 w-4" />
              Enable Two-Factor Authentication
            </Button>
          ) : (
            <div className="space-y-4">
              <form onSubmit={handleDisable} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="disable-password">Password</Label>
                  <Input
                    id="disable-password"
                    type="password"
                    value={disablePassword}
                    onChange={(e) => setDisablePassword(e.target.value)}
                    placeholder="Enter your password"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="disable-code">Authentication Code</Label>
                  <Input
                    id="disable-code"
                    type="text"
                    maxLength={6}
                    value={disableCode}
                    onChange={(e) => setDisableCode(e.target.value.replace(/\D/g, ''))}
                    placeholder="000000"
                    required
                  />
                </div>
                <Button
                  type="submit"
                  variant="destructive"
                  className="w-full"
                  disabled={disableMutation.isPending}
                >
                  {disableMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Disabling...
                    </>
                  ) : (
                    'Disable Two-Factor Authentication'
                  )}
                </Button>
              </form>
            </div>
          )}
        </div>
      )}

      {/* Enrollment View */}
      {step === 'enroll' && (
        <div className="space-y-6">
          <div className="p-6 bg-card border border-border rounded-lg">
            <h2 className="text-lg font-semibold mb-4">Step 1: Verify Your Identity</h2>
            <form onSubmit={handleEnroll} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  required
                  autoFocus
                />
              </div>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setStep('status')
                    setPassword('')
                  }}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={enrollMutation.isPending} className="flex-1">
                  {enrollMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Generating...
                    </>
                  ) : (
                    'Continue'
                  )}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Verification View */}
      {step === 'verify' && enrollData && (
        <div className="space-y-6">
          {/* QR Code Card */}
          <div className="p-6 bg-card border border-border rounded-lg text-center space-y-4">
            <h2 className="text-lg font-semibold">Step 2: Scan QR Code</h2>
            <p className="text-sm text-muted-foreground">
              Use Google Authenticator, Authy, or any TOTP app
            </p>
            <div className="flex justify-center">
              <img src={enrollData.qr_code} alt="QR Code" className="border border-border rounded-lg" />
            </div>
            <div className="pt-4 border-t border-border">
              <p className="text-xs text-muted-foreground mb-2">Or enter this code manually:</p>
              <code className="px-3 py-1.5 bg-muted rounded text-sm font-mono">{enrollData.secret}</code>
            </div>
          </div>

          {/* Backup Codes Card */}
          <div className="p-6 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg space-y-4">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
              <div className="space-y-2 flex-1">
                <p className="font-medium text-yellow-900 dark:text-yellow-100">Backup Recovery Codes</p>
                <p className="text-sm text-yellow-800 dark:text-yellow-200">
                  Save these codes in a secure location. Each code can be used once if you lose access to your
                  authenticator app.
                </p>
              </div>
            </div>
            <div className="font-mono text-sm space-y-1 bg-yellow-100 dark:bg-yellow-900/40 p-4 rounded">
              {enrollData.backup_codes.map((code, i) => (
                <div key={i} className="text-yellow-900 dark:text-yellow-100">
                  {code}
                </div>
              ))}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={downloadBackupCodes}
              className="w-full border-yellow-300 dark:border-yellow-700"
            >
              <Download className="mr-2 h-4 w-4" />
              Download Backup Codes
            </Button>
          </div>

          {/* Verification Form */}
          <div className="p-6 bg-card border border-border rounded-lg">
            <h2 className="text-lg font-semibold mb-4">Step 3: Verify Setup</h2>
            <form onSubmit={handleVerify} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="verify-code">Enter 6-digit code from your app</Label>
                <Input
                  id="verify-code"
                  type="text"
                  maxLength={6}
                  value={verifyCode}
                  onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, ''))}
                  placeholder="000000"
                  className="text-center text-2xl tracking-widest font-mono"
                  required
                  autoFocus
                />
              </div>
              <div className="flex gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setStep('status')
                    setVerifyCode('')
                    setEnrollData(null)
                  }}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={verifyMutation.isPending || verifyCode.length !== 6}
                  className="flex-1"
                >
                  {verifyMutation.isPending ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Verifying...
                    </>
                  ) : (
                    'Complete Setup'
                  )}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
