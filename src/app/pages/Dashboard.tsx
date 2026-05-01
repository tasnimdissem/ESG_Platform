import { LayoutDashboard } from 'lucide-react';

export default function Dashboard() {
  return (
    <div className="p-8 space-y-8 bg-gray-50 min-h-screen">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3">
          <LayoutDashboard className="w-8 h-8 text-emerald-600" />
          Dashboard ESG Global
        </h1>
        <p className="text-gray-600">
          Vue d'ensemble et données consolidées de l'entreprise (Intégration PowerBI)
        </p>
      </div>

      {/* PowerBI Iframe Container */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden" style={{ height: '80vh' }}>
        <div className="p-4 bg-gray-100 border-b border-gray-200 flex justify-between items-center">
          <span className="font-semibold text-gray-700 text-sm">Rapport Interactif PowerBI</span>
          <span className="text-xs px-2 py-1 bg-emerald-100 text-emerald-800 rounded-full font-medium">Connecté en temps réel</span>
        </div>
        
        {/* Replace the src with your actual PowerBI publish-to-web or embedded URL */}
        <iframe
          title="PowerBI ESG Dashboard"
          className="w-full h-full border-none"
          src="https://app.powerbi.com/reportEmbed?reportId=votre_id_de_rapport&autoAuth=true&ctid=votre_tenant_id"
          allowFullScreen={true}
          style={{ minHeight: '600px' }}
        ></iframe>
      </div>
    </div>
  );
}
