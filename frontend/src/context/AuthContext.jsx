import { useState } from 'react';
import { AuthContext } from './authContextDef';

export function AuthProvider({ children }) {
  // Lazy initializers run synchronously on first render —
  // no useEffect needed because localStorage is a sync API.
  const [token, setToken] = useState(
    () => localStorage.getItem('access_token')
  );

  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('user_info');
      return stored ? JSON.parse(stored) : null;
    } catch {
      // Corrupted storage — clear it immediately
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_info');
      return null;
    }
  });

  function login(tokenData, userInfo) {
    localStorage.setItem('access_token', tokenData);
    localStorage.setItem('user_info', JSON.stringify(userInfo));
    setToken(tokenData);
    setUser(userInfo);
  }

  function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_info');
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated: !!token }}>
      {children}
    </AuthContext.Provider>
  );
}
