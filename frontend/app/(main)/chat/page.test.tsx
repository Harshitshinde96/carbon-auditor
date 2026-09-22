import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ChatPage from './page';
import { apiClient } from '@/lib/api-client';

jest.mock('@/lib/api-client', () => ({
  apiClient: jest.fn(),
}));

jest.mock('react-markdown', () => {
  return function MockReactMarkdown({ children }: { children: string }) {
    return <div>{children}</div>;
  };
});

describe('ChatPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (HTMLElement.prototype as any).scrollIntoView = jest.fn();
  });

  it('renders initial welcome message', () => {
    render(<ChatPage />);
    expect(screen.getByText(/I am your AI compliance assistant/i)).toBeInTheDocument();
  });

  it('sends message and renders AI response', async () => {
    (apiClient as jest.Mock).mockResolvedValueOnce({
      data: {
        answer: 'Yes, this is scope 3.',
        sources: ['Doc1.pdf'],
        confidence_score: 0.95
      }
    });

    render(<ChatPage />);
    
    const input = screen.getByPlaceholderText(/Ask a question/i);
    fireEvent.change(input, { target: { value: 'Is this scope 3?' } });
    
    fireEvent.click(screen.getByRole('button', { name: /Send/i }));
    
    // User message should appear immediately
    expect(screen.getByText('Is this scope 3?')).toBeInTheDocument();
    
    // Thinking state
    expect(screen.getByText('AI is thinking...')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('Yes, this is scope 3.')).toBeInTheDocument();
    });

    // Check sources
    expect(screen.getByText('Sources:')).toBeInTheDocument();
    expect(screen.getByText('Doc1.pdf')).toBeInTheDocument();
  });

  it('renders fallback warning for low confidence', async () => {
    (apiClient as jest.Mock).mockResolvedValueOnce({
      data: {
        answer: 'I am sorry, I can only answer questions related to your uploaded carbon bills.',
        confidence_score: 0.40
      }
    });

    render(<ChatPage />);
    
    fireEvent.change(screen.getByPlaceholderText(/Ask a question/i), { target: { value: 'What is the meaning of life?' } });
    fireEvent.click(screen.getByRole('button', { name: /Send/i }));

    await waitFor(() => {
      expect(screen.getByText('I am sorry, I can only answer questions related to your uploaded carbon bills.')).toBeInTheDocument();
    });

    expect(screen.getByText(/Low confidence response/i)).toBeInTheDocument();
  });
});
