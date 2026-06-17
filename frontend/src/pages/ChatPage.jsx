import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  MessageSquare,
  Plus,
  Send,
  LogOut,
  Paperclip,
  Bot,
  User,
  ChevronLeft,
  ChevronRight,
  Loader2,
} from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { apiCreateThread, apiGetThreads, apiUploadFile } from '../api';

// ── Typing indicator ──────────────────────────────────────────────────────────
function TypingIndicator() {
  return (
    <div className="flex items-start gap-3">
      <div className="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
        <Bot className="w-4 h-4 text-blue-600" />
      </div>
      <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm px-4 py-3">
        <div className="flex gap-1">
          <span className="typing-dot w-2 h-2 bg-gray-400 rounded-full inline-block" />
          <span className="typing-dot w-2 h-2 bg-gray-400 rounded-full inline-block" />
          <span className="typing-dot w-2 h-2 bg-gray-400 rounded-full inline-block" />
        </div>
      </div>
    </div>
  );
}

// ── Chat message ──────────────────────────────────────────────────────────────
function Message({ role, content }) {
  const isUser = role === 'user';
  return (
    <div className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div
        className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 ${
          isUser ? 'bg-blue-600' : 'bg-blue-100'
        }`}
      >
        {isUser ? (
          <User className="w-4 h-4 text-white" />
        ) : (
          <Bot className="w-4 h-4 text-blue-600" />
        )}
      </div>
      <div
        className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
          isUser
            ? 'bg-blue-600 text-white rounded-tr-sm'
            : 'bg-white border border-gray-200 text-gray-800 rounded-tl-sm'
        }`}
      >
        {content}
      </div>
    </div>
  );
}

// ── Main Chat Page ────────────────────────────────────────────────────────────
export default function ChatPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [threads, setThreads] = useState([]);
  const [activeThread, setActiveThread] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [loadingThreads, setLoadingThreads] = useState(true);
  const [uploadingFile, setUploadingFile] = useState(false);

  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const textareaRef = useRef(null);

  // Load threads on mount
  useEffect(() => {
    loadThreads();
  }, []);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  async function loadThreads() {
    try {
      const data = await apiGetThreads();
      setThreads(data.threads || []);
    } catch (err) {
      console.error('Failed to load threads:', err);
    } finally {
      setLoadingThreads(false);
    }
  }

  async function handleNewChat() {
    try {
      const data = await apiCreateThread();
      const newThread = {
        thread_id: data.thread_id,
        title: 'New Chat',
        created_at: new Date().toISOString(),
      };
      setThreads((prev) => [newThread, ...prev]);
      setActiveThread(newThread);
      setMessages([]);
    } catch (err) {
      console.error('Failed to create thread:', err);
    }
  }

  function handleSelectThread(thread) {
    setActiveThread(thread);
    // In a real app you'd load thread messages from the backend here
    setMessages([]);
  }

  async function handleSend() {
    const text = input.trim();
    if (!text || !activeThread) return;

    const userMsg = { role: 'user', content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput('');
    setIsTyping(true);

    // Resize textarea back
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    try {
      // ── Real integration: POST to your chat endpoint ──
      // Replace this block with your actual backend chat endpoint call
      // e.g. const res = await apiChat(activeThread.thread_id, text);
      await new Promise((r) => setTimeout(r, 1200));
      const botMsg = {
        role: 'assistant',
        content: `This is a placeholder response. Connect your chat endpoint to get real AI replies for thread: ${activeThread.thread_id}`,
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `Error: ${err.message}` },
      ]);
    } finally {
      setIsTyping(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function handleTextareaChange(e) {
    setInput(e.target.value);
    // Auto-resize
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 160) + 'px';
  }

  async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file || !activeThread) return;

    setUploadingFile(true);
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: `📎 Uploading file: ${file.name}` },
    ]);

    try {
      const result = await apiUploadFile(activeThread.thread_id, file);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: result.success
            ? `✅ File "${file.name}" uploaded and processed successfully. You can now ask questions about it.`
            : `❌ Upload failed: ${result.error}`,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: `❌ Upload error: ${err.message}` },
      ]);
    } finally {
      setUploadingFile(false);
      e.target.value = '';
    }
  }

  function handleLogout() {
    logout();
    navigate('/login', { replace: true });
  }

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">

      {/* ── Sidebar ───────────────────────────────────────────────────────── */}
      <aside
        className={`${
          sidebarOpen ? 'w-64' : 'w-0'
        } transition-all duration-300 bg-white border-r border-gray-200 flex flex-col overflow-hidden flex-shrink-0`}
      >
        {/* Sidebar Header */}
        <div className="p-4 border-b border-gray-100 flex items-center gap-2">
          <div className="w-7 h-7 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
            <MessageSquare className="w-4 h-4 text-white" />
          </div>
          <span className="font-semibold text-gray-800 text-sm truncate">ChatAgent</span>
        </div>

        {/* New Chat Button */}
        <div className="p-3">
          <button
            id="new-chat-btn"
            onClick={handleNewChat}
            className="w-full flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition"
          >
            <Plus className="w-4 h-4" />
            New chat
          </button>
        </div>

        {/* Thread List */}
        <div className="flex-1 overflow-y-auto px-2 pb-2">
          {loadingThreads ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-5 h-5 text-gray-400 animate-spin" />
            </div>
          ) : threads.length === 0 ? (
            <p className="text-xs text-gray-400 text-center py-8 px-3">
              No conversations yet. Start a new chat!
            </p>
          ) : (
            <div className="space-y-0.5">
              {threads.map((t) => (
                <button
                  key={t.thread_id}
                  onClick={() => handleSelectThread(t)}
                  className={`w-full text-left px-3 py-2 rounded-lg text-sm transition truncate ${
                    activeThread?.thread_id === t.thread_id
                      ? 'bg-blue-50 text-blue-700 font-medium'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  {t.title || 'New Chat'}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Sidebar Footer – User info + Logout */}
        <div className="p-3 border-t border-gray-100">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 bg-gray-200 rounded-full flex items-center justify-center flex-shrink-0">
              <User className="w-4 h-4 text-gray-500" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-gray-700 truncate">{user?.name || user?.email || 'User'}</p>
              <p className="text-xs text-gray-400 truncate">{user?.email}</p>
            </div>
            <button
              id="logout-btn"
              onClick={handleLogout}
              title="Sign out"
              className="text-gray-400 hover:text-red-500 transition p-1 rounded"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* ── Main Panel ──────────────────────────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0">

        {/* Top bar */}
        <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3">
          <button
            id="toggle-sidebar-btn"
            onClick={() => setSidebarOpen((p) => !p)}
            className="text-gray-400 hover:text-gray-600 transition"
          >
            {sidebarOpen ? <ChevronLeft className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
          </button>
          <h2 className="text-sm font-medium text-gray-700 flex-1">
            {activeThread ? (activeThread.title || 'New Chat') : 'Select or start a conversation'}
          </h2>
        </header>

        {/* Messages area */}
        <div className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
          {!activeThread ? (
            /* Welcome state */
            <div className="h-full flex flex-col items-center justify-center text-center px-8">
              <div className="w-14 h-14 bg-blue-100 rounded-2xl flex items-center justify-center mb-4">
                <Bot className="w-7 h-7 text-blue-600" />
              </div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">
                How can I help you today?
              </h3>
              <p className="text-sm text-gray-500 mb-6 max-w-sm">
                Start a new chat or select an existing conversation from the sidebar.
                You can also upload documents for the AI to analyze.
              </p>
              <button
                onClick={handleNewChat}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition"
              >
                <Plus className="w-4 h-4" />
                Start new chat
              </button>
            </div>
          ) : messages.length === 0 ? (
            /* Empty thread */
            <div className="h-full flex flex-col items-center justify-center text-center px-8">
              <p className="text-sm text-gray-400">Send a message to get started.</p>
            </div>
          ) : (
            /* Message list */
            <>
              {messages.map((msg, i) => (
                <Message key={i} role={msg.role} content={msg.content} />
              ))}
              {isTyping && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input bar */}
        {activeThread && (
          <div className="bg-white border-t border-gray-200 px-4 py-3">
            <div className="flex items-end gap-2 max-w-4xl mx-auto">
              {/* File upload */}
              <input
                ref={fileInputRef}
                type="file"
                id="file-upload-input"
                className="hidden"
                accept=".pdf,.docx,.pptx,.txt"
                onChange={handleFileUpload}
              />
              <button
                id="attach-file-btn"
                onClick={() => fileInputRef.current?.click()}
                disabled={uploadingFile}
                title="Upload document"
                className="p-2 text-gray-400 hover:text-blue-600 transition rounded-lg hover:bg-gray-100 flex-shrink-0 disabled:opacity-40"
              >
                {uploadingFile ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <Paperclip className="w-5 h-5" />
                )}
              </button>

              {/* Text input */}
              <textarea
                ref={textareaRef}
                id="chat-input"
                rows={1}
                value={input}
                onChange={handleTextareaChange}
                onKeyDown={handleKeyDown}
                placeholder="Type a message… (Enter to send, Shift+Enter for new line)"
                className="flex-1 resize-none px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition overflow-hidden"
                style={{ minHeight: '40px', maxHeight: '160px' }}
              />

              {/* Send */}
              <button
                id="send-message-btn"
                onClick={handleSend}
                disabled={!input.trim() || isTyping}
                className="p-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-200 text-white disabled:text-gray-400 rounded-lg transition flex-shrink-0"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
