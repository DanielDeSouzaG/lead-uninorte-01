import { useEffect, useState } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ThemeProvider } from "next-themes";
import LoginPage from "@/pages/LoginPage";
import DashboardLayout from "@/components/DashboardLayout";
import DashboardVendedor from "@/pages/DashboardVendedor";
import DashboardCoordenador from "@/pages/DashboardCoordenador";
import DashboardAdmin from "@/pages/DashboardAdmin";
import LeadsPage from "@/pages/LeadsPage";
import UsersPage from "@/pages/UsersPage";
import AuditLogsPage from "@/pages/AuditLogsPage";
import ConfigPage from "@/pages/ConfigPage";
import { Toaster } from "@/components/ui/sonner";

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    
    if (token && userData) {
      setUser(JSON.parse(userData));
    }
    setLoading(false);
  }, []);

  const handleLogin = (token, userData) => {
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-lg">Carregando...</div>
      </div>
    );
  }

  return (
    <ThemeProvider attribute="class" defaultTheme="light">
      <BrowserRouter>
        <Routes>
          <Route
            path="/login"
            element={!user ? <LoginPage onLogin={handleLogin} /> : <Navigate to="/" />}
          />
          
          <Route
            path="/"
            element={
              user ? (
                <DashboardLayout user={user} onLogout={handleLogout}>
                  {user.tipo === 'vendedor' && <DashboardVendedor />}
                  {user.tipo === 'coordenador' && <DashboardCoordenador />}
                  {user.tipo === 'administrador' && <DashboardAdmin />}
                </DashboardLayout>
              ) : (
                <Navigate to="/login" />
              )
            }
          />

          <Route
            path="/leads"
            element={
              user ? (
                <DashboardLayout user={user} onLogout={handleLogout}>
                  <LeadsPage userType={user.tipo} userId={user.id} />
                </DashboardLayout>
              ) : (
                <Navigate to="/login" />
              )
            }
          />

          <Route
            path="/users"
            element={
              user && user.tipo === 'administrador' ? (
                <DashboardLayout user={user} onLogout={handleLogout}>
                  <UsersPage />
                </DashboardLayout>
              ) : (
                <Navigate to="/" />
              )
            }
          />

          <Route
            path="/audit"
            element={
              user && user.tipo === 'administrador' ? (
                <DashboardLayout user={user} onLogout={handleLogout}>
                  <AuditLogsPage />
                </DashboardLayout>
              ) : (
                <Navigate to="/" />
              )
            }
          />

          <Route
            path="/config"
            element={
              user && user.tipo === 'administrador' ? (
                <DashboardLayout user={user} onLogout={handleLogout}>
                  <ConfigPage />
                </DashboardLayout>
              ) : (
                <Navigate to="/" />
              )
            }
          />
        </Routes>
        <Toaster position="top-right" />
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;