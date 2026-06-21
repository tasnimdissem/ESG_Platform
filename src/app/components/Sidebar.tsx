import { NavLink } from 'react-router';
import { LayoutDashboard, LineChart, MessageSquare, Lightbulb, LogOut, Leaf, Calculator, ShieldAlert, User, Building2, X } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import trituxLogo from '../../assets/tritux_logo.png';

type NavItem = { path: string; icon: React.ElementType; label: string };

const ALL_NAV_ITEMS: (NavItem & { roles: string[] })[] = [
  { path: '/',               icon: LayoutDashboard, label: 'Tableau de bord',   roles: ['admin', 'decideur', 'metier'] },
  { path: '/analytics',      icon: LineChart,        label: 'Analyses',          roles: ['admin', 'decideur', 'metier'] },
  { path: '/profile',        icon: User,             label: 'Mon profil',        roles: ['admin', 'decideur', 'metier'] },
  { path: '/prediction',     icon: Calculator,       label: 'ESG Studio',        roles: ['admin', 'metier'] },
  { path: '/chatbot',        icon: MessageSquare,    label: 'ESGénie',           roles: ['admin', 'metier'] },
  { path: '/recommendations',icon: Lightbulb,        label: 'Recommandations',   roles: ['admin', 'decideur', 'metier'] },
  { path: '/companies',      icon: Building2,        label: 'Entreprises',       roles: ['admin', 'metier'] },
  { path: '/admin',          icon: ShieldAlert,      label: 'Administration',    roles: ['admin'] },
];

type SidebarProps = { isOpen: boolean; onClose: () => void };

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const { logout, user } = useAuth();
  const role = user?.role === 'user' ? 'decideur' : (user?.role ?? 'decideur');

  const navItems = ALL_NAV_ITEMS.filter((item) => item.roles.includes(role));

  return (
    <div className={`w-64 bg-gradient-to-b from-emerald-900 to-emerald-950 text-white flex-col h-screen shadow-xl md:sticky md:top-0 md:flex ${isOpen ? 'flex fixed inset-y-0 left-0 z-30' : 'hidden'}`}>
      <div className="p-5 border-b border-emerald-800/70 relative">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 p-1.5 rounded-lg text-emerald-200 hover:bg-emerald-800 md:hidden"
          aria-label="Fermer le menu"
        >
          <X className="w-4 h-4" />
        </button>
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-xl flex items-center justify-center shadow-lg shadow-emerald-900/50">
            <Leaf className="w-6 h-6 drop-shadow" />
          </div>
          <div>
            <h1 className="font-bold text-lg leading-tight">Plateforme ESG</h1>
            <p className="text-[11px] text-emerald-400">Intelligence & Prédiction</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            onClick={onClose}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-2.5 rounded-xl transition-all duration-150 ${
                isActive
                  ? 'bg-gradient-to-r from-emerald-500 to-emerald-600 text-white shadow-lg shadow-emerald-900/40'
                  : 'text-emerald-100 hover:bg-emerald-800/70 hover:text-white'
              }`
            }
          >
            <item.icon className="w-5 h-5 flex-shrink-0" />
            <span className="font-medium text-sm">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-emerald-800 space-y-2">
        {user && (
          <div className="px-4 py-2 rounded-lg bg-emerald-800/50 text-xs text-emerald-200 truncate">
            <span className="font-semibold">{user.name}</span>
            <span className="ml-1 opacity-70">· {role}</span>
          </div>
        )}
        <button
          onClick={logout}
          className="flex items-center gap-3 px-4 py-3 rounded-lg w-full text-emerald-100 hover:bg-red-900/60 transition-all"
        >
          <LogOut className="w-5 h-5" />
          <span className="font-medium">Déconnexion</span>
        </button>
      </div>

      {/* Tritux branding */}
      <div className="px-4 pb-4 pt-2 border-t border-emerald-800/60">
        <div className="flex items-center justify-center gap-2 opacity-40 hover:opacity-75 transition-opacity duration-300">
          <span className="text-[9px] text-emerald-300 tracking-widest uppercase font-light">Powered by</span>
          <div className="h-px w-3 bg-emerald-500/60" />
          <img src={trituxLogo} alt="Tritux" className="h-4 w-auto object-contain brightness-150" />
        </div>
      </div>
    </div>
  );
}
