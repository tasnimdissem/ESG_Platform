// La page Analytics récupère maintenant les données ESG en direct depuis le backend afin que les graphiques reflètent l'historique de prédictions CatBoost au lieu de valeurs de démonstration statiques.
import { useEffect, useState } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Download, TrendingUp } from 'lucide-react';

type MonthlyPoint = {
  mois: string;
  score: number | null;
};

type VariablePoint = {
  feature: string;
  importance: number;
};

type CorrelationCell = {
  x: string;
  y: string;
  value: number;
};

type AnalyticsSummary = {
  score_moyen: number | null;
  score_min: number | null;
  score_max: number | null;
  nb_predictions: number;
  evolution_mensuelle: MonthlyPoint[];
  top_variables: VariablePoint[];
  correlation_matrix: CorrelationCell[];
};

const emptySummary: AnalyticsSummary = {
  score_moyen: null,
  score_min: null,
  score_max: null,
  nb_predictions: 0,
  evolution_mensuelle: [],
  top_variables: [],
  correlation_matrix: [],
};

function formatScore(value: number | null) {
  return value === null ? '—' : value.toFixed(1);
}

function toSafeNumber(value: unknown, fallback = 0) {
  const parsed = typeof value === 'number' ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function formatTooltipNumber(value: unknown, digits = 2) {
  const num = Number(value);
  return Number.isFinite(num) ? num.toFixed(digits) : '—';
}

export default function Analytics() {
  const [selectedPeriod, setSelectedPeriod] = useState('12m');
  const [analyticsData, setAnalyticsData] = useState<AnalyticsSummary>(emptySummary);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const loadAnalytics = async () => {
      try {
        setIsLoading(true);
        setErrorMessage(null);
        const qs = new URLSearchParams({ period: selectedPeriod });
        const response = await fetch(`/api/analytics/summary?${qs.toString()}`, { credentials: 'include' });
        if (!response.ok) {
          throw new Error('Impossible de charger les analyses');
        }
        const data = (await response.json()) as AnalyticsSummary;
        setAnalyticsData({
          ...emptySummary,
          ...data,
        });
      } catch (error) {
        setErrorMessage(error instanceof Error ? error.message : 'Erreur inconnue');
        setAnalyticsData(emptySummary);
      } finally {
        setIsLoading(false);
      }
    };

    void loadAnalytics();
  }, []);

  const evolutionData = analyticsData.evolution_mensuelle.map((item) => ({
    month: item.mois,
    score: item.score === null ? null : toSafeNumber(item.score, 0),
  }));

  const topVariables = analyticsData.top_variables.map((item) => ({
    feature: item.feature,
    importance: toSafeNumber(item.importance, 0) * 100,
  }));

  // correlation heatmap removed per design preference

  const exportAnalyticsCSV = () => {
    const lines: string[] = [];
    // Summary
    lines.push('Metric,Value');
    lines.push(`Score moyen,${analyticsData.score_moyen ?? ''}`);
    lines.push(`Score min,${analyticsData.score_min ?? ''}`);
    lines.push(`Score max,${analyticsData.score_max ?? ''}`);
    lines.push(`Nombre de predictions,${analyticsData.nb_predictions}`);
    lines.push('');
    // Evolution
    lines.push('Mois,Score');
    evolutionData.forEach((d) => {
      lines.push(`${d.month},${d.score === null ? '' : d.score}`);
    });
    lines.push('');
    // Top variables
    lines.push('Variable,Importance (%)');
    topVariables.forEach((v) => lines.push(`${v.feature},${v.importance.toFixed(2)}`));

    const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analytics_${selectedPeriod}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  };

  const isEmptyState = !isLoading && analyticsData.nb_predictions < 2;

  if (isLoading) {
    return (
      <div className="p-8 space-y-8 bg-gray-50 min-h-screen animate-pulse">
        <div className="flex items-center justify-between">
          <div className="space-y-3">
            <div className="h-8 w-80 rounded bg-gray-200" />
            <div className="h-4 w-96 rounded bg-gray-200" />
          </div>
          <div className="h-10 w-40 rounded-lg bg-gray-200" />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {Array.from({ length: 4 }).map((_, index) => (
            <div key={index} className="h-28 rounded-xl bg-gray-200" />
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-96 rounded-xl bg-gray-200" />
          <div className="h-96 rounded-xl bg-gray-200" />
        </div>

        <div className="h-64 rounded-xl bg-gray-200" />
      </div>
    );
  }

  return (
    <div className="p-8 space-y-8 bg-gray-50 min-h-screen">
      {/* Header with Filters */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Analyses ESG détaillées</h1>
          <p className="text-gray-600">Analyse en temps réel basée sur l’historique CatBoost de la plateforme.</p>
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
              <option value="12m">12 Mois</option>
              <option value="all">Tout</option>
            </select>

            <button onClick={exportAnalyticsCSV} className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-all flex items-center gap-2">
              <Download className="w-4 h-4" />
              Exporter
            </button>
          </div>
      </div>

      {errorMessage && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          {errorMessage}
        </div>
      )}

      {isEmptyState ? (
        <div className="rounded-2xl border border-dashed border-gray-300 bg-white p-8 text-center text-gray-500">
          Aucune prédiction enregistrée, utilisez le calculateur pour commencer.
        </div>
      ) : (
        <>
          {/* Key Performance Indicators */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <div className="bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-xl p-6 text-white">
              <p className="text-emerald-100 text-sm mb-2">Score Global Moyen</p>
              <p className="text-4xl font-bold mb-2">{formatScore(analyticsData.score_moyen)}</p>
              <div className="flex items-center gap-2 text-sm">
                <TrendingUp className="w-4 h-4" />
                <span>{analyticsData.nb_predictions} prédiction(s)</span>
              </div>
            </div>

            <div className="bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl p-6 text-white">
              <p className="text-blue-100 text-sm mb-2">Prédictions</p>
              <p className="text-4xl font-bold mb-2">{analyticsData.nb_predictions}</p>
              <p className="text-sm text-blue-100">Historique CatBoost</p>
            </div>

            <div className="bg-gradient-to-br from-purple-500 to-purple-600 rounded-xl p-6 text-white">
              <p className="text-purple-100 text-sm mb-2">Score Minimum</p>
              <p className="text-4xl font-bold mb-2">{formatScore(analyticsData.score_min)}</p>
              <p className="text-sm text-purple-100">Période active</p>
            </div>

            <div className="bg-gradient-to-br from-orange-500 to-orange-600 rounded-xl p-6 text-white">
              <p className="text-orange-100 text-sm mb-2">Score Maximum</p>
              <p className="text-4xl font-bold mb-2">{formatScore(analyticsData.score_max)}</p>
              <p className="text-sm text-orange-100">Période active</p>
            </div>
          </div>

          {/* Evolution and variables */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
              <h3 className="font-bold text-lg mb-4">Évolution Mensuelle ESG</h3>
              <ResponsiveContainer width="100%" height={350}>
                <LineChart data={evolutionData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="month" stroke="#6b7280" />
                  <YAxis stroke="#6b7280" domain={[0, 100]} />
                  <Tooltip formatter={(value) => [formatTooltipNumber(value, 1), 'Score moyen']} />
                  <Legend />
                  <Line type="monotone" dataKey="score" stroke="#10b981" strokeWidth={3} dot={{ r: 5 }} name="Score moyen" />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm">
              <h3 className="font-bold text-lg mb-4">Importance des Variables</h3>
              <ResponsiveContainer width="100%" height={350}>
                <BarChart data={topVariables} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis type="number" stroke="#6b7280" />
                  <YAxis type="category" dataKey="feature" stroke="#6b7280" width={140} />
                  <Tooltip formatter={(value) => [`${formatTooltipNumber(value, 2)}%`, 'Importance']} />
                  <Bar dataKey="importance" fill="#10b981" radius={[0, 8, 8, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

        </>
      )}
    </div>
  );
}
