import { render, screen, waitFor } from '@testing-library/react';
import DashboardPage from './page';
import { apiClient } from '@/lib/api-client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

jest.mock('@/lib/api-client', () => ({
  apiClient: jest.fn(),
}));

// Recharts is notoriously hard to test in jsdom, so we mock it
jest.mock('recharts', () => {
  const OriginalRecharts = jest.requireActual('recharts');
  return {
    ...OriginalRecharts,
    ResponsiveContainer: ({ children }: any) => <div>{children}</div>,
    BarChart: ({ children }: any) => <div data-testid="mock-barchart">{children}</div>,
    Bar: () => <div data-testid="mock-bar" />,
  };
});

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

describe('DashboardPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    queryClient.clear();
  });

  it('renders loading state initially', () => {
    (apiClient as jest.Mock).mockImplementation(() => new Promise(() => {}));
    const { container } = renderWithClient(<DashboardPage />);
    expect(container.querySelector('.animate-pulse')).toBeInTheDocument();
  });

  it('renders stats and charts when data is available', async () => {
    (apiClient as jest.Mock).mockResolvedValue({
      data: {
        total_co2e_kg: 15050.2,
        breakdown: {
          'SCOPE_1': 2000.0,
          'SCOPE_2': 12050.2,
          'SCOPE_3': 1000.0
        }
      }
    });

    renderWithClient(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText('15,050.2 kg', { exact: false })).toBeInTheDocument();
    });

    expect(screen.getByText('2,000', { exact: false })).toBeInTheDocument();
    expect(screen.getByText('12,050.2', { exact: false })).toBeInTheDocument();
    expect(screen.getByText('7%', { exact: false })).toBeInTheDocument();
  });
});
