import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router';
import { Bell, User, ExternalLink, RefreshCw, Menu } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { fetchNewsItems, type NewsItem } from '../services/api';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { getRoleLabel } from '../utils/roles';

const CATEGORY_FILTERS = ['Tout', 'Environnement', 'Social', 'Gouvernance', 'ESG'] as const;
type CategoryFilter = typeof CATEGORY_FILTERS[number];

const CATEGORY_COLORS: Record<string, string> = {
  Environnement: 'bg-green-100 text-green-700',
  Social: 'bg-blue-100 text-blue-700',
  Gouvernance: 'bg-purple-100 text-purple-700',
  ESG: 'bg-emerald-100 text-emerald-700',
};

function formatDate(dateStr: string): string {
  if (!dateStr) return '';
  try {
    return new Date(dateStr).toLocaleDateString('fr-FR', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return dateStr;
  }
}

type HeaderProps = { onMenuToggle: () => void };

export function Header({ onMenuToggle }: HeaderProps) {
  const { user } = useAuth();
  const [newsItems, setNewsItems] = useState<NewsItem[]>([]);
  const [showNews, setShowNews] = useState(false);
  const [activeFilter, setActiveFilter] = useState<CategoryFilter>('Tout');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const panelRef = useRef<HTMLDivElement>(null);

  const loadNews = async () => {
    setIsRefreshing(true);
    try {
      const items = await fetchNewsItems(12);
      setNewsItems(items);
    } catch {
      setNewsItems([]);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => { void loadNews(); }, []);

  // Close panel on outside click
  useEffect(() => {
    if (!showNews) return;
    const handler = (e: MouseEvent) => {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setShowNews(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [showNews]);

  const filteredItems = activeFilter === 'Tout'
    ? newsItems
    : newsItems.filter((item) => item.category === activeFilter);

  return (
    <header className="bg-white border-b border-gray-200 px-4 md:px-8 py-3 md:py-4 sticky top-0 z-10">
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <button
            onClick={onMenuToggle}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-all md:hidden"
            aria-label="Menu"
          >
            <Menu className="w-5 h-5" />
          </button>
          <div className="hidden md:block flex-1 max-w-xl" />
        </div>

        <div className="flex items-center gap-2 md:gap-4">
          <div className="relative" ref={panelRef}>
            <button
              onClick={() => setShowNews((v) => !v)}
              className="relative p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-all"
              title="Actualités ESG"
            >
              <Bell className="w-5 h-5" />
              {newsItems.length > 0 && (
                <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center px-1">
                  {newsItems.length}
                </span>
              )}
            </button>

            {showNews && (
              <div className="absolute right-0 mt-3 w-[calc(100vw-1rem)] max-w-[420px] bg-white border border-gray-200 rounded-xl shadow-2xl z-30 overflow-hidden">
                {/* Header */}
                <div className="px-4 py-3 border-b border-gray-100 flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900">Actualités ESG mondiales</h3>
                    <p className="text-xs text-gray-500">Durabilité · Climat · Énergie · Gouvernance</p>
                  </div>
                  <button
                    onClick={() => void loadNews()}
                    disabled={isRefreshing}
                    className="p-1.5 rounded-lg hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-all disabled:opacity-40"
                    title="Rafraîchir"
                  >
                    <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                  </button>
                </div>

                {/* Category filter tabs */}
                <div className="px-4 py-2 border-b border-gray-100 flex gap-1.5 overflow-x-auto">
                  {CATEGORY_FILTERS.map((cat) => (
                    <button
                      key={cat}
                      onClick={() => setActiveFilter(cat)}
                      className={`flex-shrink-0 px-3 py-1 rounded-full text-xs font-medium transition-all ${
                        activeFilter === cat
                          ? 'bg-emerald-600 text-white'
                          : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                      }`}
                    >
                      {cat}
                    </button>
                  ))}
                </div>

                {/* Articles list */}
                <div className="max-h-[420px] overflow-y-auto divide-y divide-gray-50">
                  {filteredItems.length === 0 ? (
                    <div className="p-6 text-center">
                      <p className="text-sm text-gray-400">
                        {isRefreshing ? 'Chargement…' : 'Aucun article disponible.'}
                      </p>
                    </div>
                  ) : (
                    filteredItems.map((item) => (
                      <a
                        key={item.id}
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block p-4 hover:bg-gray-50 transition-colors group"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0 flex-1">
                            {/* Category badge */}
                            <span className={`inline-block mb-1.5 px-2 py-0.5 rounded-full text-[10px] font-semibold ${CATEGORY_COLORS[item.category] ?? 'bg-gray-100 text-gray-600'}`}>
                              {item.category}
                            </span>
                            {/* Title */}
                            <p className="font-medium text-sm text-gray-900 group-hover:text-emerald-600 leading-snug line-clamp-2">
                              {item.title}
                            </p>
                            {/* Description */}
                            {item.description && (
                              <p className="text-xs text-gray-500 mt-1 line-clamp-2 leading-relaxed">
                                {item.description}
                              </p>
                            )}
                            {/* Meta */}
                            <p className="text-[11px] text-gray-400 mt-1.5 flex items-center gap-1.5">
                              <span className="font-medium text-gray-500">{item.source}</span>
                              <span>·</span>
                              <span>{item.region}</span>
                              <span>·</span>
                              <span>{formatDate(item.date)}</span>
                            </p>
                          </div>
                          <ExternalLink className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5 opacity-0 group-hover:opacity-100 transition-opacity" />
                        </div>
                      </a>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center gap-2 md:gap-3 pl-2 md:pl-4 border-l border-gray-200">
            <Link to="/profile" className="flex items-center gap-2 md:gap-3 rounded-lg px-1 md:px-2 py-1 hover:bg-gray-50 transition-colors">
              <div className="text-right hidden sm:block">
                <p className="font-semibold text-sm">{user?.name}</p>
                <p className="text-xs text-gray-500">{getRoleLabel(user?.role)}</p>
              </div>
              <Avatar className="w-10 h-10">
                <AvatarImage src={user?.avatar_url ?? undefined} alt={user?.name ?? 'Utilisateur'} />
                <AvatarFallback className="bg-gradient-to-br from-emerald-500 to-emerald-700 text-white">
                  <User className="w-5 h-5" />
                </AvatarFallback>
              </Avatar>
            </Link>
          </div>
        </div>
      </div>
    </header>
  );
}
