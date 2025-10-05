import { useState, useEffect, useRef } from 'react';
import './App.css';
import { X, Minus, Mic, MicOff, Send } from 'lucide-react';

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

  // TTS controls
  const [voiceOn, setVoiceOn] = useState(true);
  const audioRef = useRef(null);
  const lastSpokenIdRef = useRef(null);

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

  // Human-friendly event text for steps
  useEffect(() => {
    function formatCountWord(n) {
      if (n <= 0 || n == null) return 'nothing';
      if (n <= 3) return 'a few things';
      if (n <= 10) return 'several things';
      return 'many things';
    }

    function humanizeAction(action) {
      const map = {
        click: 'click',
        tap: 'tap',
        type: 'type',
        open_app: 'open',
        focus: 'open',
        press_key: 'press a key',
        select: 'select',
        scroll: 'scroll'
      };
      return map[action] || action || 'do something';
    }

    function formatEvent(msg) {
      if (msg?.event !== 'step') {
        if (msg?.event === 'started')   return `Okay — I’ll do: “${msg.goal || 'your task'}”.`;
        if (msg?.event === 'finished')  return `All set! I’m done.`;
        if (msg?.event === 'error')     return `Hmm, something went wrong. I’ll try another way.`;
        return null;
      }

      const k = msg.kind;

      if (k === 'focus.result') {
        return msg.success
          ? `I’ve opened ${msg.app}.`
          : `I couldn’t open ${msg.app}. I’ll try a different way.`;
      }
      if (k === 'plan.start') {
        return `I’m planning the steps.`;
      }
      if (k === 'plan.created') {
        const count = msg.steps ?? 0;
        return count > 0
          ? `I have a short plan with ${count} step${count > 1 ? 's' : ''}.`
          : `I’ll take it one step at a time.`;
      }
      if (k === 'loop.iteration') {
        return `Working… (round ${msg.n}).`;
      }
      if (k === 'perceive.start') {
        return `I’m looking at what’s on the screen.`;
      }
      if (k === 'perceive.end') {
        const found = formatCountWord(Number(msg.ui || 0) + Number(msg.visual || 0));
        return `I can see the screen now — I found ${found}.`;
      }
      if (k === 'reason.start') {
        return `I’m deciding the next best step.`;
      }
      if (k === 'reason.end') {
        const a = msg.actions ?? 0;
        if (a <= 0) return `I know what to do next.`;
        if (a === 1) return `I’ll do the next step now.`;
        return `I’ve got the next few steps ready.`;
      }
      if (k === 'action.execute') {
        const verb = humanizeAction(msg.action);
        if (msg.target) return `Now I’ll ${verb} “${msg.target}”.`;
        return `Now I’ll ${verb}.`;
      }
      if (k === 'action.result') {
        return msg.success ? `That worked.` : `That didn’t work — I’ll try another way.`;
      }
      if (k === 'action.partial_return') {
        return `Checking how that went…`;
      }
      if (k === 'goal.achieved') {
        return `All set — I finished that task.`;
      }
      if (k === 'loop.max_iterations') {
        return `I couldn’t finish this time. Want me to keep trying?`;
      }
      return null;
    }

    const onAgentEvent = (_evt, msg) => {
      const t = formatEvent(msg);
      if (!t) return;
      setMessages(prev => [...prev, { id: genId(), role: 'assistant', text: t }]);
    };

    window.ipcrenderer.on('agent-event', onAgentEvent);
    return () => window.ipcrenderer.off('agent-event', onAgentEvent);
  }, []);

  // ---------- TTS helpers (ElevenLabs via main IPC) ----------
  function playBase64Audio(base64, mime = 'audio/mpeg') {
    try {
      const bstr = atob(base64);
      const bytes = new Uint8Array(bstr.length);
      for (let i = 0; i < bstr.length; i++) bytes[i] = bstr.charCodeAt(i);
      const blob = new Blob([bytes], { type: mime });
      const url = URL.createObjectURL(blob);

      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = '';
        audioRef.current = null;
      }

      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => URL.revokeObjectURL(url);
      audio.play().catch(() => URL.revokeObjectURL(url));
    } catch (e) {
      console.error('Audio playback failed:', e);
    }
  }

  async function speak(text) {
    if (!voiceOn || !text) return;
    try {
      const { audioBase64, mime } = await window.ipcrenderer.invoke('tts/speak', { text });
      if (audioBase64) playBase64Audio(audioBase64, mime);
    } catch (e) {
      console.error('TTS failed:', e);
    }
  }

  function stopSpeech() {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.src = '';
      audioRef.current = null;
    }
  }

  // Auto-speak the latest assistant message once
  useEffect(() => {
    if (!voiceOn) return;
    const last = [...messages].reverse().find(m => m.role === 'assistant' && m.text);
    if (!last) return;
    if (lastSpokenIdRef.current === last.id) return;
    lastSpokenIdRef.current = last.id;
    speak(last.text);
  }, [messages, voiceOn]);

  // ---------- Window controls ----------
  const handleMinimize = () => window.ipcrenderer.send('minimize-window');
  const handleClose = () => window.ipcrenderer.send('close-window');

  // ---------- Lock / unlock composer ----------
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

  // ---------- File handling ----------
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

  // ---------- STT (ElevenLabs via main IPC) ----------
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

  // ---------- Mic handling ----------
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

        (async () => {
          try {
            const t = await transcribeAudioBlob(blob);
            if (t) setText(prev => (prev ? `${prev} ${t}` : t));
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

  // ---------- Send handling ----------
  const handleSend = async () => {
    if (awaitingResponse) return;
    if (!text && files.length === 0 && !audioBlob) return;

    // If audio exists but no text yet, transcribe now
    let finalText = text;
    if (!finalText && audioBlob && !isTranscribing) {
      try { finalText = await transcribeAudioBlob(audioBlob); } catch {}
    }

    const userMsg = {
      id: genId(),
      role: 'user',
      text: finalText || '',
      files: files.map(f => ({ name: f.name, type: f.type, size: f.size })),
      hasAudio: !!audioBlob,
    };
    setMessages(prev => [...prev, userMsg]);

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
        {/* Header: window + voice controls */}
        <div className="w-full flex items-center justify-between pt-2">
          <div className="flex items-center gap-3 text-xs text-white/90">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={voiceOn}
                onChange={(e) => setVoiceOn(e.target.checked)}
              />
              Voice
            </label>
            <button
              onClick={stopSpeech}
              className="text-white/80 hover:text-white px-2 py-1 rounded bg-white/10"
            >
              Stop voice
            </button>
          </div>
          <div className="flex backdrop-blur-3xl bg-sky-300/[0.15] px-2 rounded">
            <div>
              <Minus onClick={handleMinimize} className="w-[18px] text-white mr-2 hover:w-[22px] transition-all cursor-pointer" />
            </div>
            <X onClick={handleClose} className="w-[18px] text-white hover:w-[22px] transition-all cursor-pointer" />
          </div>
        </div>

        {/* Messages */}
        <div ref={listRef} className="messages_list flex-1 mt-3 overflow-y-auto pr-1 space-y-2">
          {messages.map(m => (
            <div key={m.id} className={m.role === 'user' ? 'flex justify-end' : 'flex justify-start'}>
              <div
                className={
                  m.role === 'user'
                    ? 'max-w-[85%] bg-sky-300/20 text-white text-sm px-3 py-2 rounded-2xl rounded-tr-sm ring-1 ring-white/10'
                    : 'max-w-[85%] bg-white/10 text-white text-lg font-light px-3 py-2 rounded-2xl rounded-tl-sm ring-1 ring-white/10'
                }
              >
                <p className="whitespace-pre-wrap text-left">{m.text}</p>

                {m.files?.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {m.files.map((f, i) => (
                      <span key={i} className="text-[11px] px-2 py-1 rounded-full bg-white/10 ring-1 ring-white/10">
                        {f.name}
                      </span>
                    ))}
                  </div>
                )}

                {m.hasAudio && (
                  <div className="mt-2 text-[11px] opacity-80">Audio attached</div>
                )}
              </div>
            </div>
          ))}

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

        {/* Selected file chips */}
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

        {/* Audio indicator / Transcribing */}
        {audioBlob && !awaitingResponse && (
          <div className="mt-2 text-xs text-white/90">
            {isTranscribing && <span className="ml-2 opacity-80">Transcribing…</span>}
          </div>
        )}

        {/* Composer */}
        <form onSubmit={handleSubmit} className="sticky bottom-0 left-0 right-0 py-3">
          <div className={`w-full rounded-2xl bg-sky-300/10 backdrop-blur-2xl border border-white/10 p-2 flex items-center gap-2 ${awaitingResponse ? 'opacity-60' : ''}`}>

            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              multiple
              onChange={handleFilesSelected}
              disabled={awaitingResponse || isTranscribing}
            />

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

            <button
              type="submit"
              className="px-3 py-2 rounded-xl bg-white/15 hover:bg-white/25 transition flex items-center gap-1 disabled:opacity-60"
              title="Send"
              aria-label="Send message"
              disabled={
                awaitingResponse ||
                isTranscribing ||           // disabled during STT
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
