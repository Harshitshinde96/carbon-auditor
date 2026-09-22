'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useParams } from 'next/navigation';
import { apiClient } from '@/lib/api-client';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { useToast } from '@/hooks/use-toast';
import { Loader2 } from 'lucide-react';

export default function BillDetailsPage() {
  const params = useParams();
  const billId = params.id as string;
  const { toast } = useToast();
  
  const [isReprocessing, setIsReprocessing] = useState(false);

  const fetchBill = async () => {
    const response = await apiClient(`/bills/${billId}`);
    return response.data;
  };

  const { data: bill, isLoading, error, refetch } = useQuery({
    queryKey: ['bill', billId],
    queryFn: fetchBill,
    refetchInterval: (query) => {
      const status = query.state?.data?.status;
      // Poll every 3 seconds if status is PENDING or PROCESSING
      return status === 'PENDING' || status === 'PROCESSING' ? 3000 : false;
    },
  });

  const handleRecalculate = async () => {
    setIsReprocessing(true);
    try {
      await apiClient(`/bills/${billId}/reprocess`, {
        method: 'POST',
      });
      toast({ title: 'Recalculating', description: 'Bill is being reprocessed.' });
      refetch();
    } catch (e: any) {
      toast({ title: 'Error', description: e.message || 'Failed to reprocess bill.', variant: 'destructive' });
    } finally {
      setIsReprocessing(false);
    }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto max-w-5xl py-8 px-4 space-y-6">
        <Skeleton className="h-10 w-1/3" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Skeleton className="h-[500px]" />
          <Skeleton className="h-[500px]" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto max-w-5xl py-8 px-4">
        <Card className="border-ink bg-surface/10">
          <CardHeader>
            <CardTitle className="text-ink">Error loading bill</CardTitle>
          </CardHeader>
          <CardContent>
            <p>{error.message}</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const isProcessing = bill?.status === 'PENDING' || bill?.status === 'PROCESSING';
  const isFailed = bill?.status === 'FAILED' || bill?.status === 'FAILED_OCR_QUALITY';

  return (
    <div className="container mx-auto max-w-6xl py-8 px-4 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-ink">Bill Details</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium px-3 py-1 bg-surface border border-border rounded-full">
            Status: {bill?.status}
          </span>
          <Button 
            onClick={handleRecalculate} 
            disabled={isProcessing || isReprocessing}
          >
            {isReprocessing ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
            {isFailed ? 'Retry Processing' : 'Recalculate'}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Document Viewer (Stubbed for now since we just have S3 keys in a real app) */}
        <Card className="border-border bg-surface h-[600px] flex flex-col">
          <CardHeader>
            <CardTitle>Document Viewer</CardTitle>
          </CardHeader>
          <CardContent className="flex-1 bg-background border rounded-md m-4 flex items-center justify-center text-ink-secondary">
            {isProcessing ? (
              <div className="flex flex-col items-center">
                <Loader2 className="w-8 h-8 animate-spin mb-4" />
                <p>Processing document...</p>
              </div>
            ) : bill?.s3_key ? (
              <iframe 
                src={`/api/v1/bills/${billId}/file`} 
                className="w-full h-full rounded-md" 
                title="Document Preview" 
              />
            ) : (
              <p>Document preview available here</p>
            )}
          </CardContent>
        </Card>

        {/* Extracted Data Form */}
        <Card className="border-border bg-surface flex flex-col">
          <CardHeader>
            <CardTitle>Extracted Data</CardTitle>
            <CardDescription>Verify and edit the extracted carbon values before final calculation.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 flex-1">
            {isProcessing ? (
              <div className="h-full flex items-center justify-center">
                <p className="text-ink-secondary">Waiting for OCR and AI extraction...</p>
              </div>
            ) : isFailed ? (
              <div className="p-4 border border-ink bg-surface/10 rounded-md">
                <p className="text-ink font-semibold">Processing Failed</p>
                <p className="text-sm">{bill?.error_message || 'Could not extract data from the document.'}</p>
              </div>
            ) : (
              <form className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-medium text-ink">Utility Type</label>
                  <Input defaultValue={bill?.extracted_data?.utility_type || ''} readOnly className="bg-background" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-ink">Period Start</label>
                    <Input defaultValue={bill?.extracted_data?.billing_period_start || ''} readOnly className="bg-background" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-ink">Period End</label>
                    <Input defaultValue={bill?.extracted_data?.billing_period_end || ''} readOnly className="bg-background" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-ink">Consumption Value</label>
                    <Input defaultValue={bill?.extracted_data?.consumption || ''} readOnly className="bg-background" />
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium text-ink">Unit</label>
                    <Input defaultValue={bill?.extracted_data?.unit || ''} readOnly className="bg-background" />
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-medium text-ink">Total Amount ($)</label>
                  <Input defaultValue={bill?.extracted_data?.cost || ''} readOnly className="bg-background" />
                </div>

                <div className="mt-8 pt-4 border-t border-border">
                  <h3 className="text-lg font-bold text-ink mb-2">Calculated Emissions</h3>
                  {bill?.emissions ? (
                    <div className="p-4 bg-background border border-border rounded-md">
                      <p className="text-2xl font-bold text-ink">{bill.emissions.calculated_co2e_kg} kg CO2e</p>
                      <p className="text-sm text-ink-secondary mt-1">Scope: {bill.emissions.scope}</p>
                    </div>
                  ) : (
                    <p className="text-sm text-ink-secondary">Not calculated yet.</p>
                  )}
                </div>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
