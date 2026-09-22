'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { Download, FileText, Loader2 } from 'lucide-react';

export default function ReportsPage() {
  const [periodStart, setPeriodStart] = useState('');
  const [periodEnd, setPeriodEnd] = useState('');
  const [reportId, setReportId] = useState<string | null>(null);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();

  const validateDates = () => {
    setError(null);
    if (!periodStart || !periodEnd) {
      setError('Please select both start and end dates.');
      return false;
    }

    const start = new Date(periodStart);
    const end = new Date(periodEnd);

    if (start >= end) {
      setError('Start date must be strictly before end date.');
      return false;
    }

    const diffTime = Math.abs(end.getTime() - start.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)); 
    
    if (diffDays > 366) {
      setError('Report period cannot exceed 366 days.');
      return false;
    }

    return true;
  };

  const handleGenerate = async () => {
    if (!validateDates()) return;
    
    setIsGenerating(true);
    try {
      const response = await apiClient('/reports/generate', {
        method: 'POST',
        body: JSON.stringify({
          period_start: periodStart,
          period_end: periodEnd
        }),
      });
      setReportId(response.report_id);
      toast({ title: 'Report Generation Started', description: 'Your report is being generated.' });
    } catch (e: any) {
      setError(e.data?.message || 'Failed to start report generation.');
    } finally {
      setIsGenerating(false);
    }
  };

  const fetchReportStatus = async () => {
    if (!reportId) return null;
    const response = await apiClient(`/reports/${reportId}`);
    return response;
  };

  const { data: reportData } = useQuery({
    queryKey: ['report', reportId],
    queryFn: fetchReportStatus,
    enabled: !!reportId,
    refetchInterval: (query) => {
      const status = query.state?.data?.status;
      return status !== 'COMPLETED' && status !== 'FAILED' ? 3000 : false;
    },
  });

  const isPolling = reportData && reportData.status !== 'COMPLETED' && reportData.status !== 'FAILED';

  return (
    <div className="container mx-auto max-w-4xl py-8 px-4 space-y-6">
      <h1 className="text-3xl font-bold text-ink">Generate Report</h1>
      <p className="text-ink-secondary">Generate an AI-powered sustainability report for a specific period.</p>
      
      <Card className="border-border bg-surface">
        <CardHeader>
          <CardTitle>Report Parameters</CardTitle>
          <CardDescription>Select a date range of up to 366 days.</CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="mb-4 p-3 bg-surface/10 border border-ink text-ink rounded-md" role="alert">
              {error}
            </div>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div className="space-y-2">
              <label className="text-sm font-medium text-ink">Period Start</label>
              <Input 
                type="date" 
                value={periodStart}
                onChange={(e) => setPeriodStart(e.target.value)}
                disabled={isGenerating || isPolling}
                aria-label="Period Start"
              />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-ink">Period End</label>
              <Input 
                type="date" 
                value={periodEnd}
                onChange={(e) => setPeriodEnd(e.target.value)}
                disabled={isGenerating || isPolling}
                aria-label="Period End"
              />
            </div>
          </div>
          <Button 
            onClick={handleGenerate} 
            disabled={isGenerating || isPolling || !periodStart || !periodEnd}
          >
            {isGenerating ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <FileText className="w-4 h-4 mr-2" />}
            Generate Report
          </Button>
        </CardContent>
      </Card>

      {reportId && reportData && (
        <Card className="border-border bg-surface">
          <CardHeader>
            <CardTitle>Report Status</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center justify-center p-8 space-y-4 text-center">
            {reportData.status === 'COMPLETED' ? (
              <>
                <FileText className="w-16 h-16 text-ink" />
                <h3 className="text-xl font-bold text-ink">Report Ready</h3>
                <p className="text-ink-secondary">Your sustainability report has been generated successfully.</p>
                <a 
                  href={reportData.pdf_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="mt-4"
                >
                  <Button size="lg" aria-label="Download Report">
                    <Download className="w-5 h-5 mr-2" />
                    Download PDF
                  </Button>
                </a>
              </>
            ) : reportData.status === 'FAILED' ? (
              <>
                <h3 className="text-xl font-bold text-ink">Generation Failed</h3>
                <p className="text-ink-secondary">{reportData.error_message || 'An unknown error occurred.'}</p>
                <Button onClick={() => setReportId(null)} variant="outline" className="mt-4">
                  Try Again
                </Button>
              </>
            ) : (
              <>
                <Loader2 className="w-16 h-16 animate-spin text-ink-secondary" />
                <h3 className="text-xl font-bold text-ink">Generating...</h3>
                <p className="text-ink-secondary">This might take a minute as AI analyzes your data.</p>
              </>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
