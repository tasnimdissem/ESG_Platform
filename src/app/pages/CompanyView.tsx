import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { ESGIndicatorForm } from '../components/ESGIndicatorForm';
import { DEFAULT_INDICATORS, ESGIndicators } from '../utils/esgIndicators';

const STORAGE_KEY = 'esg_companies_v1';

function loadCompanies() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveCompanies(list: any[]) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(list));
}

export default function CompanyView() {
  const { id } = useParams();
  const [company, setCompany] = useState<any>(null);
  const [companies, setCompanies] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [indicators, setIndicators] = useState<ESGIndicators>(DEFAULT_INDICATORS);
  const [showForm, setShowForm] = useState(false);

  useEffect(() => {
    const list = loadCompanies();
    setCompanies(list);
    const found = list.find((c: any) => c.entreprise_id === id);
    setCompany(found ?? null);
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
        body: JSON.stringify(indicators),
      });
      const data = await res.json();
      const score = data.score ?? null;

      const entry = {
        date: new Date().toISOString().split('T')[0],
        indicateurs: indicators,
        scores: { E: score, S: score, G: score, global: score },
      };

      const updated = companies.map((c) => (c.entreprise_id === company.entreprise_id ? { ...c, historique: [entry, ...(c.historique || [])] } : c));
      saveCompanies(updated);
      setCompanies(updated);
      setCompany(updated.find((c) => c.entreprise_id === company.entreprise_id));
      setShowForm(false);
      setIndicators(DEFAULT_INDICATORS);
    } catch (err) {
      console.error(err);
      alert('Erreur lors du calcul');
    } finally {
      setIsLoading(false);
    }
  };

  if (!company) return <div className="p-6">Entreprise introuvable.</div>;

  const chartData = (company.historique || []).map((h: any) => ({ date: h.date, score: h.scores?.global ?? null })).reverse();

  return (
    <div className="p-6">
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
      <div className="mb-6 bg-white border border-slate-200 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-lg">Ajouter une nouvelle prédiction</h3>
          {!showForm && (
            <button onClick={() => setShowForm(true)} className="px-4 py-2 bg-emerald-600 text-white rounded-md hover:bg-emerald-700">
              + Nouvelle prédiction
            </button>
          )}
        </div>

        {showForm && (
          <div className="mt-4 p-4 bg-emerald-50 border border-emerald-200 rounded">
            <ESGIndicatorForm
              data={indicators}
              onChange={handleIndicatorChange}
              submitLabel={isLoading ? 'Calcul en cours...' : 'Calculer et enregistrer'}
              onSubmit={addPrediction}
              isLoading={isLoading}
              onCancel={() => {
                setShowForm(false);
                setIndicators(DEFAULT_INDICATORS);
              }}
            />
          </div>
        )}
      </div>

      {/* Historique détaillé */}
      <div className="bg-white border border-slate-200 rounded-lg p-6">
        <h3 className="font-semibold text-lg mb-4">Historique complet</h3>
        <div className="space-y-3">
          {(company.historique || []).length === 0 ? (
            <div className="text-center py-8 text-slate-500">Aucun historique disponible.</div>
          ) : (
            (company.historique || []).map((h: any, idx: number) => (
              <div key={idx} className="p-4 border border-slate-200 rounded flex items-start justify-between hover:bg-slate-50">
                <div>
                  <div className="font-semibold text-slate-900">{h.date}</div>
                  <div className="text-sm text-slate-600 mt-1">Score global: <span className="font-semibold text-emerald-600">{h.scores?.global?.toFixed(1) ?? 'N/A'}</span></div>
                  <div className="text-xs text-slate-500 mt-1">E: {h.scores?.E?.toFixed(1)}, S: {h.scores?.S?.toFixed(1)}, G: {h.scores?.G?.toFixed(1)}</div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
