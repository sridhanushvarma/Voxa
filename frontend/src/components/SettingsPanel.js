import React from 'react';
import { motion } from 'framer-motion';
import './SettingsPanel.css';
import { useSettings } from '../contexts/SettingsContext';
import { useSound } from '../hooks/useSound';

const THEMES = [
  { id: 'cyan', label: 'CLU Cyan', c: '#00d9ff' },
  { id: 'green', label: 'Matrix', c: '#2bff88' },
  { id: 'amber', label: 'Amber', c: '#ffb627' },
  { id: 'magenta', label: 'Synthwave', c: '#ff4dd2' },
  { id: 'ice', label: 'Ice', c: '#8ab4ff' },
];

function Toggle({ label, desc, on, onChange }) {
  return (
    <div className="set-row">
      <div>
        <div className="set-label">{label}</div>
        <div className="set-desc">{desc}</div>
      </div>
      <button
        className={`switch ${on ? 'on' : ''}`}
        role="switch"
        aria-checked={on}
        onClick={onChange}
      >
        <span className="knob" />
      </button>
    </div>
  );
}

export default function SettingsPanel({ onClose }) {
  const { settings, update, toggle } = useSettings();
  const sfx = useSound();

  const flip = (key) => () => {
    toggle(key);
    sfx('toggle');
  };

  return (
    <>
      <motion.div
        className="sidebar-scrim"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        onClick={onClose}
      />
      <motion.aside
        className="settings-panel glass"
        initial={{ x: '-100%' }}
        animate={{ x: 0 }}
        exit={{ x: '-100%' }}
        transition={{ type: 'spring', stiffness: 320, damping: 34 }}
      >
        <div className="sidebar-head">
          <h3>Settings</h3>
          <button className="sidebar-x" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>

        <div className="set-section">
          <div className="set-section-title">Accent Theme</div>
          <div className="theme-grid">
            {THEMES.map((t) => (
              <button
                key={t.id}
                className={`theme-cell ${settings.theme === t.id ? 'sel' : ''}`}
                style={{ '--tc': t.c }}
                onClick={() => {
                  update({ theme: t.id });
                  sfx('toggle');
                }}
              >
                <span className="theme-swatch" />
                {t.label}
              </button>
            ))}
          </div>
        </div>

        <div className="set-section">
          <div className="set-section-title">Interface</div>
          <Toggle
            label="Animations"
            desc="Motion, transitions & particle field"
            on={settings.animations}
            onChange={flip('animations')}
          />
          <Toggle
            label="Scanlines"
            desc="Retro CRT overlay effect"
            on={settings.scanlines}
            onChange={flip('scanlines')}
          />
          <Toggle
            label="Sound Effects"
            desc="Subtle UI feedback tones"
            on={settings.sound}
            onChange={flip('sound')}
          />
          <Toggle
            label="Spoken Replies"
            desc="Read Voxa's answers aloud"
            on={settings.voiceOutput}
            onChange={flip('voiceOutput')}
          />
        </div>

        <div className="set-section">
          <div className="set-section-title">
            Text Size — {Math.round(settings.fontScale * 100)}%
          </div>
          <input
            type="range"
            className="set-range"
            min="0.85"
            max="1.3"
            step="0.05"
            value={settings.fontScale}
            onChange={(e) =>
              update({ fontScale: parseFloat(e.target.value) })
            }
          />
        </div>

        <p className="set-foot">Preferences are saved to this browser.</p>
      </motion.aside>
    </>
  );
}
