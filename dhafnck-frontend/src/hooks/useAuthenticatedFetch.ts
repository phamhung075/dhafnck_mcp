import { useCallback } from 'react';
import { useAuth } from './useAuth';

interface FetchOptions extends RequestInit {
  skipAuth?: boolean;
}

// Standalone function for use outside of React components
export const authenticatedFetch = async (url: string, options: RequestInit = {}): Promise<Response> => {
  // Get tokens from localStorage or cookies
  const tokensStr = localStorage.getItem('auth_tokens');
  const tokens = tokensStr ? JSON.parse(tokensStr) : null;
  
  // Add authorization header if token exists
  const fetchOptions = { ...options };
  if (tokens?.access_token) {
    fetchOptions.headers = {
      ...fetchOptions.headers,
      'Authorization': `Bearer ${tokens.access_token}`,
    };
  }
  
  const response = await fetch(url, fetchOptions);
  
  // If unauthorized, the hook version will handle refresh
  // For the standalone version, just return the response
  return response;
};

export const useAuthenticatedFetch = () => {
  const { tokens, refreshToken, logout } = useAuth();

  const authenticatedFetch = useCallback(
    async (url: string, options: FetchOptions = {}): Promise<Response> => {
      const { skipAuth = false, ...fetchOptions } = options;

      // Add authorization header if not skipping auth
      if (!skipAuth && tokens?.access_token) {
        fetchOptions.headers = {
          ...fetchOptions.headers,
          'Authorization': `Bearer ${tokens.access_token}`,
        };
      }

      let response = await fetch(url, fetchOptions);

      // If unauthorized, try to refresh token
      if (response.status === 401 && !skipAuth && tokens?.refresh_token) {
        try {
          await refreshToken();
          
          // Retry the request with new token
          if (tokens?.access_token) {
            fetchOptions.headers = {
              ...fetchOptions.headers,
              'Authorization': `Bearer ${tokens.access_token}`,
            };
            response = await fetch(url, fetchOptions);
          }
        } catch (error) {
          // Refresh failed, logout user
          logout();
          throw new Error('Session expired. Please login again.');
        }
      }

      return response;
    },
    [tokens, refreshToken, logout]
  );

  return authenticatedFetch;
};