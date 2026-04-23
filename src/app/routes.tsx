import { createBrowserRouter, Navigate } from 'react-router';
import { useAuth } from './contexts/AuthContext';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Analytics from './pages/Analytics';
import ChatbotRag from './pages/ChatbotRag';
import RecommendationsRag from './pages/RecommendationsRag';
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

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />,
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
        element: <Analytics />,
      },
      {
        path: 'chatbot',
        element: <ChatbotRag />,
      },
      {
        path: 'recommendations',
        element: <RecommendationsRag />,
      },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
]);
