'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { Save, User, Building2, Globe } from 'lucide-react';
import { apiClient } from '@/lib/api-client';

export default function SettingsPage() {
  const [currency, setCurrency] = useState('USD');
  const [isCurrencySaved, setIsCurrencySaved] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    // In a real app, this would fetch from /settings
    // Since backend for settings isn't fully implemented in MVP, we use localStorage as fallback
    const fetchSettings = async () => {
      try {
        const response = await apiClient('/settings').catch(() => null);
        if (response?.data?.currency) {
          setCurrency(response.data.currency);
          setIsCurrencySaved(true);
        } else {
          const local = localStorage.getItem('ca_currency');
          if (local) {
            setCurrency(local);
            setIsCurrencySaved(true);
          }
        }
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchSettings();
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await apiClient('/settings', {
        method: 'POST',
        body: JSON.stringify({ currency })
      }).catch(() => {
        // Fallback to local storage if API fails
        localStorage.setItem('ca_currency', currency);
      });
      
      setIsCurrencySaved(true);
      toast({ title: 'Settings saved', description: 'Your preferences have been updated.' });
    } catch {
      toast({ title: 'Error', description: 'Failed to save settings.', variant: 'destructive' });
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto max-w-4xl py-8 px-4 flex justify-center">
        <div className="animate-pulse flex space-x-4">
          <div className="flex-1 space-y-6 py-1">
            <div className="h-4 bg-surface rounded w-3/4"></div>
            <div className="space-y-3">
              <div className="h-4 bg-surface rounded"></div>
              <div className="h-4 bg-surface rounded w-5/6"></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-4xl py-8 px-4 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-ink">Settings</h1>
        <p className="text-ink-secondary mt-2">Manage your company profile and preferences.</p>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1 space-y-4">
          <Card className="border-border bg-surface">
            <CardContent className="p-6">
              <div className="flex flex-col items-center text-center">
                <div className="w-24 h-24 bg-border rounded-full flex items-center justify-center mb-4">
                  <Building2 className="w-12 h-12 text-ink-secondary" />
                </div>
                <h3 className="text-lg font-bold text-ink">Acme Corp</h3>
                <p className="text-sm text-ink-secondary">Admin User</p>
                
                <div className="w-full mt-6 space-y-3">
                  <div className="flex items-center text-sm text-ink-secondary">
                    <User className="w-4 h-4 mr-3" />
                    admin@acme.com
                  </div>
                  <div className="flex items-center text-sm text-ink-secondary">
                    <Globe className="w-4 h-4 mr-3" />
                    North America Region
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="md:col-span-2 space-y-6">
          <Card className="border-border bg-surface">
            <CardHeader>
              <CardTitle>Financial Preferences</CardTitle>
              <CardDescription>
                Set the base currency for your emission intensity calculations. 
                <strong className="text-ink block mt-1">Note: Currency can only be set once to maintain reporting consistency.</strong>
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2 max-w-sm">
                <label className="text-sm font-medium text-ink">Base Currency Code</label>
                <div className="flex space-x-2">
                  <Input 
                    value={currency} 
                    onChange={(e) => setCurrency(e.target.value.toUpperCase())}
                    maxLength={3}
                    placeholder="USD"
                    disabled={isCurrencySaved || isSaving}
                    aria-label="Currency Code"
                    className="uppercase"
                  />
                  <Button 
                    onClick={handleSave} 
                    disabled={isCurrencySaved || isSaving || currency.length !== 3}
                  >
                    <Save className="w-4 h-4 mr-2" />
                    Save
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border bg-surface">
            <CardHeader>
              <CardTitle>Reporting Configuration</CardTitle>
              <CardDescription>Configure calculation methodologies.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-ink">Scope 2 Methodology</label>
                <Input value="Location-based (Default)" disabled className="bg-background" />
                <p className="text-xs text-ink-secondary">Market-based overrides require Enterprise tier.</p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
