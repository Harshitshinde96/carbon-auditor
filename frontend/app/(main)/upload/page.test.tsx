import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import UploadPage from './page';
import { apiClient } from '@/lib/api-client';

// Mock the apiClient
jest.mock('@/lib/api-client', () => ({
  apiClient: jest.fn(),
}));

const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
}));

const mockToast = jest.fn();
jest.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: mockToast,
  }),
}));

describe('UploadPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders upload area', () => {
    render(<UploadPage />);
    expect(screen.getByText('Upload Utility Bill', { selector: 'div' })).toBeInTheDocument();
    expect(screen.getByText(/Click or drag file to this area to upload/i)).toBeInTheDocument();
  });

  it('validates file size (15MB limit)', async () => {
    const { container } = render(<UploadPage />);
    
    const file = new File(['x'.repeat(16 * 1024 * 1024)], 'huge.pdf', { type: 'application/pdf' });
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    
    // Using fireEvent.change to simulate file selection
    fireEvent.change(input, { target: { files: [file] } });
    
    expect(screen.getByRole('alert')).toHaveTextContent(/File too large/i);
    expect(apiClient).not.toHaveBeenCalled();
  });

  it('validates file type', async () => {
    const { container } = render(<UploadPage />);
    
    const file = new File(['content'], 'test.txt', { type: 'text/plain' });
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    
    fireEvent.change(input, { target: { files: [file] } });
    
    expect(screen.getByRole('alert')).toHaveTextContent(/Unsupported file type/i);
  });

  it('handles successful upload and redirects to bill details', async () => {
    const mockApiClient = apiClient as jest.Mock;
    mockApiClient.mockResolvedValueOnce({
      status: 'success',
      data: { bill_id: 'bill-123', message: 'Accepted' },
    });
    
    jest.useFakeTimers();

    const { container } = render(<UploadPage />);
    
    const file = new File(['fake-pdf-content'], 'test.pdf', { type: 'application/pdf' });
    const input = container.querySelector('input[type="file"]') as HTMLInputElement;
    
    fireEvent.change(input, { target: { files: [file] } });
    
    // File details should appear
    expect(screen.getByText('test.pdf')).toBeInTheDocument();
    
    // Click upload
    fireEvent.click(screen.getByRole('button', { name: /Upload and Process/i }));
    
    await waitFor(() => {
      expect(mockApiClient).toHaveBeenCalledWith('/bills/upload', expect.objectContaining({
        method: 'POST',
        body: expect.any(FormData),
      }));
    });

    expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({ title: 'Upload successful' }));
    
    // Advance timers for the setTimeout redirect
    jest.advanceTimersByTime(500);
    
    expect(mockPush).toHaveBeenCalledWith('/bills/bill-123');
    
    jest.useRealTimers();
  });
});
