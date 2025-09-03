import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { User } from '../types';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  login: (userData: User) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);

  const login = useCallback((userData: User) => {
    setUser(userData);
    // In a real app, you'd also store the token in localStorage/sessionStorage
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    // In a real app, you'd also clear the token from storage
  }, []);

  // Mock user authentication on initial load
  useEffect(() => {
    const mockUser: User = {
      id: 'user_admin',
      email: 'admin@example.com',
      name: 'Admin User',
      role: 'admin'
    };
    login(mockUser);
  }, [login]);

  const isAuthenticated = !!user;

  return (
    <AuthContext.Provider value={{ user, isAuthenticated, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
