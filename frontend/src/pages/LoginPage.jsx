import { useState } from 'react';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { LogIn, Eye, EyeOff, GraduationCap, Users, TrendingUp } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export default function LoginPage({ onLogin }) {
  const [email, setEmail] = useState('');
  const [senha, setSenha] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/auth/login`, { email, senha });
      const { access_token, user } = response.data;
      
      toast.success(`Bem-vindo, ${user.nome}!`);
      onLogin(access_token, user);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao fazer login');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex relative overflow-hidden">
      {/* Lado esquerdo - Branding */}
      <div className="hidden lg:flex lg:w-1/2 relative gradient-bg items-center justify-center p-12">
        {/* Decorative circles */}
        <div className="absolute top-20 left-20 w-72 h-72 bg-white/10 rounded-full blur-3xl" />
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-blue-300/20 rounded-full blur-3xl" />
        
        <div className="relative z-10 text-white max-w-lg">
          <div className="mb-8 flex items-center gap-4">
            <div className="w-20 h-20 bg-white rounded-2xl flex items-center justify-center shadow-2xl">
              <span className="text-4xl font-bold text-blue-600">U</span>
            </div>
            <div>
              <h1 className="text-5xl font-bold mb-2">UNINORTE</h1>
              <p className="text-xl text-blue-100">Gestão de Leads</p>
            </div>
          </div>
          
          <p className="text-lg text-blue-50 mb-8 leading-relaxed">
            Sistema completo para gerenciamento de leads educacionais. 
            Acompanhe suas vendas, gerencie equipes e tome decisões baseadas em dados.
          </p>
          
          <div className="space-y-4">
            <div className="flex items-center gap-4 p-4 bg-white/10 backdrop-blur-sm rounded-xl">
              <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                <Users className="text-white" size={24} />
              </div>
              <div>
                <h3 className="font-semibold text-lg">Gestão de Equipe</h3>
                <p className="text-sm text-blue-100">Controle total sobre vendedores e coordenadores</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4 p-4 bg-white/10 backdrop-blur-sm rounded-xl">
              <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                <TrendingUp className="text-white" size={24} />
              </div>
              <div>
                <h3 className="font-semibold text-lg">Relatórios e Analytics</h3>
                <p className="text-sm text-blue-100">Dashboards interativos com métricas em tempo real</p>
              </div>
            </div>
            
            <div className="flex items-center gap-4 p-4 bg-white/10 backdrop-blur-sm rounded-xl">
              <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                <GraduationCap className="text-white" size={24} />
              </div>
              <div>
                <h3 className="font-semibold text-lg">Foco Educacional</h3>
                <p className="text-sm text-blue-100">Desenvolvido especialmente para instituições de ensino</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Lado direito - Form de Login */}
      <div className="flex-1 flex items-center justify-center p-4 bg-gray-50 dark:bg-gray-900">
        <div className="w-full max-w-md animate-fade-in">
          {/* Logo mobile */}
          <div className="lg:hidden text-center mb-8">
            <div className="w-20 h-20 mx-auto mb-4 bg-blue-600 rounded-2xl flex items-center justify-center shadow-xl">
              <span className="text-3xl font-bold text-white">U</span>
            </div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-1">UNINORTE</h1>
            <p className="text-gray-600 dark:text-gray-400">Gestão de Leads</p>
          </div>

          <Card className="shadow-2xl border-0 overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-600 to-blue-400" />
            
            <CardHeader className="space-y-1 pb-4">
              <CardTitle className="text-2xl font-bold text-gray-900 dark:text-white">Bem-vindo de volta</CardTitle>
              <CardDescription>Entre com suas credenciais para acessar o sistema</CardDescription>
            </CardHeader>
            
            <CardContent>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="email" className="text-sm font-medium">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="seu@email.com.br"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    data-testid="login-email-input"
                    className="h-11 border-gray-300 dark:border-gray-600 focus:border-blue-600 dark:focus:border-blue-500"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="senha" className="text-sm font-medium">Senha</Label>
                  <div className="relative">
                    <Input
                      id="senha"
                      type={showPassword ? 'text' : 'password'}
                      placeholder="••••••••"
                      value={senha}
                      onChange={(e) => setSenha(e.target.value)}
                      required
                      data-testid="login-password-input"
                      className="h-11 pr-10 border-gray-300 dark:border-gray-600 focus:border-blue-600 dark:focus:border-blue-500"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
                      data-testid="toggle-password-visibility"
                    >
                      {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                    </button>
                  </div>
                </div>

                <Button
                  type="submit"
                  className="w-full h-11 text-base font-semibold gradient-bg hover:opacity-90 shadow-lg hover:shadow-xl transition-all"
                  disabled={loading}
                  data-testid="login-submit-button"
                >
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      Entrando...
                    </span>
                  ) : (
                    <>
                      <LogIn className="mr-2" size={20} />
                      Entrar no Sistema
                    </>
                  )}
                </Button>
              </form>

              <div className="mt-6 p-4 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-950 dark:to-blue-900 rounded-xl border border-blue-200 dark:border-blue-800">
                <p className="text-sm font-semibold mb-3 text-blue-900 dark:text-blue-100 flex items-center gap-2">
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" />
                  Credenciais de teste:
                </p>
                <div className="space-y-2 text-xs text-blue-800 dark:text-blue-200">
                  <div className="flex items-center justify-between p-2 bg-white/50 dark:bg-black/20 rounded">
                    <span className="font-medium">Vendedor:</span>
                    <span className="font-mono">vendedor@lead.com.br / vendedor123</span>
                  </div>
                  <div className="flex items-center justify-between p-2 bg-white/50 dark:bg-black/20 rounded">
                    <span className="font-medium">Coordenador:</span>
                    <span className="font-mono">coordenador@lead.com.br / coordenador123</span>
                  </div>
                  <div className="flex items-center justify-between p-2 bg-white/50 dark:bg-black/20 rounded">
                    <span className="font-medium">Admin:</span>
                    <span className="font-mono">adm@lead.com.br / adm123</span>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <p className="text-center text-sm text-gray-500 dark:text-gray-400 mt-6">
            © 2025 UNINORTE. Todos os direitos reservados.
          </p>
        </div>
      </div>
    </div>
  );
}