import { useEffect, useState } from 'react';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { History, User, FileEdit } from 'lucide-react';
import { format } from 'date-fns';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const getAuthHeaders = () => ({
  headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
});

export default function AuditLogsPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    try {
      const response = await axios.get(`${API}/audit-logs?limit=200`, getAuthHeaders());
      setLogs(response.data);
    } catch (error) {
      toast.error('Erro ao carregar logs');
    } finally {
      setLoading(false);
    }
  };

  const getActionColor = (action) => {
    switch (action) {
      case 'CREATE':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'UPDATE':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'DELETE':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'BACKUP':
        return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-800 dark:text-gray-200';
    }
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64">Carregando...</div>;
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2" data-testid="audit-page-title">
          Logs de Auditoria
        </h1>
        <p className="text-gray-600 dark:text-gray-400">Histórico de ações no sistema</p>
      </div>

      <Card data-testid="audit-logs-card">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History size={20} />
            Atividades Recentes ({logs.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {logs.length === 0 ? (
            <p className="text-center text-gray-500 dark:text-gray-400 py-8">
              Nenhum log encontrado
            </p>
          ) : (
            <div className="space-y-3">
              {logs.map((log) => (
                <div
                  key={log.id}
                  className="flex items-start gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg"
                  data-testid={`audit-log-${log.id}`}
                >
                  <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center flex-shrink-0">
                    {log.acao === 'CREATE' && <FileEdit size={20} className="text-blue-600 dark:text-blue-400" />}
                    {log.acao === 'UPDATE' && <FileEdit size={20} className="text-blue-600 dark:text-blue-400" />}
                    {log.acao === 'BACKUP' && <History size={20} className="text-purple-600 dark:text-purple-400" />}
                    {!['CREATE', 'UPDATE', 'BACKUP'].includes(log.acao) && <User size={20} className="text-gray-600 dark:text-gray-400" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getActionColor(log.acao)}`}>
                        {log.acao}
                      </span>
                      <span className="text-xs text-gray-500 dark:text-gray-400">
                        {format(new Date(log.criado_em), 'dd/MM/yyyy HH:mm:ss')}
                      </span>
                    </div>
                    <p className="text-sm font-semibold text-gray-900 dark:text-white">
                      {log.usuario_nome}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {log.detalhes || `${log.acao} em ${log.entidade}`}
                    </p>
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