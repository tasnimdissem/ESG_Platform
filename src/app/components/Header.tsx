import { useEffect, useState } from 'react';
import { Link } from 'react-router';
import { Bell, User, ExternalLink } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { fetchNewsItems } from '../services/api';
import { Avatar, AvatarFallback, AvatarImage } from './ui/avatar';
import { getRoleLabel } from '../utils/roles';

type NewsItem = {
  id: number;
  title: string;
  source: string;
  region: string;
  category: string;
  date: string;
  url: string;
};

export function Header() {
  const { user } = useAuth();
  const [newsItems, setNewsItems] = useState<NewsItem[]>([]);
  const [showNews, setShowNews] = useState(false);

  useEffect(() => {
    const loadNews = async () => {
      try {
        const items = await fetchNewsItems();
        setNewsItems(items);
      } catch {
        setNewsItems([]);
      }
    };

    loadNews();
  }, []);

  return (
    <header className="bg-white border-b border-gray-200 px-8 py-4 sticky top-0 z-10">
      <div className="flex items-center justify-between">
        <div className="flex-1 max-w-xl" />

        <div className="flex items-center gap-4">
          <div className="relative">
            <button
              onClick={() => setShowNews((value) => !value)}
              className="relative p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-lg transition-all"
              title="Actualites ESG"
            >
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"></span>
            </button>

            {showNews && (
              <div className="absolute right-0 mt-3 w-[360px] bg-white border border-gray-200 rounded-xl shadow-xl z-30 overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-100">
                  <h3 className="font-semibold text-gray-900">Actualites ESG mondiales</h3>
                  <p className="text-xs text-gray-500">Durabilite, climat, energie, gouvernance</p>
                </div>
                <div className="max-h-96 overflow-y-auto">
                  {newsItems.length === 0 ? (
                    <div className="p-4 text-sm text-gray-500">Aucune actualite disponible pour le moment.</div>
                  ) : (
                    newsItems.map((item) => (
                      <a
                        key={item.id}
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block p-4 border-b border-gray-100 hover:bg-gray-50 transition-colors cursor-pointer"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="font-medium text-sm text-gray-900 hover:text-emerald-600">{item.title}</p>
                            <p className="text-xs text-gray-500 mt-1">{item.source} · {item.region} · {item.category}</p>
                          </div>
                          <ExternalLink className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                        </div>
                      </a>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center gap-3 pl-4 border-l border-gray-200">
            <Link to="/profile" className="flex items-center gap-3 rounded-lg px-2 py-1 hover:bg-gray-50 transition-colors">
              <div className="text-right">
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
