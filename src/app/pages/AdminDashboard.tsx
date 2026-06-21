import React, { useEffect, useState } from 'react';
import {
  Ban,
  Building2,
  CheckCircle,
  MailCheck,
  Search,
  Settings2,
  ShieldAlert,
  ShieldCheck,
  Trash2,
  Users,
  XCircle,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router';
import { getRoleLabel } from '../utils/roles';
import { Button } from '../components/ui/button';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '../components/ui/alert-dialog';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';

type User = {
  id: number;
  name: string;
  email: string;
  role: string;
  company_id: number | null;
  is_blocked: boolean;
  is_approved: boolean;
  is_verified: boolean;
  created_at: string;
};

type Company = {
  id: number;
  name: string;
};

const ROLE_OPTIONS = [
  { value: 'metier', label: 'Utilisateur métier' },
  { value: 'decideur', label: 'Décideur' },
  { value: 'admin', label: 'Administrateur' },
] as const;

export default function AdminDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [roleDraft, setRoleDraft] = useState('metier');
  const [modalError, setModalError] = useState<string | null>(null);
  const [isSavingRole, setIsSavingRole] = useState(false);
  const [userToDelete, setUserToDelete] = useState<User | null>(null);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [companyDraft, setCompanyDraft] = useState<string>('none');
  const [isSavingCompany, setIsSavingCompany] = useState(false);
  const [approvingUser, setApprovingUser] = useState<User | null>(null);
  const [approveRoleDraft, setApproveRoleDraft] = useState<string>('metier');
  const [isApprovingWithRole, setIsApprovingWithRole] = useState(false);
  const [userToReject, setUserToReject] = useState<User | null>(null);
  const [isRejecting, setIsRejecting] = useState(false);

  useEffect(() => {
    // Redirection si non admin
    if (user && user.role !== 'admin') {
      navigate('/');
      return;
    }

    fetchUsers();
  }, [user, navigate]);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch('/api/admin/users', { credentials: 'include' });
      if (!res.ok) throw new Error('Erreur lors du chargement des utilisateurs');
      const data = await res.json();
      setUsers(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchCompanies = async () => {
    try {
      const res = await fetch('/api/companies', { credentials: 'include' });
      if (!res.ok) return;
      const data = await res.json();
      setCompanies(
        (data as Array<{ id?: number; entreprise_id?: number; name?: string; nom?: string }>).map((c) => ({
          id: c.id ?? c.entreprise_id ?? 0,
          name: c.name ?? c.nom ?? '',
        }))
      );
    } catch {
      // silently ignore — companies list is optional
    }
  };

  const openManageModal = (targetUser: User) => {
    setSelectedUser(targetUser);
    setRoleDraft(targetUser.role);
    setCompanyDraft(targetUser.company_id != null ? String(targetUser.company_id) : 'none');
    setModalError(null);
    fetchCompanies();
  };

  const updateUserInState = (updatedUser: User) => {
    setUsers((currentUsers) => currentUsers.map((entry) => (entry.id === updatedUser.id ? updatedUser : entry)));
    setSelectedUser((currentSelected) => (currentSelected?.id === updatedUser.id ? updatedUser : currentSelected));
  };

  const handleSaveRole = async () => {
    if (!selectedUser || roleDraft === selectedUser.role) return;

    try {
      setIsSavingRole(true);
      setModalError(null);
      const res = await fetch(`/api/admin/users/${selectedUser.id}/role`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ role: roleDraft }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || 'Erreur lors de la modification du rôle');
      }

      const data = await res.json();
      updateUserInState(data.user);
    } catch (err: any) {
      setModalError(err.message);
    } finally {
      setIsSavingRole(false);
    }
  };

  const handleDelete = async (targetUser: User) => {
    try {
      const res = await fetch(`/api/admin/users/${targetUser.id}`, {
        method: 'DELETE',
        credentials: 'include',
      });
      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        throw new Error(data.error || 'Erreur lors de la suppression');
      }

      setUsers((currentUsers) => currentUsers.filter((entry) => entry.id !== targetUser.id));
      setSelectedUser((currentSelected) => (currentSelected?.id === targetUser.id ? null : currentSelected));
      setUserToDelete(null);
    } catch (err: any) {
      setModalError(err.message);
    }
  };

  const handleToggleBlock = async (targetUser: User) => {
    const action = targetUser.is_blocked ? 'débloquer' : 'bloquer';

    try {
      const res = await fetch(`/api/admin/users/${targetUser.id}/block`, {
        method: 'PUT',
        credentials: 'include',
      });
      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || `Erreur lors de l'action de ${action}`);
      }
      const data = await res.json();
      updateUserInState(data.user);
    } catch (err: any) {
      setModalError(err.message);
    }
  };

  const handleAssignCompany = async () => {
    if (!selectedUser) return;
    const newCompanyId = companyDraft === 'none' ? null : parseInt(companyDraft, 10);
    if (newCompanyId === selectedUser.company_id) return;

    try {
      setIsSavingCompany(true);
      setModalError(null);
      const res = await fetch(`/api/admin/users/${selectedUser.id}/company`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ company_id: newCompanyId }),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.error || "Erreur lors de l'assignation de l'entreprise");
      }

      const data = await res.json();
      updateUserInState(data.user);
    } catch (err: any) {
      setModalError(err.message);
    } finally {
      setIsSavingCompany(false);
    }
  };

  const handleApproveWithRole = async () => {
    if (!approvingUser) return;
    setIsApprovingWithRole(true);
    try {
      const res = await fetch(`/api/admin/users/${approvingUser.id}/approve`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ role: approveRoleDraft }),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || 'Erreur lors de la validation');
      updateUserInState(data.user);
      setApprovingUser(null);
    } catch (err: any) {
      setModalError(err.message);
    } finally {
      setIsApprovingWithRole(false);
    }
  };

  const handleRejectUser = async () => {
    if (!userToReject) return;
    setIsRejecting(true);
    try {
      const res = await fetch(`/api/admin/users/${userToReject.id}/reject`, {
        method: 'PUT',
        credentials: 'include',
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || 'Erreur lors du refus');
      setUsers((prev) => prev.filter((u) => u.id !== userToReject.id));
      setUserToReject(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsRejecting(false);
    }
  };

  const filteredUsers = users.filter(u => 
    u.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    u.email.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (loading) {
    return <div className="p-8 flex justify-center text-gray-500">Chargement de l'espace administration...</div>;
  }

  return (
    <div className="min-h-full bg-[radial-gradient(circle_at_top_right,_rgba(16,185,129,0.12),_transparent_28%),radial-gradient(circle_at_0%_0%,_rgba(15,23,42,0.05),_transparent_30%),linear-gradient(to_bottom,_#f8fafc,_#ffffff)] px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl animate-in fade-in slide-in-from-bottom-4 duration-500">
        <div className="mb-8 flex flex-col gap-4 rounded-3xl border border-emerald-100 bg-white/85 p-6 shadow-[0_20px_80px_-30px_rgba(15,23,42,0.2)] backdrop-blur sm:flex-row sm:items-end sm:justify-between">
          <div className="max-w-2xl">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-emerald-700">
              <ShieldAlert className="h-3.5 w-3.5" />
              Administration
            </div>
            <h1 className="flex items-center gap-3 text-3xl font-black tracking-tight text-slate-900 sm:text-4xl">
              Administration Plateforme
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-600 sm:text-base">
              Gérez les accès, rôles et statuts des utilisateurs depuis une interface plus claire,
              avec des actions regroupées dans une modale dédiée.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3 sm:min-w-[280px]">
            <div className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-4 text-center shadow-sm">
              <span className="block text-3xl font-black text-slate-900">{users.length}</span>
              <span className="mt-1 block text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-500">Total</span>
            </div>
            <div className="rounded-2xl border border-emerald-200 bg-emerald-50 px-4 py-4 text-center shadow-sm">
              <span className="block text-3xl font-black text-emerald-700">
                {users.filter((entry) => entry.role === 'admin').length}
              </span>
              <span className="mt-1 block text-[11px] font-semibold uppercase tracking-[0.18em] text-emerald-700/80">Admins</span>
            </div>
          </div>
        </div>

      {error && (
        <div className="mb-6 rounded-2xl border border-red-100 bg-red-50 px-4 py-3 text-red-700 shadow-sm">
          {error}
        </div>
      )}

        <div className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-[0_20px_70px_-35px_rgba(15,23,42,0.25)]">
          <div className="flex flex-col gap-4 border-b border-slate-100 bg-slate-50/80 p-5 sm:flex-row sm:items-center sm:justify-between">
            <h2 className="flex items-center gap-2 text-lg font-bold text-slate-800">
              <Users className="h-5 w-5 text-emerald-600" />
              Liste des utilisateurs
            </h2>
            <div className="relative w-full sm:w-80">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Rechercher par nom ou email..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full rounded-2xl border border-slate-200 bg-white py-2.5 pl-10 pr-4 text-sm outline-none transition focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10"
              />
            </div>
          </div>

          {/* ── Mobile : cards ──────────────────────────────────────────────── */}
          <div className="md:hidden divide-y divide-slate-100">
            {filteredUsers.length === 0 ? (
              <p className="px-5 py-10 text-center text-sm text-slate-500">Aucun utilisateur trouvé.</p>
            ) : (
              filteredUsers.map((entry) => (
                <div key={entry.id} className="p-4 space-y-3">
                  {/* Header : nom + rôle */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="font-semibold text-slate-900 truncate">{entry.name}</p>
                      <p className="text-xs text-slate-500 truncate mt-0.5">{entry.email}</p>
                      <p className="text-xs text-slate-400 mt-0.5">{new Date(entry.created_at).toLocaleDateString('fr-FR')}</p>
                    </div>
                    <span className={`shrink-0 inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ${
                      entry.role === 'admin'
                        ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                        : entry.role === 'non_attribue'
                        ? 'border-amber-200 bg-amber-50 text-amber-700'
                        : 'border-slate-200 bg-slate-100 text-slate-700'
                    }`}>
                      {getRoleLabel(entry.role)}
                    </span>
                  </div>

                  {/* Statut badges */}
                  <div className="flex flex-wrap gap-1.5">
                    {entry.is_blocked ? (
                      <span className="inline-flex items-center gap-1 rounded-full border border-red-200 bg-red-50 px-2.5 py-1 text-xs font-semibold text-red-700">
                        <Ban className="h-3 w-3" /> Bloqué
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">
                        <CheckCircle className="h-3 w-3" /> Actif
                      </span>
                    )}
                    {!entry.is_approved && (
                      <span className="inline-flex items-center gap-1 rounded-full border border-sky-200 bg-sky-50 px-2.5 py-1 text-xs font-semibold text-sky-700">
                        <MailCheck className="h-3 w-3" /> En attente admin
                      </span>
                    )}
                    {entry.is_approved && !entry.is_verified && (
                      <span className="inline-flex rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700">
                        En attente vérification
                      </span>
                    )}
                  </div>

                  {/* Boutons d'action */}
                  <div className="flex flex-wrap gap-2">
                    {!entry.is_approved && (
                      <>
                        <button
                          onClick={() => { setApprovingUser(entry); setApproveRoleDraft('metier'); setModalError(null); }}
                          className="inline-flex h-9 items-center gap-1.5 rounded-xl border border-emerald-200 bg-emerald-50 px-3 text-xs font-medium text-emerald-700 transition-all hover:bg-emerald-100"
                        >
                          <MailCheck className="h-3.5 w-3.5" /> Valider
                        </button>
                        <button
                          onClick={() => setUserToReject(entry)}
                          className="inline-flex h-9 items-center gap-1.5 rounded-xl border border-red-200 bg-red-50 px-3 text-xs font-medium text-red-700 transition-all hover:bg-red-100"
                        >
                          <XCircle className="h-3.5 w-3.5" /> Refuser
                        </button>
                      </>
                    )}
                    <button
                      onClick={() => handleToggleBlock(entry)}
                      disabled={user?.id === entry.id}
                      className={`inline-flex h-9 items-center gap-1.5 rounded-xl border px-3 text-xs font-medium transition-all ${
                        user?.id === entry.id
                          ? 'cursor-not-allowed border-slate-200 bg-slate-50 text-slate-300'
                          : entry.is_blocked
                            ? 'border-emerald-200 bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
                            : 'border-amber-200 bg-amber-50 text-amber-700 hover:bg-amber-100'
                      }`}
                    >
                      <Ban className="h-3.5 w-3.5" />
                      {entry.is_blocked ? 'Débloquer' : 'Bloquer'}
                    </button>
                    <Button
                      type="button"
                      variant="outline"
                      className="h-9 rounded-xl border-slate-200 bg-white px-3 text-xs text-slate-700 hover:bg-slate-50"
                      onClick={() => openManageModal(entry)}
                      disabled={user?.id === entry.id}
                    >
                      <Settings2 className="h-3.5 w-3.5 mr-1.5" /> Gérer
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* ── Desktop : table ──────────────────────────────────────────────── */}
          <div className="hidden md:block overflow-x-auto">
            <table className="w-full text-left">
              <thead className="border-b border-slate-100 bg-white/90">
                <tr>
                  <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">Utilisateur</th>
                  <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">Email</th>
                  <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">Rôle</th>
                  <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">Statut</th>
                  <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">Date d'inscription</th>
                  <th className="px-4 py-4 text-right text-xs font-bold uppercase tracking-wider text-slate-500">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredUsers.map((entry) => (
                  <tr key={entry.id} className="transition-colors hover:bg-slate-50/70">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-semibold text-slate-900">{entry.name}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-600">
                      {entry.email}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex rounded-full border px-3 py-1 text-xs font-semibold ${
                        entry.role === 'admin'
                          ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                          : entry.role === 'non_attribue'
                          ? 'border-amber-200 bg-amber-50 text-amber-700'
                          : 'border-slate-200 bg-slate-100 text-slate-700'
                      }`}>
                        {getRoleLabel(entry.role)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex flex-col gap-1.5">
                        {entry.is_blocked ? (
                          <span className="inline-flex items-center gap-1.5 rounded-full border border-red-200 bg-red-50 px-2.5 py-1 text-xs font-semibold text-red-700">
                            <Ban className="h-3.5 w-3.5" /> Bloqué
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-1 text-xs font-semibold text-emerald-700">
                            <CheckCircle className="h-3.5 w-3.5" /> Actif
                          </span>
                        )}
                        {!entry.is_approved && (
                          <span className="inline-flex items-center gap-1.5 rounded-full border border-sky-200 bg-sky-50 px-2.5 py-1 text-xs font-semibold text-sky-700">
                            <MailCheck className="h-3.5 w-3.5" /> En attente admin
                          </span>
                        )}
                        {entry.is_approved && !entry.is_verified && (
                          <span className="inline-flex rounded-full border border-amber-200 bg-amber-50 px-2.5 py-1 text-xs font-semibold text-amber-700">
                            En attente
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                      {new Date(entry.created_at).toLocaleDateString('fr-FR')}
                    </td>
                    <td className="px-4 py-4 text-right text-sm font-medium">
                      <div className="flex flex-wrap items-center justify-end gap-1.5">
                        {!entry.is_approved && (
                          <>
                            <button
                              onClick={() => { setApprovingUser(entry); setApproveRoleDraft('metier'); setModalError(null); }}
                              className="inline-flex h-8 items-center justify-center rounded-xl border border-emerald-200 bg-emerald-50 px-2.5 text-xs font-medium text-emerald-700 transition-all hover:bg-emerald-100"
                              title="Valider et attribuer un rôle"
                            >
                              <MailCheck className="mr-1 h-3.5 w-3.5" />
                              Valider
                            </button>
                            <button
                              onClick={() => setUserToReject(entry)}
                              className="inline-flex h-8 items-center justify-center rounded-xl border border-red-200 bg-red-50 px-2.5 text-xs font-medium text-red-700 transition-all hover:bg-red-100"
                              title="Refuser la demande d'accès"
                            >
                              <XCircle className="mr-1 h-3.5 w-3.5" />
                              Refuser
                            </button>
                          </>
                        )}

                        <button
                          onClick={() => handleToggleBlock(entry)}
                          disabled={user?.id === entry.id}
                          className={`inline-flex h-8 items-center justify-center rounded-xl border px-2.5 text-xs font-medium transition-all ${
                            user?.id === entry.id
                              ? 'cursor-not-allowed border-slate-200 bg-slate-50 text-slate-300'
                              : entry.is_blocked
                                ? 'border-emerald-200 bg-emerald-50 text-emerald-700 hover:bg-emerald-100'
                                : 'border-amber-200 bg-amber-50 text-amber-700 hover:bg-amber-100'
                          }`}
                          title={entry.is_blocked ? 'Débloquer le compte' : 'Bloquer le compte'}
                        >
                          <Ban className="mr-1 h-3.5 w-3.5" />
                          {entry.is_blocked ? 'Débloquer' : 'Bloquer'}
                        </button>

                        <Button
                          type="button"
                          variant="outline"
                          className="h-8 rounded-xl border-slate-200 bg-white px-2.5 text-xs text-slate-700 hover:bg-slate-50"
                          onClick={() => openManageModal(entry)}
                          disabled={user?.id === entry.id}
                        >
                          <Settings2 className="h-3.5 w-3.5" />
                          Gérer
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}

                {filteredUsers.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-6 py-10 text-center text-slate-500">
                      Aucun utilisateur trouvé.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <Dialog open={Boolean(selectedUser)} onOpenChange={(open) => {
        if (!open) {
          setSelectedUser(null);
          setModalError(null);
        }
      }}>
        <DialogContent className="max-w-sm rounded-2xl border-slate-200 bg-white p-5 shadow-xl">
          {selectedUser && (
            <>
              <DialogHeader className="text-left mb-1">
                <DialogTitle className="text-base font-bold text-slate-900 leading-tight">
                  {selectedUser.name}
                </DialogTitle>
                <DialogDescription className="text-xs text-slate-400 truncate">
                  {selectedUser.email}
                </DialogDescription>
              </DialogHeader>

              {modalError && (
                <div className="rounded-xl border border-red-100 bg-red-50 px-3 py-2 text-xs text-red-700">
                  {modalError}
                </div>
              )}

              <div className="space-y-3 mt-1">
                {/* Rôle */}
                <div className="flex items-center gap-2">
                  <span className="w-20 shrink-0 text-xs font-medium text-slate-500">Rôle</span>
                  <Select value={roleDraft} onValueChange={setRoleDraft}>
                    <SelectTrigger className="h-8 flex-1 rounded-lg border-slate-200 bg-slate-50 text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {ROLE_OPTIONS.map((option) => (
                        <SelectItem key={option.value} value={option.value} className="text-xs">
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button
                    type="button"
                    size="sm"
                    onClick={handleSaveRole}
                    disabled={isSavingRole || roleDraft === selectedUser.role}
                    className="h-8 rounded-lg bg-emerald-600 px-3 text-xs text-white hover:bg-emerald-700 shrink-0"
                  >
                    <ShieldCheck className="h-3.5 w-3.5" />
                  </Button>
                </div>

                {/* Entreprise */}
                <div className="flex items-center gap-2">
                  <span className="w-20 shrink-0 text-xs font-medium text-slate-500">Entreprise</span>
                  <Select value={companyDraft} onValueChange={setCompanyDraft}>
                    <SelectTrigger className="h-8 flex-1 rounded-lg border-slate-200 bg-slate-50 text-xs">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="none" className="text-xs">— Aucune —</SelectItem>
                      {companies.map((c) => (
                        <SelectItem key={c.id} value={String(c.id)} className="text-xs">
                          {c.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <Button
                    type="button"
                    size="sm"
                    onClick={handleAssignCompany}
                    disabled={
                      isSavingCompany ||
                      companyDraft === (selectedUser.company_id != null ? String(selectedUser.company_id) : 'none')
                    }
                    className="h-8 rounded-lg bg-slate-700 px-3 text-xs text-white hover:bg-slate-800 shrink-0"
                  >
                    <Building2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>

              {/* Actions destructives */}
              <div className="mt-4 flex gap-2 border-t border-slate-100 pt-4">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => handleToggleBlock(selectedUser)}
                  disabled={selectedUser.id === user?.id}
                  className="flex-1 h-8 rounded-lg border-slate-200 text-xs text-slate-700 hover:bg-slate-50"
                >
                  <Ban className="h-3.5 w-3.5 mr-1" />
                  {selectedUser.is_blocked ? 'Débloquer' : 'Bloquer'}
                </Button>
                <Button
                  type="button"
                  variant="destructive"
                  size="sm"
                  onClick={() => setUserToDelete(selectedUser)}
                  disabled={selectedUser.id === user?.id}
                  className="flex-1 h-8 rounded-lg text-xs"
                >
                  <Trash2 className="h-3.5 w-3.5 mr-1" />
                  Supprimer
                </Button>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* ── Dialog : Valider avec rôle ─────────────────────────────────────── */}
      <AlertDialog open={Boolean(approvingUser)} onOpenChange={(open) => { if (!open) setApprovingUser(null); }}>
        <AlertDialogContent className="rounded-3xl border-slate-200">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-left text-xl font-black text-slate-900">
              Valider le compte de {approvingUser?.name}
            </AlertDialogTitle>
            <AlertDialogDescription className="text-left text-sm text-slate-600">
              Attribuez un rôle avant de valider. L'utilisateur recevra un e-mail d'activation.
            </AlertDialogDescription>
          </AlertDialogHeader>

          {modalError && (
            <div className="rounded-xl border border-red-100 bg-red-50 px-4 py-2 text-sm text-red-700">
              {modalError}
            </div>
          )}

          <div className="mt-2">
            <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-slate-500">Rôle à attribuer</p>
            <Select value={approveRoleDraft} onValueChange={setApproveRoleDraft}>
              <SelectTrigger className="h-11 rounded-xl border-slate-200 bg-white">
                <SelectValue placeholder="Sélectionner un rôle" />
              </SelectTrigger>
              <SelectContent>
                {ROLE_OPTIONS.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <AlertDialogFooter className="mt-2">
            <AlertDialogCancel className="rounded-xl" onClick={() => setApprovingUser(null)}>
              Annuler
            </AlertDialogCancel>
            <AlertDialogAction
              className="rounded-xl bg-emerald-600 text-white hover:bg-emerald-700"
              onClick={(e) => { e.preventDefault(); void handleApproveWithRole(); }}
              disabled={isApprovingWithRole}
            >
              <MailCheck className="mr-2 h-4 w-4" />
              {isApprovingWithRole ? 'Validation...' : 'Valider le compte'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* ── Dialog : Refuser ──────────────────────────────────────────────── */}
      <AlertDialog open={Boolean(userToReject)} onOpenChange={(open) => { if (!open) setUserToReject(null); }}>
        <AlertDialogContent className="rounded-3xl border-slate-200">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-left text-xl font-black text-slate-900">
              Refuser la demande d'accès ?
            </AlertDialogTitle>
            <AlertDialogDescription className="text-left text-sm leading-6 text-slate-600">
              {userToReject
                ? `La demande de ${userToReject.name} (${userToReject.email}) sera rejetée et le compte supprimé définitivement.`
                : ''}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="rounded-xl">Annuler</AlertDialogCancel>
            <AlertDialogAction
              className="rounded-xl bg-red-600 text-white hover:bg-red-700"
              onClick={(e) => { e.preventDefault(); void handleRejectUser(); }}
              disabled={isRejecting}
            >
              <XCircle className="mr-2 h-4 w-4" />
              {isRejecting ? 'Refus en cours...' : 'Refuser définitivement'}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={Boolean(userToDelete)} onOpenChange={(open) => {
        if (!open) {
          setUserToDelete(null);
        }
      }}>
        <AlertDialogContent className="rounded-3xl border-slate-200">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-left text-2xl font-black text-slate-900">
              Supprimer ce compte ?
            </AlertDialogTitle>
            <AlertDialogDescription className="text-left text-sm leading-6 text-slate-600">
              {userToDelete
                ? `${userToDelete.name} (${userToDelete.email}) sera supprimé définitivement. Les historiques liés seront détachés avant la suppression pour éviter une erreur serveur.`
                : 'Cette action est irréversible.'}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel className="rounded-xl">Annuler</AlertDialogCancel>
            <AlertDialogAction
              className="rounded-xl bg-red-600 text-white hover:bg-red-700"
              onClick={(event) => {
                event.preventDefault();
                if (userToDelete) {
                  void handleDelete(userToDelete);
                }
              }}
            >
              Supprimer définitivement
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
