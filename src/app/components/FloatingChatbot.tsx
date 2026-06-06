import { useLocation, useNavigate } from 'react-router';
import { Bot } from 'lucide-react';

export function FloatingChatbot() {
  const location = useLocation();
  const navigate = useNavigate();

  // Hide on the chatbot page itself
  if (location.pathname === '/chatbot' || location.pathname === '/chatbot-rag') return null;

  return (
    <button
      onClick={() => navigate('/chatbot')}
      title="Ouvrir ESGénie"
      className="fixed bottom-6 right-6 z-50 group flex items-center gap-3 bg-gradient-to-br from-emerald-500 to-emerald-700 text-white rounded-full shadow-2xl transition-all duration-300 hover:shadow-emerald-500/40 hover:scale-105 active:scale-95"
      style={{ padding: '14px 20px' }}
    >
      {/* Pulse ring */}
      <span className="absolute inset-0 rounded-full bg-emerald-400 animate-ping opacity-20 pointer-events-none" />

      <Bot className="w-6 h-6 flex-shrink-0" />
      <span className="text-sm font-semibold overflow-hidden max-w-0 group-hover:max-w-[80px] transition-all duration-300 whitespace-nowrap">
        ESGénie
      </span>
    </button>
  );
}
