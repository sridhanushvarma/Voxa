import React, { useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import './NLUVisualization.css';

const confColor = (c) =>
  c >= 0.75 ? 'var(--ok)' : c >= 0.45 ? 'var(--warn)' : 'var(--secondary)';

export default function NLUVisualization({ nluData }) {
  const [open, setOpen] = useState(false);
  if (!nluData || !nluData.intent) return null;

  const { intent, confidence = 0, method, entities = {}, all_scores = {}, sentiment } =
    nluData;

  const topScores = Object.entries(all_scores)
    .sort(([, a], [, b]) => b - a)
    .slice(0, 4);
  const entityList = Object.entries(entities || {});

  return (
    <div className="nlu">
      <button
        className="nlu-toggle"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <span className="nlu-tag" style={{ '--c': confColor(confidence) }}>
          🧠 {intent}
        </span>
        <span className="nlu-conf" style={{ color: confColor(confidence) }}>
          {(confidence * 100).toFixed(0)}%
        </span>
        {sentiment && (
          <span className="nlu-sent" title={`Sentiment: ${sentiment.label}`}>
            {sentiment.emoji}
          </span>
        )}
        <span className="nlu-method">{method}</span>
        <span className={`nlu-chevron ${open ? 'open' : ''}`}>⌄</span>
      </button>

      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            className="nlu-detail"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
          >
            <div className="nlu-inner">
              {topScores.length > 0 && (
                <div className="nlu-block">
                  <div className="nlu-block-title">Intent confidence</div>
                  {topScores.map(([name, score]) => (
                    <div key={name} className="bar-row">
                      <span className="bar-name">{name}</span>
                      <div className="bar-track">
                        <motion.div
                          className="bar-fill"
                          initial={{ width: 0 }}
                          animate={{ width: `${score * 100}%` }}
                          transition={{ duration: 0.6, ease: 'easeOut' }}
                          style={{ background: confColor(score) }}
                        />
                      </div>
                      <span className="bar-val">
                        {(score * 100).toFixed(0)}%
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {entityList.length > 0 && (
                <div className="nlu-block">
                  <div className="nlu-block-title">Entities</div>
                  <div className="entity-tags">
                    {entityList.map(([k, v]) => (
                      <span key={k} className="entity-tag">
                        <b>{k}</b>: {String(v)}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {sentiment && (
                <div className="nlu-block">
                  <div className="nlu-block-title">Sentiment</div>
                  <span className="entity-tag">
                    {sentiment.emoji} {sentiment.label} ({sentiment.score})
                  </span>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
