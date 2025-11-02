import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { useTheme } from 'next-themes';
import {
  LayoutDashboard,
  Users,
  UserCircle,
  Settings,
  LogOut,
  Sun,
  Moon,
  Menu,
  X,
  FileText,
  History,
  List
} from 'lucide-react';

export default function DashboardLayout({ children, user, onLogout }) {
  const { theme, setTheme } = useTheme();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const isActive = (path) => location.pathname === path;

  const menuItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard, roles: ['vendedor', 'coordenador', 'administrador'] },
    { path: '/leads', label: 'Leads', icon: List, roles: ['vendedor', 'coordenador', 'administrador'] },
    { path: '/users', label: 'Usuários', icon: Users, roles: ['administrador'] },
    { path: '/config', label: 'Configurações', icon: Settings, roles: ['administrador'] },
    { path: '/audit', label: 'Auditoria', icon: History, roles: ['administrador'] },
  ].filter(item => item.roles.includes(user.tipo));

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-40">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="lg:hidden p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700"
              data-testid="toggle-sidebar-button"
            >
              {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
            
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-xl font-bold text-white">U</span>
              </div>
              <div className="hidden sm:block">
                <h1 className="text-lg font-bold text-gray-900 dark:text-white">UNINORTE</h1>
                <p className="text-xs text-gray-500 dark:text-gray-400">Gestão de Leads</p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              data-testid="theme-toggle-button"
              className="rounded-full"
            >
              {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
            </Button>

            <div className="hidden sm:flex items-center gap-2 px-3 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
              <UserCircle size={20} className="text-gray-600 dark:text-gray-300" />
              <div>
                <p className="text-sm font-semibold text-gray-900 dark:text-white">{user.nome}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">{user.tipo}</p>
              </div>
            </div>

            <Button
              variant="ghost"
              size="icon"
              onClick={onLogout}
              data-testid="logout-button"
              className="rounded-full text-red-600 hover:text-red-700 hover:bg-red-50 dark:hover:bg-red-950"
            >
              <LogOut size={20} />
            </Button>
          </div>
        </div>
      </header>

      <div className="flex">
        {/* Sidebar */}
        <aside
          className={`
            fixed lg:static inset-y-0 left-0 z-30
            w-64 bg-white dark:bg-gray-800 border-r border-gray-200 dark:border-gray-700
            transition-transform duration-300 ease-in-out lg:translate-x-0
            ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
            mt-[65px] lg:mt-0
          `}
        >
          <nav className="p-4 space-y-2">
            <p className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase px-3 mb-3">Navegação</p>
            {menuItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  data-testid={`nav-link-${item.label.toLowerCase()}`}
                  className={`
                    flex items-center gap-3 px-3 py-2.5 rounded-lg font-medium
                    transition-all
                    ${isActive(item.path)
                      ? 'bg-blue-600 text-white shadow-md'
                      : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }
                  `}
                >
                  <Icon size={20} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </nav>

          <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-2 px-3 py-2 bg-blue-50 dark:bg-blue-950 rounded-lg">
              <UserCircle size={32} className="text-blue-600 dark:text-blue-400" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">{user.nome}</p>
                <p className="text-xs text-gray-600 dark:text-gray-400 capitalize">{user.tipo}</p>
              </div>
            </div>
          </div>
        </aside>

        {/* Overlay for mobile */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/50 z-20 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Main content */}
        <main className="flex-1 p-4 lg:p-8">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}