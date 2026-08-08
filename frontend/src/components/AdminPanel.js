import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import './AdminPanel.css';
import { useToast } from './ui/Toast';

const API = process.env.REACT_APP_API_URL || 'http://localhost:5000';
const authHeaders = () => ({
  Authorization: `Bearer ${localStorage.getItem('access_token')}`,
});

export default function AdminPanel({ user, onClose }) {
  const [tab, setTab] = useState('intents');
  const [intents, setIntents] = useState({});
  const [trainingData, setTrainingData] = useState({});
  const [selectedIntent, setSelectedIntent] = useState('');
  const [newUtterance, setNewUtterance] = useState('');
  const [testText, setTestText] = useState('');
  const [testResult, setTestResult] = useState(null);
  const [isTraining, setIsTraining] = useState(false);
  const { toast } = useToast();

  const fetchIntents = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/admin/intents`, { headers: authHeaders() });
      const d = await r.json();
      if (d.success) setIntents(d.intents);
    } catch {
      toast('Failed to load intents', 'error');
    }
  }, [toast]);

  const fetchTraining = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/admin/training-data`, {
        headers: authHeaders(),
      });
      const d = await r.json();
      if (d.success) setTrainingData(d.training_data);
    } catch {
      /* non-fatal */
    }
  }, []);

  useEffect(() => {
    fetchIntents();
    fetchTraining();
  }, [fetchIntents, fetchTraining]);

  const addUtterance = async () => {
    if (!selectedIntent || !newUtterance.trim()) {
      toast('Select an intent and enter an utterance', 'warn');
      return;
    }
    try {
      const r = await fetch(`${API}/api/admin/training-data`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({
          intent: selectedIntent,
          utterances: [newUtterance],
        }),
      });
      const d = await r.json();
      if (d.success) {
        toast('Utterance added', 'success');
        setNewUtterance('');
        fetchTraining();
      } else toast(d.error || 'Failed', 'error');
    } catch {
      toast('Failed to add utterance', 'error');
    }
  };

  const retrain = async () => {
    setIsTraining(true);
    try {
      const r = await fetch(`${API}/api/admin/retrain`, {
        method: 'POST',
        headers: authHeaders(),
      });
      const d = await r.json();
      toast(
        d.success ? 'Model retrained successfully' : d.error || 'Failed',
        d.success ? 'success' : 'error'
      );
    } catch {
      toast('Failed to retrain', 'error');
    } finally {
      setIsTraining(false);
    }
  };

  const analyze = async () => {
    if (!testText.trim()) {
      toast('Enter text to analyze', 'warn');
      return;
    }
    try {
      const r = await fetch(`${API}/api/nlu/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({ text: testText }),
      });
      const d = await r.json();
      if (d.success) setTestResult(d.analysis);
      else toast(d.error || 'Failed', 'error');
    } catch {
      toast('Failed to analyze', 'error');
    }
  };

  return (
    <div className="admin-scrim" onClick={onClose}>
      <motion.div
        className="admin-modal glass"
        onClick={(e) => e.stopPropagation()}
        initial={{ opacity: 0, scale: 0.94, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.94 }}
        transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
      >
        <div className="admin-head">
          <h2>🛠 NLU Control Center</h2>
          <button className="sidebar-x" onClick={onClose}>
            ✕
          </button>
        </div>

        <div className="admin-tabs">
          {['intents', 'training', 'test'].map((t) => (
            <button
              key={t}
              className={tab === t ? 'active' : ''}
              onClick={() => setTab(t)}
            >
              {t}
            </button>
          ))}
        </div>

        <div className="admin-content">
          {tab === 'intents' && (
            <div className="intent-grid">
              {Object.entries(intents).map(([name, meta]) => (
                <div key={name} className="intent-card">
                  <div className="intent-card-name">
                    {meta.icon || '•'} {name}
                  </div>
                  <div className="intent-card-desc">{meta.description}</div>
                  <div className="intent-card-action">→ {meta.action}</div>
                </div>
              ))}
            </div>
          )}

          {tab === 'training' && (
            <div className="train-pane">
              <div className="train-form">
                <select
                  className="field-input"
                  value={selectedIntent}
                  onChange={(e) => setSelectedIntent(e.target.value)}
                >
                  <option value="">Select intent…</option>
                  {Object.keys(intents).map((i) => (
                    <option key={i} value={i}>
                      {i}
                    </option>
                  ))}
                </select>
                <textarea
                  className="field-input"
                  rows="2"
                  placeholder="New training utterance…"
                  value={newUtterance}
                  onChange={(e) => setNewUtterance(e.target.value)}
                />
                <button className="btn primary" onClick={addUtterance}>
                  Add Utterance
                </button>
              </div>

              <div className="train-list">
                {Object.entries(trainingData).map(([intent, utts]) => (
                  <div key={intent} className="train-card">
                    <div className="train-card-head">
                      <span>{intent}</span>
                      <span className="train-count">{utts.length}</span>
                    </div>
                    {utts.slice(0, 3).map((u, i) => (
                      <div key={i} className="train-utt">
                        • {u}
                      </div>
                    ))}
                    {utts.length > 3 && (
                      <div className="train-more">
                        +{utts.length - 3} more
                      </div>
                    )}
                  </div>
                ))}
              </div>

              <button
                className="btn"
                onClick={retrain}
                disabled={isTraining}
              >
                {isTraining ? 'Training…' : '🔄 Retrain Model'}
              </button>
            </div>
          )}

          {tab === 'test' && (
            <div className="test-pane">
              <textarea
                className="field-input"
                rows="3"
                placeholder="Enter text to run through the NLU pipeline…"
                value={testText}
                onChange={(e) => setTestText(e.target.value)}
              />
              <button className="btn primary" onClick={analyze}>
                Analyze
              </button>

              {testResult && (
                <div className="test-result">
                  <div className="tr-row">
                    <strong>Intent</strong>
                    <span>
                      {testResult.intent.intent} ·{' '}
                      {(testResult.intent.confidence * 100).toFixed(1)}% ·{' '}
                      {testResult.intent.method}
                    </span>
                  </div>
                  {testResult.sentiment && (
                    <div className="tr-row">
                      <strong>Sentiment</strong>
                      <span>
                        {testResult.sentiment.emoji}{' '}
                        {testResult.sentiment.label} (
                        {testResult.sentiment.score})
                      </span>
                    </div>
                  )}
                  <div className="tr-row">
                    <strong>Response</strong>
                    <span>{testResult.response}</span>
                  </div>
                  <div className="tr-scores">
                    {Object.entries(testResult.intent.all_scores || {})
                      .sort(([, a], [, b]) => b - a)
                      .map(([i, s]) => (
                        <div key={i} className="tr-score">
                          <span>{i}</span>
                          <div className="tr-bar">
                            <div
                              className="tr-bar-fill"
                              style={{ width: `${s * 100}%` }}
                            />
                          </div>
                          <span>{(s * 100).toFixed(0)}%</span>
                        </div>
                      ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </motion.div>
    </div>
  );
}
