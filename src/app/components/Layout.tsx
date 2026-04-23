import { Outlet } from 'react-router';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

export default function Layout() {
  return (
    <div className="flex min-h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
