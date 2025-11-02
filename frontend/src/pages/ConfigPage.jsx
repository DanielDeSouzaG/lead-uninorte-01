import { useEffect, useState } from 'react';
import axios from 'axios';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { toast } from 'sonner';
import { Plus, Download, Settings, BookOpen, Tag } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const getAuthHeaders = () => ({
  headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
});

export default function ConfigPage() {
  const [courses, setCourses] = useState([]);
  const [statuses, setStatuses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [courseDialogOpen, setCourseDialogOpen] = useState(false);
  const [statusDialogOpen, setStatusDialogOpen] = useState(false);
  
  const [newCourse, setNewCourse] = useState('');
  const [newStatus, setNewStatus] = useState({ nome: '', cor: '#3B82F6' });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [coursesRes, statusesRes] = await Promise.all([
        axios.get(`${API}/courses`, getAuthHeaders()),
        axios.get(`${API}/lead-status`, getAuthHeaders())
      ]);
      setCourses(coursesRes.data);
      setStatuses(statusesRes.data);
    } catch (error) {
      toast.error('Erro ao carregar dados');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCourse = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/courses`, { nome: newCourse, ativo: true }, getAuthHeaders());
      toast.success('Curso criado com sucesso!');
      setCourseDialogOpen(false);
      setNewCourse('');
      fetchData();
    } catch (error) {
      toast.error('Erro ao criar curso');
    }
  };

  const handleCreateStatus = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/lead-status`, newStatus, getAuthHeaders());
      toast.success('Status criado com sucesso!');
      setStatusDialogOpen(false);
      setNewStatus({ nome: '', cor: '#3B82F6' });
      fetchData();
    } catch (error) {
      toast.error('Erro ao criar status');
    }
  };

  const handleBackup = async () => {
    try {
      const response = await axios.get(`${API}/system/backup`, {
        ...getAuthHeaders(),
        responseType: 'blob'
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', 'backup_uninorte.xlsx');
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      toast.success('Backup gerado com sucesso!');
    } catch (error) {
      toast.error('Erro ao gerar backup');
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64">Carregando...</div>;
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2" data-testid="config-page-title">
          Configurações do Sistema
        </h1>
        <p className="text-gray-600 dark:text-gray-400">Gerencie cursos, status e backups</p>
      </div>

      {/* Backup do Sistema */}
      <Card className="border-blue-200 dark:border-blue-800" data-testid="backup-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Settings size={20} className="text-blue-600" />
            Backup do Sistema
          </CardTitle>
          <CardDescription>Exportar todos os dados do sistema</CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={handleBackup} className="gradient-bg" data-testid="backup-button">
            <Download className="mr-2" size={16} />
            Gerar Backup Completo
          </Button>
        </CardContent>
      </Card>

      {/* Gestão de Cursos */}
      <Card data-testid="courses-card">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <BookOpen size={20} className="text-blue-600" />
                Cursos Disponíveis
              </CardTitle>
              <CardDescription>Gerenciar cursos oferecidos pela instituição</CardDescription>
            </div>
            <Dialog open={courseDialogOpen} onOpenChange={setCourseDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" data-testid="add-course-button">
                  <Plus size={16} className="mr-2" />
                  Adicionar Curso
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Adicionar Novo Curso</DialogTitle>
                  <DialogDescription>Digite o nome do curso</DialogDescription>
                </DialogHeader>
                <form onSubmit={handleCreateCourse} className="space-y-4">
                  <div>
                    <Label htmlFor="course-name">Nome do Curso</Label>
                    <Input
                      id="course-name"
                      value={newCourse}
                      onChange={(e) => setNewCourse(e.target.value)}
                      placeholder="Ex: Engenharia Civil"
                      required
                      data-testid="course-name-input"
                    />
                  </div>
                  <Button type="submit" className="w-full" data-testid="submit-course-button">
                    Adicionar Curso
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {courses.map((course) => (
              <div
                key={course.id}
                className="p-3 bg-blue-50 dark:bg-blue-950 rounded-lg"
                data-testid={`course-item-${course.id}`}
              >
                <p className="text-sm font-medium text-gray-900 dark:text-white">{course.nome}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Gestão de Status */}
      <Card data-testid="status-card">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Tag size={20} className="text-orange-600" />
                Status de Leads
              </CardTitle>
              <CardDescription>Gerenciar status dos leads no sistema</CardDescription>
            </div>
            <Dialog open={statusDialogOpen} onOpenChange={setStatusDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" data-testid="add-status-button">
                  <Plus size={16} className="mr-2" />
                  Adicionar Status
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Adicionar Novo Status</DialogTitle>
                  <DialogDescription>Configure o nome e cor do status</DialogDescription>
                </DialogHeader>
                <form onSubmit={handleCreateStatus} className="space-y-4">
                  <div>
                    <Label htmlFor="status-name">Nome do Status</Label>
                    <Input
                      id="status-name"
                      value={newStatus.nome}
                      onChange={(e) => setNewStatus({...newStatus, nome: e.target.value})}
                      placeholder="Ex: Aguardando documentação"
                      required
                      data-testid="status-name-input"
                    />
                  </div>
                  <div>
                    <Label htmlFor="status-color">Cor</Label>
                    <Input
                      id="status-color"
                      type="color"
                      value={newStatus.cor}
                      onChange={(e) => setNewStatus({...newStatus, cor: e.target.value})}
                      data-testid="status-color-input"
                    />
                  </div>
                  <Button type="submit" className="w-full" data-testid="submit-status-button">
                    Adicionar Status
                  </Button>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3">
            {statuses.map((status) => (
              <div
                key={status.id}
                className="p-3 rounded-lg flex items-center gap-2"
                style={{ backgroundColor: `${status.cor}20`, borderLeft: `4px solid ${status.cor}` }}
                data-testid={`status-item-${status.id}`}
              >
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: status.cor }} />
                <p className="text-sm font-medium text-gray-900 dark:text-white">{status.nome}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}