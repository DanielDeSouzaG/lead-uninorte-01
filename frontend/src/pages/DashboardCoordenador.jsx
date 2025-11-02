import { useEffect, useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Users, CheckCircle, Clock, TrendingUp } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const getAuthHeaders = () => ({
  headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
});

const COLORS = ['#3B82F6', '#F97316', '#10B981', '#EF4444'];

export default function DashboardCoordenador() {
  const [dashboard, setDashboard] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const response = await axios.get(`${API}/dashboard`, getAuthHeaders());
      setDashboard(response.data);
    } catch (error) {
      toast.error('Erro ao carregar dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64">Carregando...</div>;
  }

  const statusData = dashboard?.status_distribution || [];
  const cursoData = dashboard?.curso_distribution || [];
  const vendedorRanking = dashboard?.vendedor_ranking || [];
  const monthlyData = dashboard?.monthly_leads || [];

  const totalLeads = dashboard?.total_leads || 0;
  const matriculados = statusData.find(s => s._id === 'Matriculado')?.count || 0;
  const emNegociacao = statusData.find(s => s._id === 'Em negociação')?.count || 0;
  const novos = statusData.find(s => s._id === 'Novo')?.count || 0;

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2" data-testid="coordenador-dashboard-title">
          Dashboard Geral
        </h1>
        <p className="text-gray-600 dark:text-gray-400">Visão completa dos leads e desempenho</p>
      </div>

      {/* Cards de estatísticas */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="card-hover gradient-bg text-white" data-testid="total-leads-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-white/90">Total de Leads</CardTitle>
            <Users className="w-5 h-5" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{totalLeads}</div>
            <p className="text-xs text-white/80 mt-1">No sistema</p>
          </CardContent>
        </Card>

        <Card className="card-hover bg-green-600 text-white" data-testid="matriculados-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-white/90">Matriculados</CardTitle>
            <CheckCircle className="w-5 h-5" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{matriculados}</div>
            <p className="text-xs text-white/80 mt-1">
              Taxa: {totalLeads > 0 ? ((matriculados / totalLeads) * 100).toFixed(1) : 0}%
            </p>
          </CardContent>
        </Card>

        <Card className="card-hover gradient-orange text-white" data-testid="em-negociacao-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-white/90">Em Negociação</CardTitle>
            <Clock className="w-5 h-5" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{emNegociacao}</div>
            <p className="text-xs text-white/80 mt-1">Requer acompanhamento</p>
          </CardContent>
        </Card>

        <Card className="card-hover" data-testid="novos-leads-card">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 dark:text-gray-400">Novos Leads</CardTitle>
            <TrendingUp className="w-5 h-5 text-blue-600" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-900 dark:text-white">{novos}</div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Aguardando contato</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Leads por Curso */}
        <Card data-testid="leads-por-curso-chart">
          <CardHeader>
            <CardTitle>Leads por Curso (Top 5)</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={cursoData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="_id" angle={-45} textAnchor="end" height={100} fontSize={12} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="count" fill="#2563EB" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Distribuição por Status */}
        <Card data-testid="distribuicao-status-chart">
          <CardHeader>
            <CardTitle>Distribuição por Status</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={statusData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => `${entry._id}: ${entry.count}`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {statusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Ranking de Vendedores */}
      <Card data-testid="ranking-vendedores-card">
        <CardHeader>
          <CardTitle>Ranking dos Vendedores</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {vendedorRanking.map((vendedor, index) => {
              const taxaConversao = vendedor.total_leads > 0 
                ? ((vendedor.matriculados / vendedor.total_leads) * 100).toFixed(1)
                : 0;

              return (
                <div
                  key={vendedor._id}
                  className="flex items-center gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
                  data-testid={`vendedor-rank-${index + 1}`}
                >
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-600 to-blue-400 flex items-center justify-center text-white font-bold text-lg">
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <p className="font-semibold text-gray-900 dark:text-white">{vendedor.vendedor_nome}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {vendedor.total_leads} leads • {vendedor.matriculados} matriculados
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-blue-600">{taxaConversao}%</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Taxa de conversão</p>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Evolução de Leads por Mês */}
      <Card data-testid="evolucao-mensal-chart">
        <CardHeader>
          <CardTitle>Evolução de Leads por Mês</CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={monthlyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="_id" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="count" stroke="#2563EB" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}