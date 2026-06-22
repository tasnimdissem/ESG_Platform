import { useState } from 'react';
import { Link } from 'react-router';
import { Mail, ArrowRight, KeyRound } from 'lucide-react';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const response = await fetch('/api/auth/forgot-password', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      });

      const data = (await response.json()) as { message?: string; error?: string };
      if (!response.ok) {
        throw new Error(data.error ?? 'Impossible d’envoyer la demande de réinitialisation');
      }

      setSuccessMessage(data.message ?? 'Si le compte existe, un e-mail de réinitialisation a été envoyé.');
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Erreur lors de la demande de réinitialisation.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-emerald-950 to-teal-950 flex items-center justify-center p-4">
      <div className="w-full max-w-2xl bg-white rounded-2xl shadow-2xl p-5 sm:p-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-12 h-12 bg-emerald-500 rounded-xl flex items-center justify-center text-white">
            <KeyRound className="w-7 h-7" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Mot de passe oublié</h1>
            <p className="text-gray-600">Recevez un lien de réinitialisation par e-mail.</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {errorMessage && <div className="bg-red-50 text-red-700 border border-red-200 rounded-lg p-3 text-sm">{errorMessage}</div>}
          {successMessage && <div className="bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-lg p-3 text-sm">{successMessage}</div>}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">E-mail</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                placeholder="votre@email.com"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-gradient-to-r from-emerald-600 to-emerald-700 text-white py-3 rounded-lg font-semibold hover:from-emerald-700 hover:to-emerald-800 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {isLoading ? 'Envoi...' : 'Envoyer le lien'}
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
