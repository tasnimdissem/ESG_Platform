import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router';
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

export default function Companies() {
  const [companies, setCompanies] = useState<any[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState('');
  const [indicators, setIndicators] = useState<ESGIndicators>(DEFAULT_INDICATORS);
  const [isSaving, setIsSaving] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    setCompanies(loadCompanies());
  }, []);

  const handleIndicatorChange = (field: keyof ESGIndicators, value: string | number) => {
    setIndicators((prev) => ({
      ...prev,
      [field]: typeof DEFAULT_INDICATORS[field] === 'number' ? (typeof value === 'string' ? parseFloat(value) || 0 : value) : value,
    }));
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      alert('Veuillez entrer un nom d\'entreprise');
      return;
    }
    setIsSaving(true);

    try {
      const res = await fetch('/api/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(indicators),
      });

      const data = await res.json();
      const score = data.score ?? null;

      const id = (crypto && (crypto as any).randomUUID ? (crypto as any).randomUUID() : `id-${Date.now()}`);
      const newCompany = {
        entreprise_id: id,
        nom: name,
        historique: [
          {
            date: new Date().toISOString().split('T')[0],
            indicateurs: indicators,
            scores: { E: score, S: score, G: score, global: score },
          },
        ],
      };

      const updated = [newCompany, ...companies];
      setCompanies(updated);
      saveCompanies(updated);
      setShowForm(false);
      setName('');
      setIndicators(DEFAULT_INDICATORS);
      navigate(`/companies/${id}`);
    } catch (err) {
      console.error('Erreur ajout entreprise', err);
      alert('Erreur lors du calcul du score');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Mes entreprises</h2>
        <button
          onClick={() => setShowForm(true)}
          className="bg-emerald-600 text-white px-4 py-2 rounded-md hover:bg-emerald-700"
        >
          + Ajouter une entreprise
        </button>
      </div>

      {showForm && (
        <div className="mb-6 p-4 border border-slate-300 rounded-md bg-white">
          <h3 className="text-lg font-semibold mb-4">Nouvelle entreprise</h3>
          <div className="mb-4">
            <label className="block text-sm font-medium text-slate-700 mb-1">Nom de l'entreprise *</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Ex: TechCorp SA"
              className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
            />
          </div>

          <h4 className="font-semibold text-slate-700 mb-3">Indicateurs ESG</h4>
          <ESGIndicatorForm
            data={indicators}
            onChange={handleIndicatorChange}
            submitLabel={isSaving ? 'Calcul en cours...' : 'Calculer et ajouter'}
            onSubmit={handleAdd}
            isLoading={isSaving}
            onCancel={() => {
              setShowForm(false);
              setName('');
              setIndicators(DEFAULT_INDICATORS);
            }}
          />
        </div>
      )}

      <div className="grid grid-cols-1 gap-3">
        {companies.length === 0 && (
          <div className="p-4 border border-dashed border-slate-300 rounded text-slate-500">
            Aucune entreprise enregistrée. Cliquez sur "+ Ajouter une entreprise" pour commencer.
          </div>
        )}
        {companies.map((c) => (
          <div key={c.entreprise_id} className="p-4 border border-slate-200 rounded-md flex items-center justify-between hover:bg-slate-50">
            <div>
              <div className="font-semibold text-slate-900">{c.nom}</div>
              <div className="text-sm text-slate-500">Dernière mise à jour: {c.historique?.[0]?.date}</div>
              <div className="text-xs text-emerald-600">Score: {c.historique?.[0]?.scores?.global?.toFixed(1) ?? 'N/A'}</div>
            </div>
            <Link to={`/companies/${c.entreprise_id}`} className="px-4 py-2 bg-emerald-500 text-white rounded hover:bg-emerald-600">
              Voir détails
            </Link>
          </div>
        ))}
      </div>
    </div>
  );
}
