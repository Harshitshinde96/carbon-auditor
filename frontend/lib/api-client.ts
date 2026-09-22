export class APIError extends Error {
  status: number;
  data: unknown;

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  constructor(status: number, data: any) {
    // eslint-disable-next-line @typescript-eslint/no-unsafe-member-access
    super(data?.message || 'An error occurred');
    this.status = status;
    this.data = data;
  }
}

export async function apiClient(endpoint: string, options: RequestInit = {}) {
  const isServer = typeof window === 'undefined';
  
  const headers = new Headers(options.headers || {});
  
  // Basic content type
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
  const url = `${baseUrl}/api/v1${endpoint}`; // Bypass Next.js proxy to avoid 30s timeout on slow LLM calls

  try {
    const res = await fetch(url, {
      ...options,
      headers,
    });

    if (!res.ok) {
      if (res.status >= 500 && !isServer) {
        // Trigger generic toast event, components listen to this
        window.dispatchEvent(new CustomEvent('toast-error', { detail: { message: 'Internal server error' } }));
      }
      
      let data = null;
      try {
        data = await res.json();
      } catch {
        data = { message: res.statusText };
      }
      
      throw new APIError(res.status, data);
    }
    
    // For 204 No Content
    if (res.status === 204) {
      return null;
    }
    
    return res.json();
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }
    // Network errors
    if (!isServer) {
      window.dispatchEvent(new CustomEvent('toast-error', { detail: { message: 'Network error' } }));
    }
    throw error;
  }
}
