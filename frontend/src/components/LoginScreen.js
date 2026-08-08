import React, { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import './LoginScreen.css';
import { useSound } from '../hooks/useSound';

const COLORS = [
  { value: '#00d9ff', label: 'Cyan' },
  { value: '#2bff88', label: 'Green' },
  { value: '#ffb627', label: 'Amber' },
  { value: '#ff4dd2', label: 'Magenta' },
  { value: '#8ab4ff', label: 'Ice' },
  { value: '#ff4d6d', label: 'Crimson' },
];

function strength(pw) {
  let s = 0;
  if (pw.length >= 6) s++;
  if (pw.length >= 10) s++;
  if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) s++;
  if (/\d/.test(pw)) s++;
  if (/[^A-Za-z0-9]/.test(pw)) s++;
  return Math.min(s, 4);
}
const STRENGTH_LABEL = ['Too weak', 'Weak', 'Fair', 'Good', 'Strong'];

export default function LoginScreen({ onLogin, onRegister }) {
  const [mode, setMode] = useState('login'); // 'login' | 'register'
  const isLogin = mode === 'login';
  const [form, setForm] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    terminal_color: '#00d9ff',
  });
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const sfx = useSound();

  const set = (k) => (e) => {
    setForm((f) => ({ ...f, [k]: e.target.value }));
    setError('');
  };

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    if (!isLogin && form.password !== form.confirmPassword) {
      setError('Passwords do not match');
      sfx('error');
      return;
    }
    setBusy(true);
    try {
      if (isLogin) {
        await onLogin({ username: form.username, password: form.password });
      } else {
        await onRegister({
          username: form.username,
          email: form.email,
          password: form.password,
          terminal_color: form.terminal_color,
        });
      }
    } catch (err) {
      setError(err.message || 'An error occurred');
      sfx('error');
      setBusy(false);
    }
  };

  const pwScore = strength(form.password);

  return (
    <div className="login-screen">
      <motion.div
        className="login-card glass"
        initial={{ opacity: 0, y: 28, scale: 0.96 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="login-brand">
          <div className="login-logo">V</div>
          <h1 className="login-title">VOXA</h1>
          <p className="login-tagline">Voice-Enabled Neural Assistant</p>
        </div>

        <div className="login-tabs" role="tablist">
          {['login', 'register'].map((m) => (
            <button
              key={m}
              role="tab"
              aria-selected={mode === m}
              className={`login-tab ${mode === m ? 'active' : ''}`}
              onClick={() => {
                setMode(m);
                setError('');
                sfx('toggle');
              }}
            >
              {m === 'login' ? 'Sign In' : 'Register'}
              {mode === m && (
                <motion.span layoutId="tabUnderline" className="tab-underline" />
              )}
            </button>
          ))}
        </div>

        <form className="login-form" onSubmit={submit}>
          <div className="field">
            <label className="field-label">Username</label>
            <input
              className="field-input"
              value={form.username}
              onChange={set('username')}
              required
              autoFocus
              placeholder="your handle"
            />
          </div>

          <AnimatePresence mode="popLayout">
            {!isLogin && (
              <motion.div
                key="email"
                className="field"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
              >
                <label className="field-label">Email</label>
                <input
                  type="email"
                  className="field-input"
                  value={form.email}
                  onChange={set('email')}
                  required
                  placeholder="you@example.com"
                />
              </motion.div>
            )}
          </AnimatePresence>

          <div className="field">
            <label className="field-label">Password</label>
            <div className="field-control">
              <input
                type={showPw ? 'text' : 'password'}
                className="field-input"
                value={form.password}
                onChange={set('password')}
                required
                placeholder="••••••••"
              />
              <button
                type="button"
                className="pw-toggle"
                onClick={() => setShowPw((v) => !v)}
                aria-label={showPw ? 'Hide password' : 'Show password'}
              >
                {showPw ? '🙈' : '👁'}
              </button>
            </div>
            {!isLogin && form.password && (
              <div className="pw-strength">
                <div className="pw-bars">
                  {[0, 1, 2, 3].map((i) => (
                    <span
                      key={i}
                      className={`pw-bar ${i < pwScore ? `lvl-${pwScore}` : ''}`}
                    />
                  ))}
                </div>
                <span className="pw-label">{STRENGTH_LABEL[pwScore]}</span>
              </div>
            )}
          </div>

          <AnimatePresence mode="popLayout">
            {!isLogin && (
              <motion.div
                key="extra"
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
              >
                <div className="field">
                  <label className="field-label">Confirm Password</label>
                  <input
                    type={showPw ? 'text' : 'password'}
                    className="field-input"
                    value={form.confirmPassword}
                    onChange={set('confirmPassword')}
                    required
                    placeholder="repeat password"
                  />
                </div>
                <div className="field">
                  <label className="field-label">Accent Color</label>
                  <div className="color-picker">
                    {COLORS.map((c) => (
                      <button
                        type="button"
                        key={c.value}
                        title={c.label}
                        className={`color-dot ${
                          form.terminal_color === c.value ? 'selected' : ''
                        }`}
                        style={{ '--dot': c.value }}
                        onClick={() =>
                          setForm((f) => ({ ...f, terminal_color: c.value }))
                        }
                      />
                    ))}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <AnimatePresence>
            {error && (
              <motion.div
                className="login-error"
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
              >
                ⚠ {error}
              </motion.div>
            )}
          </AnimatePresence>

          <button type="submit" className="btn primary login-submit" disabled={busy}>
            {busy ? (
              <span className="spinner-sm" />
            ) : isLogin ? (
              'Access Terminal'
            ) : (
              'Create Account'
            )}
          </button>
        </form>

        <p className="login-foot">
          Voxa CLI · created by{' '}
          <a href="https://github.com/Sridhanush-Varma/Voxa" target="_blank" rel="noreferrer">
            Sridhanush Varma
          </a>
        </p>
      </motion.div>
    </div>
  );
}
