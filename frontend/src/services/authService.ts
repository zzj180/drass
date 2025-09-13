import { getApiUrl } from '../config/config';

interface LoginCredentials {
  email: string;
  password: string;
}

interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  created_at: string;
}

class AuthService {
  private readonly TOKEN_KEY = 'access_token';
  private readonly REFRESH_TOKEN_KEY = 'refresh_token';
  private readonly USER_KEY = 'current_user';

  // Store token in localStorage
  private setTokens(tokens: AuthTokens): void {
    localStorage.setItem(this.TOKEN_KEY, tokens.access_token);
    localStorage.setItem(this.REFRESH_TOKEN_KEY, tokens.refresh_token);

    // Set token expiry
    const expiresAt = new Date().getTime() + (tokens.expires_in * 1000);
    localStorage.setItem('token_expires_at', expiresAt.toString());
  }

  // Get stored token
  getAccessToken(): string | null {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY);
  }

  // Check if token is expired
  isTokenExpired(): boolean {
    const expiresAt = localStorage.getItem('token_expires_at');
    if (!expiresAt) return true;

    return new Date().getTime() > parseInt(expiresAt);
  }

  // Login
  async login(credentials: LoginCredentials): Promise<User> {
    const formData = new FormData();
    formData.append('username', credentials.email); // OAuth2 spec uses 'username'
    formData.append('password', credentials.password);

    const response = await fetch(`${getApiUrl('backendUrl')}/api/v1/auth/login`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const tokens: AuthTokens = await response.json();
    this.setTokens(tokens);

    // Get user info
    const user = await this.getCurrentUser();
    localStorage.setItem(this.USER_KEY, JSON.stringify(user));

    return user;
  }

  // Register
  async register(email: string, password: string, name: string): Promise<User> {
    const response = await fetch(`${getApiUrl('backendUrl')}/api/v1/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password, name }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    return response.json();
  }

  // Get current user
  async getCurrentUser(): Promise<User> {
    const token = this.getAccessToken();
    if (!token) {
      throw new Error('No authentication token');
    }

    const response = await fetch(`${getApiUrl('backendUrl')}/api/v1/auth/me`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to get user info');
    }

    return response.json();
  }

  // Refresh token
  async refreshToken(): Promise<void> {
    const refreshToken = this.getRefreshToken();
    if (!refreshToken) {
      throw new Error('No refresh token');
    }

    const response = await fetch(`${getApiUrl('backendUrl')}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      throw new Error('Failed to refresh token');
    }

    const tokens: AuthTokens = await response.json();
    this.setTokens(tokens);
  }

  // Logout
  async logout(): Promise<void> {
    const token = this.getAccessToken();

    // Call logout endpoint if token exists
    if (token) {
      try {
        await fetch(`${getApiUrl('backendUrl')}/api/v1/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
      } catch (error) {
        console.error('Logout API call failed:', error);
      }
    }

    // Clear local storage
    localStorage.removeItem(this.TOKEN_KEY);
    localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    localStorage.removeItem(this.USER_KEY);
    localStorage.removeItem('token_expires_at');
  }

  // Get stored user
  getStoredUser(): User | null {
    const userStr = localStorage.getItem(this.USER_KEY);
    if (!userStr) return null;

    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  }

  // Check if user is authenticated
  isAuthenticated(): boolean {
    return !!this.getAccessToken() && !this.isTokenExpired();
  }

  // Get authorization headers
  getAuthHeaders(): HeadersInit {
    const token = this.getAccessToken();
    if (!token) {
      return {};
    }

    return {
      'Authorization': `Bearer ${token}`,
    };
  }
}

export const authService = new AuthService();
export type { LoginCredentials, User };