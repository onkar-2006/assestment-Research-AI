import React, { useState, useRef, useEffect, useMemo } from 'react';
import axios from 'axios';
import './App.css';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState('');
  const scrollRef = useRef(null);

  // 1. Generate a stable Session ID for memory
  const threadId = useMemo(() => crypto.randomUUID(), []);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const onUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    setUploading(true);
    setStatus('Processing PDF...');

    try {
      const res = await axios.post(`${API_BASE_URL}/upload`, formData);
      setStatus(`Success! Split into ${res.data.chunks_created} chunks.`);
    } catch (err) {
      setStatus('Upload failed. Check backend connection.');
    } finally {
      setUploading(false);
    }
  };

  const onSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userMsg = { text: input, sender: 'user', id: Date.now() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);

    try {
      const res = await axios.post(`${API_BASE_URL}/chat`, { 
        message: input,
        thread_id: threadId // 2. Pass thread_id for backend memory
      });
      
      setMessages(prev => [...prev, { text: res.data.response, sender: 'ai', id: Date.now() + 1 }]);
    } catch (err) {
      setMessages(prev => [...prev, { text: "Error: Could not reach agent.", sender: 'ai', id: Date.now() + 1 }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <aside className="sidebar">
        <div className="logo">
          <span className="icon">🔬</span>
          <h1>Research AI</h1>
        </div>
        
        <div className="upload-box">
          <p>Analyze New Paper</p>
          <label className={`upload-btn ${uploading ? 'disabled' : ''}`}>
            {uploading ? '⏳ Processing...' : '➕ Upload PDF'}
            <input type="file" hidden onChange={onUpload} accept=".pdf" disabled={uploading} />
          </label>
        </div>

        {status && <div className="status-badge">{status}</div>}
        
        <div className="sidebar-footer">
          <small>Session ID: {threadId.slice(0, 8)}</small>
        </div>
      </aside>

      <main className="main-chat">
        <div className="chat-window">
          {messages.length === 0 && (
            <div className="welcome-screen">
              <h2>How can I help with your research?</h2>
              <p>Upload a PDF to ask specific questions or search ArXiv for new topics.</p>
            </div>
          )}
          
          {messages.map((m) => (
            <div key={m.id} className={`message-row ${m.sender === 'user' ? 'user-row' : 'ai-row'}`}>
              <div className="avatar">{m.sender === 'user' ? '👤' : '🤖'}</div>
              <div className="bubble">
                {m.text}
              </div>
            </div>
          ))}
          
          {loading && (
            <div className="message-row ai-row">
              <div className="avatar">🤖</div>
              <div className="bubble thinking">
                <span className="dot"></span><span className="dot"></span><span className="dot"></span>
              </div>
            </div>
          )}
          <div ref={scrollRef} />
        </div>

        <div className="input-container">
          <form className="input-wrapper" onSubmit={onSend}>
            <input 
              type="text" 
              placeholder="Ask a question or search ArXiv..." 
              value={input}
              onChange={(e) => setInput(e.target.value)}
            />
            <button className="send-icon-btn" type="submit" disabled={!input.trim() || loading}>
              <svg viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}

export default App;