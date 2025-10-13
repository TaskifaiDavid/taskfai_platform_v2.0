import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Settings as SettingsIcon, User, Bell, Shield, Lock, ArrowRight } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'

export function Settings() {
  const { user } = useAuth()
  const navigate = useNavigate()

  const handleSave = () => {
    toast.success('Settings saved successfully')
  }

  return (
    <div className="space-y-8 animate-in fade-in-0 duration-500">
      {/* Header */}
      <div className="flex items-center gap-4">
        <div className="h-12 w-12 rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center border border-primary/30 shadow-sm">
          <SettingsIcon className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h1 className="text-3xl font-bold">Settings</h1>
          <p className="text-sm text-muted-foreground mt-1">Manage your account preferences and application settings</p>
        </div>
      </div>

      {/* Profile Settings */}
      <Card className="border-border bg-card shadow-sm">
        <CardHeader className="border-b border-border bg-background/50">
          <CardTitle className="flex items-center gap-2 text-lg">
            <div className="h-8 w-8 rounded-lg bg-primary/10 flex items-center justify-center">
              <User className="h-4 w-4 text-primary" />
            </div>
            Profile
          </CardTitle>
          <CardDescription>View and manage your profile information</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 pt-6">
          <div className="space-y-2">
            <Label htmlFor="email" className="text-xs uppercase tracking-wide font-semibold text-muted-foreground">
              Email
            </Label>
            <Input
              id="email"
              type="email"
              value={user?.email || ''}
              disabled
              className="bg-muted/30 border-border"
            />
            <p className="text-xs text-muted-foreground">Your email address cannot be changed</p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="role" className="text-xs uppercase tracking-wide font-semibold text-muted-foreground">
              Role
            </Label>
            <Input
              id="role"
              value={user?.role || ''}
              disabled
              className="bg-muted/30 border-border capitalize"
            />
          </div>
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card className="border-border bg-card shadow-sm">
        <CardHeader className="border-b border-border bg-background/50">
          <CardTitle className="flex items-center gap-2 text-lg">
            <div className="h-8 w-8 rounded-lg bg-accent/10 flex items-center justify-center">
              <Bell className="h-4 w-4 text-accent" />
            </div>
            Notifications
          </CardTitle>
          <CardDescription>Configure how you receive notifications</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 pt-6">
          <div className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-background/50 transition-colors">
            <div>
              <p className="font-semibold text-foreground">Upload Notifications</p>
              <p className="text-sm text-muted-foreground mt-1">Get notified when file uploads complete</p>
            </div>
            <input
              type="checkbox"
              defaultChecked
              className="h-5 w-5 rounded border-border text-primary focus:ring-2 focus:ring-primary focus:ring-offset-2"
            />
          </div>

          <div className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-background/50 transition-colors">
            <div>
              <p className="font-semibold text-foreground">Query Results</p>
              <p className="text-sm text-muted-foreground mt-1">Get notified when AI chat queries finish</p>
            </div>
            <input
              type="checkbox"
              defaultChecked
              className="h-5 w-5 rounded border-border text-primary focus:ring-2 focus:ring-primary focus:ring-offset-2"
            />
          </div>

          <div className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-background/50 transition-colors">
            <div>
              <p className="font-semibold text-foreground">System Updates</p>
              <p className="text-sm text-muted-foreground mt-1">Receive updates about new features</p>
            </div>
            <input
              type="checkbox"
              className="h-5 w-5 rounded border-border text-primary focus:ring-2 focus:ring-primary focus:ring-offset-2"
            />
          </div>
        </CardContent>
      </Card>

      {/* Security */}
      <Card className="border-border bg-card shadow-sm">
        <CardHeader className="border-b border-border bg-background/50">
          <CardTitle className="flex items-center gap-2 text-lg">
            <div className="h-8 w-8 rounded-lg bg-destructive/10 flex items-center justify-center">
              <Lock className="h-4 w-4 text-destructive" />
            </div>
            Security & Authentication
          </CardTitle>
          <CardDescription>Manage your account security settings</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 pt-6">
          <div className="flex items-center justify-between p-4 rounded-lg border border-border hover:bg-background/50 transition-colors cursor-pointer" onClick={() => navigate('/settings/security')}>
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-lg bg-primary/10 flex items-center justify-center">
                <Shield className="h-6 w-6 text-primary" />
              </div>
              <div>
                <p className="font-semibold text-foreground">Two-Factor Authentication (2FA)</p>
                <p className="text-sm text-muted-foreground mt-1">Add an extra layer of security to your account</p>
              </div>
            </div>
            <ArrowRight className="h-5 w-5 text-muted-foreground" />
          </div>
        </CardContent>
      </Card>

      {/* Preferences */}
      <Card className="border-border bg-card shadow-sm">
        <CardHeader className="border-b border-border bg-background/50">
          <CardTitle className="flex items-center gap-2 text-lg">
            <div className="h-8 w-8 rounded-lg bg-success/10 flex items-center justify-center">
              <Shield className="h-4 w-4 text-success" />
            </div>
            Preferences
          </CardTitle>
          <CardDescription>Customize your application experience</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 pt-6">
          <div className="space-y-2">
            <Label htmlFor="dateFormat" className="text-xs uppercase tracking-wide font-semibold text-muted-foreground">
              Date Format
            </Label>
            <select
              id="dateFormat"
              className="w-full h-10 px-3 rounded-md border border-border bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-primary"
            >
              <option value="MM/DD/YYYY">MM/DD/YYYY</option>
              <option value="DD/MM/YYYY">DD/MM/YYYY</option>
              <option value="YYYY-MM-DD">YYYY-MM-DD</option>
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="currency" className="text-xs uppercase tracking-wide font-semibold text-muted-foreground">
              Currency
            </Label>
            <select
              id="currency"
              className="w-full h-10 px-3 rounded-md border border-border bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-primary"
            >
              <option value="EUR">EUR (€)</option>
              <option value="USD">USD ($)</option>
              <option value="GBP">GBP (£)</option>
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="timezone" className="text-xs uppercase tracking-wide font-semibold text-muted-foreground">
              Timezone
            </Label>
            <select
              id="timezone"
              className="w-full h-10 px-3 rounded-md border border-border bg-background text-foreground focus:ring-2 focus:ring-primary focus:border-primary"
            >
              <option value="UTC">UTC</option>
              <option value="America/New_York">Eastern Time</option>
              <option value="America/Los_Angeles">Pacific Time</option>
              <option value="Europe/London">London</option>
              <option value="Europe/Paris">Paris</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Save Button */}
      <div className="flex justify-end">
        <Button
          onClick={handleSave}
          size="lg"
          className="bg-primary hover:bg-primary/90 shadow-lg hover:shadow-xl transition-all"
        >
          Save Changes
        </Button>
      </div>
    </div>
  )
}
