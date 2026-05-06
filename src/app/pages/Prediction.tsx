import React, { useState, useRef } from 'react';
import { Calculator, Activity, Leaf, Users, Building, ShieldCheck, Zap, Download } from 'lucide-react';
import { fetchRecommendations, type RecommendationItem } from '../services/api';
import html2canvas from 'html2canvas';
import { jsPDF } from 'jspdf';

type ValidationErrorDetail = {
  field: string;
  message: string;
};

const initialFormState = {
  primary_industry: 'Technology',
  log_market_cap: 20.5,
  log_employees: 8.1,
  log_revenue_wins: 15.2,
  log_scope_1: 4.5,
  log_scope_2: 3.2,
  log_scope_3: 5.1,
  log_energy_consumption: 6.8,
  log_waste_production: 3.4,
  log_water_consumption: 7.2,
  log_hours_of_training_wins: 5.0,
  log_ceo_compensation: 14.5,
  independent_board_members_percentage: 65.0,
  log_legal_costs_paid_for_controversies: 0.0,
  intensity_scope_1: 0.5,
  intensity_scope_2: 0.3,
  intensity_scope_3: 1.2,
  intensity_energy: 0.8,
  intensity_waste: 0.1,
  intensity_water: 0.9,
  intensity_training: 0.4,
  intensity_productivity: 1.5,
  revenue_negative_flag: 0
};

export default function Prediction() {
  const [formData, setFormData] = useState(initialFormState);
  const [score, setScore] = useState<number | null>(null);
  const [suggestions, setSuggestions] = useState<RecommendationItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationErrors, setValidationErrors] = useState<ValidationErrorDetail[]>([]);
  const resultPanelRef = useRef<HTMLDivElement>(null);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: type === 'number' ? parseFloat(value) || 0 : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);
    setValidationErrors([]);
    setScore(null);

    try {
      const response = await fetch('/api/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          // If auth is enabled, you might need to add Authorization header here
          // 'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (!response.ok) {
        if (Array.isArray(data.details)) {
          setValidationErrors(
            data.details
              .filter((detail: any) => detail && typeof detail.field === 'string' && typeof detail.message === 'string')
              .map((detail: any) => ({ field: detail.field, message: detail.message }))
          );
        }

        throw new Error(data.error || 'Erreur lors de la prédiction');
      }

      setScore(data.score);
      // Fetch top recommendations to show inline with the score
      try {
        const recs = await fetchRecommendations({ score: data.score, focus_area: formData.primary_industry });
        setSuggestions(recs.recommendations?.slice(0, 3) ?? []);
      } catch {
        setSuggestions([]);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const getScoreColor = (value: number) => {
    if (value >= 80) return 'text-emerald-500';
    if (value >= 50) return 'text-amber-500';
    return 'text-red-500';
  };

  const getScoreBg = (value: number) => {
    if (value >= 80) return 'from-emerald-400 to-emerald-600';
    if (value >= 50) return 'from-amber-400 to-amber-600';
    return 'from-red-400 to-red-600';
  };

  const handleExportPDF = async () => {
    if (!resultPanelRef.current) return;
    
    setIsExporting(true);
    try {
      const canvas = await html2canvas(resultPanelRef.current, {
        scale: 2, // High quality
        backgroundColor: '#ffffff',
      });
      
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF({
        orientation: 'portrait',
        unit: 'mm',
        format: 'a4',
      });

      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (canvas.height * pdfWidth) / canvas.width;

      pdf.text('Rapport de Simulation ESG', 14, 15);
      pdf.setFontSize(10);
      pdf.setTextColor(100);
      pdf.text(`Secteur: ${formData.primary_industry} | Date: ${new Date().toLocaleDateString()}`, 14, 22);
      
      pdf.addImage(imgData, 'PNG', 15, 30, pdfWidth - 30, pdfHeight - 30);
      pdf.save('Rapport_Simulation_ESG.pdf');
    } catch (err) {
      console.error('Erreur lors de la génération du PDF', err);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="p-8 max-w-7xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
            <Calculator className="w-8 h-8 text-emerald-600" />
            Calculateur de Score ESG
          </h1>
          <p className="text-gray-500 mt-2">
            Entrez les métriques de l'entreprise pour calculer son score ESG via notre modèle.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Formulaire (Prend 2 colonnes sur grand écran) */}
        <div className="lg:col-span-2 bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
          <form onSubmit={handleSubmit} className="space-y-8">
            
            {/* Section: Informations Entreprise */}
            <section>
              <h2 className="text-xl font-semibold text-gray-800 flex items-center gap-2 mb-4 border-b pb-2">
                <Building className="w-5 h-5 text-emerald-500" />
                Informations Entreprise
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-sm font-medium text-gray-700">Secteur d'activité</label>
                  <select name="primary_industry" value={formData.primary_industry} onChange={handleChange} className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all">
                    <option value="Technology">Technologie</option>
                    <option value="Finance">Finance</option>
                    <option value="Energy">Énergie</option>
                    <option value="Healthcare">Santé</option>
                    <option value="Consumer Goods">Biens de consommation</option>
                    <option value="Industrials">Industrie</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-sm font-medium text-gray-700">Log Market Cap</label>
                  <input type="number" step="0.1" name="log_market_cap" value={formData.log_market_cap} onChange={handleChange} className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all" />
                </div>
                <div className="space-y-1">
                  <label className="text-sm font-medium text-gray-700">Log Employés</label>
                  <input type="number" step="0.1" name="log_employees" value={formData.log_employees} onChange={handleChange} className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all" />
                </div>
                <div className="space-y-1">
                  <label className="text-sm font-medium text-gray-700">Log Revenue Wins</label>
                  <input type="number" step="0.1" name="log_revenue_wins" value={formData.log_revenue_wins} onChange={handleChange} className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all" />
                </div>
              </div>
            </section>

            {/* Section: Impact Environnemental */}
            <section>
              <h2 className="text-xl font-semibold text-gray-800 flex items-center gap-2 mb-4 border-b pb-2">
                <Leaf className="w-5 h-5 text-emerald-500" />
                Environnement (E)
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[
                  { name: 'log_scope_1', label: 'Log Scope 1' },
                  { name: 'log_scope_2', label: 'Log Scope 2' },
                  { name: 'log_scope_3', label: 'Log Scope 3' },
                  { name: 'log_energy_consumption', label: 'Log Energy' },
                  { name: 'log_waste_production', label: 'Log Waste' },
                  { name: 'log_water_consumption', label: 'Log Water' },
                  { name: 'intensity_scope_1', label: 'Intensité Scope 1' },
                  { name: 'intensity_energy', label: 'Intensité Énergie' },
                  { name: 'intensity_waste', label: 'Intensité Déchets' },
                ].map((field) => (
                  <div key={field.name} className="space-y-1">
                    <label className="text-sm font-medium text-gray-700">{field.label}</label>
                    <input type="number" step="0.1" name={field.name} value={(formData as any)[field.name]} onChange={handleChange} className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all" />
                  </div>
                ))}
              </div>
            </section>

            {/* Section: Social & Gouvernance */}
            <section>
              <h2 className="text-xl font-semibold text-gray-800 flex items-center gap-2 mb-4 border-b pb-2">
                <Users className="w-5 h-5 text-emerald-500" />
                Social & Gouvernance (S & G)
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {[
                  { name: 'log_hours_of_training_wins', label: 'Log Heures Formation' },
                  { name: 'independent_board_members_percentage', label: '% Membres Indépendants' },
                  { name: 'log_ceo_compensation', label: 'Log CEO Compensation' },
                  { name: 'log_legal_costs_paid_for_controversies', label: 'Log Coûts Légaux' },
                  { name: 'intensity_productivity', label: 'Intensité Productivité' },
                  { name: 'revenue_negative_flag', label: 'Revenue Negative Flag (0/1)' },
                ].map((field) => (
                  <div key={field.name} className="space-y-1">
                    <label className="text-sm font-medium text-gray-700">{field.label}</label>
                    <input type="number" step="0.1" name={field.name} value={(formData as any)[field.name]} onChange={handleChange} className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-all" />
                  </div>
                ))}
              </div>
            </section>

            <button
              type="submit"
              disabled={isLoading}
              className={`w-full py-4 px-6 rounded-xl text-white font-bold text-lg shadow-lg hover:shadow-xl transition-all flex items-center justify-center gap-3 ${
                isLoading ? 'bg-emerald-400 cursor-not-allowed' : 'bg-gradient-to-r from-emerald-600 to-teal-500 hover:scale-[1.01]'
              }`}
            >
              {isLoading ? (
                <>
                  <Activity className="w-6 h-6 animate-spin" />
                  Calcul en cours...
                </>
              ) : (
                <>
                  <Zap className="w-6 h-6" />
                  Prédire le Score ESG
                </>
              )}
            </button>

            {error && (
              <div className="p-4 bg-red-50 text-red-700 rounded-lg border border-red-200 space-y-3">
                <div className="flex items-center gap-3">
                  <ShieldCheck className="w-5 h-5 text-red-500" />
                  <p className="font-medium">{error}</p>
                </div>

                {validationErrors.length > 0 && (
                  <div className="rounded-lg bg-white/80 border border-red-100 p-3">
                    <p className="text-sm font-semibold text-red-700 mb-2">Détails de validation</p>
                    <ul className="space-y-2 text-sm">
                      {validationErrors.map((validationError) => (
                        <li key={`${validationError.field}-${validationError.message}`} className="flex gap-2">
                          <span className="font-semibold text-red-600 min-w-0 shrink-0">{validationError.field}:</span>
                          <span className="text-red-700">{validationError.message}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </form>
        </div>

        {/* Résultat (Panneau latéral collant) */}
        <div className="lg:col-span-1">
          <div ref={resultPanelRef} className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 sticky top-24 overflow-hidden relative group">
            {/* Effet décoratif en fond */}
            <div className="absolute top-0 right-0 -mr-8 -mt-8 w-32 h-32 rounded-full bg-gradient-to-br from-emerald-50 to-teal-50 opacity-50 group-hover:scale-150 transition-transform duration-700"></div>

            <h3 className="text-xl font-bold text-gray-800 mb-6 flex items-center gap-2 relative z-10">
              <Activity className="w-6 h-6 text-emerald-500" />
              Résultat de l'IA
            </h3>

            {score !== null ? (
              <div className="text-center relative z-10 animate-in zoom-in duration-500">
                <div className="mb-4">
                  <span className="text-sm font-semibold uppercase tracking-wider text-gray-500">Score Global ESG</span>
                </div>
                
                {/* Jauge stylisée */}
                <div className={`mx-auto w-48 h-48 rounded-full flex items-center justify-center shadow-inner relative bg-gradient-to-br ${getScoreBg(score)}`}>
                  <div className="absolute inset-2 bg-white rounded-full flex items-center justify-center shadow-lg">
                    <span className={`text-6xl font-black ${getScoreColor(score)}`}>
                      {score.toFixed(1)}
                    </span>
                  </div>
                </div>

                <div className="mt-8 space-y-4">
                  <div className="p-4 bg-gray-50 rounded-xl border border-gray-100">
                    <p className="text-sm text-gray-600 font-medium">Interprétation :</p>
                    <p className={`text-lg font-bold mt-1 ${getScoreColor(score)}`}>
                      {score >= 80 ? 'Excellente Performance' : score >= 50 ? 'Performance Moyenne' : 'Risque Élevé'}
                    </p>
                  </div>
                  
                  <p className="text-xs text-gray-400">
                    Modèle CatBoost v1.2 (Précision estimée: 89%)
                  </p>

                  <button
                    onClick={handleExportPDF}
                    disabled={isExporting}
                    type="button"
                    className="mt-6 w-full py-3 px-4 rounded-xl border-2 border-emerald-500 text-emerald-600 font-bold hover:bg-emerald-50 transition-colors flex items-center justify-center gap-2"
                  >
                    <Download className="w-5 h-5" />
                    {isExporting ? 'Génération...' : 'Exporter en PDF'}
                  </button>

                  {/* Inline recommendations */}
                  {suggestions.length > 0 && (
                    <div className="mt-6">
                      <h4 className="font-semibold mb-3">Recommandations suggérées</h4>
                      <div className="space-y-3">
                        {suggestions.map((rec) => (
                          <div key={rec.id} className="p-3 bg-gray-50 rounded-lg border border-gray-100">
                            <div className="flex items-start justify-between">
                              <div>
                                <p className="font-semibold text-sm">{rec.title}</p>
                                <p className="text-xs text-gray-600 mt-1">Impact: +{rec.impact} pts • Effort: {rec.effort}</p>
                              </div>
                              <div>
                                <button
                                  onClick={() => (window.location.href = `/recommendations?focus=${encodeURIComponent(formData.primary_industry)}`)}
                                  className="text-sm text-emerald-600 font-semibold"
                                >
                                  Voir tout
                                </button>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-center py-12 relative z-10 opacity-60">
                <Calculator className="w-16 h-16 text-gray-200 mx-auto mb-4" />
                <p className="text-gray-400 font-medium">
                  Remplissez le formulaire et lancez la prédiction pour voir le résultat apparaître ici.
                </p>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
