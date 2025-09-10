import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

interface LoginResponse {
  user: {
    id: string;
    email: string;
    name: string;
    role: string;
    avatar?: string;
  };
  token: string;
}

/**
 * Authentication Service
 */
export const authService = {
  /**
   * Login user
   */
  async login(email: string, password: string): Promise<LoginResponse> {
    const response = await axios.post(`${API_BASE_URL}/auth/login`, {
      email,
      password,
    });
    return response.data;
  },

  /**
   * Register new user
   */
  async register(email: string, password: string, name: string): Promise<LoginResponse> {
    const response = await axios.post(`${API_BASE_URL}/auth/register`, {
      email,
      password,
      name,
    });
    return response.data;
  },

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    const token = localStorage.getItem('auth_token');
    await axios.post(
      `${API_BASE_URL}/auth/logout`,
      {},
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
  },

  /**
   * Validate token
   */
  async validateToken(token: string): Promise<LoginResponse['user']> {
    const response = await axios.get(`${API_BASE_URL}/auth/validate`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data.user;
  },
};