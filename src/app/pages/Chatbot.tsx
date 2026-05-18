import { useEffect, useRef, useState } from 'react';
import { Send, Bot, User, Sparkles, Lightbulb, AlertTriangle } from 'lucide-react';
import { fetchChatResponse } from '../services/api';

type Message = {
  id: string;
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  sources?: string[];
  isFallback?: boolean;
};

const suggestedQuestions = [
  'Comment ameliorer mon score environnemental ?',
  'Quelles sont les tendances ESG pour 2027 ?',
  'Analysez mes points faibles en gouvernance',
  'Predisez mon score ESG pour le prochain trimestre',
];

export default function Chatbot() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      text: "Bonjour ! Je suis votre assistant IA spécialisé en ESG. Posez-moi une question sur vos KPI, vos recommandations ou la navigation du tableau de bord.",
      sender: 'bot',
      timestamp: new Date(),
      sources: ['Aperçu du tableau de bord ESG'],
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async (text?: string) => {
    const messageText = text || inputText.trim();
    if (!messageText || isTyping) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      text: messageText,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText('');
    setIsTyping(true);
    setErrorMessage(null);

    try {
      const response = await fetchChatResponse(messageText);
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          text: response.answer || 'Aucune réponse renvoyée par le service RAG.',
          sender: 'bot',
          timestamp: new Date(),
          sources: response.sources,
          isFallback: response.isFallback, // FIXED: Sauvegarder l'état fallback
        },
      ]);
    } catch {
      setErrorMessage('Le service RAG est indisponible pour le moment.');
      setMessages((prev) => [
        ...prev,
        {
          id: (Date.now() + 1).toString(),
          text: 'Service temporairement indisponible. Veuillez réessayer dans un instant.',
          sender: 'bot',
          timestamp: new Date(),
        },
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void handleSendMessage();
    }
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <div className="max-w-5xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">ESGénie</h1>
          <p className="text-gray-600">Assistant alimenté par le backend Flask local et son contrat RAG.</p>
        </div>

        {errorMessage && (
          <div className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
            {errorMessage}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-200 flex flex-col" style={{ height: '700px' }}>
            <div className="flex-1 overflow-y-auto p-6 space-y-4">
              {messages.map((message) => (
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
                    {message.sender === 'bot' && message.isFallback && (
                      <div className="mb-2 flex items-center gap-1 text-[11px] font-semibold text-amber-700 bg-amber-100 px-2 py-1 rounded-md w-max border border-amber-200">
                        <AlertTriangle className="w-3 h-3" />
                        Mode hors-ligne
                      </div>
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
                    <span className="text-xs opacity-70 mt-2 block">
                      {message.timestamp.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>
              ))}

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

            <div className="border-t border-gray-200 p-4">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder="Posez votre question ESG..."
                  className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
                <button
                  onClick={() => void handleSendMessage()}
                  disabled={!inputText.trim()}
                  className="px-6 py-3 bg-gradient-to-r from-emerald-600 to-emerald-700 text-white rounded-lg hover:from-emerald-700 hover:to-emerald-800 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            <div className="bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-xl p-6 text-white">
              <div className="flex items-center gap-2 mb-3">
                <Sparkles className="w-5 h-5" />
                <h3 className="font-bold">IA Assistant</h3>
              </div>
              <p className="text-sm text-emerald-100 mb-4">
                Propulse par le backend local et le contrat RAG de cette plateforme
              </p>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-white/20 rounded-lg p-3">
                  <p className="text-2xl font-bold">500+</p>
                  <p className="text-xs text-emerald-100">Questions repondues</p>
                </div>
                <div className="bg-white/20 rounded-lg p-3">
                  <p className="text-2xl font-bold">98%</p>
                  <p className="text-xs text-emerald-100">Satisfaction</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <h3 className="font-bold mb-4 flex items-center gap-2">
                <Lightbulb className="w-5 h-5 text-yellow-500" />
                Questions suggérées
              </h3>
              <div className="space-y-2">
                {suggestedQuestions.map((question) => (
                  <button
                    key={question}
                    onClick={() => void handleSendMessage(question)}
                    className="w-full text-left p-3 bg-gray-50 hover:bg-emerald-50 border border-gray-200 hover:border-emerald-300 rounded-lg transition-all text-sm"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>

            <div className="bg-white rounded-xl p-6 border border-gray-200">
              <h3 className="font-bold mb-4">Capacités de l’IA</h3>
              <div className="space-y-3 text-sm">
                <div className="flex items-start gap-2">
                  <div className="w-5 h-5 bg-emerald-100 rounded flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-emerald-600 text-xs">✓</span>
                  </div>
                  <span className="text-gray-700">Analyse des scores ESG en temps réel</span>
                </div>
                <div className="flex items-start gap-2">
                  <div className="w-5 h-5 bg-emerald-100 rounded flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-emerald-600 text-xs">✓</span>
                  </div>
                  <span className="text-gray-700">Réponses alimentées par le RAG local</span>
                </div>
                <div className="flex items-start gap-2">
                  <div className="w-5 h-5 bg-emerald-100 rounded flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-emerald-600 text-xs">✓</span>
                  </div>
                  <span className="text-gray-700">Recommandations d’amélioration</span>
                </div>
                <div className="flex items-start gap-2">
                  <div className="w-5 h-5 bg-emerald-100 rounded flex items-center justify-center flex-shrink-0 mt-0.5">
                    <span className="text-emerald-600 text-xs">✓</span>
                  </div>
                  <span className="text-gray-700">Veille tendances ESG</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
