import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

/**
 * ProtectedRoute – authentication wrapper.
 * Redirects unauthenticated users to /login, preserving the intended destination.
 *
 * No loading spinner needed — auth state is read from localStorage synchronously
 * via useState lazy initializers, so it is available on the very first render.
 */
export default function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return children;
}
