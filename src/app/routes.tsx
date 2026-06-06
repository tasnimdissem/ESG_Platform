import { createBrowserRouter, Navigate } from 'react-router';
import { useAuth } from './contexts/AuthContext';
import Login from './pages/Login';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import VerifyEmail from './pages/VerifyEmail';
import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics';
import ChatbotRag from './pages/ChatbotRag';
import RecommendationsRag from './pages/RecommendationsRag';
import Prediction from './pages/Prediction';
import Companies from './pages/Companies';
import CompanyView from './pages/CompanyView';
import AdminDashboard from './pages/AdminDashboard';
import Profile from './pages/Profile';
import PowerBIDashboard from './pages/PowerBIDashboard';
import Layout from './components/Layout';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isAuthLoading } = useAuth();

  if (isAuthLoading) {
    return <div className="p-8">Verification de la session...</div>;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

function RoleRoute({ children, allowedRoles }: { children: React.ReactNode; allowedRoles: string[] }) {
  const { user, isAuthLoading } = useAuth();

  if (isAuthLoading) {
    return <div className="p-8">Verification des permissions...</div>;
  }

  if (!user || !allowedRoles.includes(user.role)) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
}

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/register',
    element: <Register />,
  },
  {
    path: '/forgot-password',
    element: <ForgotPassword />,
  },
  {
    path: '/reset-password',
    element: <ResetPassword />,
  },
  {
    path: '/verify-email',
    element: <VerifyEmail />,
  },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <Layout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: <Dashboard />,
      },
      {
        path: 'analytics',
        element: (
          <RoleRoute allowedRoles={['admin', 'decideur', 'metier']}>
            <Analytics />
          </RoleRoute>
        ),
      },
      {
        path: 'profile',
        element: <Profile />,
      },
      {
        path: 'powerbi',
        element: <PowerBIDashboard />,
      },
      {
        path: 'chatbot',
        element: (
          <RoleRoute allowedRoles={['admin', 'metier']}>
            <ChatbotRag />
          </RoleRoute>
        ),
      },
      {
        path: 'recommendations',
        element: (
          <RoleRoute allowedRoles={['admin', 'decideur', 'metier']}>
            <RecommendationsRag />
          </RoleRoute>
        ),
      },
      {
        path: 'prediction',
        element: (
          <RoleRoute allowedRoles={['admin', 'metier']}>
            <Prediction />
          </RoleRoute>
        ),
      },
      {
        path: 'companies',
        element: (
          <RoleRoute allowedRoles={['admin', 'metier']}>
            <Companies />
          </RoleRoute>
        ),
      },
      {
        path: 'companies/:id',
        element: (
          <RoleRoute allowedRoles={['admin', 'metier']}>
            <CompanyView />
          </RoleRoute>
        ),
      },
      {
        path: 'admin',
        element: (
          <RoleRoute allowedRoles={['admin']}>
            <AdminDashboard />
          </RoleRoute>
        ),
      },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
]);
