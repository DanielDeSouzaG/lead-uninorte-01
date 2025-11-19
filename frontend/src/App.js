// Importação de hooks e funcionalidades do React
import { useEffect, useState } from "react";
// Importação do arquivo de estilos CSS global
import "@/App.css";
// Importação de componentes de roteamento do React Router
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
// Importação do ThemeProvider para suporte a temas claro/escuro
import { ThemeProvider } from "next-themes";
// Importação das páginas da aplicação
import LoginPage from "@/pages/LoginPage";
import DashboardLayout from "@/components/DashboardLayout";
import DashboardVendedor from "@/pages/DashboardVendedor";
import DashboardCoordenador from "@/pages/DashboardCoordenador";
import DashboardAdmin from "@/pages/DashboardAdmin";
import LeadsPage from "@/pages/LeadsPage";
import UsersPage from "@/pages/UsersPage";
import AuditLogsPage from "@/pages/AuditLogsPage";
import ConfigPage from "@/pages/ConfigPage";
// Importação do componente de notificações toast
import { Toaster } from "@/components/ui/sonner";

// Componente principal da aplicação React
function App() {
  // Estado para armazenar os dados do usuário logado
  // Inicialmente null (usuário não logado)
  const [user, setUser] = useState(null);
  
  // Estado para controlar o carregamento inicial da aplicação
  // Inicialmente true (carregando) enquanto verifica autenticação
  const [loading, setLoading] = useState(true);

  // Hook useEffect que executa uma vez quando o componente é montado
  // Verifica se existe um usuário autenticado no localStorage
  useEffect(() => {
    // Recupera o token JWT do localStorage
    const token = localStorage.getItem('token');
    // Recupera os dados do usuário do localStorage
    const userData = localStorage.getItem('user');
    
    // Verifica se existe token e dados do usuário no localStorage
    if (token && userData) {
      // Se existir, atualiza o estado do usuário com os dados parseados de JSON
      setUser(JSON.parse(userData));
    }
    // Finaliza o estado de carregamento independente do resultado
    setLoading(false);
  }, []); // Array de dependências vazio = executa apenas uma vez na montagem

  // Função para lidar com o login do usuário
  // Recebe o token JWT e os dados do usuário como parâmetros
  const handleLogin = (token, userData) => {
    // Armazena o token JWT no localStorage para persistência
    localStorage.setItem('token', token);
    // Armazena os dados do usuário no localStorage como string JSON
    localStorage.setItem('user', JSON.stringify(userData));
    // Atualiza o estado do usuário com os novos dados
    setUser(userData);
  };

  // Função para lidar com o logout do usuário
  const handleLogout = () => {
    // Remove o token JWT do localStorage
    localStorage.removeItem('token');
    // Remove os dados do usuário do localStorage
    localStorage.removeItem('user');
    // Limpa o estado do usuário (define como null)
    setUser(null);
  };

  // Se a aplicação ainda está carregando (verificando autenticação), exibe um indicador
  if (loading) {
    return (
      // Container centralizado na tela inteira usando flexbox
      <div className="flex items-center justify-center min-h-screen">
        {/* Texto de carregamento simples */}
        <div className="text-lg">Carregando...</div>
      </div>
    );
  }

  // Renderização principal da aplicação
  return (
    // Provider de temas que permite alternar entre tema claro e escuro
    // attribute="class" significa que o tema será controlado via classes CSS
    // defaultTheme="light" define o tema padrão como claro
    <ThemeProvider attribute="class" defaultTheme="light">
      {/* Componente que habilita o roteamento na aplicação */}
      <BrowserRouter>
        {/* Container para definir todas as rotas da aplicação */}
        <Routes>
          
          {/* Rota para a página de login */}
          <Route
            path="/login"
            // Renderização condicional:
            // Se não há usuário logado, exibe a página de login
            // Se há usuário logado, redireciona para a página inicial (/)
            element={!user ? <LoginPage onLogin={handleLogin} /> : <Navigate to="/" />}
          />
          
          {/* Rota para a página inicial (dashboard) */}
          <Route
            path="/"
            element={
              // Se há usuário logado, exibe o layout do dashboard com o conteúdo apropriado
              user ? (
                // Layout base do dashboard que recebe o usuário e função de logout
                // Este componente provavelmente inclui header, sidebar, etc.
                <DashboardLayout user={user} onLogout={handleLogout}>
                  {
                    // Renderização condicional do conteúdo do dashboard
                    // Baseado no tipo de usuário (vendedor, coordenador, administrador)
                    
                    // Se for vendedor, exibe o dashboard específico para vendedores
                    user.tipo === 'vendedor' && <DashboardVendedor />
                  }
                  {
                    // Se for coordenador, exibe o dashboard específico para coordenadores
                    user.tipo === 'coordenador' && <DashboardCoordenador />
                  }
                  {
                    // Se for administrador, exibe o dashboard específico para administradores
                    user.tipo === 'administrador' && <DashboardAdmin />
                  }
                </DashboardLayout>
              ) : (
                // Se não há usuário logado, redireciona para a página de login
                <Navigate to="/login" />
              )
            }
          />

          {/* Rota para a página de gestão de leads */}
          <Route
            path="/leads"
            element={
              // Acesso permitido para todos os usuários logados
              user ? (
                <DashboardLayout user={user} onLogout={handleLogout}>
                  {/* Componente de gestão de leads que recebe o tipo e ID do usuário */}
                  <LeadsPage userType={user.tipo} userId={user.id} />
                </DashboardLayout>
              ) : (
                // Se não está logado, redireciona para login
                <Navigate to="/login" />
              )
            }
          />

          {/* Rota para a página de gestão de usuários */}
          <Route
            path="/users"
            element={
              // Acesso RESTRITO - apenas administradores podem acessar
              // Verifica se existe usuário E se é do tipo administrador
              user && user.tipo === 'administrador' ? (
                <DashboardLayout user={user} onLogout={handleLogout}>
                  {/* Componente de gestão de usuários */}
                  <UsersPage />
                </DashboardLayout>
              ) : (
                // Se não é administrador, redireciona para a página inicial
                <Navigate to="/" />
              )
            }
          />

          {/* Rota para a página de logs de auditoria */}
          <Route
            path="/audit"
            element={
              // Acesso RESTRITO - apenas administradores podem acessar
              user && user.tipo === 'administrador' ? (
                <DashboardLayout user={user} onLogout={handleLogout}>
                  {/* Componente de visualização de logs de auditoria */}
                  <AuditLogsPage />
                </DashboardLayout>
              ) : (
                // Se não é administrador, redireciona para a página inicial
                <Navigate to="/" />
              )
            }
          />

          {/* Rota para a página de configurações do sistema */}
          <Route
            path="/config"
            element={
              // Acesso RESTRITO - apenas administradores podem acessar
              user && user.tipo === 'administrador' ? (
                <DashboardLayout user={user} onLogout={handleLogout}>
                  {/* Componente de configurações do sistema */}
                  <ConfigPage />
                </DashboardLayout>
              ) : (
                // Se não é administrador, redireciona para a página inicial
                <Navigate to="/" />
              )
            }
          />
          
        </Routes>
        
        {/* Componente de notificações toast (mensagens temporárias) */}
        {/* position="top-right" posiciona as notificações no canto superior direito */}
        <Toaster position="top-right" />
        
      </BrowserRouter>
    </ThemeProvider>
  );
}

// Exporta o componente App como padrão para ser usado em outros arquivos
export default App;