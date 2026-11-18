import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { MemberAPI } from '../api/client';

const TOKEN_STORAGE_KEY = 'restaurant_member_token';

const AuthContext = createContext(null);

function readStoredToken() {
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      return window.localStorage.getItem(TOKEN_STORAGE_KEY);
    }
  } catch (e) {
    // ignore storage errors
  }
  return null;
}

function writeStoredToken(token) {
  try {
    if (typeof window !== 'undefined' && window.localStorage) {
      if (token) {
        window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
      } else {
        window.localStorage.removeItem(TOKEN_STORAGE_KEY);
      }
    }
  } catch (e) {
    // ignore storage errors
  }
}

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => readStoredToken());
  const [user, setUser] = useState(null);
  const [authReady, setAuthReady] = useState(false);

  const refreshProfile = useCallback(async (activeToken) => {
    if (!activeToken) {
      setUser(null);
      setAuthReady(true);
      return;
    }
    try {
      const res = await MemberAPI.getProfile(activeToken);
      if (res.success && res.data && res.data.role === 'MEMBER') {
        setUser(res.data);
      } else {
        writeStoredToken(null);
        setToken(null);
        setUser(null);
      }
    } catch (err) {
      writeStoredToken(null);
      setToken(null);
      setUser(null);
    } finally {
      setAuthReady(true);
    }
  }, []);

  useEffect(() => {
    refreshProfile(token);
  }, [token, refreshProfile]);

  const login = async (email, password) => {
    const res = await MemberAPI.login(email, password);
    if (res.success && res.data) {
      writeStoredToken(res.data.token);
      setToken(res.data.token);
      setUser(res.data.user);
      return res.data.user;
    }
    throw new Error('登入失敗');
  };

  const register = async (email, password, displayName, phone, gender, birthday) => {
    const res = await MemberAPI.register(email, password, displayName, phone, gender, birthday);
    if (res.success && res.data) {
      if (res.data.token) {
        writeStoredToken(res.data.token);
        setToken(res.data.token);
        setUser({
          user_id: res.data.user_id,
          email: res.data.email,
          display_name: res.data.display_name,
          phone: res.data.phone || phone,
          gender: res.data.gender || gender,
          birthday: res.data.birthday || birthday,
          role: res.data.role
        });
      }
      return res.data;
    }
    throw new Error('註冊失敗');
  };

  const logout = async () => {
    try {
      await MemberAPI.logout();
    } catch (e) {
      // stateless logout
    }
    writeStoredToken(null);
    setToken(null);
    setUser(null);
  };

  const updateProfile = async (fields) => {
    if (!token) throw new Error('請先登入');
    const res = await MemberAPI.updateProfile(token, fields);
    if (res.success && res.data) {
      setUser(res.data);
      return res.data;
    }
    throw new Error('更新失敗');
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        authReady,
        isLoggedIn: Boolean(token && user),
        login,
        register,
        logout,
        updateProfile,
        refreshProfile: () => refreshProfile(token)
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}
