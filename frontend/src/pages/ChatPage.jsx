import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';

import {
  Bot,
  ChevronLeft,
  ChevronRight,
  FileText,
  Image as ImageIcon,
  Loader2,
  LogOut,
  MessageSquare,
  Paperclip,
  Plus,
  Send,
  Trash2,
  User,
  X,
} from 'lucide-react';

import { useAuth } from '../hooks/useAuth';
import {
  apiCreateThread,
  apiGetFiles,
  apiGetMessages,
  apiGetThreads,
  apiStreamChat,
  apiUploadFile,
  apiDeleteThread
} from '../api';

const ACCEPTED_FILE_TYPES = '.pdf,.ppt,.pptx,.txt,.png,.jpg,.jpeg,.webp';

function TypingIndicator() {
  return (
    <div className="flex items-start gap-3">
      <Avatar role="assistant" />
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

function Avatar({ role }) {
  const isUser = role === 'user';

  return (
    <div
      className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
        isUser ? 'bg-blue-600' : 'bg-blue-100'
      }`}
    >
      {isUser ? (
        <User className="w-4 h-4 text-white" />
      ) : (
        <Bot className="w-4 h-4 text-blue-600" />
      )}
    </div>
  );
}

function Message({
  role,
  content,
  file_name,
  suggestions = [],
  onSuggestionClick,
}) {
  const isUser = role === 'user';

  return (
    <div className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}>
      <Avatar role={role} />

      <div
        className={`max-w-[75%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
          isUser
            ? 'bg-blue-600 text-white rounded-tr-sm'
            : 'bg-white border border-gray-200 text-gray-800 rounded-tl-sm'
        }`}
      >
        {file_name && (
          <div className="mb-2 flex items-center gap-2 text-xs opacity-90">
            <FileText className="w-3.5 h-3.5" />
            {file_name}
          </div>
        )}

        {isUser ? (
          <span>{content}</span>
        ) : (
          <div className="markdown-body">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        )}
        {role === 'assistant' && suggestions.length > 0 && (
  <div className="mt-3 flex flex-wrap gap-2">
    {suggestions.map((suggestion, index) => (
      <button
        key={index}
        onClick={() => onSuggestionClick?.(suggestion)}
        className="
          text-xs
          px-3
          py-1.5
          rounded-full
          border
          border-gray-300
          hover:bg-gray-100
          transition
        "
      >
        {suggestion}
      </button>
    ))}
  </div>
)}
      </div>
    </div>
  );
}


function FileIcon({ fileName = '' }) {
  const lower = fileName.toLowerCase();

  if (/\.(png|jpg|jpeg|webp)$/.test(lower)) {
    return <ImageIcon className="w-4 h-4 text-blue-600" />;
  }

  return <FileText className="w-4 h-4 text-blue-600" />;
}

export default function ChatPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const [threads, setThreads] = useState([]);
  const [activeThread, setActiveThread] = useState(null);

  const [messages, setMessages] = useState([]);
  const [threadFiles, setThreadFiles] = useState([]);
  const [selectedFileId, setSelectedFileId] = useState(null);

  const [input, setInput] = useState('');
  const [pendingFile, setPendingFile] = useState(null);

  const [isTyping, setIsTyping] = useState(false);
  const [loadingThreads, setLoadingThreads] = useState(true);
  const [loadingThreadData, setLoadingThreadData] = useState(false);
  const [sending, setSending] = useState(false);

  const [leftOpen, setLeftOpen] = useState(true);
  const [rightOpen, setRightOpen] = useState(true);

  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const textareaRef = useRef(null);
  const streamAbortRef = useRef(null);

  useEffect(() => {
    loadThreads();

    return () => {
      stopRunningStream();
    };
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  function stopRunningStream() {
    if (streamAbortRef.current) {
      streamAbortRef.current.abort();
      streamAbortRef.current = null;
    }

    setSending(false);
    setIsTyping(false);
  }

  async function loadThreads() {
    try {
      setLoadingThreads(true);

      const data = await apiGetThreads();
      const list = data.threads || data || [];

      setThreads(list);

      const savedThreadId = localStorage.getItem('active_thread_id');

      const threadToOpen =
        list.find((t) => t.thread_id === savedThreadId) || list[0];

      if (threadToOpen) {
        selectThread(threadToOpen);
      }
    } catch (err) {
      console.error('Failed to load threads:', err);
    } finally {
      setLoadingThreads(false);
    }
  }

  // ─── Delete empty thread when switching away ───────────────────────────
  async function deleteIfEmpty(thread) {
    if (!thread) return;
    // Only delete if it's still titled 'New Chat' and has no messages
    if (thread.title !== 'New Chat') return;
    try {
      await apiDeleteThread(thread.thread_id);
      setThreads((prev) => prev.filter((t) => t.thread_id !== thread.thread_id));
      if (localStorage.getItem('active_thread_id') === thread.thread_id) {
        localStorage.removeItem('active_thread_id');
      }
    } catch (_) {
      // silently ignore — thread may already have messages
    }
  }

  // ─── Delete thread instantly from sidebar ──────────────────────────────
  async function handleDeleteThread(thread) {
    try {
      // Optimistic update: remove from UI immediately
      setThreads((prev) => prev.filter((t) => t.thread_id !== thread.thread_id));

      if (activeThread?.thread_id === thread.thread_id) {
        setActiveThread(null);
        setMessages([]);
        setThreadFiles([]);
        setSelectedFileId(null);
        localStorage.removeItem('active_thread_id');
      }

      // Then actually delete on backend
      await apiDeleteThread(thread.thread_id);
    } catch (err) {
      console.error('Delete failed:', err);
      // Reload threads to restore correct state if delete failed
      loadThreads();
    }
  }

  async function handleNewChat() {
    stopRunningStream();

    // Delete current thread if it's empty (no messages sent yet)
    if (activeThread && messages.length === 0) {
      await deleteIfEmpty(activeThread);
    }

    try {
      const data = await apiCreateThread();

      const newThread = {
        thread_id: data.thread_id,
        title: data.title || 'New Chat',
        created_at: data.created_at || new Date().toISOString(),
      };

      localStorage.setItem('active_thread_id', newThread.thread_id);

      setThreads((prev) => [newThread, ...prev]);
      setActiveThread(newThread);
      setMessages([]);
      setThreadFiles([]);
      setSelectedFileId(null);
      setPendingFile(null);
    } catch (err) {
      console.error('Failed to create thread:', err);
    }
  }

  async function selectThread(thread) {
    stopRunningStream();

    // Clean up current thread if it's empty before switching
    if (activeThread && activeThread.thread_id !== thread.thread_id && messages.length === 0) {
      await deleteIfEmpty(activeThread);
    }

    localStorage.setItem('active_thread_id', thread.thread_id);

    setActiveThread(thread);
    setSelectedFileId(null);
    setPendingFile(null);

    try {
      setLoadingThreadData(true);

      const [messageData, fileData] = await Promise.all([
        apiGetMessages(thread.thread_id),
        apiGetFiles(thread.thread_id),
      ]);

      setMessages(messageData.messages || []);
      setThreadFiles(fileData.files || []);
    } catch (err) {
      console.error('Failed to load thread data:', err);
      setMessages([]);
      setThreadFiles([]);
    } finally {
      setLoadingThreadData(false);
    }
  }

  function handleTextareaChange(e) {
    setInput(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 160) + 'px';
  }

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendText();
    }
  }

  function handleChooseFile(e) {
    const file = e.target.files?.[0];
    if (!file) return;

    setPendingFile(file);
    e.target.value = '';
  }

  function cancelPendingFile() {
    setPendingFile(null);
  }

  async function handleUploadPendingFile() {
    if (!activeThread || !pendingFile || sending) return;

    const file = pendingFile;

    setPendingFile(null);
    setSending(true);

    setMessages((prev) => [
      ...prev,
      {
        role: 'user',
        content: `Uploaded file: ${file.name}`,
        file_name: file.name,
      },
    ]);

    try {
      const result = await apiUploadFile({
        thread_id: activeThread.thread_id,
        file,
      });

      const uploadedFile = result.file || {
        file_id: result.file_id,
        file_name: result.file_name || file.name,
        file_type: result.file_type || file.type,
      };

      setThreadFiles((prev) => [uploadedFile, ...prev]);

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content:
            result.answer ||
            result.message ||
            `File "${file.name}" uploaded and processed successfully.`,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: `Upload failed: ${err.message}`,
        },
      ]);
    } finally {
      setSending(false);
    }
  }

  async function handleSendText() {
    const text = input.trim();

    if (!text || !activeThread || sending) return;

    stopRunningStream();

    setMessages((prev) => [
      ...prev,
      {
        role: 'user',
        content: text,
        selected_file_id: selectedFileId,
      },
    ]);

    setInput('');
    setSending(true);
    setIsTyping(true);

    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    // Auto-title: use first message text (truncated to 40 chars) as thread title
    const isFirstMessage = messages.length === 0;
    if (isFirstMessage) {
      const newTitle = text.length > 40 ? text.slice(0, 40) + '…' : text;
      setActiveThread((prev) => ({ ...prev, title: newTitle }));
      setThreads((prev) =>
        prev.map((t) =>
          t.thread_id === activeThread.thread_id ? { ...t, title: newTitle } : t
        )
      );
    }

    try {
      let assistantText = '';

      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: '',
        },
      ]);

      setIsTyping(false);

      streamAbortRef.current = new AbortController();

          await apiStreamChat({
            thread_id: activeThread.thread_id,
            message: text,
            selected_file_id: selectedFileId,
            signal: streamAbortRef.current.signal,

            onToken: (token) => {
              assistantText += token;

              setMessages((prev) => {
                const updated = [...prev];

                updated[updated.length - 1] = {
                  ...updated[updated.length - 1],
                  role: 'assistant',
                  content: assistantText,
                };

                return updated;
              });
            },

            onComplete: ({ suggestions }) => {
              setMessages((prev) => {
                const updated = [...prev];

                if (
                  updated.length > 0 &&
                  updated[updated.length - 1].role === 'assistant'
                ) {
                  updated[updated.length - 1] = {
                    ...updated[updated.length - 1],
                    suggestions: suggestions || [],
                  };
                }

                return updated;
              });
            },
          });
    } catch (err) {
      if (err.name === 'AbortError') {
        return;
      }

      setMessages((prev) => {
        const updated = [...prev];

        if (
          updated.length > 0 &&
          updated[updated.length - 1].role === 'assistant'
        ) {
          updated[updated.length - 1] = {
            role: 'assistant',
            content: `Error: ${err.message}`,
          };
        } else {
          updated.push({
            role: 'assistant',
            content: `Error: ${err.message}`,
          });
        }

        return updated;
      });
    } finally {
      streamAbortRef.current = null;
      setSending(false);
      setIsTyping(false);
    }
  }

  function handleLogout() {
    stopRunningStream();
    logout();
    navigate('/login', { replace: true });
  }

  return (
    <div className="flex h-screen bg-gray-50 overflow-hidden">
      <aside
        className={`${
          leftOpen ? 'w-72' : 'w-0'
        } transition-all duration-300 bg-white border-r border-gray-200 flex flex-col overflow-hidden flex-shrink-0`}
      >
        <div className="p-4 border-b border-gray-100 flex items-center gap-2">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <MessageSquare className="w-4 h-4 text-white" />
          </div>

          <span className="font-semibold text-gray-800 text-sm truncate">
            ChatAgent
          </span>
        </div>

        <div className="p-3">
          <button
            onClick={handleNewChat}
            className="w-full flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition"
          >
            <Plus className="w-4 h-4" />
            New chat
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-2 pb-2">
          {loadingThreads ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-5 h-5 text-gray-400 animate-spin" />
            </div>
          ) : threads.length === 0 ? (
            <p className="text-xs text-gray-400 text-center py-8 px-3">
              No conversations yet.
            </p>
          ) : (
            <div className="space-y-1">
              {threads.map((t) => (
                <div
                  key={t.thread_id}
                  className="flex items-center gap-1"
                >
                  <button
                    onClick={() => selectThread(t)}
                    className={`flex-1 text-left px-3 py-2 rounded-lg text-sm transition truncate ${
                      activeThread?.thread_id === t.thread_id
                        ? 'bg-blue-50 text-blue-700 font-medium'
                        : 'text-gray-600 hover:bg-gray-50'
                    }`}
                  >
                    {t.title || 'New Chat'}
                  </button>

                  <button
                    onClick={() => handleDeleteThread(t)}
                    className="p-2 text-gray-400 hover:text-red-500"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="p-3 border-t border-gray-100">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
              <User className="w-4 h-4 text-gray-500" />
            </div>

            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium text-gray-700 truncate">
                {user?.name || user?.email || 'User'}
              </p>
              <p className="text-xs text-gray-400 truncate">{user?.email}</p>
            </div>

            <button
              onClick={handleLogout}
              title="Sign out"
              className="text-gray-400 hover:text-red-500 transition p-1 rounded"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      <main className="flex-1 flex flex-col min-w-0">
        <header className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3">
          <button
            onClick={() => setLeftOpen((p) => !p)}
            className="text-gray-400 hover:text-gray-600 transition"
            title="Toggle threads"
          >
            {leftOpen ? (
              <ChevronLeft className="w-5 h-5" />
            ) : (
              <ChevronRight className="w-5 h-5" />
            )}
          </button>

          <h2 className="text-sm font-medium text-gray-700 flex-1 truncate">
            {activeThread
              ? activeThread.title || 'New Chat'
              : 'Start a conversation'}
          </h2>

          <button
            onClick={() => setRightOpen((p) => !p)}
            className="text-gray-400 hover:text-gray-600 transition"
            title="Toggle files"
          >
            {rightOpen ? (
              <ChevronRight className="w-5 h-5" />
            ) : (
              <ChevronLeft className="w-5 h-5" />
            )}
          </button>
        </header>

        <section className="flex-1 overflow-y-auto px-4 py-6 space-y-4">
          {!activeThread ? (
            <div className="h-full flex flex-col items-center justify-center text-center px-8">
              <div className="w-16 h-16 bg-blue-100 rounded-2xl flex items-center justify-center mb-4">
                <Bot className="w-8 h-8 text-blue-600" />
              </div>

              <h3 className="text-xl font-semibold text-gray-800 mb-2">
                How can I help you today?
              </h3>

              <button
                onClick={handleNewChat}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition"
              >
                <Plus className="w-4 h-4" />
                Start new chat
              </button>
            </div>
          ) : loadingThreadData ? (
            <div className="h-full flex items-center justify-center">
              <Loader2 className="w-6 h-6 text-gray-400 animate-spin" />
            </div>
          ) : messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center px-8">
              <p className="text-sm text-gray-400">
                Send a message or upload a file.
              </p>
            </div>
          ) : (
            <>
              {messages.map((msg, i) => (
                    <Message
                      key={`${msg.id || i}-${msg.role}`}
                      role={msg.role}
                      content={msg.content}
                      file_name={msg.file_name}
                      suggestions={msg.suggestions}
                      onSuggestionClick={(text) => {
                        setInput(text);

                        setTimeout(() => {
                          textareaRef.current?.focus();
                        }, 0);
                      }}
                    />
              ))}

              {isTyping && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </>
          )}
        </section>

        {activeThread && (
          <footer className="bg-white border-t border-gray-200 px-4 py-3">
            <div className="max-w-4xl mx-auto">
              {selectedFileId && (
                <div className="mb-2 flex items-center justify-between rounded-lg bg-blue-50 border border-blue-100 px-3 py-2 text-xs text-blue-700">
                  <span className="truncate">
                    Asking from selected file:{' '}
                    {
                      threadFiles.find((f) => f.file_id === selectedFileId)
                        ?.file_name
                    }
                  </span>

                  <button onClick={() => setSelectedFileId(null)}>
                    <X className="w-4 h-4" />
                  </button>
                </div>
              )}

              {pendingFile && (
                <div className="mb-2 flex items-center gap-2 rounded-lg bg-gray-50 border border-gray-200 px-3 py-2">
                  <FileIcon fileName={pendingFile.name} />

                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium text-gray-700 truncate">
                      {pendingFile.name}
                    </p>
                    <p className="text-[11px] text-gray-400">
                      Ready to upload. You can cancel before sending.
                    </p>
                  </div>

                  <button
                    onClick={cancelPendingFile}
                    className="p-1 text-gray-400 hover:text-red-500"
                    title="Cancel upload"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>

                  <button
                    onClick={handleUploadPendingFile}
                    disabled={sending}
                    className="px-3 py-1.5 text-xs bg-blue-600 hover:bg-blue-700 text-white rounded-md disabled:opacity-50"
                  >
                    Upload
                  </button>
                </div>
              )}

              <div className="flex items-end gap-2">
                <input
                  ref={fileInputRef}
                  type="file"
                  className="hidden"
                  accept={ACCEPTED_FILE_TYPES}
                  onChange={handleChooseFile}
                />

                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={sending}
                  title="Attach file"
                  className="p-2 text-gray-400 hover:text-blue-600 transition rounded-lg hover:bg-gray-100 disabled:opacity-40"
                >
                  <Paperclip className="w-5 h-5" />
                </button>

                <textarea
                  ref={textareaRef}
                  rows={1}
                  value={input}
                  onChange={handleTextareaChange}
                  onKeyDown={handleKeyDown}
                  placeholder="Message ChatAgent..."
                  className="flex-1 resize-none px-3 py-2 border border-gray-300 rounded-lg text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition overflow-hidden"
                  style={{ minHeight: '40px', maxHeight: '160px' }}
                />

                <button
                  onClick={handleSendText}
                  disabled={!input.trim() || sending}
                  className="p-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-200 text-white disabled:text-gray-400 rounded-lg transition"
                >
                  {sending ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : (
                    <Send className="w-5 h-5" />
                  )}
                </button>
              </div>
            </div>
          </footer>
        )}
      </main>

      <aside
        className={`${
          rightOpen ? 'w-80' : 'w-0'
        } transition-all duration-300 bg-white border-l border-gray-200 flex flex-col overflow-hidden flex-shrink-0`}
      >
        <div className="p-4 border-b border-gray-100">
          <h3 className="font-semibold text-gray-800 text-sm">Thread files</h3>
          <p className="text-xs text-gray-400 mt-1">
            Select one file to restrict RAG search.
          </p>
        </div>

        <div className="flex-1 overflow-y-auto p-3">
          {!activeThread ? (
            <p className="text-xs text-gray-400 text-center py-8">
              Select a thread first.
            </p>
          ) : threadFiles.length === 0 ? (
            <p className="text-xs text-gray-400 text-center py-8">
              No files uploaded in this thread.
            </p>
          ) : (
            <div className="space-y-2">
              <button
                onClick={() => setSelectedFileId(null)}
                className={`w-full text-left rounded-lg border px-3 py-2 text-sm transition ${
                  selectedFileId === null
                    ? 'border-blue-200 bg-blue-50 text-blue-700'
                    : 'border-gray-200 hover:bg-gray-50 text-gray-700'
                }`}
              >
                Search all files
              </button>

              {threadFiles.map((file) => (
                <button
                  key={file.file_id}
                  onClick={() =>
                    setSelectedFileId((prev) =>
                      prev === file.file_id ? null : file.file_id
                    )
                  }
                  className={`w-full text-left rounded-lg border px-3 py-2 transition ${
                    selectedFileId === file.file_id
                      ? 'border-blue-200 bg-blue-50'
                      : 'border-gray-200 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <FileIcon fileName={file.file_name} />
                    <p className="text-sm font-medium text-gray-700 truncate">
                      {file.file_name}
                    </p>
                  </div>

                  <p className="text-[11px] text-gray-400 mt-1 truncate">
                    {file.file_type || file.mime_type || 'document'}
                  </p>
                </button>
              ))}
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}