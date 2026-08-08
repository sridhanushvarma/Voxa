import React, {
  useState,
  useEffect,
  useRef,
  useCallback,
  useMemo,
  memo,
} from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './ChatInterface.css';
import NLUVisualization from './NLUVisualization';
import AdminPanel from './AdminPanel';
import HistorySidebar from './HistorySidebar';
import SettingsPanel from './SettingsPanel';
import { useSettings } from '../contexts/SettingsContext';
import { useSound } from '../hooks/useSound';
import { useToast } from './ui/Toast';

const newSessionId = () =>
  `session_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;

const QUICK_ACTIONS = [
  { icon: '🕐', label: 'Time', text: 'What time is it?' },
  { icon: '🧮', label: 'Math', text: 'Calculate 15% of 240' },
  { icon: '📐', label: 'Convert', text: 'Convert 10 km to miles' },
  { icon: '🌤️', label: 'Weather', text: 'Weather in Tokyo' },
  { icon: '🔍', label: 'Search', text: 'Search for the James Webb telescope' },
  { icon: '😄', label: 'Joke', text: 'Tell me a joke' },
];

const SLASH_COMMANDS = [
  { cmd: '/help', desc: 'Show available commands' },
  { cmd: '/clear', desc: 'Clear the terminal' },
  { cmd: '/new', desc: 'Start a new conversation' },
  { cmd: '/history', desc: 'Toggle conversation history' },
  { cmd: '/settings', desc: 'Open settings panel' },
  { cmd: '/export', desc: 'Download this conversation' },
  { cmd: '/voice', desc: 'Toggle spoken responses' },
  { cmd: '/theme', desc: 'Cycle accent theme' },
];

/* ---------- Markdown renderer ----------------------------------- */
const MD = memo(function MD({ children }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        a: ({ children, ...props }) => (
          <a {...props} target="_blank" rel="noreferrer">
            {children}
          </a>
        ),
        code: ({ inline, children, ...p }) =>
          inline ? (
            <code className="md-code" {...p}>
              {children}
            </code>
          ) : (
            <pre className="md-pre">
              <code {...p}>{children}</code>
            </pre>
          ),
      }}
    >
      {children}
    </ReactMarkdown>
  );
});

/* ---------- Typewriter for bot replies -------------------------- */
function useTypewriter(text, enabled) {
  const [out, setOut] = useState(enabled ? '' : text);
  useEffect(() => {
    if (!enabled) {
      setOut(text);
      return;
    }
    let i = 0;
    setOut('');
    const step = Math.max(1, Math.round(text.length / 90));
    const id = setInterval(() => {
      i += step;
      setOut(text.slice(0, i));
      if (i >= text.length) clearInterval(id);
    }, 16);
    return () => clearInterval(id);
  }, [text, enabled]);
  return out;
}

/* ---------- One message row (memoized) -------------------------- */
const MessageRow = memo(function MessageRow({
  message,
  isLast,
  animations,
  onCopy,
  onSpeak,
}) {
  const isBot = message.type === 'bot';
  const stream = isBot && isLast && animations && !message.restored;
  const text = useTypewriter(message.content, stream);

  const avatar =
    message.type === 'user'
      ? '◢◤'
      : message.type === 'bot'
      ? '◉'
      : message.type === 'error'
      ? '⚠'
      : '⚙';

  return (
    <motion.div
      className={`msg msg-${message.type}`}
      initial={animations ? { opacity: 0, y: 18 } : false}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.32, ease: [0.22, 1, 0.36, 1] }}
      layout={animations ? 'position' : false}
    >
      <div className="msg-avatar" aria-hidden="true">
        {avatar}
      </div>
      <div className="msg-body">
        <div className="msg-head">
          <span className="msg-role">
            {message.type === 'user'
              ? 'You'
              : message.type === 'bot'
              ? 'Voxa'
              : message.type === 'error'
              ? 'Error'
              : 'System'}
          </span>
          <span className="msg-time">
            {new Date(message.timestamp).toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
          {(isBot || message.type === 'system') && (
            <div className="msg-actions">
              <button
                className="msg-act"
                title="Copy"
                onClick={() => onCopy(message.content)}
              >
                ⧉
              </button>
              {isBot && (
                <button
                  className="msg-act"
                  title="Speak"
                  onClick={() => onSpeak(message.content)}
                >
                  ▶
                </button>
              )}
            </div>
          )}
        </div>
        <div className="msg-content">
          {isBot ? (
            <MD>{text}</MD>
          ) : (
            <span className="msg-text">{message.content}</span>
          )}
          {stream && text.length < message.content.length && (
            <span className="stream-caret">▋</span>
          )}
        </div>
        {isBot && message.nluData && message.nluData.intent && (
          <NLUVisualization nluData={message.nluData} />
        )}
      </div>
    </motion.div>
  );
});

/* ================================================================ */
export default function ChatInterface({ user, socket, connStatus, onLogout }) {
  const { settings, update, toggle } = useSettings();
  const sfx = useSound();
  const { toast } = useToast();

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sessionId, setSessionId] = useState(newSessionId);
  const [isTyping, setIsTyping] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showAdmin, setShowAdmin] = useState(false);
  const [showPalette, setShowPalette] = useState(false);
  const [paletteIdx, setPaletteIdx] = useState(0);
  const [atBottom, setAtBottom] = useState(true);

  const bodyRef = useRef(null);
  const endRef = useRef(null);
  const inputRef = useRef(null);
  const recognitionRef = useRef(null);

  const addMessage = useCallback((type, content, nluData = null, restored = false) => {
    setMessages((prev) => [
      ...prev,
      {
        id: `${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
        type,
        content,
        nluData,
        restored,
        timestamp: new Date().toISOString(),
      },
    ]);
  }, []);

  /* ---- scrolling ---- */
  const scrollToBottom = useCallback((smooth = true) => {
    endRef.current?.scrollIntoView({ behavior: smooth ? 'smooth' : 'auto' });
  }, []);

  useEffect(() => {
    if (atBottom) scrollToBottom();
  }, [messages, isTyping, atBottom, scrollToBottom]);

  const onBodyScroll = () => {
    const el = bodyRef.current;
    if (!el) return;
    setAtBottom(el.scrollHeight - el.scrollTop - el.clientHeight < 80);
  };

  /* ---- speech synthesis ---- */
  const speak = useCallback(
    (text) => {
      if (!('speechSynthesis' in window)) return;
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text.replace(/[#*`_>]/g, ''));
      u.rate = 1.05;
      window.speechSynthesis.speak(u);
    },
    []
  );

  const copy = useCallback(
    (text) => {
      navigator.clipboard?.writeText(text);
      toast('Copied to clipboard', 'success', 1800);
      sfx('toggle');
    },
    [toast, sfx]
  );

  /* ---- socket wiring ---- */
  useEffect(() => {
    if (!socket) return;

    const onTyping = () => setIsTyping(true);
    const onBot = (data) => {
      setIsTyping(false);
      sfx('receive');
      addMessage('bot', data.content, data.nlu_data || null);
      if (settings.voiceOutput) speak(data.content);
    };
    const onErr = (data) => {
      setIsTyping(false);
      sfx('error');
      addMessage('error', data?.message || 'An error occurred');
    };

    socket.on('bot_typing', onTyping);
    socket.on('bot_response', onBot);
    socket.on('chat_message', onBot); // backward compat
    socket.on('error', onErr);
    return () => {
      socket.off('bot_typing', onTyping);
      socket.off('bot_response', onBot);
      socket.off('chat_message', onBot);
      socket.off('error', onErr);
    };
  }, [socket, addMessage, settings.voiceOutput, speak, sfx]);

  /* ---- welcome ---- */
  useEffect(() => {
    addMessage(
      'system',
      `Connection established. Welcome, **${user.username}**.\n\nType a question, hit a quick action, or press **Ctrl + K** for commands.`
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /* ---- voice recognition ---- */
  useEffect(() => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) return;
    const rec = new SR();
    rec.continuous = false;
    rec.interimResults = true;
    rec.lang = 'en-US';
    rec.onresult = (e) => {
      const t = Array.from(e.results)
        .map((r) => r[0].transcript)
        .join('');
      setInput(t);
      if (e.results[e.results.length - 1].isFinal) setIsListening(false);
    };
    rec.onerror = () => setIsListening(false);
    rec.onend = () => setIsListening(false);
    recognitionRef.current = rec;
    return () => rec.abort();
  }, []);

  const toggleVoice = () => {
    const rec = recognitionRef.current;
    if (!rec) {
      toast('Voice input not supported in this browser', 'warn');
      return;
    }
    if (isListening) {
      rec.stop();
      setIsListening(false);
    } else {
      try {
        rec.start();
        setIsListening(true);
        sfx('open');
      } catch {
        setIsListening(false);
      }
    }
  };

  /* ---- session controls ---- */
  const startNewSession = useCallback(() => {
    setSessionId(newSessionId());
    setMessages([]);
    addMessage('system', 'New session initialized. History cleared.');
    toast('New conversation started', 'info');
  }, [addMessage, toast]);

  const loadSession = useCallback(
    (session) => {
      setSessionId(session.session_id);
      setMessages(
        session.messages.map((m) => ({
          id: `${m.id}`,
          type: m.type,
          content: m.content,
          timestamp: m.timestamp || new Date().toISOString(),
          nluData: null,
          restored: true,
        }))
      );
      setShowHistory(false);
      toast(`Loaded "${session.title}"`, 'success');
    },
    [toast]
  );

  /* ---- export ---- */
  const exportChat = useCallback(() => {
    const md = messages
      .map(
        (m) =>
          `**${m.type.toUpperCase()}** (${new Date(
            m.timestamp
          ).toLocaleString()}):\n${m.content}\n`
      )
      .join('\n---\n\n');
    const blob = new Blob([`# Voxa conversation\n\n${md}`], {
      type: 'text/markdown',
    });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `voxa-${sessionId}.md`;
    a.click();
    URL.revokeObjectURL(a.href);
    toast('Conversation exported', 'success');
  }, [messages, sessionId, toast]);

  /* ---- command handling ---- */
  const runLocalCommand = useCallback(
    (raw) => {
      const [cmd, ...rest] = raw.trim().split(/\s+/);
      const arg = rest.join(' ');
      switch (cmd) {
        case '/help':
          addMessage(
            'system',
            'Available commands:\n\n' +
              SLASH_COMMANDS.map((s) => `\`${s.cmd}\` — ${s.desc}`).join('\n')
          );
          return true;
        case '/clear':
          setMessages([]);
          addMessage('system', 'Terminal cleared.');
          return true;
        case '/new':
          startNewSession();
          return true;
        case '/history':
          setShowHistory((v) => !v);
          return true;
        case '/settings':
          setShowSettings(true);
          return true;
        case '/export':
          exportChat();
          return true;
        case '/voice':
          toggle('voiceOutput');
          addMessage(
            'system',
            `Spoken responses ${settings.voiceOutput ? 'disabled' : 'enabled'}.`
          );
          return true;
        case '/theme': {
          const order = ['cyan', 'green', 'amber', 'magenta', 'ice'];
          const next =
            arg && order.includes(arg)
              ? arg
              : order[(order.indexOf(settings.theme) + 1) % order.length];
          update({ theme: next });
          addMessage('system', `Theme set to **${next}**.`);
          return true;
        }
        default:
          return false;
      }
    },
    [
      addMessage,
      startNewSession,
      exportChat,
      toggle,
      update,
      settings.voiceOutput,
      settings.theme,
    ]
  );

  const send = useCallback(
    (raw) => {
      const text = (raw ?? input).trim();
      if (!text) return;
      setInput('');
      setShowPalette(false);

      if (text.startsWith('/')) {
        addMessage('user', text);
        if (!runLocalCommand(text))
          addMessage('error', `Unknown command: ${text}. Try /help`);
        return;
      }

      addMessage('user', text);
      sfx('send');

      if (socket && socket.connected) {
        setIsTyping(true);
        socket.emit('chat_message', {
          message: text,
          session_id: sessionId,
          user_id: user.id || user.username,
        });
      } else {
        addMessage('error', 'Not connected to server. Reconnecting…');
      }
    },
    [input, addMessage, runLocalCommand, socket, sessionId, user, sfx]
  );

  /* ---- slash palette filter ---- */
  const paletteMatches = useMemo(() => {
    if (!input.startsWith('/')) return [];
    const q = input.slice(1).toLowerCase();
    return SLASH_COMMANDS.filter((s) => s.cmd.slice(1).startsWith(q));
  }, [input]);

  useEffect(() => {
    setShowPalette(input.startsWith('/') && paletteMatches.length > 0);
    setPaletteIdx(0);
  }, [input, paletteMatches.length]);

  /* ---- keyboard ---- */
  const onKeyDown = (e) => {
    if (showPalette && paletteMatches.length) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        setPaletteIdx((i) => (i + 1) % paletteMatches.length);
        return;
      }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        setPaletteIdx(
          (i) => (i - 1 + paletteMatches.length) % paletteMatches.length
        );
        return;
      }
      if (e.key === 'Tab') {
        e.preventDefault();
        setInput(paletteMatches[paletteIdx].cmd + ' ');
        return;
      }
    }
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  useEffect(() => {
    const onGlobal = (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setInput('/');
        inputRef.current?.focus();
      }
    };
    window.addEventListener('keydown', onGlobal);
    return () => window.removeEventListener('keydown', onGlobal);
  }, []);

  const statusMeta = {
    connected: { label: 'Online', cls: 'ok' },
    connecting: { label: 'Connecting', cls: 'warn' },
    reconnecting: { label: 'Reconnecting', cls: 'warn' },
    disconnected: { label: 'Offline', cls: 'bad' },
  }[connStatus] || { label: connStatus, cls: 'warn' };

  return (
    <div className="chat-shell">
      <header className="chat-header glass">
        <div className="chat-brand">
          <span className="brand-mark">◉</span>
          <span className="brand-name">VOXA</span>
          <span className="brand-sub">CLI</span>
        </div>

        <div className={`conn-pill conn-${statusMeta.cls}`}>
          <span className="conn-dot" />
          {statusMeta.label}
        </div>

        <div className="header-actions">
          <button
            className="hbtn"
            title="History"
            onClick={() => {
              setShowHistory((v) => !v);
              sfx('open');
            }}
          >
            🗂
          </button>
          <button
            className="hbtn"
            title="Settings"
            onClick={() => {
              setShowSettings(true);
              sfx('open');
            }}
          >
            ⚙
          </button>
          <button
            className="hbtn"
            title="NLU Admin"
            onClick={() => setShowAdmin(true)}
          >
            🛠
          </button>
          <div className="user-chip" style={{ '--uc': user.terminal_color }}>
            <span className="user-dot" />
            {user.username}
          </div>
          <button className="btn ghost" onClick={onLogout}>
            Logout
          </button>
        </div>
      </header>

      <main
        className="chat-body"
        ref={bodyRef}
        onScroll={onBodyScroll}
      >
        <div className="chat-stream">
          {messages.map((m, i) => (
            <MessageRow
              key={m.id}
              message={m}
              isLast={i === messages.length - 1}
              animations={settings.animations}
              onCopy={copy}
              onSpeak={speak}
            />
          ))}

          <AnimatePresence>
            {isTyping && (
              <motion.div
                className="msg msg-bot"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
              >
                <div className="msg-avatar">◉</div>
                <div className="msg-body">
                  <div className="typing">
                    <span />
                    <span />
                    <span />
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
          <div ref={endRef} />
        </div>

        <AnimatePresence>
          {!atBottom && (
            <motion.button
              className="scroll-fab"
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              onClick={() => scrollToBottom()}
              title="Jump to latest"
            >
              ↓
            </motion.button>
          )}
        </AnimatePresence>
      </main>

      {messages.filter((m) => m.type === 'user').length === 0 && (
        <div className="quick-actions">
          {QUICK_ACTIONS.map((q) => (
            <button
              key={q.label}
              className="quick-chip"
              onClick={() => send(q.text)}
            >
              <span>{q.icon}</span>
              {q.label}
            </button>
          ))}
        </div>
      )}

      <footer className="chat-input-wrap">
        <AnimatePresence>
          {showPalette && (
            <motion.div
              className="palette glass"
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: 8 }}
            >
              {paletteMatches.map((s, i) => (
                <button
                  key={s.cmd}
                  className={`palette-item ${i === paletteIdx ? 'active' : ''}`}
                  onMouseEnter={() => setPaletteIdx(i)}
                  onClick={() => {
                    if (s.cmd === '/theme') setInput('/theme ');
                    else send(s.cmd);
                  }}
                >
                  <span className="palette-cmd">{s.cmd}</span>
                  <span className="palette-desc">{s.desc}</span>
                </button>
              ))}
            </motion.div>
          )}
        </AnimatePresence>

        <div className="chat-input glass">
          <span className="prompt-sigil">❯</span>
          <textarea
            ref={inputRef}
            className="chat-textarea"
            rows={1}
            value={input}
            placeholder="Ask Voxa anything…  (/ for commands)"
            onChange={(e) => {
              setInput(e.target.value);
              if (e.target.value.length && e.nativeEvent.inputType)
                sfx('key');
            }}
            onKeyDown={onKeyDown}
            autoFocus
          />
          <button
            className={`mic-btn ${isListening ? 'listening' : ''}`}
            onClick={toggleVoice}
            title="Voice input"
          >
            {isListening ? '◉' : '🎙'}
          </button>
          <button
            className="send-btn"
            onClick={() => send()}
            disabled={!input.trim()}
            title="Send (Enter)"
          >
            ➤
          </button>
        </div>
      </footer>

      <AnimatePresence>
        {showHistory && (
          <HistorySidebar
            currentSessionId={sessionId}
            onClose={() => setShowHistory(false)}
            onLoad={loadSession}
            onNew={startNewSession}
          />
        )}
        {showSettings && (
          <SettingsPanel onClose={() => setShowSettings(false)} />
        )}
      </AnimatePresence>

      {showAdmin && (
        <AdminPanel user={user} onClose={() => setShowAdmin(false)} />
      )}
    </div>
  );
}
