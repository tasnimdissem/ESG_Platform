import { useState } from 'react';
import { LineChart, Line, BarChart, Bar, ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { Download, Filter, Calendar, TrendingUp } from 'lucide-react';

const detailedMetrics = [
  { category: 'Émissions CO2', actual: 75, target: 90, trend: 'up', change: '+8%' },
  { category: 'Consommation Eau', actual: 82, target: 85, trend: 'up', change: '+5%' },
  { category: 'Déchets Recyclés', actual: 68, target: 80, trend: 'up', change: '+12%' },
  { category: 'Énergie Renouvelable', actual: 85, target: 95, trend: 'up', change: '+15%' },
  { category: 'Diversité Genre', actual: 78, target: 85, trend: 'up', change: '+6%' },
  { category: 'Formation Employés', actual: 88, target: 90, trend: 'stable', change: '+2%' },
  { category: 'Sécurité Travail', actual: 92, target: 95, trend: 'up', change: '+4%' },
  { category: 'Satisfaction Employés', actual: 84, target: 88, trend: 'up', change: '+7%' },
  { category: 'Conformité Réglementaire', actual: 95, target: 98, trend: 'stable', change: '+1%' },
  { category: 'Transparence Financière', actual: 90, target: 92, trend: 'up', change: '+3%' },
];

const monthlyData = [
  { month: 'Jan', E: 72, S: 68, G: 75 },
  { month: 'Fév', E: 74, S: 70, G: 76 },
  { month: 'Mar', E: 76, S: 72, G: 78 },
  { month: 'Avr', E: 78, S: 74, G: 80 },
  { month: 'Mai', E: 80, S: 76, G: 82 },
  { month: 'Jun', E: 82, S: 78, G: 84 },
];

const correlationData = [
  { feature: 'Revenue', score: 78, correlation: 0.65 },
  { feature: 'Employees', score: 82, correlation: 0.72 },
  { feature: 'R&D Invest', score: 85, correlation: 0.81 },
  { feature: 'Market Cap', score: 75, correlation: 0.58 },
  { feature: 'Industry Age', score: 70, correlation: 0.45 },
  { feature: 'Board Size', score: 88, correlation: 0.77 },
  { feature: 'ESG Budget', score: 92, correlation: 0.89 },
];

export default function Analytics() {
  const [selectedPeriod, setSelectedPeriod] = useState('6m');

  return (
    <div className="p-8 space-y-8 bg-gray-50 min-h-screen">
      {/* Header with Filters */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Analytics ESG Détaillées</h1>
          <p className="text-gray-600">Analyse approfondie des métriques et corrélations</p>
        </div>
        
        <div className="flex items-center gap-3">
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value)}
            className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
          >
            <option value="1m">1 Mois</option>
            <option value="3m">3 Mois</option>
            <option value="6m">6 Mois</option>
            <option value="1y">1 An</option>
            <option value="all">Tout</option>
          </select>
          
          <button className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-all flex items-center gap-2">
            <Download className="w-4 h-4" />
            Exporter
          </button>
        </div>
      </div>

      {/* Key Performance Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-xl p-6 text-white">
          <p className="text-emerald-100 text-sm mb-2">Score Global Prédit</p>
          <p className="text-4xl font-bold mb-2">90.2</p>
          <div className="flex items-center gap-2 text-sm">
            <TrendingUp className="w-4 h-4" />
            <span>+11% vs année dernière</span>
          </div>
        </div>

        <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 text-white">
          <p className="text-blue-100 text-sm mb-2">Précision Modèle ML</p>
          <p className="text-4xl font-bold mb-2">94.2%</p>
          <p className="text-sm text-blue-100">Random Forest + XGBoost</p>
        </div>

        <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-6 text-white">
          <p className="text-purple-100 text-sm mb-2">Features Analysées</p>
          <p className="text-4xl font-bold mb-2">47</p>
          <p className="text-sm text-purple-100">Variables prédictives</p>
        </div>

        <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl p-6 text-white">
          <p className="text-orange-100 text-sm mb-2">Améliorations Possibles</p>
          <p className="text-4xl font-bold mb-2">+12pts</p>
          <p className="text-sm text-orange-100">Potentiel d'optimisation</p>
        </div>
      </div>

      {/* Detailed Metrics Table */}
      <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
        <h3 className="font-bold text-lg mb-4">Métriques Détaillées par Catégorie</h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Catégorie</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Score Actuel</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Objectif</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Progression</th>
                <th className="text-left py-3 px-4 font-semibold text-gray-700">Tendance</th>
              </tr>
            </thead>
            <tbody>
              {detailedMetrics.map((metric, index) => (
                <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-3 px-4 font-medium">{metric.category}</td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">{metric.actual}</span>
                      <div className="w-20 h-2 bg-gray-200 rounded-full">
                        <div
                          className="h-full bg-emerald-500 rounded-full"
                          style={{ width: `${metric.actual}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-gray-600">{metric.target}</td>
                  <td className="py-3 px-4">
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="h-full bg-blue-500 rounded-full"
                        style={{ width: `${(metric.actual / metric.target) * 100}%` }}
                      />
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="inline-flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-semibold">
                      <TrendingUp className="w-3 h-3" />
                      {metric.change}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly Trends */}
        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
          <h3 className="font-bold text-lg mb-4">Évolution Mensuelle E-S-G</h3>
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={monthlyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="month" stroke="#6b7280" />
              <YAxis stroke="#6b7280" domain={[60, 90]} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="E" stroke="#10b981" strokeWidth={3} dot={{ r: 5 }} name="Environnemental" />
              <Line type="monotone" dataKey="S" stroke="#3b82f6" strokeWidth={3} dot={{ r: 5 }} name="Social" />
              <Line type="monotone" dataKey="G" stroke="#8b5cf6" strokeWidth={3} dot={{ r: 5 }} name="Gouvernance" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Feature Correlation */}
        <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
          <h3 className="font-bold text-lg mb-4">Corrélation Features ML</h3>
          <ResponsiveContainer width="100%" height={350}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis type="number" dataKey="correlation" name="Corrélation" stroke="#6b7280" domain={[0, 1]} />
              <YAxis type="number" dataKey="score" name="Score" stroke="#6b7280" domain={[60, 100]} />
              <Tooltip cursor={{ strokeDasharray: '3 3' }} />
              <Scatter name="Features" data={correlationData} fill="#8b5cf6">
                {correlationData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.correlation > 0.7 ? '#10b981' : entry.correlation > 0.5 ? '#3b82f6' : '#f59e0b'} />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
          <div className="mt-4 flex items-center justify-center gap-6 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-emerald-500 rounded-full" />
              <span>Forte corrélation (&gt;0.7)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-blue-500 rounded-full" />
              <span>Moyenne (0.5-0.7)</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-orange-500 rounded-full" />
              <span>Faible (&lt;0.5)</span>
            </div>
          </div>
        </div>
      </div>

      {/* ML Model Insights */}
      <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
        <h3 className="font-bold text-lg mb-4">Insights du Modèle ML</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
            <h4 className="font-semibold mb-2">Top Feature</h4>
            <p className="text-2xl font-bold text-purple-700 mb-1">ESG Budget</p>
            <p className="text-sm text-gray-600">Corrélation: 0.89 | Importance: 23.4%</p>
          </div>
          
          <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
            <h4 className="font-semibold mb-2">Algorithme Principal</h4>
            <p className="text-2xl font-bold text-blue-700 mb-1">Random Forest</p>
            <p className="text-sm text-gray-600">500 arbres | Profondeur max: 15</p>
          </div>
          
          <div className="p-4 bg-green-50 rounded-lg border border-green-200">
            <h4 className="font-semibold mb-2">Validation Croisée</h4>
            <p className="text-2xl font-bold text-green-700 mb-1">93.8%</p>
            <p className="text-sm text-gray-600">K-Fold (k=5) | RMSE: 2.3</p>
          </div>
        </div>
      </div>
    </div>
  );
}
