import { useEffect, useState } from 'react';
import { LayoutDashboard } from 'lucide-react';

export default function Dashboard() {
  const [powerBiUrl, setPowerBiUrl] = useState('');

  useEffect(() => {
    const loadPowerBiUrl = async () => {
      try {
        const res = await fetch('/api/powerbi-url', { credentials: 'include' });
        if (!res.ok) return;
        const data = (await res.json()) as { url?: string };
        if (data.url) {
          setPowerBiUrl(data.url);
        }
      } catch {
        // Keep empty src if API is unavailable.
      }
    };

    void loadPowerBiUrl();
  }, []);

  return (
    <div className="p-4 md:p-8 space-y-8 bg-gray-50 min-h-screen">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3">
          <LayoutDashboard className="w-8 h-8 text-emerald-600" />
          Tableau de bord ESG global
        </h1>
        <p className="text-gray-600">
          Vue d’ensemble et données consolidées de l’entreprise (intégration Power BI)
        </p>
      </div>

      {/* PowerBI Iframe Container */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden" style={{ height: '80vh' }}>
        <div className="p-4 bg-gray-100 border-b border-gray-200 flex justify-between items-center">
          <span className="font-semibold text-gray-700 text-sm">Rapport interactif Power BI</span>
          <span className="text-xs px-2 py-1 bg-emerald-100 text-emerald-800 rounded-full font-medium">Connecté en temps réel</span>
        </div>
        
        {powerBiUrl ? (
          <iframe
            title="Tableau de bord ESG Power BI"
            className="w-full h-full border-none"
            src={powerBiUrl}
            allowFullScreen={true}
            style={{ minHeight: '600px' }}
          ></iframe>
        ) : (
          <div className="flex h-full min-h-[600px] items-center justify-center text-sm text-gray-500">
            URL Power BI non configurée.
          </div>
        )}
      </div>
    </div>
  );
}
