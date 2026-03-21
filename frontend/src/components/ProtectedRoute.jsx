import { useEffect, useRef } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { notify } from './Notification';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();
  const notified = useRef(false);

  useEffect(() => {
    if (!loading && !user && !notified.current) {
      notified.current = true;
      notify('Please log in or create an account to access this page.', 'warning');
    }
  }, [loading, user]);

  if (loading) return null;

  if (!user) return <Navigate to="/login" replace />;

  return children;
};

export default ProtectedRoute;
