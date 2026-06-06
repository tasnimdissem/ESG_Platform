import { useState } from 'react';
import { Link } from 'react-router';
import { Leaf, Mail, Lock, User, ArrowRight } from 'lucide-react';

export default function Register() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const response = await fetch('/api/auth/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, email, password }),
      });

      if (!response.ok) {
        const errorBody = await response.text();
        let message = 'Inscription échouée';
        try {
          const parsed = JSON.parse(errorBody) as { error?: string; message?: string };
          message = parsed.error ?? parsed.message ?? message;
        } catch {
          if (errorBody) {
            message = errorBody;
          }
        }
        throw new Error(message);
      }

      const data = await response.json() as { needs_approval?: boolean; needs_verification?: boolean; message?: string };
      setSuccessMessage(
        data.message ??
          (data.needs_approval
            ? 'Compte créé. Il sera activé après validation par un administrateur.'
            : 'Compte créé. Vérifiez votre e-mail pour l’activer.'),
      );
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Impossible de créer le compte.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-emerald-950 to-teal-950 flex items-center justify-center p-4">
      <div className="w-full max-w-6xl grid md:grid-cols-2 gap-8 items-center">
        <div className="text-white space-y-6">
          <div className="flex items-center gap-3">
            <div className="w-16 h-16 bg-emerald-500 rounded-2xl flex items-center justify-center">
              <Leaf className="w-10 h-10" />
            </div>
            <div>
              <h1 className="text-4xl font-bold">ESG Predictor</h1>
              <p className="text-emerald-200">Créez votre compte</p>
            </div>
          </div>
          <p className="text-xl text-emerald-100">
            Crée ton compte pour accéder aux KPI ESG, recommandations et chatbot.
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-2xl p-8">
          <h2 className="text-2xl font-bold mb-2">Créer un compte</h2>
          <p className="text-gray-600 mb-8">Inscription rapide pour la plateforme ESG.</p>

          <form onSubmit={handleSubmit} className="space-y-6">
            {errorMessage && (
              <div className="bg-red-50 text-red-700 border border-red-200 rounded-lg p-3 text-sm">
                {errorMessage}
              </div>
            )}

            {successMessage && (
              <div className="bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-lg p-3 text-sm">
                {successMessage}
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Nom</label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  placeholder="Ton nom"
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
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

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Mot de passe</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  placeholder="••••••••"
                  required
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-gradient-to-r from-emerald-600 to-emerald-700 text-white py-3 rounded-lg font-semibold hover:from-emerald-700 hover:to-emerald-800 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
            >
              {isLoading ? 'Création...' : 'Créer le compte'}
              <ArrowRight className="w-5 h-5" />
            </button>
          </form>

          <div className="mt-6 text-sm text-gray-600">
            Déjà un compte ?{' '}
            <Link to="/login" className="text-emerald-600 font-semibold hover:underline">
              Se connecter
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
