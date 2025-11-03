import { useEffect, useState } from 'react';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { Plus, Search, Download, Filter } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const getAuthHeaders = () => ({
  headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
});

export default function LeadsPage({ userType, userId }) {
  const [leads, setLeads] = useState([]);
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingLead, setEditingLead] = useState(null);
  
  // Filtros
  const [filterCurso, setFilterCurso] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  // Form
  const [formData, setFormData] = useState({
    nome_completo: '',
    telefone: '',
    curso: '',
    status: 'Novo'
  });

  useEffect(() => {
    fetchData();
  }, [filterCurso, filterStatus]);

  const fetchData = async () => {
    try {
      const params = {};
      if (filterCurso) params.curso = filterCurso;
      if (filterStatus) params.status = filterStatus;

      const endpoint = userType === 'vendedor' ? `${API}/leads/my` : `${API}/leads`;
      const [leadsRes, coursesRes] = await Promise.all([
        axios.get(endpoint, { ...getAuthHeaders(), params }),
        axios.get(`${API}/courses`, getAuthHeaders())
      ]);
      
      setLeads(leadsRes.data);
      setCourses(coursesRes.data);
    } catch (error) {
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (userType === 'vendedor') {
        await axios.post(`${API}/leads`, formData, getAuthHeaders());
        toast.success('Lead criado com sucesso!');
      }
      setDialogOpen(false);
      setFormData({ nome_completo: '', telefone: '', curso: '', status: 'Novo' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erro ao criar lead');
    }
  };

  const handleUpdateStatus = async (leadId, newStatus) => {
    try {
      await axios.patch(`${API}/leads/${leadId}`, { status: newStatus }, getAuthHeaders());
      toast.success('Status atualizado!');
      fetchData();
    } catch (error) {
      toast.error('Erro ao atualizar status');
    }
  };

  const handleExport = async (format) => {
    try {
      const params = {};
      if (filterCurso) params.curso = filterCurso;
      if (filterStatus) params.status = filterStatus;

      const response = await axios.get(`${API}/reports/export/${format}`, {
        ...getAuthHeaders(),
        params,
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `leads.${format}`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success(`Relatório ${format.toUpperCase()} exportado!`);
    } catch (error) {
      toast.error('Erro ao exportar relatório');
    }
  };

  const filteredLeads = leads.filter(lead => {
    const matchesSearch = lead.nome_completo.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         lead.telefone.includes(searchTerm) ||
                         lead.curso.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesSearch;
  });

  if (loading) {
    return <div className="flex items-center justify-center h-64">Carregando...</div>;
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2" data-testid="leads-page-title">
            Gestão de Leads
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            {userType === 'vendedor' ? 'Seus leads cadastrados' : 'Todos os leads do sistema'}
          </p>
        </div>

        <div className="flex gap-2">
          {userType !== 'vendedor' && (
            <>
              <Button
                variant="outline"
                onClick={() => handleExport('csv')}
                data-testid="export-csv-button"
              >
                <Download className="mr-2" size={16} />
                CSV
              </Button>
              <Button
                variant="outline"
                onClick={() => handleExport('excel')}
                data-testid="export-excel-button"
              >
                <Download className="mr-2" size={16} />
                Excel
              </Button>
            </>
          )}
          
          {userType === 'vendedor' && (
            <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
              <DialogTrigger asChild>
                <Button className="gradient-bg" data-testid="create-lead-button">
                  <Plus className="mr-2" size={16} />
                  Novo Lead
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Cadastrar Novo Lead</DialogTitle>
                  <DialogDescription>Preencha os dados do lead</DialogDescription>
                </DialogHeader>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <Label htmlFor="nome_completo">Nome Completo</Label>
                    <Input
                      id="nome_completo"
                      value={formData.nome_completo}
                      onChange={(e) => setFormData({...formData, nome_completo: e.target.value})}
                      required
                      data-testid="lead-nome-input"
                    />
                  </div>
                  <div>
                    <Label htmlFor="telefone">Telefone</Label>
                    <Input
                      id="telefone"
                      value={formData.telefone}
                      onChange={(e) => setFormData({...formData, telefone: e.target.value})}
                      placeholder="(84) 98765-4321"
                      required
                      data-testid="lead-telefone-input"
                    />
                  </div>
                  <div>
                    <Label htmlFor="curso">Curso de Interesse</Label>
                    <Select
                      value={formData.curso}
                      onValueChange={(value) => setFormData({...formData, curso: value})}
                    >
                      <SelectTrigger data-testid="lead-curso-select">
                        <SelectValue placeholder="Selecione um curso" />
                      </SelectTrigger>
                      <SelectContent>
                        {courses.map(course => (
                          <SelectItem key={course.id} value={course.nome}>
                            {course.nome}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <Button type="submit" className="w-full" data-testid="submit-lead-button">
                    Cadastrar Lead
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          )}
        </div>
      </div>

      {/* Filtros */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter size={20} />
            Filtros
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <Label htmlFor="search">Buscar</Label>
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={18} />
                <Input
                  id="search"
                  placeholder="Nome, telefone ou curso..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-10"
                  data-testid="search-leads-input"
                />
              </div>
            </div>
            <div>
              <Label>Curso</Label>
              <Select value={filterCurso || "all"} onValueChange={(val) => setFilterCurso(val === "all" ? "" : val)}>
                <SelectTrigger data-testid="filter-curso-select">
                  <SelectValue placeholder="Todos os cursos" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos os cursos</SelectItem>
                  {courses.map(course => (
                    <SelectItem key={course.id} value={course.nome}>
                      {course.nome}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Status</Label>
              <Select value={filterStatus || "all"} onValueChange={(val) => setFilterStatus(val === "all" ? "" : val)}>
                <SelectTrigger data-testid="filter-status-select">
                  <SelectValue placeholder="Todos os status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">Todos os status</SelectItem>
                  <SelectItem value="Novo">Novo</SelectItem>
                  <SelectItem value="Em negociação">Em negociação</SelectItem>
                  <SelectItem value="Matriculado">Matriculado</SelectItem>
                  <SelectItem value="Não tem interesse">Não tem interesse</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Lista de Leads */}
      <Card data-testid="leads-list-card">
        <CardHeader>
          <CardTitle>Leads ({filteredLeads.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {filteredLeads.length === 0 ? (
            <p className="text-center text-gray-500 dark:text-gray-400 py-8">
              Nenhum lead encontrado
            </p>
          ) : (
            <div className="space-y-3">
              {filteredLeads.map((lead) => (
                <div
                  key={lead.id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg gap-4"
                  data-testid={`lead-item-${lead.id}`}
                >
                  <div className="flex-1">
                    <p className="font-semibold text-gray-900 dark:text-white">{lead.nome_completo}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{lead.curso}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-500">
                      {lead.telefone} • Vendedor: {lead.vendedor_nome}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    {userType !== 'vendedor' ? (
                      <Select
                        value={lead.status}
                        onValueChange={(value) => handleUpdateStatus(lead.id, value)}
                      >
                        <SelectTrigger className="w-[180px]" data-testid={`status-select-${lead.id}`}>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Novo">Novo</SelectItem>
                          <SelectItem value="Em negociação">Em negociação</SelectItem>
                          <SelectItem value="Matriculado">Matriculado</SelectItem>
                          <SelectItem value="Não tem interesse">Não tem interesse</SelectItem>
                        </SelectContent>
                      </Select>
                    ) : (
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
                    )}
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