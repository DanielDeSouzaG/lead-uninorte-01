import { useEffect, useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Users, TrendingUp } from 'lucide-react';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const getAuthHeaders = () => ({
  headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
});

export default function DashboardVendedor() {
  const [stats, setStats] = useState(null);
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, leadsRes] = await Promise.all([
        axios.get(`${API}/leads/stats`, getAuthHeaders()),
        axios.get(`${API}/leads/my`, getAuthHeaders())
      ]);
      
      setStats(statsRes.data);
      setLeads(leadsRes.data);
    } catch (error) {
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64">Carregando...</div>;
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2" data-testid="vendedor-dashboard-title">
          Meu Dashboard
        </h1>
        <p className="text-gray-600 dark:text-gray-400">Acompanhe seus leads e desempenho</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card className="card-hover" data-testid="total-leads-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">
              Total de Leads
            </CardTitle>
            <Users className="w-5 h-5 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900 dark:text-white">{stats?.total || 0}</div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Leads cadastrados por você</p>
          </CardContent>
        </Card>

        <Card className="card-hover gradient-orange text-white" data-testid="monthly-leads-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-white/90">
              Este Mês
            </CardTitle>
            <TrendingUp className="w-5 h-5 text-white" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {stats?.monthly?.[0]?.count || 0}
            </div>
            <p className="text-xs text-white/80 mt-1">Novos leads este mês</p>
          </CardContent>
        </Card>
      </div>

      <Card data-testid="recent-leads-card">
        <CardHeader>
          <CardTitle>Meus Leads Recentes</CardTitle>
        </CardHeader>
        <CardContent>
          {leads.length === 0 ? (
            <p className="text-center text-gray-500 dark:text-gray-400 py-8">
              Você ainda não cadastrou nenhum lead
            </p>
          ) : (
            <div className="space-y-4">
              {leads.slice(0, 5).map((lead) => (
                <div
                  key={lead.id}
                  className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
                  data-testid={`lead-item-${lead.id}`}
                >
                  <div>
                    <p className="font-semibold text-gray-900 dark:text-white">{lead.nome_completo}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{lead.curso}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-500">{lead.telefone}</p>
                  </div>
                  <div>
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-medium ${
                        lead.status === 'Novo'
                          ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                          : lead.status === 'Em negociação'
                          ? 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200'
                          : lead.status === 'Matriculado'
                          ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                          : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                      }`}
                    >
                      {lead.status}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}