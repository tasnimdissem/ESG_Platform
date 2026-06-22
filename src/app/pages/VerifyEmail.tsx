import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router';
import { CheckCircle2, Loader2, MailWarning, ArrowRight } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { Button } from '../components/ui/button';

type VerifyState = 'loading' | 'success' | 'error';

export default function VerifyEmail() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { updateUser } = useAuth();
  const [state, setState] = useState<VerifyState>('loading');
  const [message, setMessage] = useState('Vérification de votre compte en cours...');
  const redirectTimerRef = useRef<number | null>(null);

  useEffect(() => {
    const token = searchParams.get('token')?.trim() ?? '';

    if (!token) {
      setState('error');
      setMessage('Lien invalide : aucun jeton de vérification n’a été fourni.');
      return;
    }

    const activateAccount = async () => {
      try {
        const response = await fetch(`/api/auth/verify-email?token=${encodeURIComponent(token)}`, {
          credentials: 'include',
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok) {
          throw new Error(data.error || 'Lien d’activation invalide ou expiré.');
        }

        if (data.user) {
          updateUser(data.user);
        }

        setState('success');
        setMessage(data.message || 'Compte activé avec succès.');
        redirectTimerRef.current = window.setTimeout(() => {
          navigate('/');
        }, 1800);
      } catch (error) {
        setState('error');
        setMessage(error instanceof Error ? error.message : 'La vérification a échoué.');
      }
    };

    void activateAccount();
    return () => {
      if (redirectTimerRef.current !== null) {
        window.clearTimeout(redirectTimerRef.current);
      }
    };
  }, [navigate, searchParams, updateUser]);

  const isLoading = state === 'loading';

  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(16,185,129,0.22),_transparent_32%),linear-gradient(135deg,#052e2b_0%,#0f766e_52%,#f8fafc_52%,#ffffff_100%)] px-4 py-10 sm:px-6 lg:px-8">
      <div className="mx-auto flex min-h-[calc(100vh-5rem)] max-w-6xl items-center">
        <div className="grid w-full gap-8 overflow-hidden rounded-[2rem] border border-white/40 bg-white/90 shadow-[0_30px_120px_-45px_rgba(15,23,42,0.45)] backdrop-blur md:grid-cols-[1.15fr_0.85fr]">
          <div className="flex flex-col justify-between gap-8 bg-slate-950 px-8 py-10 text-white sm:px-10 lg:px-12">
            <div>
              <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-emerald-400/30 bg-emerald-400/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-emerald-200">
                ESG Platform
              </div>
              <h1 className="max-w-xl text-4xl font-black tracking-tight sm:text-5xl">
                Activation de votre compte
              </h1>
              <p className="mt-4 max-w-lg text-sm leading-7 text-slate-300 sm:text-base">
                Cette étape finalise la création de votre accès. Une fois le compte vérifié, vous serez automatiquement redirigé vers la plateforme.
              </p>
            </div>

            <div className="grid gap-3 text-sm text-slate-300 sm:grid-cols-2">
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                Vérification email
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                JWT sécurisé via cookie HttpOnly
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                Accès personnalisé selon votre rôle
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                Multi-tenancy par entreprise
              </div>
            </div>
          </div>

          <div className="flex items-center justify-center px-6 py-10 sm:px-10 lg:px-12">
            <div className="w-full max-w-md space-y-6 rounded-[1.75rem] border border-slate-200 bg-white p-8 shadow-lg">
              <div className="flex items-center gap-3">
                <div className={`flex h-14 w-14 items-center justify-center rounded-2xl ${state === 'success' ? 'bg-emerald-100 text-emerald-700' : state === 'error' ? 'bg-red-100 text-red-600' : 'bg-slate-100 text-slate-600'}`}>
                  {isLoading ? <Loader2 className="h-7 w-7 animate-spin" /> : state === 'success' ? <CheckCircle2 className="h-7 w-7" /> : <MailWarning className="h-7 w-7" />}
                </div>
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Vérification</p>
                  <h2 className="text-2xl font-black tracking-tight text-slate-900">
                    {isLoading ? 'Traitement en cours' : state === 'success' ? 'Compte activé' : 'Activation impossible'}
                  </h2>
                </div>
              </div>

              <p className="text-sm leading-6 text-slate-600">
                {message}
              </p>

              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600">
                Si la redirection ne se lance pas automatiquement, utilisez le bouton ci-dessous pour continuer.
              </div>

              <div className="flex flex-col gap-3 sm:flex-row">
                {state === 'success' ? (
                  <Button
                    type="button"
                    className="h-11 flex-1 rounded-xl bg-emerald-600 text-white hover:bg-emerald-700"
                    onClick={() => navigate('/')}
                  >
                    Continuer vers la plateforme
                    <ArrowRight className="h-4 w-4" />
                  </Button>
                ) : (
                  <Button
                    type="button"
                    className="h-11 flex-1 rounded-xl bg-slate-900 text-white hover:bg-slate-800"
                    onClick={() => navigate('/login')}
                  >
                    Aller à la connexion
                  </Button>
                )}

                <Button
                  type="button"
                  variant="outline"
                  className="h-11 flex-1 rounded-xl border-slate-200"
                  asChild
                >
                  <Link to="/login">Retour</Link>
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}