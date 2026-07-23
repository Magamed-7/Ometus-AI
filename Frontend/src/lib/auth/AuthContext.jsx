import { createContext, useCallback, useContext, useEffect, useState } from "react";
import * as authApi from "../api/auth.js";
import * as usersApi from "../api/users.js";
import { clearTokens, hasSession, onTokensCleared, setTokens } from "./tokens.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(hasSession());

  const refreshUser = useCallback(async () => {
    const me = await usersApi.getMe();
    setUser(me);
    return me;
  }, []);

  useEffect(() => {
    if (!hasSession()) {
      setLoading(false);
      return;
    }

    refreshUser()
      .catch((err) => {
        if (err && err.status === 401) clearTokens();
      })
      .finally(() => setLoading(false));
  }, [refreshUser]);

  useEffect(() => onTokensCleared(() => setUser(null)), []);

  const login = useCallback(
    async (email, password) => {
      const tokens = await authApi.login(email, password);
      setTokens(tokens);
      return refreshUser();
    },
    [refreshUser]
  );

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout, refreshUser, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);

  if (context === null) throw new Error("useAuth должен использоваться внутри AuthProvider");

  return context;
}
