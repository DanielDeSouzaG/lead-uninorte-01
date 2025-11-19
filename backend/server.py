# Importação de bibliotecas necessárias para o funcionamento do sistema
from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
from io import BytesIO
import pandas as pd
from openpyxl import Workbook
from fastapi.responses import StreamingResponse

# Configuração do diretório raiz do projeto
ROOT_DIR = Path(__file__).parent
# Carrega variáveis de ambiente do arquivo .env
load_dotenv(ROOT_DIR / '.env')

# Configuração da conexão com o MongoDB
# MONGO_URL deve estar definida no arquivo .env (ex: mongodb://localhost:27017)
mongo_url = os.environ['MONGO_URL']
# Cria cliente assíncrono para MongoDB
client = AsyncIOMotorClient(mongo_url)
# Seleciona o banco de dados a ser usado
db = client[os.environ['DB_NAME']]

# Configurações JWT para autenticação
# Chave secreta para assinatura dos tokens JWT
SECRET_KEY = os.environ.get('JWT_SECRET', 'uninorte-secret-key-2025')
# Algoritmo de criptografia para JWT
ALGORITHM = "HS256"
# Tempo de expiração do token em minutos (8 horas)
ACCESS_TOKEN_EXPIRE_MINUTES = 480

# Sistema de segurança para autenticação Bearer Token
security = HTTPBearer()

# Cria instância principal do FastAPI
app = FastAPI()
# Cria roteador para agrupar endpoints com prefixo /api
api_router = APIRouter(prefix="/api")

# ==================== MODELOS PYDANTIC PARA VALIDAÇÃO DE DADOS ====================

# Modelo base para usuário contendo campos essenciais
class UserBase(BaseModel):
    email: EmailStr  # Email com validação automática de formato
    nome: str        # Nome completo do usuário
    tipo: str        # Tipo de usuário: "vendedor", "coordenador", "administrador"

# Modelo para criação de usuário, herda de UserBase e adiciona campo senha
class UserCreate(UserBase):
    senha: str  # Senha em texto puro (será hasheada antes de salvar)

# Modelo completo de usuário para respostas da API
class User(UserBase):
    # Configuração para ignorar campos extras não definidos no modelo
    model_config = ConfigDict(extra="ignore")
    # ID único gerado automaticamente usando UUID
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    # Status do usuário (ativo/inativo)
    ativo: bool = True
    # Data e hora de criação em UTC
    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Modelo para requisição de login
class UserLogin(BaseModel):
    email: EmailStr  # Email do usuário
    senha: str       # Senha do usuário

# Modelo para resposta de autenticação
class Token(BaseModel):
    access_token: str    # Token JWT para autenticação
    token_type: str      # Tipo do token (sempre "bearer")
    user: Dict[str, Any] # Dados do usuário autenticado

# Modelo base para Lead (potencial aluno)
class LeadBase(BaseModel):
    nome_completo: str  # Nome completo do lead
    telefone: str       # Telefone para contato
    curso: str          # Curso de interesse

# Modelo para criação de lead (herda todos os campos do LeadBase)
class LeadCreate(LeadBase):
    pass  # Não adiciona campos novos, apenas herda

# Modelo para atualização parcial de lead (todos os campos são opcionais)
class LeadUpdate(BaseModel):
    status: Optional[str] = None        # Novo status do lead
    nome_completo: Optional[str] = None # Novo nome (se necessário alterar)
    telefone: Optional[str] = None      # Novo telefone
    curso: Optional[str] = None         # Novo curso de interesse

# Modelo completo de Lead para respostas da API
class Lead(LeadBase):
    # Ignora campos extras não definidos
    model_config = ConfigDict(extra="ignore")
    # ID único do lead
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    # Status atual do lead, padrão é "Novo"
    status: str = "Novo"
    # ID do vendedor responsável pelo lead
    vendedor_id: str
    # Nome do vendedor (duplicado para evitar joins)
    vendedor_nome: str
    # Data de criação do lead
    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    # Data da última atualização
    atualizado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Modelo para cursos oferecidos
class Course(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # ID único
    nome: str                                                   # Nome do curso
    ativo: bool = True                                          # Curso ativo ou não

# Modelo para status possíveis de leads
class LeadStatusModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # ID único
    nome: str                                                   # Nome do status
    cor: str                                                    # Cor para exibição no frontend

# Modelo para registro de logs de auditoria
class AuditLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # ID único
    usuario_id: str              # ID do usuário que realizou a ação
    usuario_nome: str            # Nome do usuário
    acao: str                    # Tipo de ação (CREATE, UPDATE, DELETE, etc.)
    entidade: str                # Entidade afetada (lead, user, course)
    entidade_id: str             # ID da entidade afetada
    detalhes: Optional[str] = None  # Detalhes adicionais da ação
    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))  # Data/hora

# ==================== FUNÇÕES AUXILIARES ====================

# Função para criar hash de senha usando bcrypt
def hash_password(password: str) -> str:
    # Gera salt e cria hash da senha, depois decodifica para string
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Função para verificar se senha plain text corresponde ao hash
def verify_password(plain_password: str, hashed_password: str) -> bool:
    # Compara senha plain text com hash usando bcrypt
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# Função para criar token JWT de acesso
def create_access_token(data: dict) -> str:
    # Cria cópia dos dados para não modificar o original
    to_encode = data.copy()
    # Calcula data de expiração (agora + 8 horas)
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # Adiciona campo de expiração aos dados
    to_encode.update({"exp": expire})
    # Codifica os dados em token JWT usando a chave secreta
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Dependency do FastAPI para obter usuário atual a partir do token JWT
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    try:
        # Extrai token das credenciais
        token = credentials.credentials
        # Decodifica token JWT usando chave secreta
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Obtém user_id do payload (campo "sub")
        user_id: str = payload.get("sub")
        # Se não tem user_id, token é inválido
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        
        # Busca usuário no banco de dados pelo ID
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        # Se usuário não encontrado, retorna erro
        if user is None:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        # Retorna dados do usuário
        return user
    # Trata erro de token expirado
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    # Trata outros erros JWT
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

# Função para registrar ações no log de auditoria
async def log_audit(usuario_id: str, usuario_nome: str, acao: str, entidade: str, entidade_id: str, detalhes: Optional[str] = None):
    # Cria objeto AuditLog com dados da ação
    audit = AuditLog(
        usuario_id=usuario_id,
        usuario_nome=usuario_nome,
        acao=acao,
        entidade=entidade,
        entidade_id=entidade_id,
        detalhes=detalhes
    )
    # Converte modelo para dicionário
    doc = audit.model_dump()
    # Converte datetime para string ISO para MongoDB
    doc['criado_em'] = doc['criado_em'].isoformat()
    # Insere registro no banco de dados
    await db.audit_logs.insert_one(doc)

# ==================== ENDPOINTS DE AUTENTICAÇÃO ====================

# Endpoint para login de usuário
@api_router.post("/auth/login", response_model=Token)
async def login(user_login: UserLogin):
    # Busca usuário no banco pelo email
    user = await db.users.find_one({"email": user_login.email}, {"_id": 0})
    # Verifica se usuário existe e se senha está correta
    if not user or not verify_password(user_login.senha, user['senha_hash']):
        # Retorna erro genérico para não revelar se email existe
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    
    # Verifica se usuário está ativo
    if not user.get('ativo', True):
        raise HTTPException(status_code=403, detail="Usuário desativado")
    
    # Cria token JWT com ID e tipo do usuário
    access_token = create_access_token(data={"sub": user['id'], "tipo": user['tipo']})
    
    # Remove campo senha_hash dos dados do usuário para resposta
    user_data = {k: v for k, v in user.items() if k not in ['senha_hash']}
    
    # Retorna token e dados do usuário
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_data
    }

# Endpoint para obter dados do usuário logado
@api_router.get("/auth/me")
async def get_me(current_user: Dict = Depends(get_current_user)):
    # Retorna dados do usuário atual, excluindo senha_hash
    return {k: v for k, v in current_user.items() if k != 'senha_hash'}

# ==================== ENDPOINTS DE LEADS ====================

# Endpoint para criar novo lead
@api_router.post("/leads", response_model=Lead)
async def create_lead(lead_data: LeadCreate, current_user: Dict = Depends(get_current_user)):
    # Verifica se usuário tem permissão de vendedor
    if current_user['tipo'] != 'vendedor':
        raise HTTPException(status_code=403, detail="Apenas vendedores podem criar leads")
    
    # Cria objeto Lead com dados fornecidos e informações do vendedor
    lead = Lead(
        **lead_data.model_dump(),          # Dados do lead (nome, telefone, curso)
        vendedor_id=current_user['id'],    # ID do vendedor logado
        vendedor_nome=current_user['nome'] # Nome do vendedor logado
    )
    
    # Converte modelo para dicionário
    doc = lead.model_dump()
    # Converte datas para string ISO
    doc['criado_em'] = doc['criado_em'].isoformat()
    doc['atualizado_em'] = doc['atualizado_em'].isoformat()
    
    # Insere lead no banco de dados
    await db.leads.insert_one(doc)
    # Registra ação no log de auditoria
    await log_audit(current_user['id'], current_user['nome'], 'CREATE', 'lead', lead.id, f"Lead criado: {lead.nome_completo}")
    
    # Retorna lead criado
    return lead

# Endpoint para listar leads do vendedor logado
@api_router.get("/leads/my", response_model=List[Lead])
async def get_my_leads(current_user: Dict = Depends(get_current_user)):
    # Verifica se usuário é vendedor
    if current_user['tipo'] != 'vendedor':
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Busca leads do vendedor atual (limite de 1000 registros)
    leads = await db.leads.find({"vendedor_id": current_user['id']}, {"_id": 0}).to_list(1000)
    
    # Converte strings de data para objetos datetime
    for lead in leads:
        if isinstance(lead.get('criado_em'), str):
            lead['criado_em'] = datetime.fromisoformat(lead['criado_em'])
        if isinstance(lead.get('atualizado_em'), str):
            lead['atualizado_em'] = datetime.fromisoformat(lead['atualizado_em'])
    
    # Retorna lista de leads
    return leads

# Endpoint para estatísticas de leads do vendedor
@api_router.get("/leads/stats")
async def get_leads_stats(current_user: Dict = Depends(get_current_user)):
    # Verifica se usuário é vendedor
    if current_user['tipo'] != 'vendedor':
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Conta total de leads do vendedor
    total = await db.leads.count_documents({"vendedor_id": current_user['id']})
    
    # Pipeline de agregação para contar leads por mês
    pipeline = [
        # Filtra apenas leads do vendedor atual
        {"$match": {"vendedor_id": current_user['id']}},
        # Agrupa por mês (primeiros 7 caracteres da data: YYYY-MM)
        {"$group": {
            "_id": {"$substr": ["$criado_em", 0, 7]},
            "count": {"$sum": 1}  # Conta quantidade
        }},
        # Ordena por mês decrescente (mais recente primeiro)
        {"$sort": {"_id": -1}}
    ]
    
    # Executa agregação
    monthly_leads = await db.leads.aggregate(pipeline).to_list(12)
    
    # Retorna estatísticas
    return {
        "total": total,
        "monthly": monthly_leads
    }

# Endpoint para listar todos os leads (coordenadores e administradores)
@api_router.get("/leads", response_model=List[Lead])
async def get_all_leads(
    curso: Optional[str] = None,      # Filtro por curso
    status: Optional[str] = None,     # Filtro por status
    vendedor_id: Optional[str] = None, # Filtro por vendedor
    current_user: Dict = Depends(get_current_user)
):
    # Verifica se usuário tem permissão (coordenador ou administrador)
    if current_user['tipo'] not in ['coordenador', 'administrador']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Constrói query de filtro
    query = {}
    if curso:
        query['curso'] = curso
    if status:
        query['status'] = status
    if vendedor_id:
        query['vendedor_id'] = vendedor_id
    
    # Busca leads com filtros aplicados (limite de 5000)
    leads = await db.leads.find(query, {"_id": 0}).to_list(5000)
    
    # Converte strings de data para objetos datetime
    for lead in leads:
        if isinstance(lead.get('criado_em'), str):
            lead['criado_em'] = datetime.fromisoformat(lead['criado_em'])
        if isinstance(lead.get('atualizado_em'), str):
            lead['atualizado_em'] = datetime.fromisoformat(lead['atualizado_em'])
    
    # Retorna lista de leads
    return leads

# Endpoint para atualizar lead específico
@api_router.patch("/leads/{lead_id}")
async def update_lead(lead_id: str, lead_update: LeadUpdate, current_user: Dict = Depends(get_current_user)):
    # Verifica permissão (apenas coordenadores e administradores)
    if current_user['tipo'] not in ['coordenador', 'administrador']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Verifica se lead existe
    existing_lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    if not existing_lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    
    # Prepara dados para atualização (remove campos None)
    update_data = {k: v for k, v in lead_update.model_dump().items() if v is not None}
    # Adiciona timestamp de atualização
    update_data['atualizado_em'] = datetime.now(timezone.utc).isoformat()
    
    # Atualiza lead no banco
    await db.leads.update_one({"id": lead_id}, {"$set": update_data})
    # Registra ação no log
    await log_audit(current_user['id'], current_user['nome'], 'UPDATE', 'lead', lead_id, f"Lead atualizado")
    
    # Busca lead atualizado
    updated_lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    
    # Converte datas para objetos datetime
    if isinstance(updated_lead.get('criado_em'), str):
        updated_lead['criado_em'] = datetime.fromisoformat(updated_lead['criado_em'])
    if isinstance(updated_lead.get('atualizado_em'), str):
        updated_lead['atualizado_em'] = datetime.fromisoformat(updated_lead['atualizado_em'])
    
    # Retorna lead atualizado
    return updated_lead

# Endpoint para dados do dashboard administrativo
@api_router.get("/dashboard")
async def get_dashboard(current_user: Dict = Depends(get_current_user)):
    # Verifica permissão (coordenadores e administradores)
    if current_user['tipo'] not in ['coordenador', 'administrador']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Total de leads no sistema
    total_leads = await db.leads.count_documents({})
    
    # Pipeline para distribuição por status
    status_pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_dist = await db.leads.aggregate(status_pipeline).to_list(100)
    
    # Pipeline para top 5 cursos
    curso_pipeline = [
        {"$group": {"_id": "$curso", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},  # Ordena por quantidade decrescente
        {"$limit": 5}              # Limita aos 5 primeiros
    ]
    curso_dist = await db.leads.aggregate(curso_pipeline).to_list(5)
    
    # Pipeline para ranking de vendedores
    vendedor_pipeline = [
        {"$group": {
            "_id": "$vendedor_id",
            "vendedor_nome": {"$first": "$vendedor_nome"},  # Pega primeiro nome encontrado
            "total_leads": {"$sum": 1},                     # Total de leads
            "matriculados": {
                "$sum": {"$cond": [{"$eq": ["$status", "Matriculado"]}, 1, 0]}  # Conta matriculados
            }
        }},
        {"$sort": {"total_leads": -1}}  # Ordena por total de leads
    ]
    vendedor_ranking = await db.leads.aggregate(vendedor_pipeline).to_list(100)
    
    # Pipeline para leads por mês (evolução temporal)
    monthly_pipeline = [
        {"$group": {
            "_id": {"$substr": ["$criado_em", 0, 7]},  # Agrupa por mês (YYYY-MM)
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}  # Ordena cronologicamente
    ]
    monthly_leads = await db.leads.aggregate(monthly_pipeline).to_list(12)
    
    # Retorna todos os dados do dashboard
    return {
        "total_leads": total_leads,
        "status_distribution": status_dist,
        "curso_distribution": curso_dist,
        "vendedor_ranking": vendedor_ranking,
        "monthly_leads": monthly_leads
    }

# Endpoint para exportar leads em diferentes formatos
@api_router.get("/reports/export/{format}")
async def export_leads(
    format: str,                    # Formato de exportação: "csv" ou "excel"
    curso: Optional[str] = None,    # Filtro por curso
    status: Optional[str] = None,   # Filtro por status
    vendedor_id: Optional[str] = None, # Filtro por vendedor
    current_user: Dict = Depends(get_current_user)
):
    # Verifica permissão (coordenadores e administradores)
    if current_user['tipo'] not in ['coordenador', 'administrador']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Constrói query com filtros
    query = {}
    if curso:
        query['curso'] = curso
    if status:
        query['status'] = status
    if vendedor_id:
        query['vendedor_id'] = vendedor_id
    
    # Busca leads com filtros (limite alto para exportação)
    leads = await db.leads.find(query, {"_id": 0}).to_list(10000)
    
    # Verifica se existem leads para exportar
    if not leads:
        raise HTTPException(status_code=404, detail="Nenhum lead encontrado")
    
    # Converte lista de dicionários para DataFrame do pandas
    df = pd.DataFrame(leads)
    
    # Exportação para CSV
    if format == "csv":
        output = BytesIO()  # Cria buffer em memória
        # Exporta DataFrame para CSV com encoding UTF-8 BOM (compatível com Excel)
        df.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)  # Volta para início do buffer
        # Retorna StreamingResponse para download
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=leads.csv"}
        )
    
    # Exportação para Excel
    elif format == "excel":
        output = BytesIO()
        # Cria arquivo Excel usando openpyxl como engine
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Exporta DataFrame para planilha Excel
            df.to_excel(writer, index=False, sheet_name='Leads')
        output.seek(0)
        # Retorna StreamingResponse para download
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=leads.xlsx"}
        )
    
    # Formato não suportado
    else:
        raise HTTPException(status_code=400, detail="Formato não suportado")

# ==================== GERENCIAMENTO DE USUÁRIOS (APENAS ADMIN) ====================

# Endpoint para listar todos os usuários
@api_router.get("/users", response_model=List[User])
async def get_users(current_user: Dict = Depends(get_current_user)):
    # Verifica se usuário é administrador
    if current_user['tipo'] != 'administrador':
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Busca todos os usuários, excluindo _id do MongoDB e senha_hash
    users = await db.users.find({}, {"_id": 0, "senha_hash": 0}).to_list(1000)
    
    # Converte strings de data para objetos datetime
    for user in users:
        if isinstance(user.get('criado_em'), str):
            user['criado_em'] = datetime.fromisoformat(user['criado_em'])
    
    # Retorna lista de usuários
    return users

# Endpoint para criar novo usuário
@api_router.post("/users", response_model=User)
async def create_user(user_data: UserCreate, current_user: Dict = Depends(get_current_user)):
    # Verifica se usuário é administrador
    if current_user['tipo'] != 'administrador':
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Verifica se email já está cadastrado
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    # Cria hash da senha fornecida
    senha_hash = hash_password(user_data.senha)
    # Cria objeto User com dados fornecidos
    user = User(
        email=user_data.email,
        nome=user_data.nome,
        tipo=user_data.tipo
    )
    
    # Converte modelo para dicionário
    doc = user.model_dump()
    # Adiciona hash da senha ao documento
    doc['senha_hash'] = senha_hash
    # Converte data para string ISO
    doc['criado_em'] = doc['criado_em'].isoformat()
    
    # Insere usuário no banco
    await db.users.insert_one(doc)
    # Registra ação no log de auditoria
    await log_audit(current_user['id'], current_user['nome'], 'CREATE', 'user', user.id, f"Usuário criado: {user.email}")
    
    # Retorna usuário criado
    return user

# Endpoint para atualizar usuário existente
@api_router.patch("/users/{user_id}")
async def update_user(user_id: str, updates: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    # Verifica se usuário é administrador
    if current_user['tipo'] != 'administrador':
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Verifica se usuário existe
    existing = await db.users.find_one({"id": user_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Se a atualização inclui senha, cria hash e remove campo original
    if 'senha' in updates:
        updates['senha_hash'] = hash_password(updates.pop('senha'))
    
    # Atualiza usuário no banco
    await db.users.update_one({"id": user_id}, {"$set": updates})
    # Registra ação no log
    await log_audit(current_user['id'], current_user['nome'], 'UPDATE', 'user', user_id, f"Usuário atualizado")
    
    # Busca usuário atualizado (excluindo senha_hash)
    updated_user = await db.users.find_one({"id": user_id}, {"_id": 0, "senha_hash": 0})
    
    # Converte data de criação para objeto datetime
    if isinstance(updated_user.get('criado_em'), str):
        updated_user['criado_em'] = datetime.fromisoformat(updated_user['criado_em'])
    
    # Retorna usuário atualizado
    return updated_user

# ==================== GERENCIAMENTO DE CURSOS ====================

# Endpoint para listar cursos ativos
@api_router.get("/courses", response_model=List[Course])
async def get_courses():
    # Busca cursos ativos no banco (acesso público)
    courses = await db.courses.find({"ativo": True}, {"_id": 0}).to_list(100)
    return courses

# Endpoint para criar novo curso
@api_router.post("/courses", response_model=Course)
async def create_course(course: Course, current_user: Dict = Depends(get_current_user)):
    # Verifica se usuário é administrador
    if current_user['tipo'] != 'administrador':
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Converte modelo para dicionário
    doc = course.model_dump()
    # Insere curso no banco
    await db.courses.insert_one(doc)
    # Registra ação no log
    await log_audit(current_user['id'], current_user['nome'], 'CREATE', 'course', course.id, f"Curso criado: {course.nome}")
    
    # Retorna curso criado
    return course

# ==================== GERENCIAMENTO DE STATUS DE LEADS ====================

# Endpoint para listar status de leads disponíveis
@api_router.get("/lead-status", response_model=List[LeadStatusModel])
async def get_lead_status():
    # Busca todos os status no banco (acesso público)
    statuses = await db.lead_status.find({}, {"_id": 0}).to_list(100)
    return statuses

# Endpoint para criar novo status de lead
@api_router.post("/lead-status", response_model=LeadStatusModel)
async def create_lead_status(lead_status: LeadStatusModel, current_user: Dict = Depends(get_current_user)):
    # Verifica se usuário é administrador
    if current_user['tipo'] != 'administrador':
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Converte modelo para dicionário
    doc = lead_status.model_dump()
    # Insere status no banco
    await db.lead_status.insert_one(doc)
    # Registra ação no log
    await log_audit(current_user['id'], current_user['nome'], 'CREATE', 'lead_status', lead_status.id, f"Status criado: {lead_status.nome}")
    
    # Retorna status criado
    return lead_status

# ==================== LOGS DE AUDITORIA ====================

# Endpoint para listar logs de auditoria
@api_router.get("/audit-logs", response_model=List[AuditLog])
async def get_audit_logs(
    limit: int = 100,  # Limite de registros (padrão 100)
    current_user: Dict = Depends(get_current_user)
):
    # Verifica se usuário é administrador
    if current_user['tipo'] != 'administrador':
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Busca logs ordenados por data decrescente (mais recentes primeiro)
    logs = await db.audit_logs.find({}, {"_id": 0}).sort("criado_em", -1).to_list(limit)
    
    # Converte strings de data para objetos datetime
    for log in logs:
        if isinstance(log.get('criado_em'), str):
            log['criado_em'] = datetime.fromisoformat(log['criado_em'])
    
    # Retorna lista de logs
    return logs

# ==================== CONFIGURAÇÃO DO SISTEMA ====================

# Endpoint para backup completo do sistema
@api_router.get("/system/backup")
async def backup_system(current_user: Dict = Depends(get_current_user)):
    # Verifica se usuário é administrador
    if current_user['tipo'] != 'administrador':
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Exporta todos os dados principais do sistema
    
    # Usuários (excluindo senhas hash)
    users = await db.users.find({}, {"_id": 0, "senha_hash": 0}).to_list(10000)
    # Todos os leads
    leads = await db.leads.find({}, {"_id": 0}).to_list(10000)
    # Todos os cursos
    courses = await db.courses.find({}, {"_id": 0}).to_list(10000)
    # Todos os status de leads
    statuses = await db.lead_status.find({}, {"_id": 0}).to_list(10000)
    
    # Cria buffer em memória para o arquivo Excel
    output = BytesIO()
    # Cria arquivo Excel com múltiplas abas
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Aba de usuários
        pd.DataFrame(users).to_excel(writer, index=False, sheet_name='Usuários')
        # Aba de leads
        pd.DataFrame(leads).to_excel(writer, index=False, sheet_name='Leads')
        # Aba de cursos
        pd.DataFrame(courses).to_excel(writer, index=False, sheet_name='Cursos')
        # Aba de status
        pd.DataFrame(statuses).to_excel(writer, index=False, sheet_name='Status')
    
    # Volta para início do buffer
    output.seek(0)
    
    # Registra ação de backup no log de auditoria
    await log_audit(current_user['id'], current_user['nome'], 'BACKUP', 'system', 'full', 'Backup completo realizado')
    
    # Retorna arquivo Excel para download
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=backup_uninorte.xlsx"}
    )

# ==================== CONFIGURAÇÃO FINAL DO FASTAPI ====================

# Inclui todas as rotas do api_router no app principal
# Todas as rotas terão prefixo /api
app.include_router(api_router)

# Configura middleware CORS (Cross-Origin Resource Sharing)
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,  # Permite cookies e credenciais
    # Lista de origens permitidas (separadas por vírgula no .env)
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],     # Permite todos os métodos HTTP (GET, POST, etc.)
    allow_headers=["*"],     # Permite todos os headers
)

# Configuração do sistema de logging
logging.basicConfig(
    level=logging.INFO,  # Nível de log (INFO, DEBUG, WARNING, ERROR)
    # Formato das mensagens de log
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# Cria logger para esta aplicação
logger = logging.getLogger(__name__)

# Evento executado quando o servidor inicia
@app.on_event("startup")
async def startup_db():
    """
    Função executada na inicialização do servidor.
    Cria dados iniciais se o banco estiver vazio.
    """
    
    # ========== CRIA USUÁRIOS PADRÃO SE NÃO EXISTIREM ==========
    users_exist = await db.users.count_documents({})
    if users_exist == 0:
        # Lista de usuários demo para testes
        default_users = [
            {
                "id": str(uuid.uuid4()),
                "email": "vendedor@lead.com.br",
                "nome": "Vendedor Demo",
                "tipo": "vendedor",
                "senha_hash": hash_password("vendedor123"),
                "ativo": True,
                "criado_em": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "email": "coordenador@lead.com.br",
                "nome": "Coordenador Demo",
                "tipo": "coordenador",
                "senha_hash": hash_password("coordenador123"),
                "ativo": True,
                "criado_em": datetime.now(timezone.utc).isoformat()
            },
            {
                "id": str(uuid.uuid4()),
                "email": "adm@lead.com.br",
                "nome": "DANIEL Souza",
                "tipo": "administrador",
                "senha_hash": hash_password("adm123"),
                "ativo": True,
                "criado_em": datetime.now(timezone.utc).isoformat()
            }
        ]
        # Insere todos os usuários de uma vez
        await db.users.insert_many(default_users)
        # Log informativo
        logger.info("Usuários padrão criados")
    
    # ========== CRIA CURSOS PADRÃO SE NÃO EXISTIREM ==========
    courses_exist = await db.courses.count_documents({})
    if courses_exist == 0:
        # Lista de cursos oferecidos
        courses = [
            {"id": str(uuid.uuid4()), "nome": "Enfermagem", "ativo": True},
            {"id": str(uuid.uuid4()), "nome": "Farmácia", "ativo": True},
            {"id": str(uuid.uuid4()), "nome": "Medicina Veterinária", "ativo": True},
            {"id": str(uuid.uuid4()), "nome": "Odontologia", "ativo": True},
            {"id": str(uuid.uuid4()), "nome": "Psicologia", "ativo": True},
            {"id": str(uuid.uuid4()), "nome": "Administração – Presencial", "ativo": True},
            {"id": str(uuid.uuid4()), "nome": "Administração – Semipresencial", "ativo": True},
            {"id": str(uuid.uuid4()), "nome": "Licenciatura em História", "ativo": True},
            {"id": str(uuid.uuid4()), "nome": "Licenciatura em Letras – Língua Inglesa", "ativo": True},
            {"id": str(uuid.uuid4()), "nome": "Licenciatura em Letras – Língua Portuguesa", "ativo": True},
            {"id": str(uuid.uuid4()), "nome": "Licenciatura em Matemática", "ativo": True},
            {"id": str(uuid.uuid4()), "nome": "Pedagogia", "ativo": True},
            {"id": str(uuid.uuid4()), "nome": "Ciência de Computação", "ativo": True},
            {"id": str(uuid.uuid4()), "nome": "Engenharia da Computação", "ativo": True},
            {"id": str(uuid.uuid4()), "nome": "Engenharia Elétrica", "ativo": True},
            {"id": str(uuid.uuid4()), "nome": "Engenharia Mecânica", "ativo": True},
            {"id": str(uuid.uuid4()), "nome": "Sistema da Informação", "ativo": True},
            {"id": str(uuid.uuid4()), "nome": "Direito", "ativo": True},
        ]
        await db.courses.insert_many(courses)
        logger.info("Cursos criados")
    
    # ========== CRIA STATUS DE LEADS PADRÃO SE NÃO EXISTIREM ==========
    status_exist = await db.lead_status.count_documents({})
    if status_exist == 0:
        # Status possíveis para leads com cores para o frontend
        statuses = [
            {"id": str(uuid.uuid4()), "nome": "Novo", "cor": "#3B82F6"},        # Azul
            {"id": str(uuid.uuid4()), "nome": "Em negociação", "cor": "#F97316"}, # Laranja
            {"id": str(uuid.uuid4()), "nome": "Matriculado", "cor": "#10B981"},   # Verde
            {"id": str(uuid.uuid4()), "nome": "Não tem interesse", "cor": "#EF4444"}, # Vermelho
        ]
        await db.lead_status.insert_many(statuses)
        logger.info("Status de leads criados")
    
    # ========== CRIA LEADS DE EXEMPLO SE NÃO EXISTIREM ==========
    leads_exist = await db.leads.count_documents({})
    if leads_exist == 0:
        # Busca um vendedor para associar os leads
        vendedor = await db.users.find_one({"tipo": "vendedor"})
        if vendedor:
            # Cria 12 leads de exemplo com dados variados
            sample_leads = [
                {
                    "id": str(uuid.uuid4()),
                    "nome_completo": "Maria Silva Santos",
                    "telefone": "(84) 98765-4321",
                    "curso": "Enfermagem",
                    "status": "Novo",
                    "vendedor_id": vendedor['id'],
                    "vendedor_nome": vendedor['nome'],
                    "criado_em": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat(),
                    "atualizado_em": (datetime.now(timezone.utc) - timedelta(days=5)).isoformat()
                },
                {
                    "id": str(uuid.uuid4()),
                    "nome_completo": "João Pedro Costa",
                    "telefone": "(84) 99876-5432",
                    "curso": "Engenharia da Computação",
                    "status": "Em negociação",
                    "vendedor_id": vendedor['id'],
                    "vendedor_nome": vendedor['nome'],
                    "criado_em": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
                    "atualizado_em": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
                },
                {
                    "id": str(uuid.uuid4()),
                    "nome_completo": "Ana Carolina Oliveira",
                    "telefone": "(84) 98123-4567",
                    "curso": "Administração – Presencial",
                    "status": "Matriculado",
                    "vendedor_id": vendedor['id'],
                    "vendedor_nome": vendedor['nome'],
                    "criado_em": (datetime.now(timezone.utc) - timedelta(days=20)).isoformat(),
                    "atualizado_em": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
                },
                {
                    "id": str(uuid.uuid4()),
                    "nome_completo": "Carlos Eduardo Ferreira",
                    "telefone": "(84) 99234-5678",
                    "curso": "Direito",
                    "status": "Em negociação",
                    "vendedor_id": vendedor['id'],
                    "vendedor_nome": vendedor['nome'],
                    "criado_em": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat(),
                    "atualizado_em": (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
                },
                {
                    "id": str(uuid.uuid4()),
                    "nome_completo": "Beatriz Almeida Lima",
                    "telefone": "(84) 98345-6789",
                    "curso": "Psicologia",
                    "status": "Novo",
                    "vendedor_id": vendedor['id'],
                    "vendedor_nome": vendedor['nome'],
                    "criado_em": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat(),
                    "atualizado_em": (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
                },
                {
                    "id": str(uuid.uuid4()),
                    "nome_completo": "Lucas Henrique Souza",
                    "telefone": "(84) 99456-7890",
                    "curso": "Engenharia Elétrica",
                    "status": "Matriculado",
                    "vendedor_id": vendedor['id'],
                    "vendedor_nome": vendedor['nome'],
                    "criado_em": (datetime.now(timezone.utc) - timedelta(days=15)).isoformat(),
                    "atualizado_em": (datetime.now(timezone.utc) - timedelta(days=8)).isoformat()
                },
                {
                    "id": str(uuid.uuid4()),
                    "nome_completo": "Fernanda Rodrigues Martins",
                    "telefone": "(84) 98567-8901",
                    "curso": "Farmácia",
                    "status": "Em negociação",
                    "vendedor_id": vendedor['id'],
                    "vendedor_nome": vendedor['nome'],
                    "criado_em": (datetime.now(timezone.utc) - timedelta(days=12)).isoformat(),
                    "atualizado_em": (datetime.now(timezone.utc) - timedelta(days=4)).isoformat()
                },
                {
                    "id": str(uuid.uuid4()),
                    "nome_completo": "Rafael Gomes Pereira",
                    "telefone": "(84) 99678-9012",
                    "curso": "Ciência de Computação",
                    "status": "Novo",
                    "vendedor_id": vendedor['id'],
                    "vendedor_nome": vendedor['nome'],
                    "criado_em": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
                    "atualizado_em": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
                },
                {
                    "id": str(uuid.uuid4()),
                    "nome_completo": "Juliana Mendes Rocha",
                    "telefone": "(84) 98789-0123",
                    "curso": "Pedagogia",
                    "status": "Matriculado",
                    "vendedor_id": vendedor['id'],
                    "vendedor_nome": vendedor['nome'],
                    "criado_em": (datetime.now(timezone.utc) - timedelta(days=25)).isoformat(),
                    "atualizado_em": (datetime.now(timezone.utc) - timedelta(days=18)).isoformat()
                },
                {
                    "id": str(uuid.uuid4()),
                    "nome_completo": "Gabriel Santos Barbosa",
                    "telefone": "(84) 99890-1234",
                    "curso": "Odontologia",
                    "status": "Não tem interesse",
                    "vendedor_id": vendedor['id'],
                    "vendedor_nome": vendedor['nome'],
                    "criado_em": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
                    "atualizado_em": (datetime.now(timezone.utc) - timedelta(days=28)).isoformat()
                },
                {
                    "id": str(uuid.uuid4()),
                    "nome_completo": "Camila Freitas Castro",
                    "telefone": "(84) 98901-2345",
                    "curso": "Medicina Veterinária",
                    "status": "Em negociação",
                    "vendedor_id": vendedor['id'],
                    "vendedor_nome": vendedor['nome'],
                    "criado_em": (datetime.now(timezone.utc) - timedelta(days=8)).isoformat(),
                    "atualizado_em": (datetime.now(timezone.utc) - timedelta(days=6)).isoformat()
                },
                {
                    "id": str(uuid.uuid4()),
                    "nome_completo": "Thiago Ribeiro Lopes",
                    "telefone": "(84) 99012-3456",
                    "curso": "Licenciatura em Matemática",
                    "status": "Novo",
                    "vendedor_id": vendedor['id'],
                    "vendedor_nome": vendedor['nome'],
                    "criado_em": datetime.now(timezone.utc).isoformat(),
                    "atualizado_em": datetime.now(timezone.utc).isoformat()
                }
            ]
            # Insere todos os leads de exemplo
            await db.leads.insert_many(sample_leads)
            logger.info("Leads de exemplo criados")

# Evento executado quando o servidor é desligado
@app.on_event("shutdown")
async def shutdown_db_client():
    """Fecha a conexão com o MongoDB quando o servidor é desligado"""
    client.close()