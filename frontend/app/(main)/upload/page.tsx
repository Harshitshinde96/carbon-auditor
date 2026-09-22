'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiClient } from '@/lib/api-client';
import { UploadDropzone } from '@/components/upload-dropzone';
import { useToast } from '@/hooks/use-toast';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export default function UploadPage() {
  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const router = useRouter();
  const { toast } = useToast();

  const handleUpload = async (file: File) => {
    setIsUploading(true);
    setUploadProgress(10); // Fake initial progress

    try {
      const formData = new FormData();
      formData.append('bill_file', file);

      // We can't easily track progress with native fetch in standard way without XMLHttpRequest
      // So we'll just fake a progress bar up to 90% then 100% on completion
      const interval = setInterval(() => {
        setUploadProgress((prev) => (prev < 90 ? prev + 10 : prev));
      }, 300);

      const response = await apiClient('/bills/upload', {
        method: 'POST',
        // Omit Content-Type so fetch sets it automatically with boundary for FormData
        body: formData,
      });

      clearInterval(interval);
      setUploadProgress(100);

      toast({
        title: 'Upload successful',
        description: response.data?.message || 'Bill accepted for processing.',
      });

      // Redirect to bill details
      setTimeout(() => {
        router.push(`/bills/${response.data?.bill_id}`);
      }, 500);

    } catch (error: any) {
      setIsUploading(false);
      setUploadProgress(0);
      throw error; // Re-throw to be caught by dropzone
    }
  };

  return (
    <div className="container mx-auto max-w-4xl py-12 px-4">
      <Card className="border-border bg-surface">
        <CardHeader>
          <CardTitle className="text-2xl font-bold text-ink">Upload Utility Bill</CardTitle>
          <CardDescription className="text-ink-secondary">
            Upload your electricity, gas, or water bill for automated OCR extraction and carbon emission calculation.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <UploadDropzone
            onUpload={handleUpload}
            isUploading={isUploading}
            uploadProgress={uploadProgress}
          />
        </CardContent>
      </Card>
    </div>
  );
}
