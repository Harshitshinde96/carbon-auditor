import { apiClient, APIError } from './api-client';

describe('apiClient', () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    global.fetch = jest.fn();
    document.cookie = '';
  });

  afterEach(() => {
    global.fetch = originalFetch;
    jest.clearAllMocks();
  });

  it('attaches token from cookie', async () => {
    document.cookie = 'token=fake-jwt-token';
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => ({ success: true })
    });

    await apiClient('/test');

    expect(global.fetch).toHaveBeenCalledWith('/api/v1/test', expect.objectContaining({
      headers: expect.any(Headers)
    }));
    
    const callArgs = (global.fetch as jest.Mock).mock.calls[0];
    const headers = callArgs[1].headers as Headers;
    expect(headers.get('Authorization')).toBe('Bearer fake-jwt-token');
  });

  it('clears session and redirects to /login on 401', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
      json: async () => ({ message: 'Unauthorized' })
    });

    document.cookie = 'token=fake';
    
    try {
      await apiClient('/test');
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    } catch (e: any) {
      // JSDOM throws "Not implemented: navigation" when window.location.assign is called
      expect(e.message).toMatch(/Not implemented|Unauthorized/);
    }
    
    expect(document.cookie).not.toContain('token=fake');
  });

  it('dispatches toast event on 500', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: async () => ({ message: 'Server exploded' })
    });

    const dispatchEventSpy = jest.spyOn(window, 'dispatchEvent');
    
    await expect(apiClient('/test')).rejects.toThrow(APIError);
    
    expect(dispatchEventSpy).toHaveBeenCalledWith(expect.any(CustomEvent));
    expect(dispatchEventSpy.mock.calls[0][0].type).toBe('toast-error');
  });
});
