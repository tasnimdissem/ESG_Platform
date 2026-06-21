import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router';
import { createCompany, deleteCompany, fetchCompanies, updateCompany, type CompanyRecord } from '../services/api';
import { Calculator, AlertCircle, CheckCircle, Trash2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export default function Companies() {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';
  const [companies, setCompanies] = useState<CompanyRecord[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState('');
  const [sector, setSector] = useState('');
  const [country, setCountry] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [editingCompany, setEditingCompany] = useState<CompanyRecord | null>(null);
  const [editName, setEditName] = useState('');
  const [editSector, setEditSector] = useState('');
  const [editCountry, setEditCountry] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [isDeletingId, setIsDeletingId] = useState<string | null>(null);
  const [deleteConfirm, setDeleteConfirm] = useState<CompanyRecord | null>(null);
  const [toast, setToast] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
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
        setLoadError(err instanceof Error ? err.message : 'Impossible de charger les entreprises.');
      } finally {
        setIsLoading(false);
      }
    };

    void load();
  }, []);

  const showToast = (type: 'success' | 'error', message: string) => {
    setToast({ type, message });
    setTimeout(() => setToast(null), 3000);
  };

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      showToast('error', 'Veuillez entrer un nom d\'entreprise');
      return;
    }
    setIsSaving(true);

    try {
      const newCompany = await createCompany({
        name: name.trim(),
        sector: sector.trim() || null,
        country: country.trim() || null,
      });

      setCompanies((prev) => [newCompany, ...prev.filter((company) => company.entreprise_id !== newCompany.entreprise_id)]);
      setShowForm(false);
      setName('');
      setSector('');
      setCountry('');
      showToast('success', `L'entreprise "${newCompany.nom}" a été créée avec succès.`);
    } catch (err) {
      console.error('Erreur ajout entreprise', err);
      showToast('error', 'Erreur lors de la création de l\'entreprise');
    } finally {
      setIsSaving(false);
    }
  };

  const handleCalculateScore = (companyId: string, companyName: string) => {
    navigate(`/prediction?company=${encodeURIComponent(companyName)}&companyId=${encodeURIComponent(companyId)}`);
  };

  const openEditDialog = (company: CompanyRecord) => {
    setEditingCompany(company);
    setEditName(company.nom);
    setEditSector(company.sector ?? '');
    setEditCountry(company.country ?? '');
  };

  const closeEditDialog = () => {
    setEditingCompany(null);
    setEditName('');
    setEditSector('');
    setEditCountry('');
    setIsEditing(false);
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingCompany) return;
    const nextName = editName.trim();
    if (!nextName) {
      showToast('error', 'Veuillez entrer un nom d\'entreprise valide');
      return;
    }

    setIsEditing(true);
    try {
      const updated = await updateCompany(editingCompany.entreprise_id, {
        name: nextName,
        sector: editSector.trim() || null,
        country: editCountry.trim() || null,
      });
      setCompanies((prev) => prev.map((company) => (company.entreprise_id === updated.entreprise_id ? updated : company)));
      closeEditDialog();
      showToast('success', `L'entreprise "${updated.nom}" a été mise à jour avec succès.`);
    } catch (err) {
      console.error('Erreur modification entreprise', err);
      showToast('error', 'Erreur lors de la modification de l\'entreprise');
    } finally {
      setIsEditing(false);
    }
  };

  const handleDelete = async (company: CompanyRecord) => {
    setDeleteConfirm(company);
  };

  const confirmDelete = async () => {
    if (!deleteConfirm) return;
    
    setIsDeletingId(deleteConfirm.entreprise_id);
    try {
      await deleteCompany(deleteConfirm.entreprise_id);
      setCompanies((prev) => prev.filter((item) => item.entreprise_id !== deleteConfirm.entreprise_id));
      showToast('success', `L'entreprise "${deleteConfirm.nom}" a été supprimée avec succès.`);
      setDeleteConfirm(null);
    } catch (err) {
      console.error('Erreur suppression entreprise', err);
      showToast('error', "Erreur lors de la suppression de l'entreprise");
    } finally {
      setIsDeletingId(null);
    }
  };

  const cancelDelete = () => {
    setDeleteConfirm(null);
  };

  return (
    <div className="p-4 md:p-6">
      <div className="flex flex-wrap items-center justify-between mb-6 gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <h2 className="text-2xl font-bold">Mes entreprises</h2>
          <div className="relative">
            <input
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Rechercher une entreprise..."
              className="pl-3 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 text-sm w-full sm:w-auto"
            />
          </div>
        </div>
        {isAdmin && (
          <button
            onClick={() => setShowForm(true)}
            className="bg-emerald-600 text-white px-4 py-2 rounded-md hover:bg-emerald-700"
          >
            + Ajouter une entreprise
          </button>
        )}
      </div>

      {showForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-md max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-slate-200 p-6 flex items-center justify-between">
              <h2 className="text-xl font-semibold text-slate-900">Nouvelle entreprise</h2>
              <button
                type="button"
                onClick={() => {
                  setShowForm(false);
                  setName('');
                  setSector('');
                  setCountry('');
                }}
                className="text-slate-500 hover:text-slate-700 text-2xl leading-none"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAdd} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Nom de l'entreprise *</label>
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Ex: TechCorp SA"
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  required
                  autoFocus
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Secteur (optionnel)</label>
                <input
                  value={sector}
                  onChange={(e) => setSector(e.target.value)}
                  placeholder="Ex: Industrie, Finance, Energie"
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Pays (optionnel)</label>
                <input
                  value={country}
                  onChange={(e) => setCountry(e.target.value)}
                  placeholder="Ex: Maroc, France"
                  className="w-full px-3 py-2 border border-slate-300 rounded-md focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>


              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  disabled={isSaving}
                  className="flex-1 bg-emerald-600 text-white px-4 py-2 rounded-md hover:bg-emerald-700 disabled:opacity-50 font-medium"
                >
                  {isSaving ? 'Création...' : 'Créer'}
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setShowForm(false);
                    setName('');
                    setSector('');
                    setCountry('');
                  }}
                  className="flex-1 border border-slate-300 text-slate-700 px-4 py-2 rounded-md hover:bg-slate-50"
                >
                  Annuler
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-3">
        {isLoading && (
          <div className="p-4 border border-slate-200 rounded text-slate-500">Chargement des entreprises...</div>
        )}
        {loadError && (
          <div className="p-4 border border-amber-200 rounded text-amber-700 bg-amber-50 flex items-start gap-2">
            <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
            <span>{loadError}</span>
          </div>
        )}
        {!isLoading && companies.length === 0 && !loadError && (
          <div className="p-4 border border-dashed border-slate-300 rounded text-slate-500">
            {isAdmin
              ? 'Aucune entreprise enregistrée. Cliquez sur "+ Ajouter une entreprise" pour commencer.'
              : 'Aucune entreprise disponible pour votre compte.'}
          </div>
        )}
        {companies
          .filter((c) => {
            const term = searchTerm.trim().toLowerCase();
            if (!term) return true;
            const nameMatch = c.nom.toLowerCase().includes(term);
            const score = c.historique?.[0]?.scores?.global;
            const scoreMatch = score != null && String(score).toLowerCase().includes(term);
            return nameMatch || scoreMatch;
          })
          .map((c) => (
          <div key={c.entreprise_id} className="p-4 border border-slate-200 rounded-md flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-slate-50">
            <div>
              <div className="font-semibold text-slate-900">{c.nom}</div>
              <div className="text-xs text-slate-500">
                {c.sector?.trim() ? c.sector : 'Secteur non défini'} · {c.country?.trim() ? c.country : 'Pays non défini'}
              </div>
              <div className="text-sm text-slate-500">Dernière mise à jour: {c.historique?.[0]?.date}</div>
              <div className="text-xs text-emerald-600">Score: {typeof c.historique?.[0]?.scores?.global === 'number' ? c.historique[0].scores.global.toFixed(1) : 'N/A'}</div>
            </div>
            <div className="flex items-center gap-2 flex-wrap justify-end">
              <button
                type="button"
                onClick={() => handleCalculateScore(c.entreprise_id, c.nom)}
                className="px-3 py-2 border border-blue-300 rounded text-blue-700 hover:bg-blue-50 flex items-center gap-2"
              >
                <Calculator className="w-4 h-4" />
                Calculer score
              </button>
              {isAdmin && (
                <>
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
                </>
              )}
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

              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Secteur</label>
                <input
                  value={editSector}
                  onChange={(e) => setEditSector(e.target.value)}
                  placeholder="Ex: Industrie, Finance, Energie"
                  className="w-full rounded-md border border-slate-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                />
              </div>

              <div>
                <label className="mb-1 block text-sm font-medium text-slate-700">Pays</label>
                <input
                  value={editCountry}
                  onChange={(e) => setEditCountry(e.target.value)}
                  placeholder="Ex: Maroc, France"
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

      {deleteConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-sm">
            <div className="bg-red-50 border-b border-red-200 p-6 flex items-center gap-3">
              <AlertCircle className="w-6 h-6 text-red-600" />
              <h2 className="text-lg font-semibold text-red-900">Confirmer la suppression</h2>
            </div>

            <div className="p-6 space-y-4">
              <p className="text-slate-700">
                Êtes-vous sûr de vouloir supprimer l'entreprise <span className="font-semibold">"{deleteConfirm.nom}"</span> ?
              </p>
              <p className="text-sm text-slate-500">
                ⚠️ Cette action est irréversible et supprimera tous les historiques associés.
              </p>
            </div>

            <div className="bg-slate-50 border-t border-slate-200 p-6 flex gap-3">
              <button
                type="button"
                onClick={cancelDelete}
                className="flex-1 px-4 py-2 border border-slate-300 rounded-md text-slate-700 hover:bg-slate-100 font-medium"
              >
                Annuler
              </button>
              <button
                type="button"
                onClick={confirmDelete}
                disabled={isDeletingId === deleteConfirm.entreprise_id}
                className="flex-1 px-4 py-2 bg-red-600 rounded-md text-white hover:bg-red-700 disabled:opacity-60 font-medium flex items-center justify-center gap-2"
              >
                {isDeletingId === deleteConfirm.entreprise_id ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    Suppression...
                  </>
                ) : (
                  <>
                    <Trash2 className="w-4 h-4" />
                    Supprimer
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {toast && (
        <div className="fixed bottom-6 right-6 z-40 animate-in fade-in slide-in-from-bottom-4 duration-300">
          <div className={`rounded-lg shadow-lg px-6 py-4 flex items-center gap-3 ${
            toast.type === 'success' 
              ? 'bg-emerald-50 border border-emerald-200' 
              : 'bg-red-50 border border-red-200'
          }`}>
            {toast.type === 'success' ? (
              <CheckCircle className="w-5 h-5 text-emerald-600 flex-shrink-0" />
            ) : (
              <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
            )}
            <p className={`${
              toast.type === 'success' 
                ? 'text-emerald-900' 
                : 'text-red-900'
            } font-medium`}>
              {toast.message}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
