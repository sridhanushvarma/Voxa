import React, { useEffect, useState, useCallback } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import './HistorySidebar.css';
import { chatService } from '../services/chatService';
import { useToast } from './ui/Toast';

export default function HistorySidebar({
  currentSessionId,
  onClose,
  onLoad,
  onNew,
}) {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null);
  const [draft, setDraft] = useState('');
  const { toast } = useToast();

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await chatService.getChatHistory();
      setSessions(data.sessions || []);
    } catch {
      toast('Could not load history', 'error');
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const open = async (s) => {
    try {
      const data = await chatService.getChatSession(s.session_id);
      onLoad(data.session);
    } catch {
      toast('Failed to open conversation', 'error');
    }
  };

  const remove = async (e, s) => {
    e.stopPropagation();
    try {
      await chatService.deleteChatSession(s.session_id);
      setSessions((arr) => arr.filter((x) => x.session_id !== s.session_id));
      toast('Conversation deleted', 'info');
    } catch {
      toast('Failed to delete', 'error');
    }
  };

  const saveRename = async (e, s) => {
    e.stopPropagation();
    if (!draft.trim()) {
      setEditing(null);
      return;
    }
    try {
      await chatService.renameChatSession(s.session_id, draft.trim());
      setSessions((arr) =>
        arr.map((x) =>
          x.session_id === s.session_id ? { ...x, title: draft.trim() } : x
        )
      );
      toast('Renamed', 'success');
    } catch {
      toast('Failed to rename', 'error');
    } finally {
      setEditing(null);
    }
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
        className="history-sidebar glass"
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        exit={{ x: '100%' }}
        transition={{ type: 'spring', stiffness: 320, damping: 34 }}
      >
        <div className="sidebar-head">
          <h3>Conversations</h3>
          <button className="sidebar-x" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>

        <button
          className="btn primary new-conv"
          onClick={() => {
            onNew();
            onClose();
          }}
        >
          + New Conversation
        </button>

        <div className="history-list">
          {loading && <div className="history-empty">Loading…</div>}
          {!loading && sessions.length === 0 && (
            <div className="history-empty">
              No saved conversations yet.
              <br />
              Start chatting — they’ll appear here.
            </div>
          )}
          <AnimatePresence>
            {sessions.map((s) => (
              <motion.div
                key={s.session_id}
                layout
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, x: 40 }}
                className={`history-item ${
                  s.session_id === currentSessionId ? 'active' : ''
                }`}
                onClick={() => open(s)}
              >
                {editing === s.session_id ? (
                  <input
                    className="rename-input"
                    autoFocus
                    value={draft}
                    onClick={(e) => e.stopPropagation()}
                    onChange={(e) => setDraft(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') saveRename(e, s);
                      if (e.key === 'Escape') setEditing(null);
                    }}
                    onBlur={(e) => saveRename(e, s)}
                  />
                ) : (
                  <div className="history-title">{s.title}</div>
                )}
                <div className="history-meta">
                  <span>{s.message_count} msgs</span>
                  <span>
                    {new Date(s.updated_at).toLocaleDateString([], {
                      month: 'short',
                      day: 'numeric',
                    })}
                  </span>
                </div>
                <div className="history-item-actions">
                  <button
                    title="Rename"
                    onClick={(e) => {
                      e.stopPropagation();
                      setEditing(s.session_id);
                      setDraft(s.title);
                    }}
                  >
                    ✎
                  </button>
                  <button
                    title="Delete"
                    className="del"
                    onClick={(e) => remove(e, s)}
                  >
                    🗑
                  </button>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </motion.aside>
    </>
  );
}
