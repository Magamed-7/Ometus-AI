import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { client } from "../api/client.js";
import { clearTokens, hasSession, onTokensCleared, setTokens } from "./tokens.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(hasSession());

  const refreshUser = useCallback(async () => {
    const me = await client.get("/api/users/me");
    setUser(me);
    return me;
  }, []);

  useEffect(() => {
    if (!hasSession()) {
      setLoading(false);
      return;
    }

    refreshUser()
      .catch(() => clearTokens())
      .finally(() => setLoading(false));
  }, [refreshUser]);

  useEffect(() => onTokensCleared(() => setUser(null)), []);

  const login = useCallback(
    async (email, password) => {
      const tokens = await client.post("/api/auth/login", { email, password }, { auth: false });
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
