import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { SystemAPI } from '../api/client';

const DEFAULT_CONFIG = {
  store_status: 'OPEN',
  reservations_enabled: true,
  ordering_enabled: true,
  pre_order_enabled: true,
  announcement_text: '',
  announcement_type: 'info',
  opening_time: '11:00',
  closing_time: '21:30',
  active_tables: [],
  updated_at: ''
};

const SystemConfigContext = createContext(null);

export function SystemConfigProvider({ children }) {
  const [config, setConfig] = useState(DEFAULT_CONFIG);
  const [loaded, setLoaded] = useState(false);

  const refreshConfig = useCallback(async () => {
    try {
      const res = await SystemAPI.getConfig();
      if (res && res.success && res.data) {
        setConfig(res.data);
      }
    } catch (err) {
      // Keep previous config if backend is temporarily unreachable
    } finally {
      setLoaded(true);
    }
  }, []);

  useEffect(() => {
    refreshConfig();
    const timer = setInterval(refreshConfig, 4000);

    let onFocus = null;
    if (typeof window !== 'undefined' && window.addEventListener) {
      onFocus = () => refreshConfig();
      window.addEventListener('focus', onFocus);
    }

    return () => {
      clearInterval(timer);
      if (onFocus && typeof window !== 'undefined' && window.removeEventListener) {
        window.removeEventListener('focus', onFocus);
      }
    };
  }, [refreshConfig]);

  return (
    <SystemConfigContext.Provider value={{ config, loaded, refreshConfig }}>
      {children}
    </SystemConfigContext.Provider>
  );
}

export function useSystemConfig() {
  const ctx = useContext(SystemConfigContext);
  if (!ctx) {
    throw new Error('useSystemConfig must be used within a SystemConfigProvider');
  }
  return ctx;
}
