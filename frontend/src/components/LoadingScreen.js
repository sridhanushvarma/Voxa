import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import './LoadingScreen.css';

const BOOT_LINES = [
  '> initializing voxa kernel ...........  [ OK ]',
  '> mounting nlu engine ................  [ OK ]',
  '> loading intent classifier .........  [ OK ]',
  '> calibrating entity extractor ......  [ OK ]',
  '> warming context manager ...........  [ OK ]',
  '> linking voice subsystem ...........  [ OK ]',
  '> establishing secure socket ........  [ OK ]',
];

export default function LoadingScreen() {
  const [shown, setShown] = useState(0);

  useEffect(() => {
    if (shown >= BOOT_LINES.length) return;
    const t = setTimeout(() => setShown((n) => n + 1), 230);
    return () => clearTimeout(t);
  }, [shown]);

  const progress = Math.round((shown / BOOT_LINES.length) * 100);

  return (
    <div className="loading-screen">
      <motion.div
        className="loading-core"
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="boot-logo">
          <span className="boot-ring" />
          <span className="boot-mark">V</span>
        </div>
        <h1 className="boot-title">VOXA</h1>
        <p className="boot-sub">NEURAL CLI INTERFACE</p>

        <div className="boot-console">
          {BOOT_LINES.slice(0, shown).map((line, i) => (
            <motion.div
              key={i}
              className="boot-line"
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
            >
              {line}
            </motion.div>
          ))}
          {shown < BOOT_LINES.length && (
            <span className="boot-cursor">▋</span>
          )}
        </div>

        <div className="boot-progress">
          <div className="boot-progress-fill" style={{ width: `${progress}%` }} />
        </div>
        <div className="boot-progress-label">{progress}% — booting</div>
      </motion.div>
    </div>
  );
}
