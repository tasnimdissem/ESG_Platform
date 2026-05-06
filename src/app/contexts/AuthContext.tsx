import React, { createContext, useContext, useState, useEffect } from 'react';

interface User {
  id: number;
  name: string;
  email: string;
  role: string;
  created_at?: string | null;
}

interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: boolean;
  isAuthLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const AUTH_BASE_URL = '/api/auth';

type AuthResponse = {
  message: string;
  user: User;
};

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthLoading, setIsAuthLoading] = useState(true);

  // Restore session on mount - check /me endpoint (cookies are sent automatically)
  useEffect(() => {
    const restoreSession = async () => {
      try {
        const response = await fetch(`${AUTH_BASE_URL}/me`, {
          credentials: 'include', // Send cookies with request
        });

        if (!response.ok) {
          setUser(null);
          return;
        }

        const data = (await response.json()) as { user: User };
        setUser(data.user);
      } catch {
        setUser(null);
      } finally {
        setIsAuthLoading(false);
      }
    };

    void restoreSession();
  }, []);

  const login = async (email: string, password: string) => {
    if (!email || !password) {
      throw new Error('Email and password are required');
    }

    const response = await fetch(`${AUTH_BASE_URL}/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Send cookies with request
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const errorBody = await response.text();
      let message = 'Login failed';

      try {
        const parsed = JSON.parse(errorBody) as { error?: string; message?: string };
        message = parsed.error ?? parsed.message ?? message;
      } catch {
        if (errorBody) {
          message = errorBody;
        }
      }

      throw new Error(message);
    }

    const data = (await response.json()) as AuthResponse;
    setUser(data.user);
  };

  const logout = async () => {
    try {
      await fetch(`${AUTH_BASE_URL}/logout`, {
        method: 'GET',
        credentials: 'include', // Send cookies with request
      });
    } catch {
      // Ignore errors during logout
    }
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user, isAuthLoading }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
