import React, { createContext, useContext, useState, useEffect } from 'react';
import type { User, UserRole } from '../types';
import { api } from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isAdmin: boolean;
  isStudent: boolean;
  isRecruiter: boolean;
  isInterviewer: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName?: string, role?: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(() => {
    try {
      const stored = localStorage.getItem('studyset_user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const [token, setToken] = useState<string | null>(() => {
    return localStorage.getItem('studyset_token') || null;
  });

  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    if (token) {
      api.getMe(token)
        .then((fetchedUser) => {
          setUser(fetchedUser);
          localStorage.setItem('studyset_user', JSON.stringify(fetchedUser));
        })
        .catch(() => {
          // Token expired or invalid
          setUser(null);
          setToken(null);
          localStorage.removeItem('studyset_token');
          localStorage.removeItem('studyset_user');
        })
        .finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, [token]);

  const login = async (email: string, password: string) => {
    const data = await api.login({ email, password });
    setToken(data.access_token);
    setUser(data.user);
    localStorage.setItem('studyset_token', data.access_token);
    localStorage.setItem('studyset_user', JSON.stringify(data.user));
  };

  const register = async (email: string, password: string, fullName?: string, role = 'STUDENT') => {
    const data = await api.register({ email, password, full_name: fullName, role });
    setToken(data.access_token);
    setUser(data.user);
    localStorage.setItem('studyset_token', data.access_token);
    localStorage.setItem('studyset_user', JSON.stringify(data.user));
  };

  const logout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('studyset_token');
    localStorage.removeItem('studyset_user');
  };

  const role: UserRole = user?.role || 'STUDENT';
  const isAdmin = role === 'ADMIN';
  const isStudent = role === 'STUDENT';
  const isRecruiter = role === 'RECRUITER';
  const isInterviewer = role === 'INTERVIEWER';

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        isAdmin,
        isStudent,
        isRecruiter,
        isInterviewer,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
