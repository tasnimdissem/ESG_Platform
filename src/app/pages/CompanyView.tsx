import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ESGIndicatorForm } from '../components/ESGIndicatorForm';
import { addCompanyHistory, fetchCompany, type CompanyRecord } from '../services/api';
import { DEFAULT_INDICATORS, ESGIndicators } from '../utils/esgIndicators';

export default function CompanyView() {
  const { id } = useParams();
  const [company, setCompany] = useState<CompanyRecord | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [indicators, setIndicators] = useState<ESGIndicators>(DEFAULT_INDICATORS);
  // Prediction UI moved to the dedicated ESG simulator
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      if (!id) {
        setCompany(null);
        return;
      }

      setLoadError(null);
      try {
        const found = await fetchCompany(id);
        setCompany(found);
      } catch (err) {
        console.error('Erreur chargement entreprise', err);
        setCompany(null);
        setLoadError('Entreprise introuvable ou inaccessible.');
      }
    };

    void load();
  }, [id]);

  const handleIndicatorChange = (field: keyof ESGIndicators, value: string | number) => {
    setIndicators((prev) => ({
      ...prev,
      [field]: typeof DEFAULT_INDICATORS[field] === 'number' ? (typeof value === 'string' ? parseFloat(value) || 0 : value) : value,
    }));
  };

  const addPrediction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!company) return;
    setIsLoading(true);
    try {
      const res = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(indicators),
      });
      const data = await res.json();
      const score = data.score ?? null;

      if (score === null) {
        throw new Error('Score invalide');
      }

      const updatedCompany = await addCompanyHistory(company.entreprise_id, {
        indicators,
        score,
      });

      setCompany(updatedCompany);
      setShowForm(false);
      setIndicators(DEFAULT_INDICATORS);
    } catch (err) {
      console.error(err);
      alert('Erreur lors du calcul');
    } finally {
      setIsLoading(false);
    }
  };

  if (!company) return <div className="p-4 md:p-6">{loadError ?? 'Entreprise introuvable.'}</div>;

  const chartData = (company.historique || []).map((h) => ({ date: h.date, score: h.scores?.global ?? null })).reverse();

  return (
    <div className="p-4 md:p-6">
      <div className="mb-6">
        <h2 className="text-3xl font-bold text-slate-900">{company.nom}</h2>
        <p className="text-slate-500 mt-1">Historique de {company.historique?.length || 0} prédiction(s)</p>
      </div>

      {/* Graphique d'évolution */}
      <div className="mb-6 bg-white border border-slate-200 rounded-lg p-6">
        <h3 className="font-semibold text-lg mb-4">Évolution du score global</h3>
        {chartData.length === 0 ? (
          <div className="text-center py-8 text-slate-500">Aucun historique disponible.</div>
        ) : (
          <div style={{ width: '100%', height: 300 }}>
            <ResponsiveContainer>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Line type="monotone" dataKey="score" stroke="#16a34a" strokeWidth={2} dot={{ fill: '#16a34a' }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* Formulaire d'ajout de prédiction */}
      {/* Prediction moved to the dedicated ESG simulator page */}

      {/* Historique détaillé */}
      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <h3 className="font-semibold text-lg mb-4">Historique complet</h3>
        <div className="space-y-3">
          {(company.historique || []).length === 0 ? (
            <div className="text-center py-8 text-slate-500">Aucun historique disponible.</div>
          ) : (
            (company.historique || []).map((h, idx: number) => (
              <div key={idx} className="p-4 border border-slate-200 rounded flex items-start justify-between hover:bg-slate-50">
                <div>
                  <div className="font-semibold text-slate-900">{h.date}</div>
                  <div className="text-sm text-slate-600 mt-1">Score global: <span className="font-semibold text-emerald-600">{typeof h.scores?.global === 'number' ? h.scores.global.toFixed(1) : 'N/A'}</span></div>
                  <div className="text-xs text-slate-500 mt-1">E: {typeof h.scores?.E === 'number' ? h.scores.E.toFixed(1) : 'N/A'}, S: {typeof h.scores?.S === 'number' ? h.scores.S.toFixed(1) : 'N/A'}, G: {typeof h.scores?.G === 'number' ? h.scores.G.toFixed(1) : 'N/A'}</div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
