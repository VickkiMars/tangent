import { createContext, useContext, useState, useEffect } from 'react';
import { authGetMe } from '../api';
import { notify } from '../components/Notification';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const login = (token) => {
    localStorage.setItem('token', token);
    checkAuth(token);
  };

  const logout = () => {
    localStorage.removeItem('token');
    setUser(null);
    window.location.href = '/login';
  };

  const checkAuth = async (token) => {
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }

    try {
      const userData = await authGetMe(token);
      setUser(userData);
    } catch (err) {
      localStorage.removeItem('token');
      setUser(null);
      notify('Your session has expired. Please sign in again.', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const token = localStorage.getItem('token');
    checkAuth(token);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
