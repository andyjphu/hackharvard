import { useState, useEffect, useRef } from 'react';
import './App.css';
import { X, Minus, Paperclip, Mic, MicOff, Send } from 'lucide-react';

function genId() {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

export default function App() {
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
  const [isTranscribing, setIsTranscribing] = useState(false);

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

  // Stream Python agent events (status/steps) into chat
  useEffect(() => {
    const formatEvent = (msg) => {
      const e = msg?.event;
      if (!e) return null;


      if (e === 'step') {
        const k = msg.kind;
        // short, readable one-liners
        if (k === 'focus.result')      return msg.success ? `🎯 Focused ${msg.app}` : `⚠️ Couldn’t focus ${msg.app}`;
        if (k === 'plan.start')        return `Planning steps for ${msg.app || 'current app'}…`;
        if (k === 'plan.created')      return `Plan created (${msg.steps} steps) → end: ${msg.end_state || '—'}`;
        if (k === 'loop.iteration')    return `Iteration ${msg.n}`;
        if (k === 'perceive.start')    return `Observing UI…`;
        if (k === 'perceive.end')      return `${msg.ui} UI | ${msg.visual} visual | ${msg.correlated} matched`;
        if (k === 'reason.start')      return `Reasoning…`;
        if (k === 'reason.end')        return `Plan ready (conf ${Number(msg.confidence || 0).toFixed(2)}, actions ${msg.actions || 0})`;
        if (k === 'action.execute')    return `Step ${msg.index}: ${msg.action || 'action'} ${msg.target ? '→ ' + msg.target : ''}`;
        if (k === 'action.result')     return msg.success ? `Step ${msg.index} done` : `Step ${msg.index} failed`;
        if (k === 'action.partial_return') return `🔄 Observing after step ${msg.completed}/${msg.total}…`;
        if (k === 'goal.achieved')     return `🎉 Goal achieved: ${msg.goal}`;
        if (k === 'loop.max_iterations') return `⏹️ Stopped at max iterations (${msg.iterations})`;
        // fallback
        return `ℹ️ ${k}: ${JSON.stringify(msg)}`;
      }

      // if (e === 'bridge_ready') {
      //   return `🧩 Python bridge ready (pid ${msg.pid})${msg.has_agent === false ? ' — agent_core not imported' : ''}`;
      // }
      if (e === 'warn') return `${msg.message || 'Warning from agent bridge'}`;
      if (e === 'started') return `Agent started in achieving "${msg.goal || '(none)'}"${msg.target_app ? ` in target app "${msg.target_app}"` : ''}`;
      if (e === 'selftest') return `🔬 Self-test\nPlatform: ${msg.platform}\nPython: ${String(msg.python_version).split('\n')[0]}\nGEMINI_API_KEY set: ${String(msg.env?.GEMINI_API_KEY_set)}\nagent_core import: ${String(msg.has_agent)}`;
      if (e === 'finished') {
        const r = msg.result || {};
        // return `🏁 Agent finished\nSuccess: ${String(r.success)}\nIterations: ${r.iterations ?? '—'}\nErrors: ${r.errors ?? '—'}\nProgress: ${typeof r.progress === 'number' ? r.progress.toFixed(2) : '—'}${r.message ? `\n${r.message}` : ''}`;
        return 'Task successfully completed!'
      }
      if (e === 'error') return `${msg.error || 'Unknown agent error'}`;
      if (e === 'pong') return `pong`;
      if (e === 'echo') return `echo: ${JSON.stringify(msg.data)}`;

      return `${e}: ${JSON.stringify(msg)}`;
    };

    const onAgentEvent = (_evt, msg) => {
      const t = formatEvent(msg);
      if (!t) return;
      setMessages(prev => [...prev, { id: genId(), role: 'assistant', text: t }]);
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
    }, 300000); // 5 min guard
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

  // ===== STT (ElevenLabs via main IPC) =====
  async function transcribeAudioBlob(blob) {
    if (!blob) return '';
    const buf = await blob.arrayBuffer();
    const bytes = Array.from(new Uint8Array(buf)); // serializable for IPC

    setIsTranscribing(true);
    try {
      const res = await window.ipcrenderer.invoke('stt/transcribe', {
        bytes,
        mime: blob.type || 'audio/webm',
      });
      const transcript = (typeof res === 'string') ? res : (res?.text ?? '');
      return transcript || '';
    } finally {
      setIsTranscribing(false);
    }
  }

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

        // Auto-transcribe immediately, then place text into the input
        (async () => {
          try {
            const t = await transcribeAudioBlob(blob);
            if (t) setText(prev => (prev ? `${prev} ${t}` : t));
            // Optional: clear the audio chip since we've converted it
            // setAudioBlob(null);
          } catch (e) {
            console.error('ElevenLabs STT error:', e);
            setMessages(prev => [...prev, { id: genId(), role: 'assistant', text: `🗣️ STT failed: ${e?.message || 'unknown error'}` }]);
          }
        })();
      };

      mr.start();
      setIsRecording(true);
    } catch (err) {
      console.error('Mic error:', err);
      setIsRecording(false);
    }
  };

  const stopRecording = async () => {
    const mr = mediaRecorderRef.current;
    if (mr && mr.state !== 'inactive') mr.stop();
    setIsRecording(false);
  };

  const toggleRecording = () => {
    if (awaitingResponse || isTranscribing) return;
    if (isRecording) stopRecording();
    else startRecording();
  };

  // ===== Send handling =====
  const handleSend = async () => {
    if (awaitingResponse) return;
    if (!text && files.length === 0 && !audioBlob) return;

    // If there’s audio but no text yet (user pressed send quickly), do a quick STT now
    let finalText = text;
    if (!finalText && audioBlob && !isTranscribing) {
      try { finalText = await transcribeAudioBlob(audioBlob); } catch {}
    }

    // Post the user's message
    const userMsg = {
      id: genId(),
      role: 'user',
      text: finalText || '',
      files: files.map(f => ({ name: f.name, type: f.type, size: f.size })),
      hasAudio: !!audioBlob,
    };
    setMessages(prev => [...prev, userMsg]);

    // Lock UI while agent runs
    lockComposer();

    try {
      await window.ipcrenderer.invoke('agent/run', {
        goal: finalText || text,
        target_app: null,
        max_iterations: 3,
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
      // Keep audioBlob if you want to show the chip; or clear it now:
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

        {/* Audio clip indicator (pre-send) + transcribe hint */}
        {audioBlob && !awaitingResponse && (
          <div className="mt-2 text-xs text-white/90">
            {isTranscribing && <span className="ml-2 opacity-80">⏳ Transcribing…</span>}
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
              disabled={awaitingResponse || isTranscribing}
            >
              <Paperclip className="w-5 h-5 text-white" />
            </button> */}
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              multiple
              onChange={handleFilesSelected}
              disabled={awaitingResponse || isTranscribing}
            />

            {/* Text input */}
            <input
              type="text"
              value={text}
              onChange={(e) => setText(e.target.value)}
              placeholder={
                awaitingResponse
                  ? 'Waiting for reply…'
                  : (isTranscribing ? 'Transcribing…' : 'Type your message…')
              }
              className="flex-1 w-1/2 bg-transparent text-sm outline-none text-white placeholder-white/60 px-1 py-2"
              aria-label="Message"
              disabled={awaitingResponse || isTranscribing}
            />

            {/* Mic toggle */}
            <button
              type="button"
              onClick={toggleRecording}
              className={`p-2 rounded-xl transition ${isRecording ? 'bg-red-500/30' : 'hover:bg-white/10'}`}
              title={isRecording ? 'Stop recording' : 'Start recording'}
              aria-pressed={isRecording}
              aria-label={isRecording ? 'Stop recording' : 'Start recording'}
              disabled={awaitingResponse || isTranscribing}
            >
              {isRecording ? (
                <MicOff className="w-5 h-5 text-white" />
              ) : (
                <Mic className="w-5 h-5 text-white" />
              )}
            </button>

            {/* Send (disabled until STT is done) */}
            <button
              type="submit"
              className="px-3 py-2 rounded-xl bg-white/15 hover:bg-white/25 transition flex items-center gap-1 disabled:opacity-60"
              title="Send"
              aria-label="Send message"
              disabled={
                awaitingResponse ||
                isTranscribing ||           // <-- keep disabled while STT runs
                (!text && files.length === 0 && !audioBlob)
              }
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
