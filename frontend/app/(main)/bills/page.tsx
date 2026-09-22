'use client';

import { useQuery, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/lib/api-client';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { useToast } from '@/hooks/use-toast';
import { Trash2 } from 'lucide-react';
import Link from 'next/link';

export default function BillsPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ['bills-list'],
    queryFn: async () => {
      const response = await apiClient('/bills');
      return response.data;
    },
  });

  const handleDelete = async (billId: string) => {
    if (!confirm('Are you sure you want to delete this bill? This action cannot be undone.')) return;
    try {
      await apiClient(`/bills/${billId}`, {
        method: 'DELETE',
      });
      toast({ title: 'Bill Deleted', description: 'The bill and its document have been removed.' });
      queryClient.invalidateQueries({ queryKey: ['bills-list'] });
    } catch (e: any) {
      toast({ title: 'Error', description: e.message || 'Failed to delete bill.', variant: 'destructive' });
    }
  };

  if (isLoading) {
    return (
      <div className="container mx-auto max-w-5xl py-8 px-4">
        <Skeleton className="h-[400px] w-full" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto max-w-5xl py-8 px-4">
        <p className="text-red-500">Failed to load bills: {(error as any).message}</p>
      </div>
    );
  }

  return (
    <div className="container mx-auto max-w-5xl py-8 px-4 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold text-ink">Your Bills</h1>
        <Link href="/upload" className="px-4 py-2 bg-ink text-background rounded-md text-sm font-medium hover:opacity-90">
          Upload New
        </Link>
      </div>

      <Card className="border-border bg-surface">
        <CardHeader>
          <CardTitle>Processing History</CardTitle>
          <CardDescription>All your uploaded utility bills and their current processing status.</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow className="border-border hover:bg-transparent">
                <TableHead className="text-ink">Date</TableHead>
                <TableHead className="text-ink">Filename</TableHead>
                <TableHead className="text-ink">Status</TableHead>
                <TableHead className="text-ink text-right">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data?.items?.map((bill: any) => (
                <TableRow key={bill.bill_id} className="border-border hover:bg-background">
                  <TableCell className="font-medium text-ink">
                    {new Date(bill.uploaded_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell className="text-ink-secondary">{bill.filename || 'Unknown'}</TableCell>
                  <TableCell>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      bill.status === 'COMPLETED' ? 'bg-green-100 text-green-800' :
                      bill.status === 'FAILED' ? 'bg-red-100 text-red-800' :
                      'bg-blue-100 text-blue-800'
                    }`}>
                      {bill.status}
                    </span>
                  </TableCell>
                  <TableCell className="text-right space-x-2">
                    <Link href={`/bills/${bill.bill_id}`} className="text-ink font-semibold hover:underline text-sm mr-2">
                      View Details
                    </Link>
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      onClick={() => handleDelete(bill.bill_id)}
                      title="Delete Bill"
                    >
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
              {!data?.items?.length && (
                <TableRow>
                  <TableCell colSpan={4} className="text-center py-8 text-ink-secondary">
                    No bills uploaded yet.
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
