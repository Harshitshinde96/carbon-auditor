import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ReportsPage from './page';
import { apiClient } from '@/lib/api-client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

jest.mock('@/lib/api-client', () => ({
  apiClient: jest.fn(),
}));

const mockToast = jest.fn();
jest.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: mockToast,
  }),
}));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
    },
  },
});

const renderWithClient = (ui: React.ReactElement) => {
  return render(
    <QueryClientProvider client={queryClient}>
      {ui}
    </QueryClientProvider>
  );
};

describe('ReportsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    queryClient.clear();
  });

  it('renders correctly', () => {
    renderWithClient(<ReportsPage />);
    expect(screen.getByText('Generate Report', { selector: 'h1' })).toBeInTheDocument();
  });

  it('validates start < end date', async () => {
    renderWithClient(<ReportsPage />);
    
    fireEvent.change(screen.getByLabelText(/Period Start/i), { target: { value: '2026-06-30' } });
    fireEvent.change(screen.getByLabelText(/Period End/i), { target: { value: '2026-01-01' } });
    
    fireEvent.click(screen.getByRole('button', { name: /Generate Report/i }));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/strictly before/i);
    });
    
    expect(apiClient).not.toHaveBeenCalled();
  });

  it('validates 366 day rule', async () => {
    renderWithClient(<ReportsPage />);
    
    fireEvent.change(screen.getByLabelText(/Period Start/i), { target: { value: '2025-01-01' } });
    fireEvent.change(screen.getByLabelText(/Period End/i), { target: { value: '2026-01-05' } });
    
    fireEvent.click(screen.getByRole('button', { name: /Generate Report/i }));

    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/cannot exceed 366 days/i);
    });
    
    expect(apiClient).not.toHaveBeenCalled();
  });

  it('handles generation trigger and polling', async () => {
    jest.useFakeTimers();
    const mockApiClient = apiClient as jest.Mock;
    
    // 1st call: generate request
    mockApiClient.mockResolvedValueOnce({
      data: { report_id: 'rep-123' }
    });
    
    // 2nd call: poll status processing
    mockApiClient.mockResolvedValueOnce({
      data: { status: 'PROCESSING' }
    });
    
    // 3rd call: poll status completed
    mockApiClient.mockResolvedValueOnce({
      data: { status: 'COMPLETED', download_url: 'https://example.com/report.pdf' }
    });

    renderWithClient(<ReportsPage />);
    
    fireEvent.change(screen.getByLabelText(/Period Start/i), { target: { value: '2026-01-01' } });
    fireEvent.change(screen.getByLabelText(/Period End/i), { target: { value: '2026-06-30' } });
    
    fireEvent.click(screen.getByRole('button', { name: /Generate Report/i }));

    // Wait for polling UI
    await waitFor(() => {
      expect(screen.getByText('Generating...')).toBeInTheDocument();
    });
    
    expect(mockApiClient).toHaveBeenNthCalledWith(1, '/reports/generate', expect.objectContaining({
      method: 'POST'
    }));

    // Advance timer to trigger poll
    jest.advanceTimersByTime(3000);
    
    // Advance again to trigger second poll
    jest.advanceTimersByTime(3000);

    // Next tick it should be completed
    await waitFor(() => {
      expect(screen.getByText('Report Ready')).toBeInTheDocument();
    });

    const downloadLink = screen.getByRole('button', { name: /Download Report/i }).closest('a');
    expect(downloadLink).toHaveAttribute('href', 'https://example.com/report.pdf');
    
    jest.useRealTimers();
  });
});
