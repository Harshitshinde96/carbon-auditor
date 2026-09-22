import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import SettingsPage from './page';
import { apiClient } from '@/lib/api-client';

jest.mock('@/lib/api-client', () => ({
  apiClient: jest.fn(),
}));

const mockToast = jest.fn();
jest.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: mockToast,
  }),
}));

describe('SettingsPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  it('renders company profile', async () => {
    (apiClient as jest.Mock).mockResolvedValueOnce({ data: {} });
    render(<SettingsPage />);
    
    await waitFor(() => {
      expect(screen.getByText('Acme Corp')).toBeInTheDocument();
    });
    
    expect(screen.getByText('admin@acme.com')).toBeInTheDocument();
  });

  it('allows setting currency once and then disables input', async () => {
    (apiClient as jest.Mock)
      .mockRejectedValueOnce(new Error('Not found')) // Initial fetch fails, fallback to empty
      .mockResolvedValueOnce({ status: 'success' }); // Save succeeds

    render(<SettingsPage />);
    
    let input: HTMLInputElement;
    await waitFor(() => {
      input = screen.getByLabelText(/Currency Code/i) as HTMLInputElement;
      expect(input).not.toBeDisabled();
    });

    // @ts-expect-error mock
    fireEvent.change(input, { target: { value: 'EUR' } });
    
    fireEvent.click(screen.getByRole('button', { name: /Save/i }));

    await waitFor(() => {
      expect(input).toBeDisabled();
      expect(screen.getByRole('button', { name: /Save/i })).toBeDisabled();
    });

    expect(mockToast).toHaveBeenCalledWith(expect.objectContaining({ title: 'Settings saved' }));
  });

  it('loads existing currency and disables input', async () => {
    (apiClient as jest.Mock).mockResolvedValueOnce({ data: { currency: 'GBP' } });

    render(<SettingsPage />);
    
    await waitFor(() => {
      const input = screen.getByLabelText(/Currency Code/i) as HTMLInputElement;
      expect(input).toBeDisabled();
      expect(input).toHaveValue('GBP');
      expect(screen.getByRole('button', { name: /Save/i })).toBeDisabled();
    });
  });
});
