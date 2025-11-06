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

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Settings
SECRET_KEY = os.environ.get('JWT_SECRET', 'uninorte-secret-key-2025')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

# Security
security = HTTPBearer()

app = FastAPI()
api_router = APIRouter(prefix="/api")

# ==================== MODELS ====================
class UserBase(BaseModel):
    email: EmailStr
    nome: str
    tipo: str  # "vendedor", "coordenador", "administrador"

class UserCreate(UserBase):
    senha: str

class User(UserBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ativo: bool = True
    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserLogin(BaseModel):
    email: EmailStr
    senha: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: Dict[str, Any]

class LeadBase(BaseModel):
    nome_completo: str
    telefone: str
    curso: str

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    status: Optional[str] = None
    nome_completo: Optional[str] = None
    telefone: Optional[str] = None
    curso: Optional[str] = None

class Lead(LeadBase):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "Novo"
    vendedor_id: str
    vendedor_nome: str
    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    atualizado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Course(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome: str
    ativo: bool = True

class LeadStatusModel(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nome: str
    cor: str

class AuditLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    usuario_id: str
    usuario_nome: str
    acao: str
    entidade: str
    entidade_id: str
    detalhes: Optional[str] = None
    criado_em: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ==================== FUNÇÕES AUXILIARES ====================
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict:
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if user is None:
            raise HTTPException(status_code=401, detail="Usuário não encontrado")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

async def log_audit(usuario_id: str, usuario_nome: str, acao: str, entidade: str, entidade_id: str, detalhes: Optional[str] = None):
    audit = AuditLog(
        usuario_id=usuario_id,
        usuario_nome=usuario_nome,
        acao=acao,
        entidade=entidade,
        entidade_id=entidade_id,
        detalhes=detalhes
    )
    doc = audit.model_dump()
    doc['criado_em'] = doc['criado_em'].isoformat()
    await db.audit_logs.insert_one(doc)

# ==================== PONTO DE AUTENTICAÇÃO ====================
@api_router.post("/auth/login", response_model=Token)
async def login(user_login: UserLogin):
    user = await db.users.find_one({"email": user_login.email}, {"_id": 0})
    if not user or not verify_password(user_login.senha, user['senha_hash']):
        raise HTTPException(status_code=401, detail="Email ou senha incorretos")
    
    if not user.get('ativo', True):
        raise HTTPException(status_code=403, detail="Usuário desativado")
    
    access_token = create_access_token(data={"sub": user['id'], "tipo": user['tipo']})
    
    user_data = {k: v for k, v in user.items() if k not in ['senha_hash']}
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_data
    }

@api_router.get("/auth/me")
async def get_me(current_user: Dict = Depends(get_current_user)):
    return {k: v for k, v in current_user.items() if k != 'senha_hash'}

# ==================== LEAD AUTENTICAÇÃO ====================
@api_router.post("/leads", response_model=Lead)
async def create_lead(lead_data: LeadCreate, current_user: Dict = Depends(get_current_user)):
    if current_user['tipo'] != 'vendedor':
        raise HTTPException(status_code=403, detail="Apenas vendedores podem criar leads")
    
    lead = Lead(
        **lead_data.model_dump(),
        vendedor_id=current_user['id'],
        vendedor_nome=current_user['nome']
    )
    
    doc = lead.model_dump()
    doc['criado_em'] = doc['criado_em'].isoformat()
    doc['atualizado_em'] = doc['atualizado_em'].isoformat()
    
    await db.leads.insert_one(doc)
    await log_audit(current_user['id'], current_user['nome'], 'CREATE', 'lead', lead.id, f"Lead criado: {lead.nome_completo}")
    
    return lead

@api_router.get("/leads/my", response_model=List[Lead])
async def get_my_leads(current_user: Dict = Depends(get_current_user)):
    if current_user['tipo'] != 'vendedor':
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    leads = await db.leads.find({"vendedor_id": current_user['id']}, {"_id": 0}).to_list(1000)
    
    for lead in leads:
        if isinstance(lead.get('criado_em'), str):
            lead['criado_em'] = datetime.fromisoformat(lead['criado_em'])
        if isinstance(lead.get('atualizado_em'), str):
            lead['atualizado_em'] = datetime.fromisoformat(lead['atualizado_em'])
    
    return leads

@api_router.get("/leads/stats")
async def get_leads_stats(current_user: Dict = Depends(get_current_user)):
    if current_user['tipo'] != 'vendedor':
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Total de leads
    total = await db.leads.count_documents({"vendedor_id": current_user['id']})
    
    # Leads por mês
    pipeline = [
        {"$match": {"vendedor_id": current_user['id']}},
        {"$group": {
            "_id": {"$substr": ["$criado_em", 0, 7]},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": -1}}
    ]
    
    monthly_leads = await db.leads.aggregate(pipeline).to_list(12)
    
    return {
        "total": total,
        "monthly": monthly_leads
    }

@api_router.get("/leads", response_model=List[Lead])
async def get_all_leads(
    curso: Optional[str] = None,
    status: Optional[str] = None,
    vendedor_id: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    if current_user['tipo'] not in ['coordenador', 'administrador']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    query = {}
    if curso:
        query['curso'] = curso
    if status:
        query['status'] = status
    if vendedor_id:
        query['vendedor_id'] = vendedor_id
    
    leads = await db.leads.find(query, {"_id": 0}).to_list(5000)
    
    for lead in leads:
        if isinstance(lead.get('criado_em'), str):
            lead['criado_em'] = datetime.fromisoformat(lead['criado_em'])
        if isinstance(lead.get('atualizado_em'), str):
            lead['atualizado_em'] = datetime.fromisoformat(lead['atualizado_em'])
    
    return leads

@api_router.patch("/leads/{lead_id}")
async def update_lead(lead_id: str, lead_update: LeadUpdate, current_user: Dict = Depends(get_current_user)):
    if current_user['tipo'] not in ['coordenador', 'administrador']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    existing_lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    if not existing_lead:
        raise HTTPException(status_code=404, detail="Lead não encontrado")
    
    update_data = {k: v for k, v in lead_update.model_dump().items() if v is not None}
    update_data['atualizado_em'] = datetime.now(timezone.utc).isoformat()
    
    await db.leads.update_one({"id": lead_id}, {"$set": update_data})
    await log_audit(current_user['id'], current_user['nome'], 'UPDATE', 'lead', lead_id, f"Lead atualizado")
    
    updated_lead = await db.leads.find_one({"id": lead_id}, {"_id": 0})
    
    if isinstance(updated_lead.get('criado_em'), str):
        updated_lead['criado_em'] = datetime.fromisoformat(updated_lead['criado_em'])
    if isinstance(updated_lead.get('atualizado_em'), str):
        updated_lead['atualizado_em'] = datetime.fromisoformat(updated_lead['atualizado_em'])
    
    return updated_lead

@api_router.get("/dashboard")
async def get_dashboard(current_user: Dict = Depends(get_current_user)):
    if current_user['tipo'] not in ['coordenador', 'administrador']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    total_leads = await db.leads.count_documents({})
    
    # Status distribution
    status_pipeline = [
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_dist = await db.leads.aggregate(status_pipeline).to_list(100)
    
    # Leads por curso (top 5)
    curso_pipeline = [
        {"$group": {"_id": "$curso", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    curso_dist = await db.leads.aggregate(curso_pipeline).to_list(5)
    
    # Ranking vendedores
    vendedor_pipeline = [
        {"$group": {
            "_id": "$vendedor_id",
            "vendedor_nome": {"$first": "$vendedor_nome"},
            "total_leads": {"$sum": 1},
            "matriculados": {
                "$sum": {"$cond": [{"$eq": ["$status", "Matriculado"]}, 1, 0]}
            }
        }},
        {"$sort": {"total_leads": -1}}
    ]
    vendedor_ranking = await db.leads.aggregate(vendedor_pipeline).to_list(100)
    
    # Leads por mês
    monthly_pipeline = [
        {"$group": {
            "_id": {"$substr": ["$criado_em", 0, 7]},
            "count": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]
    monthly_leads = await db.leads.aggregate(monthly_pipeline).to_list(12)
    
    return {
        "total_leads": total_leads,
        "status_distribution": status_dist,
        "curso_distribution": curso_dist,
        "vendedor_ranking": vendedor_ranking,
        "monthly_leads": monthly_leads
    }

@api_router.get("/reports/export/{format}")
async def export_leads(
    format: str,
    curso: Optional[str] = None,
    status: Optional[str] = None,
    vendedor_id: Optional[str] = None,
    current_user: Dict = Depends(get_current_user)
):
    if current_user['tipo'] not in ['coordenador', 'administrador']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    query = {}
    if curso:
        query['curso'] = curso
    if status:
        query['status'] = status
    if vendedor_id:
        query['vendedor_id'] = vendedor_id
    
    leads = await db.leads.find(query, {"_id": 0}).to_list(10000)
    
    if not leads:
        raise HTTPException(status_code=404, detail="Nenhum lead encontrado")
    
    df = pd.DataFrame(leads)
    
    if format == "csv":
        output = BytesIO()
        df.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=leads.csv"}
        )
    elif format == "excel":
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Leads')
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=leads.xlsx"}
        )
    else:
        raise HTTPException(status_code=400, detail="Formato não suportado")

# ==================== USER MANAGEMENT (ADMIN) ====================
@api_router.get("/users", response_model=List[User])
async def get_users(current_user: Dict = Depends(get_current_user)):
    if current_user['tipo'] != 'administrador':
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    users = await db.users.find({}, {"_id": 0, "senha_hash": 0}).to_list(1000)
    
    for user in users:
        if isinstance(user.get('criado_em'), str):
            user['criado_em'] = datetime.fromisoformat(user['criado_em'])
    
    return users

@api_router.post("/users", response_model=User)
async def create_user(user_data: UserCreate, current_user: Dict = Depends(get_current_user)):
    if current_user['tipo'] != 'administrador':
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    senha_hash = hash_password(user_data.senha)
    user = User(
        email=user_data.email,
        nome=user_data.nome,
        tipo=user_data.tipo
    )
    
    doc = user.model_dump()
    doc['senha_hash'] = senha_hash
    doc['criado_em'] = doc['criado_em'].isoformat()
    
    await db.users.insert_one(doc)
    await log_audit(current_user['id'], current_user['nome'], 'CREATE', 'user', user.id, f"Usuário criado: {user.email}")
    
    return user

@api_router.patch("/users/{user_id}")
async def update_user(user_id: str, updates: Dict[str, Any], current_user: Dict = Depends(get_current_user)):
    if current_user['tipo'] != 'administrador':
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    existing = await db.users.find_one({"id": user_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    if 'senha' in updates:
        updates['senha_hash'] = hash_password(updates.pop('senha'))
    
    await db.users.update_one({"id": user_id}, {"$set": updates})
    await log_audit(current_user['id'], current_user['nome'], 'UPDATE', 'user', user_id, f"Usuário atualizado")
    
    updated_user = await db.users.find_one({"id": user_id}, {"_id": 0, "senha_hash": 0})
    
    if isinstance(updated_user.get('criado_em'), str):
        updated_user['criado_em'] = datetime.fromisoformat(updated_user['criado_em'])
    
    return updated_user

# ==================== COURSES ====================
@api_router.get("/courses", response_model=List[Course])
async def get_courses():
    courses = await db.courses.find({"ativo": True}, {"_id": 0}).to_list(100)
    return courses

@api_router.post("/courses", response_model=Course)
async def create_course(course: Course, current_user: Dict = Depends(get_current_user)):
    if current_user['tipo'] != 'administrador':
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    doc = course.model_dump()
    await db.courses.insert_one(doc)
    await log_audit(current_user['id'], current_user['nome'], 'CREATE', 'course', course.id, f"Curso criado: {course.nome}")
    
    return course

# ==================== LEAD STATUS ====================
@api_router.get("/lead-status", response_model=List[LeadStatusModel])
async def get_lead_status():
    statuses = await db.lead_status.find({}, {"_id": 0}).to_list(100)
    return statuses

@api_router.post("/lead-status", response_model=LeadStatusModel)
async def create_lead_status(lead_status: LeadStatusModel, current_user: Dict = Depends(get_current_user)):
    if current_user['tipo'] != 'administrador':
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    doc = lead_status.model_dump()
    await db.lead_status.insert_one(doc)
    await log_audit(current_user['id'], current_user['nome'], 'CREATE', 'lead_status', lead_status.id, f"Status criado: {lead_status.nome}")
    
    return lead_status

# ==================== AUDIT LOGS ====================
@api_router.get("/audit-logs", response_model=List[AuditLog])
async def get_audit_logs(
    limit: int = 100,
    current_user: Dict = Depends(get_current_user)
):
    if current_user['tipo'] != 'administrador':
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    logs = await db.audit_logs.find({}, {"_id": 0}).sort("criado_em", -1).to_list(limit)
    
    for log in logs:
        if isinstance(log.get('criado_em'), str):
            log['criado_em'] = datetime.fromisoformat(log['criado_em'])
    
    return logs

# ==================== SYSTEM CONFIG ====================
@api_router.get("/system/backup")
async def backup_system(current_user: Dict = Depends(get_current_user)):
    if current_user['tipo'] != 'administrador':
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Export all data
    users = await db.users.find({}, {"_id": 0, "senha_hash": 0}).to_list(10000)
    leads = await db.leads.find({}, {"_id": 0}).to_list(10000)
    courses = await db.courses.find({}, {"_id": 0}).to_list(10000)
    statuses = await db.lead_status.find({}, {"_id": 0}).to_list(10000)
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pd.DataFrame(users).to_excel(writer, sheet_name='Usuários', index=False)
        pd.DataFrame(leads).to_excel(writer, sheet_name='Leads', index=False)
        pd.DataFrame(courses).to_excel(writer, sheet_name='Cursos', index=False)
        pd.DataFrame(statuses).to_excel(writer, sheet_name='Status', index=False)
    
    output.seek(0)
    
    await log_audit(current_user['id'], current_user['nome'], 'BACKUP', 'system', 'full', 'Backup completo realizado')
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=backup_uninorte.xlsx"}
    )

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_db():
    # Criar usuários padrão
    users_exist = await db.users.count_documents({})
    if users_exist == 0:
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
        await db.users.insert_many(default_users)
        logger.info("Usuários padrão criados")
    
    # Criar cursos
    courses_exist = await db.courses.count_documents({})
    if courses_exist == 0:
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
    
    # Criar status de leads
    status_exist = await db.lead_status.count_documents({})
    if status_exist == 0:
        statuses = [
            {"id": str(uuid.uuid4()), "nome": "Novo", "cor": "#3B82F6"},
            {"id": str(uuid.uuid4()), "nome": "Em negociação", "cor": "#F97316"},
            {"id": str(uuid.uuid4()), "nome": "Matriculado", "cor": "#10B981"},
            {"id": str(uuid.uuid4()), "nome": "Não tem interesse", "cor": "#EF4444"},
        ]
        await db.lead_status.insert_many(statuses)
        logger.info("Status de leads criados")
    
    # Criar leads de exemplo
    leads_exist = await db.leads.count_documents({})
    if leads_exist == 0:
        vendedor = await db.users.find_one({"tipo": "vendedor"})
        if vendedor:
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
            await db.leads.insert_many(sample_leads)
            logger.info("Leads de exemplo criados")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()