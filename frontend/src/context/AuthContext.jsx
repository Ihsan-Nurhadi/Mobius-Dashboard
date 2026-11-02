import { createContext, useContext, useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { apiGetMe, apiLogin, apiLogout, getToken, setToken } from "../api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [token, setTokenState] = useState(() => getToken());
  const [isLoading, setIsLoading] = useState(true);
  const queryClient = useQueryClient();

  useEffect(() => {
    const initAuth = async () => {
      const storedToken = getToken();
      if (!storedToken) {
        setIsLoading(false);
        return;
      }
      try {
        const res = await apiGetMe();
        setUser(res.user);
      } catch (err) {
        console.error("Auth validation failed:", err);
        setToken(null);
        setTokenState(null);
        setUser(null);
        queryClient.clear();
      } finally {
        setIsLoading(false);
      }
    };

    initAuth();
  }, [queryClient]);

  const login = async (username, password) => {
    queryClient.clear();
    const data = await apiLogin(username, password);
    setToken(data.token);
    setTokenState(data.token);
    setUser(data.user);
    queryClient.clear();
    return data;
  };

  const logout = async () => {
    try {
      await apiLogout();
    } catch (err) {
      console.warn("Logout error:", err);
    } finally {
      setToken(null);
      setTokenState(null);
      setUser(null);
      queryClient.clear();
    }
  };

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
