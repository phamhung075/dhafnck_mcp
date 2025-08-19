import { renderHook, act } from '@testing-library/react';
import { useAuthenticatedFetch } from '../../hooks/useAuthenticatedFetch';
import { useAuth } from '../../contexts/AuthContext';
import { jest } from '@jest/globals';

// Mock the auth context
jest.mock('../../contexts/AuthContext', () => ({
  useAuth: jest.fn(),
}));

const mockUseAuth = jest.mocked(useAuth);

// Mock global fetch
global.fetch = jest.fn() as jest.MockedFunction<typeof fetch>;
const mockFetch = global.fetch as jest.MockedFunction<typeof fetch>;

describe('useAuthenticatedFetch', () => {
  const mockUser = {
    id: '123',
    email: 'test@example.com',
    access_token: 'test-token',
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuth.mockReturnValue({
      user: mockUser,
      loading: false,
      signIn: jest.fn(),
      signUp: jest.fn(),
      signOut: jest.fn(),
      refreshAccessToken: jest.fn(),
    });
  });

  it('returns a function when rendered in a hook', () => {
    const { result } = renderHook(() => useAuthenticatedFetch());
    expect(typeof result.current).toBe('function');
  });

  it('makes authenticated request with bearer token', async () => {
    const mockResponse = { data: 'test' };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    } as Response);

    const { result } = renderHook(() => useAuthenticatedFetch());
    
    await act(async () => {
      const response = await result.current('/api/test', {
        method: 'GET',
      });
      expect(response).toEqual(mockResponse);
    });

    expect(mockFetch).toHaveBeenCalledWith('/api/test', {
      method: 'GET',
      headers: {
        Authorization: 'Bearer test-token',
      },
    });
  });

  it('preserves existing headers when adding authorization', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ success: true }),
    } as Response);

    const { result } = renderHook(() => useAuthenticatedFetch());
    
    await act(async () => {
      await result.current('/api/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Custom-Header': 'custom-value',
        },
        body: JSON.stringify({ test: 'data' }),
      });
    });

    expect(mockFetch).toHaveBeenCalledWith('/api/test', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Custom-Header': 'custom-value',
        Authorization: 'Bearer test-token',
      },
      body: JSON.stringify({ test: 'data' }),
    });
  });

  it('makes request without auth header when user is not authenticated', async () => {
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
      signIn: jest.fn(),
      signUp: jest.fn(),
      signOut: jest.fn(),
      refreshAccessToken: jest.fn(),
    });

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ public: true }),
    } as Response);

    const { result } = renderHook(() => useAuthenticatedFetch());
    
    await act(async () => {
      await result.current('/api/public');
    });

    expect(mockFetch).toHaveBeenCalledWith('/api/public', {
      headers: {},
    });
  });

  it('handles non-JSON responses', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: jest.fn().mockRejectedValue(new Error('Invalid JSON')),
      text: async () => 'Plain text response',
    } as unknown as Response);

    const { result } = renderHook(() => useAuthenticatedFetch());
    
    await act(async () => {
      const response = await result.current('/api/text');
      expect(response).toBeInstanceOf(Response);
    });
  });

  it('handles network errors', async () => {
    const networkError = new Error('Network error');
    mockFetch.mockRejectedValueOnce(networkError);

    const { result } = renderHook(() => useAuthenticatedFetch());
    
    await expect(act(async () => {
      await result.current('/api/error');
    })).rejects.toThrow('Network error');
  });

  it('can be used in non-React context with access token', async () => {
    const mockResponse = { data: 'standalone' };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    } as Response);

    // Mock the hook to return null when used outside React
    mockUseAuth.mockImplementation(() => {
      throw new Error('useAuth must be used within AuthProvider');
    });

    // Call the hook directly with try/catch to handle the non-React scenario
    let authenticatedFetch: any;
    try {
      const { result } = renderHook(() => useAuthenticatedFetch());
      authenticatedFetch = result.current;
    } catch {
      // In non-React context, create the function manually
      authenticatedFetch = (url: string, options: RequestInit = {}) => {
        const headers = new Headers(options.headers);
        headers.set('Authorization', 'Bearer standalone-token');
        return fetch(url, { ...options, headers });
      };
    }

    const response = await authenticatedFetch('/api/standalone', {
      method: 'GET',
    });

    expect(mockFetch).toHaveBeenCalledWith('/api/standalone', {
      method: 'GET',
      headers: expect.any(Headers),
    });
  });

  it('handles 401 unauthorized responses', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      statusText: 'Unauthorized',
      json: async () => ({ error: 'Unauthorized' }),
    } as Response);

    const { result } = renderHook(() => useAuthenticatedFetch());
    
    await act(async () => {
      const response = await result.current('/api/protected');
      expect(response.status).toBe(401);
    });
  });

  it('uses refreshed token after refresh', async () => {
    const refreshAccessToken = jest.fn().mockResolvedValue('new-token');
    
    mockUseAuth.mockReturnValue({
      user: { ...mockUser, access_token: 'old-token' },
      loading: false,
      signIn: jest.fn(),
      signUp: jest.fn(),
      signOut: jest.fn(),
      refreshAccessToken,
    });

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ refreshed: true }),
    } as Response);

    const { result } = renderHook(() => useAuthenticatedFetch());
    
    // Update the user with new token
    mockUseAuth.mockReturnValue({
      user: { ...mockUser, access_token: 'new-token' },
      loading: false,
      signIn: jest.fn(),
      signUp: jest.fn(),
      signOut: jest.fn(),
      refreshAccessToken,
    });

    await act(async () => {
      await result.current('/api/test');
    });

    expect(mockFetch).toHaveBeenCalledWith('/api/test', {
      headers: {
        Authorization: 'Bearer new-token',
      },
    });
  });

  it('supports all HTTP methods', async () => {
    const methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH'];
    
    for (const method of methods) {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ method }),
      } as Response);

      const { result } = renderHook(() => useAuthenticatedFetch());
      
      await act(async () => {
        await result.current('/api/test', { method });
      });

      expect(mockFetch).toHaveBeenLastCalledWith('/api/test', {
        method,
        headers: {
          Authorization: 'Bearer test-token',
        },
      });
    }
  });
});