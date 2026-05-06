import { NavLink } from 'react-router';
import { LayoutDashboard, LineChart, MessageSquare, Lightbulb, LogOut, Leaf, Calculator, ShieldAlert } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export function Sidebar() {
  const { logout, user } = useAuth();

  const navItems = [
    { path: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/analytics', icon: LineChart, label: 'Analytics' },
    { path: '/prediction', icon: Calculator, label: 'Simulateur ESG' },
    { path: '/chatbot', icon: MessageSquare, label: 'Chatbot IA' },
    { path: '/recommendations', icon: Lightbulb, label: 'Recommandations' },
  ];

  if (user && user.role === 'admin') {
    navItems.push({ path: '/admin', icon: ShieldAlert, label: 'Administration' });
  }

  return (
    <div className="w-64 bg-gradient-to-b from-emerald-900 to-emerald-950 text-white flex flex-col h-screen sticky top-0">
      <div className="p-6 border-b border-emerald-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-emerald-500 rounded-lg flex items-center justify-center">
            <Leaf className="w-6 h-6" />
          </div>
          <div>
            <h1 className="font-bold text-xl">ESG Predictor</h1>
            <p className="text-xs text-emerald-300">Platform Intelligence</p>
          </div>
        </div>
      </div>
      
      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-4 py-3 rounded-lg transition-all ${
                isActive
                  ? 'bg-emerald-500 text-white shadow-lg'
                  : 'text-emerald-100 hover:bg-emerald-800'
              }`
            }
          >
            <item.icon className="w-5 h-5" />
            <span className="font-medium">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="p-4 border-t border-emerald-800">
        <button
          onClick={logout}
          className="flex items-center gap-3 px-4 py-3 rounded-lg w-full text-emerald-100 hover:bg-red-900 transition-all"
        >
          <LogOut className="w-5 h-5" />
          <span className="font-medium">Déconnexion</span>
        </button>
      </div>
    </div>
  );
}
