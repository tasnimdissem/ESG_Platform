import { useEffect, useMemo, useState } from 'react';
import { Camera, Lock, Mail, Save, User as UserIcon } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { Avatar, AvatarFallback, AvatarImage } from '../components/ui/avatar';

export default function Profile() {
  const { user, updateUser } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!user) return;
    setName(user.name);
    setEmail(user.email);
    setAvatarPreview(user.avatar_url ?? null);
  }, [user]);

  useEffect(() => {
    if (!avatarFile) return;

    const previewUrl = URL.createObjectURL(avatarFile);
    setAvatarPreview(previewUrl);

    return () => URL.revokeObjectURL(previewUrl);
  }, [avatarFile]);

  const initials = useMemo(() => {
    const baseName = (name || user?.name || 'U').trim();
    return baseName
      .split(/\s+/)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase() ?? '')
      .join('') || 'U';
  }, [name, user?.name]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSaving(true);
    setErrorMessage(null);
    setMessage(null);

    if (newPassword || confirmPassword || currentPassword) {
      if (!currentPassword || !newPassword || !confirmPassword) {
        setErrorMessage('Veuillez renseigner le mot de passe actuel, le nouveau mot de passe et sa confirmation.');
        setIsSaving(false);
        return;
      }

      if (newPassword !== confirmPassword) {
        setErrorMessage('Les deux mots de passe ne correspondent pas.');
        setIsSaving(false);
        return;
      }
    }

    try {
      const formData = new FormData();
      formData.append('name', name);
      formData.append('email', email);

      if (currentPassword) formData.append('current_password', currentPassword);
      if (newPassword) formData.append('new_password', newPassword);
      if (avatarFile) formData.append('avatar', avatarFile);

      const response = await fetch('/api/auth/me', {
        method: 'PUT',
        credentials: 'include',
        body: formData,
      });

      const data = (await response.json()) as { message?: string; error?: string; user?: typeof user };
      if (!response.ok) {
        throw new Error(data.error ?? 'Impossible de mettre à jour le profil');
      }

      if (data.user) {
        updateUser(data.user);
      }

      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setAvatarFile(null);
      setMessage(data.message ?? 'Profil mis à jour avec succès');
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Impossible de mettre à jour le profil.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="p-8 bg-gray-50 min-h-screen">
      <div className="max-w-5xl mx-auto space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Mon profil</h1>
          <p className="text-gray-600">Modifiez vos informations personnelles et votre mot de passe.</p>
        </div>

        {message && <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">{message}</div>}
        {errorMessage && <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{errorMessage}</div>}

        <form onSubmit={handleSubmit} className="grid gap-6 lg:grid-cols-[320px_1fr]">
          <div className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
            <div className="flex flex-col items-center text-center gap-4">
              <Avatar className="h-28 w-28 border border-gray-200">
                <AvatarImage src={avatarPreview ?? undefined} alt={user?.name ?? 'Photo de profil'} />
                <AvatarFallback className="bg-gradient-to-br from-emerald-500 to-teal-700 text-white text-2xl font-semibold">
                  {initials}
                </AvatarFallback>
              </Avatar>

              <div>
                <h2 className="text-xl font-semibold text-gray-900">Photo de profil</h2>
                <p className="text-sm text-gray-500">PNG, JPG ou WEBP jusqu’à 5 Mo.</p>
              </div>

              <label className="inline-flex cursor-pointer items-center gap-2 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm font-medium text-emerald-700 hover:bg-emerald-100">
                <Camera className="h-4 w-4" />
                Choisir une image
                <input
                  type="file"
                  accept="image/png,image/jpeg,image/webp"
                  className="hidden"
                  onChange={(event) => setAvatarFile(event.target.files?.[0] ?? null)}
                />
              </label>

              <div className="w-full space-y-3 rounded-xl bg-gray-50 p-4 text-left text-sm text-gray-600">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-gray-500">Rôle</span>
                  <span>{user?.role ?? 'user'}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="font-medium text-gray-500">Compte</span>
                  <span>{user?.id ? `#${user.id}` : '—'}</span>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-6 rounded-2xl border border-gray-200 bg-white p-6 shadow-sm">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">Informations du compte</h2>
              <p className="text-sm text-gray-500">Nom d’utilisateur et adresse e-mail.</p>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label className="mb-2 block text-sm font-medium text-gray-700">Nom</label>
                <div className="relative">
                  <UserIcon className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
                  <input
                    value={name}
                    onChange={(event) => setName(event.target.value)}
                    className="w-full rounded-xl border border-gray-300 px-10 py-3 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    placeholder="Votre nom"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="mb-2 block text-sm font-medium text-gray-700">Email</label>
                <div className="relative">
                  <Mail className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
                  <input
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    className="w-full rounded-xl border border-gray-300 px-10 py-3 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    placeholder="votre@email.com"
                    required
                  />
                </div>
              </div>
            </div>

            <div className="rounded-2xl border border-gray-200 bg-gray-50 p-5">
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Sécurité</h3>
                <p className="text-sm text-gray-500">Changez votre mot de passe sans passer par le formulaire de réinitialisation.</p>
              </div>

              <div className="grid gap-4 md:grid-cols-3">
                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">Mot de passe actuel</label>
                  <div className="relative">
                    <Lock className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
                    <input
                      type="password"
                      value={currentPassword}
                      onChange={(event) => setCurrentPassword(event.target.value)}
                      className="w-full rounded-xl border border-gray-300 px-10 py-3 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                      placeholder="Mot de passe actuel"
                    />
                  </div>
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">Nouveau mot de passe</label>
                  <div className="relative">
                    <Lock className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
                    <input
                      type="password"
                      value={newPassword}
                      onChange={(event) => setNewPassword(event.target.value)}
                      className="w-full rounded-xl border border-gray-300 px-10 py-3 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                      placeholder="Nouveau mot de passe"
                    />
                  </div>
                </div>

                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">Confirmation</label>
                  <div className="relative">
                    <Lock className="pointer-events-none absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-400" />
                    <input
                      type="password"
                      value={confirmPassword}
                      onChange={(event) => setConfirmPassword(event.target.value)}
                      className="w-full rounded-xl border border-gray-300 px-10 py-3 focus:outline-none focus:ring-2 focus:ring-emerald-500"
                      placeholder="Confirmez le mot de passe"
                    />
                  </div>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3">
              <button
                type="submit"
                disabled={isSaving}
                className="inline-flex items-center gap-2 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-700 px-5 py-3 font-semibold text-white transition hover:from-emerald-700 hover:to-emerald-800 disabled:cursor-not-allowed disabled:opacity-60"
              >
                <Save className="h-5 w-5" />
                {isSaving ? 'Enregistrement...' : 'Enregistrer les modifications'}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}