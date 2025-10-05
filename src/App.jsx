import { useState, useEffect, useRef } from 'react';
import './App.css';
import { X, Minus, Paperclip, Mic, MicOff, Send } from 'lucide-react';

function genId() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

export default function App() {
  const [image, setImage] = useState(null);

  // Chat state
  const [messages, setMessages] = useState(() => ([
    { id: genId(), role: 'assistant', text: 'Hey, how can I help you today?' }
  ]));
  const [awaitingResponse, setAwaitingResponse] = useState(false);

  // Composer state
  const [text, setText] = useState('');
  const [files, setFiles] = useState([]); // File[]
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);

  // Refs
  const listRef = useRef(null);
  const fileInputRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const responseTimeoutRef = useRef(null);

  // Auto-scroll to bottom on updates
  useEffect(() => {
    const el = listRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [messages, awaitingResponse]);

  // ★ NEW: stream Python agent events into the chat as “steps”
  useEffect(() => {
    const formatEvent = (msg) => {
      const e = msg?.event;
      if (!e) return null;

      if (e === 'bridge_ready') {
        return `🧩 Python bridge ready (pid ${msg.pid})${msg.has_agent === false ? ' — agent_core not imported' : ''}`;
      }
      if (e === 'warn') return `⚠️ ${msg.message || 'Warning from agent bridge'}`;
      if (e === 'started') return `🚀 Agent started\nGoal: ${msg.goal || '(none)'}${msg.target_app ? `\nTarget app: ${msg.target_app}` : ''}`;
      if (e === 'selftest') return `🔬 Self-test\nPlatform: ${msg.platform}\nPython: ${String(msg.python_version).split('\n')[0]}\nGEMINI_API_KEY set: ${String(msg.env?.GEMINI_API_KEY_set)}\nagent_core import: ${String(msg.has_agent)}`;
      if (e === 'finished') {
        const r = msg.result || {};
        return `🏁 Agent finished\nSuccess: ${String(r.success)}\nIterations: ${r.iterations ?? '—'}\nErrors: ${r.errors ?? '—'}\nProgress: ${typeof r.progress === 'number' ? r.progress.toFixed(2) : '—'}${r.message ? `\n${r.message}` : ''}`;
      }
      if (e === 'error') return `❌ ${msg.error || 'Unknown agent error'}`;
      if (e === 'pong') return `🏓 pong`;
      if (e === 'echo') return `🔁 echo: ${JSON.stringify(msg.data)}`;

      // Fallback: show raw event
      return `ℹ️ ${e}: ${JSON.stringify(msg)}`;
    };

    const onAgentEvent = (_evt, msg) => {
      const text = formatEvent(msg);
      if (!text) return;
      setMessages(prev => [...prev, { id: genId(), role: 'assistant', text }]);
    };

    window.ipcrenderer.on('agent-event', onAgentEvent);
    return () => window.ipcrenderer.off('agent-event', onAgentEvent);
  }, []);

  // Window controls
  const handleMinimize = () => window.ipcrenderer.send('minimize-window');
  const handleClose = () => window.ipcrenderer.send('close-window');

  // Lock / unlock composer with a safety timeout
  const lockComposer = () => {
    setAwaitingResponse(true);
    clearTimeout(responseTimeoutRef.current);
    responseTimeoutRef.current = setTimeout(() => {
      setAwaitingResponse(false);
      setMessages(prev => [
        ...prev,
        { id: genId(), role: 'assistant', text: '⏳ Still working… you can type again if needed.' }
      ]);
    }, 300000);
  };
  const unlockComposer = () => {
    clearTimeout(responseTimeoutRef.current);
    responseTimeoutRef.current = null;
    setAwaitingResponse(false);
  };

  // ===== File handling =====
  const handleChooseFiles = () => fileInputRef.current?.click();
  const handleFilesSelected = (e) => {
    const selected = Array.from(e.target.files || []);
    if (selected.length) setFiles(prev => [...prev, ...selected]);
    e.target.value = ''; // allow reselecting same file
  };
  const removeFileAt = (idx) => {
    if (awaitingResponse) return;
    setFiles(prev => prev.filter((_, i) => i !== idx));
  };

  // ===== Mic handling =====
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mr = new MediaRecorder(stream);
      mediaRecorderRef.current = mr;
      audioChunksRef.current = [];

      mr.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) audioChunksRef.current.push(e.data);
      };
      mr.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        setAudioBlob(blob);
        stream.getTracks().forEach(t => t.stop());
      };

      mr.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Mic error:', err);
      setIsRecording(false);
    }
  };

  const stopRecording = () => {
    const mr = mediaRecorderRef.current;
    if (mr && mr.state !== 'inactive') mr.stop();
    setIsRecording(false);
  };

  const toggleRecording = () => {
    if (awaitingResponse) return;
    if (isRecording) stopRecording();
    else startRecording();
  };

  // ===== Send handling (invoke/handle path) =====
  const handleSend = async () => {
    if (awaitingResponse) return;
    if (!text && files.length === 0 && !audioBlob) return;

    // Optimistically add the user's message
    const userMsg = {
      id: genId(),
      role: 'user',
      text: text || '',
      files: files.map(f => ({ name: f.name, type: f.type, size: f.size })),
      hasAudio: !!audioBlob,
    };
    setMessages(prev => [...prev, userMsg]);

    // Lock UI while waiting
    lockComposer();

    try {
      // ★ CHANGED: call your Python-backed agent
        await window.ipcrenderer.invoke('agent/run', {
          goal: text, target_app: null, max_iterations: 3,
        });
    } catch (e) {
      setMessages(prev => [
        ...prev,
        { id: genId(), role: 'assistant', text: `⚠️ ${e?.message || 'Failed to run agent.'}` }
      ]);
    } finally {
      // Clear composer + unlock
      setText('');
      setFiles([]);
      setAudioBlob(null);
      if (isRecording) stopRecording();
      unlockComposer();
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    handleSend();
  };

  return (
    <>
      <div className="glass-container flex flex-col px-4 backdrop-blur-3xl">
        {/* Window controls */}
        <div className="w-full flex justify-end pt-2">
          <div className="flex backdrop-blur-3xl bg-sky-300/[0.15] px-2 rounded">
            <div>
              <Minus onClick={handleMinimize} className="w-[18px] text-white mr-2 hover:w-[22px] transition-all cursor-pointer" />
            </div>
            <X onClick={handleClose} className="w-[18px] text-white hover:w-[22px] transition-all cursor-pointer" />
          </div>
        </div>

        {/* ===== Messages list ===== */}
        <div ref={listRef} className="messages_list flex-1 mt-3 overflow-y-auto pr-1 space-y-2">
          {messages.map(m => (
            <div key={m.id} className={m.role === 'user' ? 'flex justify-end' : 'flex justify-start'}>
              <div
                className={
                  m.role === 'user'
                    ? 'max-w-[85%] bg-sky-300/20 text-white text-sm px-3 py-2 rounded-2xl rounded-tr-sm ring-1 ring-white/10'
                    : 'max-w-[85%] bg-white/10 text-white text-sm px-3 py-2 rounded-2xl rounded-tl-sm ring-1 ring-white/10'
                }
              >
                <p className="whitespace-pre-wrap">{m.text}</p>

                {/* Attached files summary */}
                {m.files?.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {m.files.map((f, i) => (
                      <span key={i} className="text-[11px] px-2 py-1 rounded-full bg-white/10 ring-1 ring-white/10">
                        {f.name}
                      </span>
                    ))}
                  </div>
                )}

                {/* Audio presence */}
                {m.hasAudio && (
                  <div className="mt-2 text-[11px] opacity-80">🎙️ Audio attached</div>
                )}
              </div>
            </div>
          ))}

          {/* Assistant thinking indicator */}
          {awaitingResponse && (
            <div className="flex justify-start">
              <div className="max-w-[70%] bg-white/10 text-white text-sm px-3 py-2 rounded-2xl rounded-tl-sm ring-1 ring-white/10">
                <span className="inline-flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-white/70 animate-pulse"></span>
                  <span className="w-2 h-2 rounded-full bg-white/70 animate-pulse [animation-delay:120ms]"></span>
                  <span className="w-2 h-2 rounded-full bg-white/70 animate-pulse [animation-delay:240ms]"></span>
                  <span className="sr-only">Assistant is typing…</span>
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Selected file chips (pre-send) */}
        {files.length > 0 && !awaitingResponse && (
          <div className="mt-2 flex flex-wrap gap-2">
            {files.map((f, i) => (
              <div
                key={`${f.name}-${i}`}
                className="flex items-center gap-2 px-2 py-1 rounded-full bg-white/10 text-white text-xs ring-1 ring-white/10"
              >
                <span className="truncate max-w-[160px]">{f.name}</span>
                <button
                  type="button"
                  onClick={() => removeFileAt(i)}
                  className="text-white/80 hover:text-white"
                  aria-label={`Remove ${f.name}`}
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}

        {/* Audio clip indicator (pre-send) */}
        {audioBlob && !awaitingResponse && (
          <div className="mt-2 text-xs text-white/90">
            🎙️ Recorded audio ready ({Math.round(audioBlob.size / 1024)} KB)
          </div>
        )}

        {/* ===== Footer composer ===== */}
        <form onSubmit={handleSubmit} className="sticky bottom-0 left-0 right-0 py-3">
          <div className={`w-full rounded-2xl bg-sky-300/10 backdrop-blur-2xl border border-white/10 p-2 flex items-center gap-2 ${awaitingResponse ? 'opacity-60' : ''}`}>

            {/* File button (optional) */}
            {/* <button
              type="button"
              onClick={handleChooseFiles}
              className="rounded-xl hover:bg-white/10 transition p-2"
              title="Attach files"
              aria-label="Attach files"
              disabled={awaitingResponse}
            >
              <Paperclip className="w-5 h-5 text-white" />
            </button> */}
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              multiple
              onChange={handleFilesSelected}
              disabled={awaitingResponse}
            />

            {/* Text input */}
            <input
              type="text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder={awaitingResponse ? 'Waiting for reply…' : 'Type your message…'}
              className="flex-1 w-1/2 bg-transparent text-sm outline-none text-white placeholder-white/60 px-1 py-2"
              aria-label="Message"
              disabled={awaitingResponse}
            />

            {/* Mic toggle */}
            <button
              type="button"
              onClick={toggleRecording}
              className={`p-2 rounded-xl transition ${isRecording ? 'bg-red-500/30' : 'hover:bg-white/10'}`}
              title={isRecording ? 'Stop recording' : 'Start recording'}
              aria-pressed={isRecording}
              aria-label={isRecording ? 'Stop recording' : 'Start recording'}
              disabled={awaitingResponse}
            >
              {isRecording ? (
                <MicOff className="w-5 h-5 text-white" />
              ) : (
                <Mic className="w-5 h-5 text-white" />
              )}
            </button>

            {/* Send */}
            <button
              type="submit"
              className="px-3 py-2 rounded-xl bg-white/15 hover:bg-white/25 transition flex items-center gap-1 disabled:opacity-60"
              title="Send"
              aria-label="Send message"
              disabled={awaitingResponse || (!text && files.length === 0 && !audioBlob)}
            >
              <Send className="w-5 h-5 text-white" />
              <span className="sr-only">Send</span>
            </button>
          </div>
        </form>
      </div>
    </>
  );
}
