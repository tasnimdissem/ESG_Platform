import { useEffect, useMemo, useState } from 'react';
import { Target, TrendingUp, AlertTriangle, CheckCircle, Clock, Zap, RefreshCcw, X } from 'lucide-react';
import { fetchRecommendations, type RecommendationItem } from '../services/api';

export default function Recommendations() {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedPriority, setSelectedPriority] = useState<string>('all');
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [ragUsed, setRagUsed] = useState(false);
  const [sourceCount, setSourceCount] = useState(0);
  const [selectedDetails, setSelectedDetails] = useState<RecommendationItem | null>(null);
  const [recommendationStatus, setRecommendationStatus] = useState<Record<string, 'not-started' | 'in-progress' | 'completed'>>({});

  const loadRecommendations = async () => {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await fetchRecommendations({
        score: 76,
        risk_level: 'Medium',
        focus_area: selectedCategory === 'all' ? 'overall' : selectedCategory,
      });
      setRecommendations(response.recommendations ?? []);
      setRagUsed(Boolean(response.rag_used));
      setSourceCount(Number(response.source_count ?? 0));
    } catch {
      setRecommendations([]);
      setErrorMessage('Impossible de charger les recommandations depuis le backend local.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadRecommendations();
  }, [selectedCategory]);

  const filteredRecommendations = useMemo(
    () =>
      recommendations.filter((rec) => {
        if (selectedCategory !== 'all' && rec.category !== selectedCategory) return false;
        if (selectedPriority !== 'all' && rec.priority !== selectedPriority) return false;
        return true;
      }),
    [recommendations, selectedCategory, selectedPriority],
  );

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-700 border-red-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'low':
        return 'bg-green-100 text-green-700 border-green-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getEffortColor = (effort: string) => {
    switch (effort) {
      case 'high':
        return 'text-red-600';
      case 'medium':
        return 'text-yellow-600';
      case 'low':
        return 'text-green-600';
      default:
        return 'text-gray-600';
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'Environmental':
        return 'bg-green-500';
      case 'Social':
        return 'bg-blue-500';
      case 'Governance':
        return 'bg-purple-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'in-progress':
        return <Clock className="w-5 h-5 text-blue-600" />;
      case 'not-started':
        return <Target className="w-5 h-5 text-gray-400" />;
      default:
        return null;
    }
  };

  const totalImpact = filteredRecommendations.reduce((sum, rec) => sum + rec.impact, 0);

  return (
    <div className="p-8 space-y-8 bg-gray-50 min-h-screen">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Système de Recommandations</h1>
        <p className="text-gray-600">Actions personnalisées alimentees par le backend RAG local de cette plateforme.</p>
      </div>

      {errorMessage && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">
          {errorMessage}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-gradient-to-br from-emerald-500 to-emerald-600 rounded-xl p-6 text-white">
          <div className="flex items-center justify-between mb-2">
            <p className="text-emerald-100 text-sm">Impact Total Potentiel</p>
            <Zap className="w-5 h-5" />
          </div>
          <p className="text-4xl font-bold">+{totalImpact}</p>
          <p className="text-sm text-emerald-100 mt-1">points ESG</p>
        </div>

        <div className="bg-white rounded-xl p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <p className="text-gray-600 text-sm">Recommandations Actives</p>
            <Target className="w-5 h-5 text-blue-600" />
          </div>
          <p className="text-4xl font-bold text-gray-900">{recommendations.length}</p>
          <p className="text-sm text-gray-500 mt-1">RAG: {ragUsed ? 'oui' : 'non'}</p>
        </div>

        <div className="bg-white rounded-xl p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <p className="text-gray-600 text-sm">Priorité Haute</p>
            <AlertTriangle className="w-5 h-5 text-red-600" />
          </div>
          <p className="text-4xl font-bold text-gray-900">{recommendations.filter((r) => r.priority === 'high').length}</p>
          <p className="text-sm text-gray-500 mt-1">Actions critiques</p>
        </div>

        <div className="bg-white rounded-xl p-6 border border-gray-200">
          <div className="flex items-center justify-between mb-2">
            <p className="text-gray-600 text-sm">Sources RAG</p>
            <Clock className="w-5 h-5 text-purple-600" />
          </div>
          <p className="text-4xl font-bold text-gray-900">{sourceCount}</p>
          <p className="text-sm text-gray-500 mt-1">sources disponibles</p>
        </div>
      </div>

      <div className="bg-white rounded-xl p-6 border border-gray-200">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">Catégorie</label>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="all">Toutes les catégories</option>
              <option value="Environmental">Environnemental</option>
              <option value="Social">Social</option>
              <option value="Governance">Gouvernance</option>
            </select>
          </div>

          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">Priorité</label>
            <select
              value={selectedPriority}
              onChange={(e) => setSelectedPriority(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="all">Toutes les priorités</option>
              <option value="high">Haute</option>
              <option value="medium">Moyenne</option>
              <option value="low">Basse</option>
            </select>
          </div>

          <button
            onClick={() => void loadRecommendations()}
            className="inline-flex items-center justify-center gap-2 rounded-lg border border-gray-300 px-4 py-2 font-semibold text-gray-700 hover:bg-gray-50"
          >
            <RefreshCcw className="h-4 w-4" />
            Rafraichir
          </button>
        </div>
      </div>

      <div className="space-y-6">
        {isLoading ? (
          <div className="rounded-xl border border-gray-200 bg-white p-6 text-sm text-gray-500">
            Chargement des recommandations RAG...
          </div>
        ) : filteredRecommendations.length === 0 ? (
          <div className="rounded-xl border border-gray-200 bg-white p-6 text-sm text-gray-500">
            Aucune recommandation disponible pour les filtres actuels.
          </div>
        ) : (
          filteredRecommendations.map((rec) => (
            <div key={rec.id} className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm hover:shadow-md transition-all">
              <div className="flex items-start justify-between mb-4">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2 flex-wrap">
                    {getStatusIcon(rec.status)}
                    <h3 className="font-bold text-xl text-gray-900">{rec.title}</h3>
                    <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${getPriorityColor(rec.priority)}`}>
                      {rec.priority === 'high' ? 'Priorite Haute' : rec.priority === 'medium' ? 'Priorite Moyenne' : 'Priorite Basse'}
                    </span>
                  </div>
                  <p className="text-gray-600 mb-3">{rec.description}</p>
                </div>

                <div className={`w-2 h-2 ${getCategoryColor(rec.category)} rounded-full ml-4`} />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
                <div className="flex items-center gap-2">
                  <TrendingUp className="w-4 h-4 text-emerald-600" />
                  <div>
                    <p className="text-xs text-gray-500">Impact</p>
                    <p className="font-semibold text-emerald-600">+{rec.impact} points</p>
                  </div>
                </div>

                <div>
                  <p className="text-xs text-gray-500 mb-1">Score Actuel -> Cible</p>
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">{rec.currentScore}</span>
                    <span className="text-gray-400">→</span>
                    <span className="font-semibold text-emerald-600">{rec.targetScore}</span>
                  </div>
                </div>

                <div>
                  <p className="text-xs text-gray-500 mb-1">Effort Requis</p>
                  <p className={`font-semibold ${getEffortColor(rec.effort)}`}>
                    {rec.effort === 'high' ? 'Élevé' : rec.effort === 'medium' ? 'Moyen' : 'Faible'}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-gray-500 mb-1">Délai</p>
                  <p className="font-semibold">{rec.timeline}</p>
                </div>
              </div>

              <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-semibold text-sm mb-3 text-gray-700">Plan d'Action:</h4>
                <div className="space-y-2">
                  {rec.actions.map((action, index) => (
                    <div key={index} className="flex items-start gap-2">
                      <div className="w-5 h-5 bg-emerald-100 rounded flex items-center justify-center flex-shrink-0 mt-0.5">
                        <span className="text-emerald-600 text-xs font-semibold">{index + 1}</span>
                      </div>
                      <p className="text-sm text-gray-700">{action}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-4 flex items-center gap-3">
                <button
                  onClick={() => {
                    setRecommendationStatus((prev) => ({
                      ...prev,
                      [rec.id]: prev[rec.id] === 'in-progress' ? 'not-started' : 'in-progress',
                    }));
                  }}
                  className={`px-6 py-2 rounded-lg transition-all font-semibold ${
                    recommendationStatus[rec.id] === 'in-progress'
                      ? 'bg-blue-100 text-blue-700 border border-blue-300'
                      : 'bg-emerald-600 text-white hover:bg-emerald-700'
                  }`}
                >
                  {recommendationStatus[rec.id] === 'in-progress' ? '✓ En cours' : 'Démarrer l\'Action'}
                </button>
                <button
                  onClick={() => setSelectedDetails(rec)}
                  className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-all font-semibold"
                >
                  Voir Détails
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {selectedDetails && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-gradient-to-r from-emerald-500 to-emerald-600 text-white p-6 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`w-3 h-3 ${getCategoryColor(selectedDetails.category)} rounded-full`}></div>
                <h2 className="text-2xl font-bold">{selectedDetails.title}</h2>
              </div>
              <button
                onClick={() => setSelectedDetails(null)}
                className="text-white hover:bg-white/20 p-2 rounded-lg transition-all"
              >
                <X className="w-6 h-6" />
              </button>
            </div>

            <div className="p-8 space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Description</h3>
                <p className="text-gray-700 leading-relaxed">{selectedDetails.description}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-emerald-50 rounded-lg p-4 border border-emerald-200">
                  <p className="text-sm font-semibold text-gray-600 mb-1">Priorité</p>
                  <p className={`text-lg font-bold ${
                    selectedDetails.priority === 'high' ? 'text-red-600' :
                    selectedDetails.priority === 'medium' ? 'text-yellow-600' :
                    'text-green-600'
                  }`}>
                    {selectedDetails.priority === 'high' ? 'Haute' : selectedDetails.priority === 'medium' ? 'Moyenne' : 'Basse'}
                  </p>
                </div>

                <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                  <p className="text-sm font-semibold text-gray-600 mb-1">Impact Potentiel</p>
                  <p className="text-lg font-bold text-emerald-600">+{selectedDetails.impact} points</p>
                </div>

                <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                  <p className="text-sm font-semibold text-gray-600 mb-1">Effort Requis</p>
                  <p className={`text-lg font-bold ${
                    selectedDetails.effort === 'high' ? 'text-red-600' :
                    selectedDetails.effort === 'medium' ? 'text-yellow-600' :
                    'text-green-600'
                  }`}>
                    {selectedDetails.effort === 'high' ? 'Élevé' : selectedDetails.effort === 'medium' ? 'Moyen' : 'Faible'}
                  </p>
                </div>

                <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
                  <p className="text-sm font-semibold text-gray-600 mb-1">Délai Estimé</p>
                  <p className="text-lg font-bold text-orange-600">{selectedDetails.timeline}</p>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Plan d'Action</h3>
                <div className="space-y-3">
                  {selectedDetails.actions.map((action, index) => (
                    <div key={index} className="flex gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
                      <div className="w-8 h-8 bg-emerald-100 rounded-full flex items-center justify-center flex-shrink-0">
                        <span className="text-emerald-600 font-bold text-sm">{index + 1}</span>
                      </div>
                      <p className="text-gray-700">{action}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-gray-600 mb-2"><span className="font-semibold">Score actuel:</span> {selectedDetails.currentScore}</p>
                <p className="text-sm text-gray-600"><span className="font-semibold">Score cible:</span> {selectedDetails.targetScore}</p>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  onClick={() => {
                    setRecommendationStatus((prev) => ({
                      ...prev,
                      [selectedDetails.id]: 'in-progress',
                    }));
                    setSelectedDetails(null);
                  }}
                  className="flex-1 px-6 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 font-semibold transition-all"
                >
                  Marquer comme en cours
                </button>
                <button
                  onClick={() => setSelectedDetails(null)}
                  className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 font-semibold transition-all"
                >
                  Fermer
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
