import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import BillDetailsPage from './page';
import { apiClient } from '@/lib/api-client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

jest.mock('@/lib/api-client', () => ({
  apiClient: jest.fn(),
}));

jest.mock('next/navigation', () => ({
  useParams: () => ({ id: 'bill-123' }),
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

describe('BillDetailsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    queryClient.clear();
  });

  it('renders loading state initially', () => {
    (apiClient as jest.Mock).mockImplementation(() => new Promise(() => {}));
    const { container } = renderWithClient(<BillDetailsPage />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('polls and renders processing state', async () => {
    (apiClient as jest.Mock).mockResolvedValueOnce({
      data: { status: 'PROCESSING' }
    });

    renderWithClient(<BillDetailsPage />);

    await waitFor(() => {
      expect(screen.getByText('Status: PROCESSING')).toBeInTheDocument();
      expect(screen.getByText('Processing document...')).toBeInTheDocument();
    });
  });

  it('renders completed state with extracted data', async () => {
    (apiClient as jest.Mock).mockResolvedValue({
      data: { 
        status: 'COMPLETED',
        extracted_data: {
          utility_type: 'ELECTRICITY',
          consumption: 4500,
          unit: 'kWh'
        },
        emissions: {
          calculated_co2e_kg: 1000,
          scope: 'Scope 2'
        }
      }
    });

    renderWithClient(<BillDetailsPage />);

    await waitFor(() => {
      expect(screen.getByText('Status: COMPLETED')).toBeInTheDocument();
    });

    expect(screen.getByDisplayValue('ELECTRICITY')).toBeInTheDocument();
    expect(screen.getByDisplayValue('4500')).toBeInTheDocument();
    expect(screen.getByText('1000 kg CO2e')).toBeInTheDocument();
  });

  it('handles recalculate action', async () => {
    (apiClient as jest.Mock).mockResolvedValueOnce({
      data: { status: 'COMPLETED' }
    }).mockResolvedValueOnce({
      status: 'success'
    });

    renderWithClient(<BillDetailsPage />);

    await waitFor(() => {
      expect(screen.getByText('Status: COMPLETED')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /Recalculate/i }));

    await waitFor(() => {
      expect(apiClient).toHaveBeenCalledWith('/bills/bill-123/reprocess', { method: 'POST' });
    });
  });
});
