import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';

const DEFAULTS = {
  theme: 'cyan',          // cyan | green | amber | magenta | ice
  animations: true,
  sound: true,
  fontScale: 1,           // 0.85 – 1.3
  scanlines: true,
  voiceOutput: false,
};

const STORAGE_KEY = 'voxa.settings';
const SettingsContext = createContext(null);

function load() {
  try {
    return { ...DEFAULTS, ...JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}') };
  } catch {
    return { ...DEFAULTS };
  }
}

export function SettingsProvider({ children }) {
  const [settings, setSettings] = useState(load);

  // Reflect settings onto <html> so CSS can react globally.
  useEffect(() => {
    const root = document.documentElement;
    root.dataset.theme = settings.theme === 'cyan' ? '' : settings.theme;
    root.dataset.animations = settings.animations ? 'on' : 'off';
    root.dataset.scanlines = settings.scanlines ? 'on' : 'off';
    root.style.setProperty('--font-scale', String(settings.fontScale));
    localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  }, [settings]);

  const update = useCallback((patch) => {
    setSettings((s) => ({ ...s, ...patch }));
  }, []);

  const toggle = useCallback((key) => {
    setSettings((s) => ({ ...s, [key]: !s[key] }));
  }, []);

  return (
    <SettingsContext.Provider value={{ settings, update, toggle }}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettings() {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error('useSettings must be used within SettingsProvider');
  return ctx;
}
