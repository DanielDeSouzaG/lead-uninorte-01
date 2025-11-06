# Sistema de Gestão de Leads UNINORTE - Guia de Acesso ao Banco de Dados

## Informações do Banco de Dados

O sistema utiliza **MongoDB** como banco de dados, que está rodando localmente no container.

### Credenciais de Conexão

```
URL de Conexão: mongodb://localhost:27017
Nome do Banco: test_database
```

## Como Acessar o Banco de Dados

### Opção 1: Via Terminal (Mongo Shell)

1. **Conectar ao MongoDB via terminal:**
```bash
mongosh mongodb://localhost:27017
```

2. **Selecionar o banco de dados:**
```javascript
use test_database
```

3. **Visualizar todas as coleções:**
```javascript
show collections
```

4. **Consultar dados de uma coleção:**
```javascript
// Ver todos os usuários
db.users.find().pretty()

// Ver todos os leads
db.leads.find().pretty()

// Ver todos os cursos
db.courses.find().pretty()

// Ver status disponíveis
db.lead_status.find().pretty()

// Ver logs de auditoria
db.audit_logs.find().pretty()
```

### Opção 2: Via Python (Motor/PyMongo)

```python
from motor.motor_asyncio import AsyncIOMotorClient

# Conectar ao MongoDB
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client["test_database"]

# Exemplo: Buscar todos os leads
async def get_all_leads():
    leads = await db.leads.find({}, {"_id": 0}).to_list(1000)
    return leads
```

### Opção 3: Via Ferramenta GUI (MongoDB Compass)

Se você tiver o MongoDB Compass instalado:

1. Abra o MongoDB Compass
2. Use a string de conexão: `mongodb://localhost:27017`
3. Navegue até o banco `test_database`
4. Explore as coleções visualmente

## Estrutura das Coleções

### 1. **users** - Usuários do Sistema
```json
{
  "id": "uuid",
  "email": "usuario@email.com",
  "nome": "Nome do Usuário",
  "tipo": "vendedor|coordenador|administrador",
  "senha_hash": "hash_bcrypt",
  "ativo": true,
  "criado_em": "2025-11-03T..."
}
```

### 2. **leads** - Leads Cadastrados
```json
{
  "id": "uuid",
  "nome_completo": "Nome do Lead",
  "telefone": "(84) 98765-4321",
  "curso": "Nome do Curso",
  "status": "Novo|Em negociação|Matriculado|Não tem interesse",
  "vendedor_id": "uuid_do_vendedor",
  "vendedor_nome": "Nome do Vendedor",
  "criado_em": "2025-11-03T...",
  "atualizado_em": "2025-11-03T..."
}
```

### 3. **courses** - Cursos Disponíveis
```json
{
  "id": "uuid",
  "nome": "Engenharia da Computação",
  "ativo": true
}
```

### 4. **lead_status** - Status dos Leads
```json
{
  "id": "uuid",
  "nome": "Matriculado",
  "cor": "#10B981"
}
```

### 5. **audit_logs** - Logs de Auditoria
```json
{
  "id": "uuid",
  "usuario_id": "uuid",
  "usuario_nome": "Nome do Usuário",
  "acao": "CREATE|UPDATE|DELETE|BACKUP",
  "entidade": "lead|user|course|...",
  "entidade_id": "uuid",
  "detalhes": "Descrição da ação",
  "criado_em": "2025-11-03T..."
}
```

## Consultas Úteis

### Buscar usuários por tipo
```javascript
db.users.find({ tipo: "vendedor" })
```

### Buscar leads por status
```javascript
db.leads.find({ status: "Matriculado" })
```

### Contar leads por vendedor
```javascript
db.leads.aggregate([
  { $group: { _id: "$vendedor_id", total: { $sum: 1 } } }
])
```

### Buscar leads criados hoje
```javascript
db.leads.find({ 
  criado_em: { 
    $gte: new Date().toISOString().split('T')[0] 
  } 
})
```

### Ver últimos logs de auditoria
```javascript
db.audit_logs.find().sort({ criado_em: -1 }).limit(10)
```

## Comandos de Administração

### Backup do Banco
```bash
mongodump --uri="mongodb://localhost:27017" --db=test_database --out=/backup/
```

### Restaurar Backup
```bash
mongorestore --uri="mongodb://localhost:27017" --db=test_database /backup/test_database
```

### Verificar tamanho do banco
```javascript
db.stats()
```

### Limpar uma coleção
```javascript
db.nome_da_colecao.deleteMany({})
```

## Notas Importantes

1. **Backup**: O sistema oferece backup via interface (Admin > Configurações > Backup), que exporta os dados em Excel.

2. **Índices**: Para melhor performance em produção, considere criar índices:
```javascript
db.leads.createIndex({ vendedor_id: 1 })
db.leads.createIndex({ status: 1 })
db.leads.createIndex({ criado_em: -1 })
```

3. **Variáveis de Ambiente**: As configurações do banco estão em `/app/backend/.env`:
```
MONGO_URL="mongodb://localhost:27017"
DB_NAME="test_database"
```

## Suporte

Se precisar de ajuda adicional com o banco de dados, verifique:
- Logs do MongoDB: `sudo supervisorctl tail mongodb`
- Status dos serviços: `sudo supervisorctl status`
- Documentação oficial: https://www.mongodb.com/docs/

---

**Sistema de Gestão de Leads UNINORTE** - Desenvolvido com FastAPI + React + MongoDB
