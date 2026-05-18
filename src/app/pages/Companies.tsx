import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router';
import { ESGIndicatorForm } from '../components/ESGIndicatorForm';
import { createCompany, deleteCompany, fetchCompanies, updateCompany, type CompanyRecord } from '../services/api';
import { DEFAULT_INDICATORS, ESGIndicators } from '../utils/esgIndicators';

export default function Companies() {
  const [companies, setCompanies] = useState<CompanyRecord[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState('');
  const [indicators, setIndicators] = useState<ESGIndicators>(DEFAULT_INDICATORS);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [editingCompany, setEditingCompany] = useState<CompanyRecord | null>(null);
  const [editName, setEditName] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [isDeletingId, setIsDeletingId] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const load = async () => {
      setIsLoading(true);
      setLoadError(null);
      try {
        const data = await fetchCompanies();
        setCompanies(data);
      } catch (err) {
        console.error('Erreur chargement entreprises', err);
        setLoadError('Impossible de charger les entreprises.');
      } finally {
        setIsLoading(false);
      }
    };

    void load();
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
        credentials: 'include',
        body: JSON.stringify(indicators),
      });

      const data = await res.json();
      const score = data.score ?? null;

      if (score === null) {
        throw new Error('Score invalide');
      }

      const newCompany = await createCompany({
        name,
        indicators,
        score,
      });

      setCompanies((prev) => [newCompany, ...prev.filter((company) => company.entreprise_id !== newCompany.entreprise_id)]);
      setShowForm(false);
      setName('');
      setIndicators(DEFAULT_INDICATORS);
      navigate(`/companies/${newCompany.entreprise_id}`);
    } catch (err) {
      console.error('Erreur ajout entreprise', err);
      alert('Erreur lors du calcul du score');
    } finally {
      setIsSaving(false);
    }
  };

  const openEditDialog = (company: CompanyRecord) => {
    setEditingCompany(company);
    setEditName(company.nom);
  };

  const closeEditDialog = () => {
    setEditingCompany(null);
    setEditName('');
    setIsEditing(false);
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingCompany) return;
    const nextName = editName.trim();
    if (!nextName) {
      alert("Veuillez entrer un nom d'entreprise valide");
      return;
    }

    setIsEditing(true);
    try {
      const updated = await updateCompany(editingCompany.entreprise_id, { name: nextName });
      setCompanies((prev) => prev.map((company) => (company.entreprise_id === updated.entreprise_id ? updated : company)));
      closeEditDialog();
    } catch (err) {
      console.error('Erreur modification entreprise', err);
      alert("Erreur lors de la modification de l'entreprise");
    } finally {
      setIsEditing(false);
    }
  };

  const handleDelete = async (company: CompanyRecord) => {
    const confirmed = window.confirm(`Supprimer l'entreprise "${company.nom}" ? Cette action est irréversible.`);
    if (!confirmed) return;

    setIsDeletingId(company.entreprise_id);
    try {
      await deleteCompany(company.entreprise_id);
      setCompanies((prev) => prev.filter((item) => item.entreprise_id !== company.entreprise_id));
    } catch (err) {
      console.error('Erreur suppression entreprise', err);
      alert("Erreur lors de la suppression de l'entreprise");
    } finally {
      setIsDeletingId(null);
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
        {isLoading && (
          <div className="p-4 border border-slate-200 rounded text-slate-500">Chargement des entreprises...</div>
        )}
        {loadError && (
          <div className="p-4 border border-amber-200 rounded text-amber-700 bg-amber-50">{loadError}</div>
        )}
        {!isLoading && companies.length === 0 && !loadError && (
          <div className="p-4 border border-dashed border-slate-300 rounded text-slate-500">
            Aucune entreprise enregistrée. Cliquez sur "+ Ajouter une entreprise" pour commencer.
          </div>
        )}
        {companies.map((c) => (
          <div key={c.entreprise_id} className="p-4 border border-slate-200 rounded-md flex items-center justify-between gap-4 hover:bg-slate-50">
            <div>
              <div className="font-semibold text-slate-900">{c.nom}</div>
              <div className="text-sm text-slate-500">Dernière mise à jour: {c.historique?.[0]?.date}</div>
              <div className="text-xs text-emerald-600">Score: {typeof c.historique?.[0]?.scores?.global === 'number' ? c.historique[0].scores.global.toFixed(1) : 'N/A'}</div>
            </div>
            <div className="flex items-center gap-2 flex-wrap justify-end">
              <button
                type="button"
                onClick={() => openEditDialog(c)}
                className="px-3 py-2 border border-slate-300 rounded text-slate-700 hover:bg-slate-100"
              >
                Modifier
              </button>
              <button
                type="button"
                onClick={() => handleDelete(c)}
                disabled={isDeletingId === c.entreprise_id}
                className="px-3 py-2 border border-red-300 rounded text-red-700 hover:bg-red-50 disabled:opacity-60"
              >
                {isDeletingId === c.entreprise_id ? 'Suppression...' : 'Supprimer'}
              </button>
              <Link to={`/companies/${c.entreprise_id}`} className="px-4 py-2 bg-emerald-500 text-white rounded hover:bg-emerald-600">
                Voir détails
              </Link>
            </div>
          </div>
        ))}
      </div>

      {editingCompany && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
          <div className="w-full max-w-lg rounded-lg bg-white p-6 shadow-xl">
            <h3 className="text-xl font-semibold text-slate-900">Modifier l'entreprise</h3>
            <p className="mt-1 text-sm text-slate-500">Renomme le dossier sans perdre l'historique.</p>

            <form onSubmit={handleEditSubmit} className="mt-4 space-y-4">
              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Nom de l'entreprise</label>
                <input
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  className="w-full rounded-md border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              <div className="flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={closeEditDialog}
                  className="rounded-md border border-slate-300 px-4 py-2 text-slate-700 hover:bg-slate-100"
                >
                  Annuler
                </button>
                <button
                  type="submit"
                  disabled={isEditing}
                  className="rounded-md bg-emerald-600 px-4 py-2 text-white hover:bg-emerald-700 disabled:opacity-60"
                >
                  {isEditing ? 'Enregistrement...' : 'Enregistrer'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
