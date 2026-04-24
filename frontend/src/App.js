import React, { useState, useRef, useEffect, useCallback } from "react";
import axios from "axios";

const API = "http://localhost:8000";

const C = {
  bg: "#0d0f14", surface: "#13161e", border: "#1e2330",
  accent: "#6c63ff", accentSoft: "rgba(108,99,255,0.12)",
  text: "#e8eaf0", muted: "#6b7280", success: "#22c55e",
  danger: "#ef4444", userBubble: "#6c63ff", aiBubble: "#1a1e2a",
};

const S = {
  root: { display: "flex", height: "100vh", background: C.bg, fontFamily: "'DM Sans', 'Segoe UI', sans-serif", color: C.text, overflow: "hidden" },
  sidebar: { width: 280, minWidth: 280, background: C.surface, borderRight: `1px solid ${C.border}`, display: "flex", flexDirection: "column", padding: "24px 16px", gap: 16 },
  logo: { fontSize: 22, fontWeight: 700, color: C.accent, letterSpacing: "-0.5px", paddingBottom: 16, borderBottom: `1px solid ${C.border}` },
  logoSub: { fontSize: 11, color: C.muted, fontWeight: 400, marginTop: 2 },
  dropZone: (dragging) => ({ border: `2px dashed ${dragging ? C.accent : C.border}`, borderRadius: 12, padding: "20px 12px", textAlign: "center", cursor: "pointer", background: dragging ? C.accentSoft : "transparent", transition: "all 0.2s" }),
  dropIcon: { fontSize: 28, marginBottom: 6 },
  dropText: { fontSize: 13, color: C.muted, lineHeight: 1.5 },
  docList: { flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: 6 },
  docItem: (active) => ({ padding: "10px 12px", borderRadius: 8, cursor: "pointer", background: active ? C.accentSoft : "transparent", border: `1px solid ${active ? C.accent : "transparent"}`, transition: "all 0.15s", fontSize: 13 }),
  docName: { fontWeight: 500, marginBottom: 2, wordBreak: "break-word" },
  docMeta: { fontSize: 11, color: C.muted, display: "flex", gap: 6, alignItems: "center" },
  main: { flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" },
  tabBar: { display: "flex", borderBottom: `1px solid ${C.border}`, background: C.surface, padding: "0 24px" },
  tab: (active) => ({ padding: "14px 20px", fontSize: 14, fontWeight: active ? 600 : 400, color: active ? C.accent : C.muted, cursor: "pointer", background: "none", border: "none", borderBottomWidth: 2, borderBottomStyle: "solid", borderBottomColor: active ? C.accent : "transparent", transition: "all 0.15s" }),
  chatPanel: { flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" },
  messages: { flex: 1, overflowY: "auto", padding: "24px", display: "flex", flexDirection: "column", gap: 16 },
  bubble: (isUser) => ({ maxWidth: "72%", alignSelf: isUser ? "flex-end" : "flex-start", background: isUser ? C.userBubble : C.aiBubble, border: isUser ? "none" : `1px solid ${C.border}`, borderRadius: isUser ? "18px 18px 4px 18px" : "18px 18px 18px 4px", padding: "12px 16px", fontSize: 14, lineHeight: 1.6, color: C.text }),
  bubbleMeta: { fontSize: 11, color: C.muted, marginTop: 6 },
  timestampChip: { display: "inline-flex", alignItems: "center", gap: 6, marginTop: 8, background: C.accentSoft, border: `1px solid ${C.accent}`, borderRadius: 20, padding: "4px 10px", fontSize: 12, color: C.accent, cursor: "pointer" },
  inputBar: { padding: "16px 24px", borderTop: `1px solid ${C.border}`, display: "flex", gap: 10, background: C.surface },
  input: { flex: 1, background: C.bg, border: `1px solid ${C.border}`, borderRadius: 10, padding: "12px 16px", color: C.text, fontSize: 14, outline: "none" },
  btn: (disabled) => ({ background: disabled ? C.border : C.accent, color: disabled ? C.muted : "#fff", border: "none", borderRadius: 10, padding: "12px 20px", fontSize: 14, fontWeight: 600, cursor: disabled ? "not-allowed" : "pointer", transition: "background 0.15s", whiteSpace: "nowrap" }),
  summaryPanel: { flex: 1, overflowY: "auto", padding: 24 },
  summaryCard: { background: C.surface, border: `1px solid ${C.border}`, borderRadius: 14, padding: 24, lineHeight: 1.8, fontSize: 14, whiteSpace: "pre-wrap" },
  tsPanel: { flex: 1, overflowY: "auto", padding: 24 },
  tsRow: { display: "flex", alignItems: "flex-start", gap: 12, padding: "12px 0", borderBottom: `1px solid ${C.border}` },
  tsBadge: { background: C.accentSoft, color: C.accent, borderRadius: 6, padding: "2px 8px", fontSize: 11, fontWeight: 600, whiteSpace: "nowrap", marginTop: 2 },
  tsText: { fontSize: 13, lineHeight: 1.5, color: C.text },
  empty: { flex: 1, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", color: C.muted, gap: 8, fontSize: 14 },
  status: (type) => ({ margin: "0 24px 12px", padding: "10px 14px", borderRadius: 8, fontSize: 13, background: type === "error" ? "rgba(239,68,68,0.1)" : type === "success" ? "rgba(34,197,94,0.1)" : C.accentSoft, color: type === "error" ? C.danger : type === "success" ? C.success : C.accent, border: `1px solid ${type === "error" ? C.danger : type === "success" ? C.success : C.accent}` }),
  loginWrap: { display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", background: C.bg },
  loginCard: { background: C.surface, border: `1px solid ${C.border}`, borderRadius: 16, padding: 40, width: 360, display: "flex", flexDirection: "column", gap: 16 },
  loginTitle: { fontSize: 24, fontWeight: 700, color: C.accent, textAlign: "center", marginBottom: 8 },
  loginInput: { background: C.bg, border: `1px solid ${C.border}`, borderRadius: 10, padding: "12px 16px", color: C.text, fontSize: 14, outline: "none", width: "100%", boxSizing: "border-box" },
  loginBtn: { background: C.accent, color: "#fff", border: "none", borderRadius: 10, padding: "13px", fontSize: 15, fontWeight: 600, cursor: "pointer", width: "100%" },
  loginHint: { fontSize: 12, color: C.muted, textAlign: "center" },
};

const fmtTime = (s) => {
  const m = Math.floor(s / 60);
  const sec = Math.floor(s % 60);
  return `${m}:${sec.toString().padStart(2, "0")}`;
};

const isVideoFile = (filename) => filename?.toLowerCase().endsWith(".mp4");
const isAudioFile = (filename) => [".mp3", ".wav", ".m4a"].some(ext => filename?.toLowerCase().endsWith(ext));
const isMediaFile = (filename) => isVideoFile(filename) || isAudioFile(filename);

const api = axios.create({ baseURL: API });
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("veda_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ─── Login Screen ─────────────────────────────────────────────────────────────
function LoginScreen({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    setLoading(true);
    setError("");
    try {
      const form = new FormData();
      form.append("username", username);
      form.append("password", password);
      const { data } = await axios.post(`${API}/auth/login`, form);
      localStorage.setItem("veda_token", data.access_token);
      onLogin(data.access_token);
    } catch {
      setError("Invalid username or password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={S.loginWrap}>
      <div style={S.loginCard}>
        <div style={S.loginTitle}>⬡ Veda</div>
        <div style={{ fontSize: 13, color: C.muted, textAlign: "center", marginBottom: 8 }}>Sign in to your AI assistant</div>
        {error && <div style={{ color: C.danger, fontSize: 13, textAlign: "center" }}>{error}</div>}
        <input style={S.loginInput} placeholder="Username" value={username} onChange={(e) => setUsername(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleLogin()} />
        <input style={S.loginInput} placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} onKeyDown={(e) => e.key === "Enter" && handleLogin()} />
        <button style={S.loginBtn} onClick={handleLogin} disabled={loading}>{loading ? "Signing in…" : "Sign In"}</button>
        <div style={S.loginHint}>Default: admin / secret</div>
      </div>
    </div>
  );
}

// ─── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [token, setToken] = useState(localStorage.getItem("veda_token"));
  const [documents, setDocuments] = useState([]);
  const [activeDoc, setActiveDoc] = useState(null);
  const [tab, setTab] = useState("chat");
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [summary, setSummary] = useState("");
  const [timestamps, setTimestamps] = useState([]);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [mediaUrl, setMediaUrl] = useState("");

  // Separate refs for audio and video — both always in DOM
  const audioRef = useRef(null);
  const videoRef = useRef(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => { if (token) fetchDocuments(); }, [token]);
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);

  useEffect(() => {
    if (!activeDoc) { setMediaUrl(""); return; }
    setMessages([]); setSummary(""); setTimestamps([]); setTab("chat");
    const url = isMediaFile(activeDoc.filename) ? `${API}/uploads/${activeDoc.filename}` : "";
    setMediaUrl(url);
  }, [activeDoc]);

  // Update the correct media element src without remounting
  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.src = (!activeDoc || isVideoFile(activeDoc.filename)) ? "" : mediaUrl;
      if (mediaUrl && isAudioFile(activeDoc?.filename)) audioRef.current.load();
    }
    if (videoRef.current) {
      videoRef.current.src = isVideoFile(activeDoc?.filename) ? mediaUrl : "";
      if (mediaUrl && isVideoFile(activeDoc?.filename)) videoRef.current.load();
    }
  }, [mediaUrl, activeDoc]);

  const showStatus = (text, type = "info", duration = 3000) => {
    setStatus({ text, type });
    if (duration) setTimeout(() => setStatus(null), duration);
  };

  const fetchDocuments = async () => {
    try {
      const { data } = await api.get("/documents");
      setDocuments(data.documents || []);
    } catch (e) {
      if (e.response?.status === 401) handleLogout();
      else showStatus("Failed to load documents", "error");
    }
  };

  const handleLogout = () => {
    localStorage.removeItem("veda_token");
    setToken(null); setDocuments([]); setActiveDoc(null); setMediaUrl("");
  };

  const uploadFile = async (file) => {
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    setLoading(true);
    showStatus(`Uploading ${file.name}…`, "info", 0);
    try {
      const { data } = await api.post("/upload", form);
      showStatus(`✓ ${file.name} uploaded`, "success");
      await fetchDocuments();
      setActiveDoc({ filename: data.filename, has_timestamps: data.has_timestamps, file_type: data.file_type });
    } catch (e) {
      showStatus(e.response?.data?.detail || "Upload failed", "error");
    } finally {
      setLoading(false);
    }
  };

  const sendChat = async () => {
    if (!question.trim() || !activeDoc) return;
    const q = question.trim();
    setMessages((m) => [...m, { role: "user", content: q }]);
    setQuestion(""); setLoading(true);
    try {
      const { data } = await api.post("/chat", { filename: activeDoc.filename, question: q });
      setMessages((m) => [...m, { role: "assistant", content: data.answer, timestamp: data.timestamp || null }]);
    } catch (e) {
      showStatus(e.response?.data?.detail || "Chat failed", "error");
    } finally { setLoading(false); }
  };

  const fetchSummary = async () => {
    if (!activeDoc || summary) return;
    setLoading(true);
    try {
      const { data } = await api.post("/summarize", { filename: activeDoc.filename });
      setSummary(data.summary);
    } catch (e) {
      showStatus(e.response?.data?.detail || "Summary failed", "error");
    } finally { setLoading(false); }
  };

  const fetchTimestamps = async () => {
    if (!activeDoc || timestamps.length) return;
    setLoading(true);
    try {
      const { data } = await api.get(`/timestamps/${activeDoc.filename}`);
      setTimestamps(data.timestamps || []);
    } catch (e) {
      showStatus("Failed to load timestamps", "error");
    } finally { setLoading(false); }
  };

  const deleteDoc = async (filename) => {
    try {
      await api.delete(`/documents/${filename}`);
      showStatus(`${filename} deleted`, "success");
      if (activeDoc?.filename === filename) { setActiveDoc(null); setMediaUrl(""); }
      await fetchDocuments();
    } catch { showStatus("Delete failed", "error"); }
  };

  // Seek the correct media element based on file type
  const playAt = useCallback((startSec) => {
    const isVid = isVideoFile(activeDoc?.filename);
    const media = isVid ? videoRef.current : audioRef.current;
    if (!media || !mediaUrl) return;
    const doSeek = () => {
      media.currentTime = startSec;
      media.play().catch(console.error);
    };
    if (media.readyState >= 2) doSeek();
    else media.addEventListener("canplay", doSeek, { once: true });
  }, [mediaUrl, activeDoc]);

  const handleTabChange = (t) => {
    setTab(t);
    if (t === "summary") fetchSummary();
    if (t === "timestamps") fetchTimestamps();
  };

  const onDrop = (e) => {
    e.preventDefault(); setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) uploadFile(file);
  };

  const showAudio = mediaUrl && isAudioFile(activeDoc?.filename);
  const showVideo = mediaUrl && isVideoFile(activeDoc?.filename);

  if (!token) return <LoginScreen onLogin={setToken} />;

  return (
    <div style={S.root}>

      {/* ── Persistent audio element — always in DOM, shown only for audio files ── */}
      <audio
        ref={audioRef}
        controls
        style={{
          position: "fixed", bottom: 0, left: 280, right: 0, zIndex: 100,
          background: C.surface, borderTop: `1px solid ${C.border}`,
          width: "calc(100% - 280px)", padding: "8px 24px", boxSizing: "border-box",
          display: showAudio ? "block" : "none", accentColor: C.accent,
        }}
      />

      {/* ── Persistent video element — always in DOM, shown only for video files ── */}
      <video
        ref={videoRef}
        controls
        style={{
          position: "fixed", bottom: 0, left: 280, right: 0, zIndex: 100,
          background: "#000", borderTop: `1px solid ${C.border}`,
          width: "calc(100% - 280px)", maxHeight: 240,
          display: showVideo ? "block" : "none",
        }}
      />

      <aside style={S.sidebar}>
        <div>
          <div style={S.logo}>⬡ Veda<div style={S.logoSub}>AI Document & Media Q&A</div></div>
        </div>
        <div style={S.dropZone(dragging)} onClick={() => fileInputRef.current.click()} onDragOver={(e) => { e.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={onDrop}>
          <div style={S.dropIcon}>📁</div>
          <div style={S.dropText}>Drop PDF, MP3, MP4, WAV here<br />or click to browse</div>
        </div>
        <input ref={fileInputRef} type="file" accept=".pdf,.mp3,.mp4,.wav,.m4a" style={{ display: "none" }} onChange={(e) => uploadFile(e.target.files[0])} />
        <div style={{ fontSize: 11, color: C.muted, textTransform: "uppercase", letterSpacing: 1 }}>Documents ({documents.length})</div>
        <div style={S.docList}>
          {documents.length === 0 && <div style={{ fontSize: 13, color: C.muted, textAlign: "center", marginTop: 12 }}>No files yet</div>}
          {documents.map((doc) => {
            const name = doc.filename || doc;
            const active = activeDoc?.filename === name;
            return (
              <div key={name} style={S.docItem(active)} onClick={() => setActiveDoc(doc)}>
                <div style={S.docName}>{name}</div>
                <div style={S.docMeta}>
                  {doc.file_type === "video" && <span>🎬 video</span>}
                  {doc.file_type === "audio" && <span>🎵 audio</span>}
                  {doc.has_timestamps && <span>⏱</span>}
                  <span style={{ marginLeft: "auto", color: C.danger, cursor: "pointer" }} onClick={(e) => { e.stopPropagation(); deleteDoc(name); }}>✕</span>
                </div>
              </div>
            );
          })}
        </div>
        <button style={{ ...S.btn(false), background: "transparent", color: C.muted, border: `1px solid ${C.border}`, padding: "8px 12px", fontSize: 13 }} onClick={handleLogout}>Sign Out</button>
      </aside>

      <main style={{ ...S.main, paddingBottom: (showAudio || showVideo) ? (showVideo ? 248 : 68) : 0 }}>
        {!activeDoc ? (
          <div style={S.empty}>
            <span style={{ fontSize: 64, marginBottom: 8 }}>⬡</span>
            <div style={{ fontSize: 22, fontWeight: 700, color: C.text, marginBottom: 4 }}>Welcome to Veda</div>
            <div style={{ fontSize: 14, color: C.muted, marginBottom: 28 }}>Your AI-powered document and media assistant</div>
            <div style={{ display: "flex", flexDirection: "column", gap: 12, width: 360 }}>
              {[
                { icon: "📄", label: "PDF Documents", desc: "Ask questions, get instant summaries" },
                { icon: "🎵", label: "Audio Files", desc: "Transcribe speech, search by timestamp" },
                { icon: "🎬", label: "Video Files", desc: "Extract key moments and play them" },
              ].map((item) => (
                <div key={item.label} style={{ display: "flex", alignItems: "center", gap: 14, padding: "14px 18px", background: C.surface, border: `1px solid ${C.border}`, borderRadius: 12, cursor: "pointer", transition: "border-color 0.2s" }} onClick={() => fileInputRef.current.click()} onMouseEnter={(e) => e.currentTarget.style.borderColor = C.accent} onMouseLeave={(e) => e.currentTarget.style.borderColor = C.border}>
                  <span style={{ fontSize: 28 }}>{item.icon}</span>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 14, fontWeight: 600, color: C.text }}>{item.label}</div>
                    <div style={{ fontSize: 12, color: C.muted, marginTop: 2 }}>{item.desc}</div>
                  </div>
                  <span style={{ color: C.accent, fontSize: 20 }}>+</span>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 24, fontSize: 12, color: C.muted }}>Drop files anywhere or use the sidebar to upload</div>
          </div>
        ) : (
          <>
            <div style={S.tabBar}>
              {["chat", "summary", "timestamps"].map((t) => (
                <button key={t} style={S.tab(tab === t)} onClick={() => handleTabChange(t)}>
                  {t === "chat" ? "💬 Chat" : t === "summary" ? "📋 Summary" : "⏱ Timestamps"}
                </button>
              ))}
              <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", fontSize: 13, color: C.muted }}>{activeDoc.filename}</div>
            </div>

            {status && <div style={S.status(status.type)}>{status.text}</div>}

            {tab === "chat" && (
              <div style={S.chatPanel}>
                <div style={S.messages}>
                  {messages.length === 0 && <div style={{ color: C.muted, fontSize: 14, textAlign: "center", marginTop: 40 }}>Ask Veda anything about <strong>{activeDoc.filename}</strong></div>}
                  {messages.map((msg, i) => (
                    <div key={i} style={S.bubble(msg.role === "user")}>
                      <div>{msg.content}</div>
                      {msg.timestamp && (
                        <div style={S.timestampChip} onClick={() => playAt(msg.timestamp.start)}>
                          ▶ Play {fmtTime(msg.timestamp.start)} – {fmtTime(msg.timestamp.end)}
                        </div>
                      )}
                      <div style={S.bubbleMeta}>{msg.role === "user" ? "You" : "Veda"}</div>
                    </div>
                  ))}
                  {loading && <div style={S.bubble(false)}><span style={{ color: C.muted }}>Veda is thinking…</span></div>}
                  <div ref={messagesEndRef} />
                </div>
                <div style={S.inputBar}>
                  <input style={S.input} placeholder="Ask a question about the document…" value={question} onChange={(e) => setQuestion(e.target.value)} onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendChat()} disabled={loading} />
                  <button style={S.btn(loading || !question.trim())} onClick={sendChat} disabled={loading || !question.trim()}>{loading ? "…" : "Send"}</button>
                </div>
              </div>
            )}

            {tab === "summary" && (
              <div style={S.summaryPanel}>
                {loading && <div style={{ color: C.muted, marginBottom: 16 }}>Generating summary…</div>}
                {!summary && !loading && <button style={{ ...S.btn(false), marginBottom: 16 }} onClick={fetchSummary}>Generate Summary</button>}
                {summary && <div style={S.summaryCard}>{summary}</div>}
              </div>
            )}

            {tab === "timestamps" && (
              <div style={S.tsPanel}>
                {!isMediaFile(activeDoc.filename) && <div style={{ color: C.muted, fontSize: 14 }}>Timestamps are only available for audio/video files.</div>}
                {isMediaFile(activeDoc.filename) && loading && <div style={{ color: C.muted }}>Loading timestamps…</div>}
                {isMediaFile(activeDoc.filename) && !loading && timestamps.length === 0 && <div style={{ color: C.muted, fontSize: 14 }}>No timestamps found.</div>}
                {isMediaFile(activeDoc.filename) && timestamps.map((seg, i) => (
                  <div key={i} style={S.tsRow}>
                    <div style={S.tsBadge}>{fmtTime(seg.start)}</div>
                    <div style={{ flex: 1 }}><div style={S.tsText}>{seg.text}</div></div>
                    <button style={{ ...S.btn(false), padding: "4px 12px", fontSize: 12 }} onClick={() => playAt(seg.start)}>▶ Play</button>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
