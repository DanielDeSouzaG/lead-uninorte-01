import { useState } from 'react';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { LogIn, Eye, EyeOff } from 'lucide-react';

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
    <div className="min-h-screen flex items-center justify-center p-4 gradient-bg">
      <div className="w-full max-w-md animate-fade-in">
        <div className="text-center mb-8">
          <div className="w-24 h-24 mx-auto mb-6 bg-white rounded-2xl flex items-center justify-center shadow-xl">
            <span className="text-4xl font-bold text-blue-600">U</span>
          </div>
          <h1 className="text-4xl font-bold text-white mb-2" data-testid="login-title">
            UNINORTE
          </h1>
          <p className="text-blue-100 text-lg">Gestão de Leads</p>
        </div>

        <Card className="shadow-2xl border-0">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl font-bold">Login</CardTitle>
            <CardDescription>Entre com suas credenciais para acessar o sistema</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="seu@email.com.br"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  data-testid="login-email-input"
                  className="h-11"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="senha">Senha</Label>
                <div className="relative">
                  <Input
                    id="senha"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="••••••••"
                    value={senha}
                    onChange={(e) => setSenha(e.target.value)}
                    required
                    data-testid="login-password-input"
                    className="h-11 pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-700"
                    data-testid="toggle-password-visibility"
                  >
                    {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                  </button>
                </div>
              </div>

              <Button
                type="submit"
                className="w-full h-11 text-base font-semibold gradient-bg hover:opacity-90"
                disabled={loading}
                data-testid="login-submit-button"
              >
                {loading ? (
                  <span>Entrando...</span>
                ) : (
                  <>
                    <LogIn className="mr-2" size={20} />
                    Entrar
                  </>
                )}
              </Button>
            </form>

            <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-950 rounded-lg">
              <p className="text-sm font-semibold mb-2 text-blue-900 dark:text-blue-100">Credenciais de teste:</p>
              <div className="space-y-1 text-xs text-blue-700 dark:text-blue-200">
                <p><strong>Vendedor:</strong> vendedor@lead.com.br / vendedor123</p>
                <p><strong>Coordenador:</strong> coordenador@lead.com.br / coordenador123</p>
                <p><strong>Admin:</strong> adm@lead.com.br / adm123</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}