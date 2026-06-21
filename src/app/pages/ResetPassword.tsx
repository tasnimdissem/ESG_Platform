import { useEffect, useRef, useState } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router';
import { Lock, ArrowRight } from 'lucide-react';

const RESET_TOKEN_STORAGE_KEY = 'reset-password-token';

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [token, setToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const tokenCapturedRef = useRef(false);

  useEffect(() => {
    const tokenFromUrl = searchParams.get('token') ?? '';
    if (tokenFromUrl) {
      tokenCapturedRef.current = true;
      sessionStorage.setItem(RESET_TOKEN_STORAGE_KEY, tokenFromUrl);
      setToken(tokenFromUrl);
      navigate('/reset-password', { replace: true });
      return;
    }

    const storedToken = sessionStorage.getItem(RESET_TOKEN_STORAGE_KEY) ?? '';
    if (!tokenCapturedRef.current && storedToken) {
      setToken(storedToken);
    }
  }, [navigate, searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    if (newPassword !== confirmPassword) {
      setErrorMessage('Les deux mots de passe ne correspondent pas.');
      setIsLoading(false);
      return;
    }

    if (!token) {
      setErrorMessage('Lien invalide: token de réinitialisation manquant.');
      setIsLoading(false);
      return;
    }

    try {
      const response = await fetch('/api/auth/reset-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token, new_password: newPassword }),
      });

      const data = (await response.json()) as { message?: string; error?: string };
      if (!response.ok) {
        throw new Error(data.error ?? 'Impossible de réinitialiser le mot de passe');
      }

      setSuccessMessage(data.message ?? 'Mot de passe réinitialisé avec succès');
      sessionStorage.removeItem(RESET_TOKEN_STORAGE_KEY);
      setTimeout(() => navigate('/login'), 1200);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Impossible de réinitialiser le mot de passe.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-emerald-950 to-teal-950 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl bg-white rounded-2xl shadow-2xl p-5 sm:p-8">
        <h1 className="text-2xl font-bold mb-2">Réinitialiser le mot de passe</h1>
        <p className="text-gray-600 mb-6">Choisissez un nouveau mot de passe pour votre compte.</p>

        <form onSubmit={handleSubmit} className="space-y-6">
          {errorMessage && <div className="bg-red-50 text-red-700 border border-red-200 rounded-lg p-3 text-sm">{errorMessage}</div>}
          {successMessage && <div className="bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-lg p-3 text-sm">{successMessage}</div>}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Nouveau mot de passe</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                placeholder="Nouveau mot de passe"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Confirmez le mot de passe</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                placeholder="Confirmez le mot de passe"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-gradient-to-r from-emerald-600 to-emerald-700 text-white py-3 rounded-lg font-semibold hover:from-emerald-700 hover:to-emerald-800 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {isLoading ? 'Réinitialisation...' : 'Réinitialiser'}
            <ArrowRight className="w-5 h-5" />
          </button>
        </form>

        <div className="mt-6 text-sm text-gray-600">
          Retour à la{' '}
          <Link to="/login" className="text-emerald-600 font-semibold hover:underline">
            connexion
          </Link>
        </div>
      </div>
    </div>
  );
}
