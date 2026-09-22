'use client';

import { useState, useCallback, useRef } from 'react';
import { UploadCloud, File, AlertCircle, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';

interface UploadDropzoneProps {
  onUpload: (file: File) => Promise<void>;
  isUploading: boolean;
  uploadProgress: number;
}

const ALLOWED_TYPES = [
  'application/pdf',
  'image/png',
  'image/jpeg',
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', // xlsx
  'text/csv',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document', // docx
  'application/vnd.openxmlformats-officedocument.presentationml.presentation', // pptx
];
const MAX_SIZE_MB = 15;
const MAX_SIZE_BYTES = MAX_SIZE_MB * 1024 * 1024;

export function UploadDropzone({ onUpload, isUploading, uploadProgress }: UploadDropzoneProps) {
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }, []);

  const validateAndSetFile = (selectedFile: File) => {
    setError(null);
    if (!ALLOWED_TYPES.includes(selectedFile.type)) {
      setError(`Unsupported file type: ${selectedFile.name}. Must be PDF, PNG, JPEG, XLSX, CSV, DOCX, or PPTX.`);
      return false;
    }
    if (selectedFile.size > MAX_SIZE_BYTES) {
      setError(`File too large: ${selectedFile.name}. Max allowed size is 15MB.`);
      return false;
    }
    setFile(selectedFile);
    return true;
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const onButtonClick = () => {
    inputRef.current?.click();
  };

  const handleUpload = async () => {
    if (!file) return;
    try {
      await onUpload(file);
    } catch (e: any) {
      setError(e.message || 'Upload failed');
    }
  };

  const clearFile = () => {
    setFile(null);
    setError(null);
    if (inputRef.current) {
      inputRef.current.value = '';
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto mt-8">
      <div 
        className={`relative border-2 border-dashed rounded-lg p-10 flex flex-col items-center justify-center transition-colors
          ${dragActive ? 'border-ink bg-surface' : 'border-border hover:border-ink hover:bg-surface/50'}
          ${isUploading ? 'opacity-50 pointer-events-none' : ''}
          ${error ? 'border-ink bg-surface/10' : ''}
        `}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          ref={inputRef}
          type="file"
          className="hidden"
          onChange={handleChange}
          accept=".pdf,.png,.jpg,.jpeg,.xlsx,.csv,.docx,.pptx"
          disabled={isUploading}
        />

        {!file ? (
          <>
            <UploadCloud className="w-12 h-12 text-ink-secondary mb-4" />
            <h3 className="text-xl font-bold text-ink mb-2">Click or drag file to this area to upload</h3>
            <p className="text-sm text-ink-secondary mb-6 text-center">
              Support for a single PDF, PNG, JPEG, XLSX, CSV, DOCX, or PPTX upload. <br />
              Maximum file size: {MAX_SIZE_MB}MB.
            </p>
            <Button onClick={onButtonClick} variant="outline" type="button">
              Select File
            </Button>
          </>
        ) : (
          <div className="w-full">
            <div className="flex items-center justify-between p-4 border border-border rounded-md bg-background mb-4">
              <div className="flex items-center gap-3 overflow-hidden">
                <File className="w-8 h-8 text-ink-secondary shrink-0" />
                <div className="truncate">
                  <p className="text-sm font-medium text-ink truncate">{file.name}</p>
                  <p className="text-xs text-ink-secondary">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                </div>
              </div>
              {!isUploading && (
                <button onClick={clearFile} className="p-2 hover:bg-surface rounded-full transition-colors shrink-0" aria-label="Remove file">
                  <X className="w-4 h-4 text-ink-secondary" />
                </button>
              )}
            </div>

            {isUploading && (
              <div className="w-full space-y-2 mb-4">
                <div className="flex justify-between text-xs font-medium text-ink">
                  <span>Uploading...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <Progress value={uploadProgress} className="h-2 w-full" />
              </div>
            )}

            {!isUploading && (
              <Button onClick={handleUpload} className="w-full">
                Upload and Process
              </Button>
            )}
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 p-4 border border-ink bg-surface flex items-start gap-3 rounded-md" role="alert">
          <AlertCircle className="w-5 h-5 text-ink shrink-0 mt-0.5" />
          <p className="text-sm font-medium text-ink">{error}</p>
        </div>
      )}
    </div>
  );
}
