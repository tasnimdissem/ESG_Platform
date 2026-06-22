import { useEffect, useRef, useState, useCallback } from 'react';
import { Send, Bot, User, Sparkles, Lightbulb, Trash2, History, Plus, X } from 'lucide-react';
import {
  fetchChatResponseWithSession,
  sendVoiceQuery,
  clearConversationHistory,
  listChatConversations,
  createChatConversation,
  getChatConversation,
  saveChatMessage,
  deleteChatConversation,
  type ChatConversationSummary,
} from '../services/api';
import VoiceRecorder, { type VoiceLanguage } from '../components/VoiceRecorder';
import { useAuth } from '../contexts/AuthContext';

type Message = {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  sources?: string[];
  isFallback?: boolean;
  transcript?: string;
  command?: string;
};

const WELCOME_MESSAGE: Message = {
  id: 'welcome',
  text: "Bonjour ! Je suis votre assistant IA spécialisé en ESG. Posez-moi une question sur vos KPI, vos recommandations ou la navigation du tableau de bord.",
  sender: 'bot',
  timestamp: new Date(),
  sources: ['Aperçu du tableau de bord ESG'],
};

const suggestedQuestions = [
  'Top 5 companies ESG 2020',
  'Quelles sont les tendances ESG pour 2025 ?',
  'Analysez les points faibles en gouvernance',
  'Compare environmental scores by sector',
];

function generateSessionId(): string {
  return typeof crypto !== 'undefined' && crypto.randomUUID
    ? crypto.randomUUID().replace(/-/g, '')
    : Math.random().toString(36).slice(2) + Date.now().toString(36);
}

function recordToMessage(r: { id: number; sender: string; text: string; sources: string[]; timestamp: string }): Message {
  return {
    id: String(r.id),
    text: r.text,
    sender: r.sender as 'user' | 'bot',
    timestamp: new Date(r.timestamp),
    sources: r.sources,
  };
}

export default function ChatbotRag() {
  const { isAuthenticated, isAuthLoading } = useAuth();

  const [messages, setMessages] = useState<Message[]>([WELCOME_MESSAGE]);
  const [inputText, setInputText] = useState('');
  const [interimText, setInterimText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [sessionId, setSessionId] = useState<string>(() => generateSessionId());
  const [voiceLanguage, setVoiceLanguage] = useState<VoiceLanguage>('auto');

  // Persistent history state
  const [showHistory, setShowHistory] = useState(false);
  const [conversations, setConversations] = useState<ChatConversationSummary[]>([]);
  const [activeConvId, setActiveConvId] = useState<number | null>(null);
  const [historyLoading, setHistoryLoading] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Load conversation list only after auth state is resolved and user is logged in
  useEffect(() => {
    if (isAuthLoading || !isAuthenticated) return;
    void (async () => {
      try {
        const list = await listChatConversations();
        setConversations(list);
        if (list.length > 0) {
          await loadConversation(list[0].id, list[0].session_id);
        }
      } catch {
        // Backend unavailable — silent fallback to in-memory mode
      }
    })();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated, isAuthLoading]);

  const loadConversation = useCallback(async (convId: number, convSessionId: string | null) => {
    setHistoryLoading(true);
    try {
      const detail = await getChatConversation(convId);
      setActiveConvId(convId);
      if (convSessionId) setSessionId(convSessionId);
      if (detail.messages.length === 0) {
        setMessages([WELCOME_MESSAGE]);
      } else {
        setMessages(detail.messages.map(recordToMessage));
      }
    } catch {
      setErrorMessage('Impossible de charger la conversation.');
    } finally {
      setHistoryLoading(false);
    }
  }, []);

  const handleNewConversation = async () => {
    const newSessionId = generateSessionId();
    setSessionId(newSessionId);
    setMessages([{ ...WELCOME_MESSAGE, id: Date.now().toString(), timestamp: new Date() }]);
    setActiveConvId(null);
    setErrorMessage(null);
    try {
      const conv = await createChatConversation('Nouvelle conversation', newSessionId);
      setConversations((prev) => [conv, ...prev]);
      setActiveConvId(conv.id);
    } catch { /* silent — will create lazily on first message */ }
  };

  const handleDeleteConversation = async (convId: number, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await deleteChatConversation(convId);
      setConversations((prev) => prev.filter((c) => c.id !== convId));
      if (activeConvId === convId) {
        const remaining = conversations.filter((c) => c.id !== convId);
        if (remaining.length > 0) {
          await loadConversation(remaining[0].id, remaining[0].session_id);
        } else {
          setActiveConvId(null);
          setMessages([{ ...WELCOME_MESSAGE, id: Date.now().toString(), timestamp: new Date() }]);
        }
      }
    } catch {
      setErrorMessage('Erreur lors de la suppression.');
    }
  };

  // Ensure an active conversation exists before saving messages
  const ensureConversation = async (): Promise<number | null> => {
    if (activeConvId !== null) return activeConvId;
    try {
      const conv = await createChatConversation('Nouvelle conversation', sessionId);
      setConversations((prev) => [conv, ...prev]);
      setActiveConvId(conv.id);
      return conv.id;
    } catch {
      return null;
    }
  };

  const addBotMessage = (text: string, sources: string[] = [], extra: Partial<Message> = {}) => {
    setMessages((prev) => [
      ...prev,
      {
        id: Date.now().toString(),
        text: text || 'Aucune réponse renvoyée par le service RAG.',
        sender: 'bot',
        timestamp: new Date(),
        sources,
        ...extra,
      },
    ]);
  };

  // ── Text chat ─────────────────────────────────────────────────────────────
  const handleSendText = async (text?: string) => {
    const messageText = (text ?? inputText).trim();
    if (!messageText || isTyping) return;

    setMessages((prev) => [
      ...prev,
      { id: Date.now().toString(), text: messageText, sender: 'user', timestamp: new Date() },
    ]);
    setInputText('');
    setIsTyping(true);
    setErrorMessage(null);

    const convId = await ensureConversation();

    try {
      // Persist user message
      if (convId) {
        await saveChatMessage(convId, 'user', messageText);
        // Update conversation title in sidebar if it was auto-set
        setConversations((prev) =>
          prev.map((c) =>
            c.id === convId && c.title === 'Nouvelle conversation'
              ? { ...c, title: messageText.slice(0, 60) + (messageText.length > 60 ? '…' : '') }
              : c
          )
        );
      }

      const response = await fetchChatResponseWithSession(messageText, sessionId);
      const uniqueSources = [...new Set(response.sources ?? [])];
      addBotMessage(response.answer, uniqueSources, { isFallback: response.isFallback });

      // Persist bot response
      if (convId && response.answer) {
        await saveChatMessage(convId, 'bot', response.answer, response.sources);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Le service RAG est indisponible.';
      setErrorMessage(msg);
      addBotMessage('Service temporairement indisponible. Veuillez réessayer.');
    } finally {
      setIsTyping(false);
    }
  };

  // ── Voice / audio upload ──────────────────────────────────────────────────
  const handleVoiceResult = async (transcript: string, audioBlob: Blob | null) => {
    const blob = audioBlob && audioBlob.size > 0 ? audioBlob : null;
    if (!blob && !transcript.trim()) return;
    setIsTyping(true);
    setErrorMessage(null);
    setInterimText('');

    const displayText = transcript.trim() || '🎙️ Audio envoyé…';
    setMessages((prev) => [
      ...prev,
      { id: Date.now().toString(), text: displayText, sender: 'user', timestamp: new Date() },
    ]);

    const convId = await ensureConversation();

    try {
      const result = await sendVoiceQuery(blob, sessionId, voiceLanguage, 5, transcript.trim() || undefined);

      if (result.transcript && result.transcript !== displayText) {
        setMessages((prev) => {
          const copy = [...prev];
          const last = copy.findLastIndex((m) => m.sender === 'user');
          if (last !== -1) copy[last] = { ...copy[last], text: result.transcript, transcript: result.transcript };
          return copy;
        });
      }

      const sourceLabels = [...new Set(
        (result.sources as Array<{ source_name?: string; chunk_id?: string; source_type?: string }>)
          .map((s, i) => s.source_name ?? s.chunk_id ?? s.source_type ?? `Source ${i + 1}`)
          .filter(Boolean)
      )];

      addBotMessage(result.answer, sourceLabels, {
        command: result.command !== 'ask' ? result.command : undefined,
      });

      const question = result.query || result.transcript || displayText;
      if (convId) {
        await saveChatMessage(convId, 'user', question);
        if (result.answer) await saveChatMessage(convId, 'bot', result.answer, sourceLabels);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'La transcription ou le RAG a échoué.';
      setErrorMessage(msg);
      addBotMessage('Service temporairement indisponible. Veuillez réessayer.');
    } finally {
      setIsTyping(false);
    }
  };

  const handleClearHistory = async () => {
    if (activeConvId !== null) {
      await handleDeleteConversation(activeConvId, { stopPropagation: () => {} } as React.MouseEvent);
    }
    try {
      await clearConversationHistory(sessionId);
    } catch { /* silent */ }
    const newSessionId = generateSessionId();
    setSessionId(newSessionId);
    setMessages([{ ...WELCOME_MESSAGE, id: Date.now().toString(), timestamp: new Date() }]);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void handleSendText();
    }
  };

  return (
    <div className="p-4 md:p-8 bg-gray-50 min-h-screen">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-1">ESGénie</h1>

          </div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => void handleNewConversation()}
              title="Nouvelle conversation"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-emerald-600 hover:bg-emerald-700 text-white transition-all"
            >
              <Plus className="w-4 h-4" />
              Nouveau
            </button>
            <button
              onClick={() => setShowHistory((v) => !v)}
              title="Historique de conversation"
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm border transition-all ${
                showHistory
                  ? 'bg-emerald-50 border-emerald-300 text-emerald-700'
                  : 'bg-white border-gray-200 hover:bg-gray-50 text-gray-600'
              }`}
            >
              <History className="w-4 h-4" />
              Historique
            </button>
            <button
              onClick={() => void handleClearHistory()}
              title="Effacer la conversation"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm bg-white border border-gray-200 hover:bg-red-50 hover:border-red-200 hover:text-red-600 text-gray-600 transition-all"
            >
              <Trash2 className="w-4 h-4" />
              Effacer
            </button>
          </div>
        </div>

        {errorMessage && (
          <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            {errorMessage}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Chat window */}
          <div
            className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-200 flex flex-col"
            style={{ height: 'min(700px, 80vh)' }}
          >
            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {historyLoading ? (
                <div className="flex items-center justify-center h-full text-gray-400 text-sm">
                  Chargement…
                </div>
              ) : (
                messages.map((message) => (
                  <div
                    key={message.id}
                    className={`flex items-start gap-3 ${message.sender === 'user' ? 'flex-row-reverse' : ''}`}
                  >
                    <div
                      className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${
                        message.sender === 'bot'
                          ? 'bg-gradient-to-br from-emerald-500 to-emerald-600'
                          : 'bg-gradient-to-br from-blue-500 to-blue-600'
                      }`}
                    >
                      {message.sender === 'bot' ? (
                        <Bot className="w-5 h-5 text-white" />
                      ) : (
                        <User className="w-5 h-5 text-white" />
                      )}
                    </div>

                    <div
                      className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                        message.sender === 'bot'
                          ? 'bg-gray-100 text-gray-900'
                          : 'bg-gradient-to-r from-emerald-600 to-emerald-700 text-white'
                      }`}
                    >
                      {message.command && (
                        <span className="inline-block mb-1 text-[10px] font-bold uppercase tracking-wide px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700">
                          {message.command}
                        </span>
                      )}
                      <p className="text-sm whitespace-pre-line leading-relaxed">{message.text}</p>
                      {message.sources && message.sources.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-2">
                          {message.sources.map((source, index) => (
                            <span
                              key={`${source}-${index}`}
                              className="rounded-full bg-white/70 px-2 py-1 text-[11px] font-semibold text-gray-700"
                            >
                              {source}
                            </span>
                          ))}
                        </div>
                      )}
                      <span className="text-xs opacity-60 mt-1 block">
                        {message.timestamp.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  </div>
                ))
              )}

              {interimText && !isTyping && (
                <div className="flex items-start gap-3 flex-row-reverse opacity-60">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center flex-shrink-0">
                    <User className="w-5 h-5 text-white" />
                  </div>
                  <div className="max-w-[80%] rounded-2xl px-4 py-3 bg-gradient-to-r from-emerald-600 to-emerald-700 text-white italic text-sm">
                    {interimText}…
                  </div>
                </div>
              )}

              {isTyping && (
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-500 to-emerald-600 flex items-center justify-center">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                  <div className="bg-gray-100 rounded-2xl px-4 py-3">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                      <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            {/* Input area */}
            <div className="border-t border-gray-200 p-4 space-y-3">
              <VoiceRecorder
                onResult={(transcript, audioBlob) => void handleVoiceResult(transcript, audioBlob)}
                onInterim={(text) => setInterimText(text)}
                disabled={isTyping}
                language={voiceLanguage}
                onLanguageChange={setVoiceLanguage}
              />

              <div className="flex gap-2">
                <input
                  type="text"
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder="Posez votre question ESG…"
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-sm"
                />
                <button
                  onClick={() => void handleSendText()}
                  disabled={!inputText.trim() || isTyping}
                  className="px-5 py-3 bg-gradient-to-r from-emerald-600 to-emerald-700 text-white rounded-lg hover:from-emerald-700 hover:to-emerald-800 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>

          {/* Side panel */}
          <div className="space-y-6">
            {/* Persistent conversation history */}
            {showHistory && (
              <div className="bg-white rounded-xl border border-gray-200 p-4 max-h-72 overflow-y-auto">
                <h3 className="font-bold text-sm mb-3 flex items-center gap-2">
                  <History className="w-4 h-4 text-gray-500" />
                  Conversations ({conversations.length})
                </h3>
                {conversations.length === 0 ? (
                  <p className="text-xs text-gray-400">Aucune conversation sauvegardée.</p>
                ) : (
                  <div className="space-y-1">
                    {conversations.map((conv) => (
                      <div
                        key={conv.id}
                        onClick={() => void loadConversation(conv.id, conv.session_id)}
                        className={`group flex items-center justify-between gap-2 px-3 py-2 rounded-lg cursor-pointer text-xs transition-all ${
                          activeConvId === conv.id
                            ? 'bg-emerald-50 border border-emerald-200 text-emerald-800'
                            : 'hover:bg-gray-50 text-gray-700'
                        }`}
                      >
                        <div className="min-w-0">
                          <p className="font-medium truncate">{conv.title}</p>
                          <p className="text-gray-400 text-[10px]">
                            {new Date(conv.created_at).toLocaleDateString('fr-FR', {
                              day: '2-digit',
                              month: 'short',
                              hour: '2-digit',
                              minute: '2-digit',
                            })}
                          </p>
                        </div>
                        <button
                          onClick={(e) => void handleDeleteConversation(conv.id, e)}
                          className="opacity-0 group-hover:opacity-100 flex-shrink-0 p-1 rounded hover:bg-red-100 hover:text-red-600 text-gray-400 transition-all"
                          title="Supprimer"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* IA card */}
            <div className="bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-xl p-6 text-white">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-5 h-5" />
                <h3 className="font-bold">IA Assistant</h3>
              </div>
              <p className="text-sm text-emerald-100 mb-4">RAG · Whisper · Multilingue</p>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-white/20 rounded-lg p-3">
                  <p className="text-2xl font-bold">8</p>
                  <p className="text-xs text-emerald-100">Langues</p>
                </div>
                <div className="bg-white/20 rounded-lg p-3">
                  <p className="text-2xl font-bold">37k</p>
                  <p className="text-xs text-emerald-100">Chunks RAG</p>
                </div>
              </div>
            </div>

            {/* Suggested questions */}
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <h3 className="font-bold mb-4 flex items-center gap-2 text-sm">
                <Lightbulb className="w-5 h-5 text-yellow-500" />
                Questions suggérées
              </h3>
              <div className="space-y-2">
                {suggestedQuestions.map((question) => (
                  <button
                    key={question}
                    onClick={() => void handleSendText(question)}
                    disabled={isTyping}
                    className="w-full text-left p-3 bg-gray-50 hover:bg-emerald-50 border border-gray-200 hover:border-emerald-300 rounded-lg transition-all text-xs disabled:opacity-50"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>

            {/* Capabilities */}
            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <h3 className="font-bold mb-4 text-sm">Capacités</h3>
              <div className="space-y-2 text-xs text-gray-700">
                {[
                  'Voix en temps réel (Web Speech API)',
                  'Upload .mp3 / .wav / .webm',
                  'Transcription Whisper multilingue',
                  'Commandes vocales détectées',
                  'Historique persistant par compte',
                  'Recherche vectorielle FAISS',
                ].map((cap) => (
                  <div key={cap} className="flex items-start gap-2">
                    <span className="mt-0.5 flex-shrink-0 w-4 h-4 bg-emerald-100 rounded flex items-center justify-center text-emerald-600 text-[10px]">
                      ✓
                    </span>
                    <span>{cap}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
