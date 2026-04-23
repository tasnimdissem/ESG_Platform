import { useEffect, useState } from 'react';
import { Bell, Search, User, ExternalLink } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { fetchNewsItems } from '../services/api';

type NewsItem = {
  id: number;
  title: string;
  source: string;
  region: string;
  category: string;
  date: string;
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
        <div className="flex-1 max-w-xl">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <input
              type="text"
              placeholder="Rechercher une entreprise, un score ESG..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>
        </div>

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
                      <div key={item.id} className="p-4 border-b border-gray-100 hover:bg-gray-50">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="font-medium text-sm text-gray-900">{item.title}</p>
                            <p className="text-xs text-gray-500 mt-1">{item.source} · {item.region} · {item.category}</p>
                          </div>
                          <ExternalLink className="w-4 h-4 text-gray-400 flex-shrink-0 mt-0.5" />
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center gap-3 pl-4 border-l border-gray-200">
            <div className="text-right">
              <p className="font-semibold text-sm">{user?.name}</p>
              <p className="text-xs text-gray-500">{user?.role}</p>
            </div>
            <div className="w-10 h-10 bg-gradient-to-br from-emerald-500 to-emerald-700 rounded-full flex items-center justify-center">
              <User className="w-5 h-5 text-white" />
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
