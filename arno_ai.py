# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════╗
║        ARNO AI — Personal Trainer Inteligente v5.0       ║
║   Análise Corporal por Foto | Steps | Animação Pro       ║
╚══════════════════════════════════════════════════════════╝
SETUP:
    pip install customtkinter pillow
    python arno_ai.py
"""

import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
import random, json, os, hashlib, re, webbrowser, math, threading
from datetime import datetime
from PIL import Image, ImageTk, ImageFilter, ImageDraw

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ╔══════════════════════════════════════════════════════════╗
# ║                    PALETA DE CORES                       ║
# ╚══════════════════════════════════════════════════════════╝
C = {
    "bg":         "#07070a",
    "bg2":        "#0f0f14",
    "bg3":        "#16161e",
    "bg4":        "#1e1e28",
    "bg5":        "#252532",
    "bg6":        "#2e2e3e",
    "green":      "#16a34a",
    "green_d":    "#15803d",
    "green_l":    "#22c55e",
    "green_xl":   "#4ade80",
    "green_dim":  "#052e16",
    "text":       "#ffffff",
    "text_dim":   "#55556a",
    "text_mid":   "#8888a0",
    "text_soft":  "#ccccdd",
    "border":     "#1a1a26",
    "border2":    "#262636",
    "border3":    "#323248",
    "success":    "#22c55e",
    "success_bg": "#052e16",
    "error":      "#ef4444",
    "error_bg":   "#1f0a0a",
    "warning":    "#f59e0b",
    "warning_bg": "#1f1500",
    "youtube":    "#ff0000",
    "youtube_d":  "#cc0000",
    "yt_bg":      "#1a0000",
    "step_done":  "#16a34a",
    "step_active":"#22c55e",
    "step_idle":  "#2e2e3e",
}

F = {
    "mega":    ("Segoe UI", 32, "bold"),
    "title":   ("Segoe UI", 20, "bold"),
    "title2":  ("Segoe UI", 15, "bold"),
    "header":  ("Segoe UI", 12, "bold"),
    "body":    ("Segoe UI", 11),
    "body_b":  ("Segoe UI", 11, "bold"),
    "small":   ("Segoe UI", 9),
    "small_b": ("Segoe UI", 9, "bold"),
    "tiny":    ("Segoe UI", 8),
    "tiny_i":  ("Segoe UI", 8, "italic"),
    "btn":     ("Segoe UI", 12, "bold"),
    "btn_lg":  ("Segoe UI", 14, "bold"),
    "step_num":("Segoe UI", 11, "bold"),
}

# ╔══════════════════════════════════════════════════════════╗
# ║                  BANCO DE DADOS LOCAL                    ║
# ╚══════════════════════════════════════════════════════════╝
DB_FILE = "arno_users.json"

def _hash(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def _load():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE,"r",encoding="utf-8") as f: return json.load(f)
        except: pass
    return {"usuarios":{}}

def _save(db):
    with open(DB_FILE,"w",encoding="utf-8") as f: json.dump(db,f,ensure_ascii=False,indent=2)

def db_cadastrar(nome,email,senha):
    db=_load(); email=email.strip().lower()
    if not re.match(r"[^@]+@[^@]+\.[^@]+",email): return False,"E-mail inválido."
    if email in db["usuarios"]: return False,"E-mail já cadastrado."
    if len(senha)<6: return False,"Senha deve ter 6+ caracteres."
    if len(nome.strip())<2: return False,"Nome muito curto."
    db["usuarios"][email]={"nome":nome.strip(),"email":email,"senha":_hash(senha),
        "criado_em":datetime.now().strftime("%d/%m/%Y %H:%M"),"treinos":0}
    _save(db); return True,"Cadastro realizado!"

def db_login(email,senha):
    db=_load(); email=email.strip().lower()
    if email not in db["usuarios"]: return False,"E-mail não encontrado.",{}
    u=db["usuarios"][email]
    if u["senha"]!=_hash(senha): return False,"Senha incorreta.",{}
    return True,"Login realizado!",u

def db_inc(email):
    db=_load()
    if email in db["usuarios"]:
        db["usuarios"][email]["treinos"]=db["usuarios"][email].get("treinos",0)+1
        _save(db)

def db_salvar_historico(email, treino_data):
    """Salva o treino gerado no histórico do usuário (máx 30 entradas)."""
    db=_load()
    if email not in db["usuarios"]: return
    hist=db["usuarios"][email].get("historico",[])
    entrada={
        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
        "data": datetime.now().strftime("%d/%m/%Y"),
        "hora": datetime.now().strftime("%H:%M"),
        "atleta": treino_data["atleta"],
        "imc_val": treino_data["imc_val"],
        "imc_cat": treino_data["imc_cat"],
        "grupos": list(treino_data["exs"].keys()),
        "total_exercicios": sum(len(v) for v in treino_data["exs"].values()),
        "exs": treino_data["exs"],
        "div": treino_data["div"],
        "dicas": treino_data["dicas"],
        "nutri": treino_data["nutri"],
        "aquec": treino_data["aquec"],
        "along": treino_data["along"],
        "frase": treino_data["frase"],
        "aviso_imc": treino_data.get("aviso_imc", False),
    }
    hist.insert(0, entrada)       # mais recente primeiro
    db["usuarios"][email]["historico"]=hist[:30]   # limite 30
    _save(db)

def db_carregar_historico(email):
    """Retorna lista de treinos do histórico do usuário."""
    db=_load()
    if email not in db["usuarios"]: return []
    return db["usuarios"][email].get("historico",[])

def db_deletar_historico(email, entry_id):
    """Remove uma entrada específica do histórico."""
    db=_load()
    if email not in db["usuarios"]: return
    hist=db["usuarios"][email].get("historico",[])
    db["usuarios"][email]["historico"]=[h for h in hist if h.get("id")!=entry_id]
    _save(db)

def db_limpar_historico(email):
    """Apaga todo o histórico do usuário."""
    db=_load()
    if email not in db["usuarios"]: return
    db["usuarios"][email]["historico"]=[]
    _save(db)


def db_recuperar_senha(email):
    db=_load(); email=email.strip().lower()
    if email not in db["usuarios"]: return False,"E-mail nao encontrado."
    codigo=str(random.randint(100000,999999))
    db["usuarios"][email]["reset_code"]=codigo
    _save(db)
    return True, codigo

def db_redefinir_senha(email, codigo, nova_senha):
    db=_load(); email=email.strip().lower()
    if email not in db["usuarios"]: return False,"E-mail nao encontrado."
    u=db["usuarios"][email]
    if u.get("reset_code","")!=codigo: return False,"Codigo invalido."
    if len(nova_senha)<6: return False,"Senha deve ter 6+ caracteres."
    u["senha"]=_hash(nova_senha)
    u.pop("reset_code",None)
    _save(db); return True,"Senha redefinida com sucesso!"

def db_atualizar_perfil(email, novo_nome, novo_email, nova_senha=None):
    db=_load(); email=email.strip().lower()
    if email not in db["usuarios"]: return False,"Usuario nao encontrado.",None
    novo_email=novo_email.strip().lower()
    if not re.match(r"[^@]+@[^@]+\.[^@]+",novo_email): return False,"E-mail invalido.",None
    if novo_email!=email and novo_email in db["usuarios"]: return False,"E-mail ja em uso.",None
    if len(novo_nome.strip())<2: return False,"Nome muito curto.",None
    u=db["usuarios"].pop(email)
    u["nome"]=novo_nome.strip(); u["email"]=novo_email
    if nova_senha:
        if len(nova_senha)<6:
            db["usuarios"][novo_email]=u; _save(db)
            return False,"Senha deve ter 6+ caracteres.",None
        u["senha"]=_hash(nova_senha)
    db["usuarios"][novo_email]=u
    _save(db); return True,"Perfil atualizado!",u

def db_stats_usuario(email):
    hist=db_carregar_historico(email)
    if not hist: return {}
    total=len(hist); grupos_count={}; obj_count={}; local_count={}; cargas=[]
    from datetime import date as _date, timedelta
    datas=[]
    for e in hist:
        for g in e.get("grupos",[]): grupos_count[g]=grupos_count.get(g,0)+1
        obj=e.get("atleta",{}).get("objetivo","")
        if obj: obj_count[obj]=obj_count.get(obj,0)+1
        loc=e.get("atleta",{}).get("local","")
        if loc: local_count[loc]=local_count.get(loc,0)+1
        try: datas.append(datetime.strptime(e["data"],"%d/%m/%Y").date())
        except: pass
        for exs in e.get("exs",{}).values():
            for ex in exs:
                c=str(ex.get("carga",""))
                if "kg" in c:
                    try: cargas.append(float(c.replace("~","").replace("kg","").strip()))
                    except: pass
    top_grupo=max(grupos_count,key=grupos_count.get) if grupos_count else "Nenhum"
    top_obj=max(obj_count,key=obj_count.get) if obj_count else "Nenhum"
    top_local=max(local_count,key=local_count.get) if local_count else "Nenhum"
    sequencia=0
    if datas:
        datas_unicas=sorted(set(datas),reverse=True)
        hoje=_date.today()
        for i,d in enumerate(datas_unicas):
            if d==hoje-timedelta(days=i): sequencia+=1
            else: break
    return {"total":total,"top_grupo":top_grupo,"top_obj":top_obj,"top_local":top_local,
            "sequencia":sequencia,"grupos_count":grupos_count,"obj_count":obj_count,
            "carga_media":round(sum(cargas)/len(cargas),1) if cargas else 0}

# ╔══════════════════════════════════════════════════════════╗
# ║         BANCO DE EXERCÍCIOS COM LINKS DO YOUTUBE         ║
# ╚══════════════════════════════════════════════════════════╝
EXERCICIOS = {
    "Peito":{"Academia":[
        {"nome":"Supino reto com barra",            "dica":"Desça até o peito, cotovelos a 45°",         "impacto":False,"yt":"https://www.youtube.com/watch?v=rT7DgCr-3pg"},
        {"nome":"Supino inclinado com halteres",    "dica":"Banco a 30-45°, controle a descida",          "impacto":False,"yt":"https://www.youtube.com/watch?v=8iPEnn-ltC8"},
        {"nome":"Crucifixo na máquina (peck deck)", "dica":"Mantenha leve flexão nos cotovelos",           "impacto":False,"yt":"https://www.youtube.com/watch?v=Iwe6AmxVf7o"},
        {"nome":"Crossover na polia",               "dica":"Cruze as mãos na frente, contraia o peito",   "impacto":False,"yt":"https://www.youtube.com/watch?v=taI4XduLpTk"},
        {"nome":"Supino declinado com barra",       "dica":"Foco na porção inferior do peitoral",         "impacto":False,"yt":"https://www.youtube.com/watch?v=LfyQTqKMPAQ"},
        {"nome":"Fly com halteres no banco reto",   "dica":"Abra os braços em arco controlado",           "impacto":False,"yt":"https://www.youtube.com/watch?v=eozdVDA78K0"},
    ],"Casa":[
        {"nome":"Flexão de braço tradicional",  "dica":"Corpo reto como tábua, desça até o chão",     "impacto":False,"yt":"https://www.youtube.com/watch?v=IODxDxX7oi4"},
        {"nome":"Flexão com pés elevados",      "dica":"Pés no sofá para focar peitoral superior",    "impacto":False,"yt":"https://www.youtube.com/watch?v=PKGFkMf5WEQ"},
        {"nome":"Flexão diamante",              "dica":"Mãos juntas formando diamante",               "impacto":False,"yt":"https://www.youtube.com/watch?v=J0DXoz9MbC4"},
        {"nome":"Flexão aberta",                "dica":"Mãos mais afastadas que os ombros",           "impacto":False,"yt":"https://www.youtube.com/watch?v=0pkjOk0EiAk"},
        {"nome":"Flexão archer (arqueiro)",     "dica":"Desloque o peso para um lado alternando",     "impacto":False,"yt":"https://www.youtube.com/watch?v=KHm--mxBTVA"},
    ]},
    "Costas":{"Academia":[
        {"nome":"Puxada frontal na polia",           "dica":"Puxe até o queixo, aperte as escápulas",    "impacto":False,"yt":"https://www.youtube.com/watch?v=CAwf7n6Luuc"},
        {"nome":"Remada curvada com barra",          "dica":"Costas retas, puxe até o abdômen",          "impacto":False,"yt":"https://www.youtube.com/watch?v=FWJR5Ve8bnQ"},
        {"nome":"Remada unilateral com halter",      "dica":"Apoie o joelho no banco",                   "impacto":False,"yt":"https://www.youtube.com/watch?v=pYcpY20QaE8"},
        {"nome":"Puxada triangular (pegada fechada)","dica":"Foco na porção central das costas",          "impacto":False,"yt":"https://www.youtube.com/watch?v=GZbfZ033f74"},
        {"nome":"Remada na máquina",                 "dica":"Peito apoiado, contraia as escápulas",      "impacto":False,"yt":"https://www.youtube.com/watch?v=xQNrFHEMhI4"},
        {"nome":"Pullover com halter",               "dica":"Braços levemente flexionados",               "impacto":False,"yt":"https://www.youtube.com/watch?v=FK4rHbDRMpo"},
    ],"Casa":[
        {"nome":"Remada com galão de água",    "dica":"Use galões cheios, puxe até a cintura",        "impacto":False,"yt":"https://www.youtube.com/watch?v=pYcpY20QaE8"},
        {"nome":"Superman (extensão lombar)",  "dica":"Eleve braços e pernas simultaneamente",        "impacto":False,"yt":"https://www.youtube.com/watch?v=cc6UVRS7PW4"},
        {"nome":"Remada invertida na mesa",    "dica":"Deite embaixo da mesa e puxe o corpo",        "impacto":False,"yt":"https://www.youtube.com/watch?v=LbeCNUSGZ0g"},
        {"nome":"Bird dog",                    "dica":"Estenda braço e perna opostos",               "impacto":False,"yt":"https://www.youtube.com/watch?v=wiFNA3sqjCA"},
    ]},
    "Ombro":{"Academia":[
        {"nome":"Desenvolvimento com halteres", "dica":"Sente reto, empurre até extensão completa",  "impacto":False,"yt":"https://www.youtube.com/watch?v=qEwKCR5JCog"},
        {"nome":"Elevação lateral com halteres","dica":"Suba até a altura dos ombros",               "impacto":False,"yt":"https://www.youtube.com/watch?v=3VcKaXpzqRo"},
        {"nome":"Elevação frontal alternada",   "dica":"Controle a descida, sem impulso",            "impacto":False,"yt":"https://www.youtube.com/watch?v=sOiBDpFJ47M"},
        {"nome":"Face pull na polia",           "dica":"Puxe em direção ao rosto, abra os cotovelos","impacto":False,"yt":"https://www.youtube.com/watch?v=HSoHeSx4JKY"},
        {"nome":"Desenvolvimento Arnold",       "dica":"Gire os punhos durante a subida",            "impacto":False,"yt":"https://www.youtube.com/watch?v=6Z15_WdXmVw"},
    ],"Casa":[
        {"nome":"Desenvolvimento com garrafas", "dica":"Empurre acima da cabeça",                    "impacto":False,"yt":"https://www.youtube.com/watch?v=qEwKCR5JCog"},
        {"nome":"Elevação lateral com garrafas","dica":"Use garrafas cheias de água/areia",           "impacto":False,"yt":"https://www.youtube.com/watch?v=3VcKaXpzqRo"},
        {"nome":"Pike push-up",                 "dica":"Posição de V invertido, cabeça entre as mãos","impacto":False,"yt":"https://www.youtube.com/watch?v=sposDXWEB0A"},
        {"nome":"Elevação Y-T-W no chão",       "dica":"Deitado de bruços, forme letras com os braços","impacto":False,"yt":"https://www.youtube.com/watch?v=c8_EvV4bDMY"},
    ]},
    "Biceps":{"Academia":[
        {"nome":"Rosca direta com barra",       "dica":"Cotovelos fixos ao corpo, sem balançar",     "impacto":False,"yt":"https://www.youtube.com/watch?v=ykJmrZ5v0Oo"},
        {"nome":"Rosca alternada com halteres", "dica":"Supine o punho durante a subida",            "impacto":False,"yt":"https://www.youtube.com/watch?v=sAq_ocpRh_I"},
        {"nome":"Rosca martelo",                "dica":"Pegada neutra, trabalha braquial",           "impacto":False,"yt":"https://www.youtube.com/watch?v=TwD-YGVP4Bk"},
        {"nome":"Rosca Scott na máquina",       "dica":"Apoie os braços no suporte",                 "impacto":False,"yt":"https://www.youtube.com/watch?v=tVPChhsEr8c"},
        {"nome":"Rosca concentrada",            "dica":"Apoie o cotovelo na coxa, isole o bíceps",  "impacto":False,"yt":"https://www.youtube.com/watch?v=Jvj2wV0vOYU"},
    ],"Casa":[
        {"nome":"Rosca com galão de água",      "dica":"Segure o galão pela alça",                   "impacto":False,"yt":"https://www.youtube.com/watch?v=ykJmrZ5v0Oo"},
        {"nome":"Rosca martelo com mochila",    "dica":"Segure a alça da mochila",                   "impacto":False,"yt":"https://www.youtube.com/watch?v=TwD-YGVP4Bk"},
        {"nome":"Rosca concentrada com peso",   "dica":"Sentado, apoie o cotovelo na coxa",          "impacto":False,"yt":"https://www.youtube.com/watch?v=Jvj2wV0vOYU"},
        {"nome":"Rosca 21 com galão",           "dica":"7 baixo + 7 meio + 7 completas",             "impacto":False,"yt":"https://www.youtube.com/watch?v=wUCUBYBt-uM"},
    ]},
    "Triceps":{"Academia":[
        {"nome":"Tríceps na polia (corda)",     "dica":"Abra a corda no final, aperte o tríceps",   "impacto":False,"yt":"https://www.youtube.com/watch?v=2-LAMcpzODU"},
        {"nome":"Tríceps testa com barra EZ",   "dica":"Desça a barra até a testa, cotovelos fixos","impacto":False,"yt":"https://www.youtube.com/watch?v=d_KZxkY_0cM"},
        {"nome":"Mergulho nas paralelas",       "dica":"Incline levemente à frente, desça até 90°", "impacto":False,"yt":"https://www.youtube.com/watch?v=2z8JmcrW-As"},
        {"nome":"Tríceps francês com halter",   "dica":"Segure o halter atrás da cabeça e estenda", "impacto":False,"yt":"https://www.youtube.com/watch?v=_gsUck-7M74"},
        {"nome":"Kickback com halter",          "dica":"Inclinado, estenda o braço para trás",      "impacto":False,"yt":"https://www.youtube.com/watch?v=6SS6K3lAwZ8"},
    ],"Casa":[
        {"nome":"Mergulho no banco/cadeira",    "dica":"Mãos no banco atrás, desça controlando",    "impacto":False,"yt":"https://www.youtube.com/watch?v=0326dy_-CzM"},
        {"nome":"Flexão fechada (tríceps)",     "dica":"Mãos na largura dos ombros, cotovelos rentes","impacto":False,"yt":"https://www.youtube.com/watch?v=EOFdpDaHk2E"},
        {"nome":"Kickback com galão",           "dica":"Incline o tronco, estenda o braço",         "impacto":False,"yt":"https://www.youtube.com/watch?v=6SS6K3lAwZ8"},
        {"nome":"Extensão overhead com mochila","dica":"Segure a mochila atrás da cabeça",           "impacto":False,"yt":"https://www.youtube.com/watch?v=_gsUck-7M74"},
    ]},
    "Perna":{"Academia":[
        {"nome":"Agachamento livre com barra",  "dica":"Desça até as coxas paralelas ao chão",      "impacto":False,"yt":"https://www.youtube.com/watch?v=ultWZbUMPL8"},
        {"nome":"Leg press 45°",                "dica":"Pés na largura dos ombros, não trave joelhos","impacto":False,"yt":"https://www.youtube.com/watch?v=yZmx_Ac3880"},
        {"nome":"Cadeira extensora",            "dica":"Estenda completamente, segure 1s no topo",  "impacto":False,"yt":"https://www.youtube.com/watch?v=YyvSfVjQeL0"},
        {"nome":"Mesa flexora",                 "dica":"Controle a descida, não deixe o peso bater","impacto":False,"yt":"https://www.youtube.com/watch?v=Orxowest56U"},
        {"nome":"Agachamento búlgaro",          "dica":"Pé traseiro no banco, desça controlando",   "impacto":False,"yt":"https://www.youtube.com/watch?v=2C-uNgKwPLE"},
        {"nome":"Stiff com barra",              "dica":"Pernas levemente flexionadas",              "impacto":False,"yt":"https://www.youtube.com/watch?v=1uDiW5--rAE"},
    ],"Casa":[
        {"nome":"Agachamento livre",            "dica":"Pés na largura dos ombros, peso nos calcanhares","impacto":False,"yt":"https://www.youtube.com/watch?v=ultWZbUMPL8"},
        {"nome":"Agachamento búlgaro",          "dica":"Pé traseiro na cadeira, desça controlando", "impacto":False,"yt":"https://www.youtube.com/watch?v=2C-uNgKwPLE"},
        {"nome":"Afundo alternado",             "dica":"Passo à frente, joelho a 90°",              "impacto":False,"yt":"https://www.youtube.com/watch?v=QOVaHwm-Q6U"},
        {"nome":"Wall sit (cadeira na parede)", "dica":"Costas na parede, coxas paralelas ao chão", "impacto":False,"yt":"https://www.youtube.com/watch?v=y-wV4Venusw"},
        {"nome":"Agachamento com salto",        "dica":"Agache e exploda para cima, amorteça",      "impacto":True, "yt":"https://www.youtube.com/watch?v=CVaEhXotL7M"},
    ]},
    "Panturrilha":{"Academia":[
        {"nome":"Elevação de panturrilha no smith","dica":"Suba na ponta dos pés, segure 2s no topo","impacto":False,"yt":"https://www.youtube.com/watch?v=-M4-G8p1fCI"},
        {"nome":"Panturrilha sentado na máquina",  "dica":"Foco no sóleo, controle a descida",       "impacto":False,"yt":"https://www.youtube.com/watch?v=JbyjNymZOt0"},
        {"nome":"Panturrilha no leg press",        "dica":"Só a ponta dos pés na plataforma",        "impacto":False,"yt":"https://www.youtube.com/watch?v=ONMFuIXDNdA"},
    ],"Casa":[
        {"nome":"Elevação na ponta dos pés",    "dica":"Use um degrau para maior amplitude",        "impacto":False,"yt":"https://www.youtube.com/watch?v=-M4-G8p1fCI"},
        {"nome":"Elevação unilateral",          "dica":"Uma perna só, segure na parede",            "impacto":False,"yt":"https://www.youtube.com/watch?v=-M4-G8p1fCI"},
        {"nome":"Panturrilha com pausa",        "dica":"Suba, segure 3s, desça em 3s",              "impacto":False,"yt":"https://www.youtube.com/watch?v=-M4-G8p1fCI"},
    ]},
    "Core/Abs":{"Academia":[
        {"nome":"Prancha abdominal",            "dica":"Corpo reto, contraia abdômen e glúteos",    "impacto":False,"yt":"https://www.youtube.com/watch?v=pSHjTRCQxIw"},
        {"nome":"Elevação de pernas no apoio",  "dica":"Eleve as pernas retas até 90°",             "impacto":False,"yt":"https://www.youtube.com/watch?v=Wp4BlxcFTkE"},
        {"nome":"Rotação russa com anilha",     "dica":"Sentado, pés elevados, gire o tronco",      "impacto":False,"yt":"https://www.youtube.com/watch?v=wkD8rjkodUI"},
        {"nome":"Prancha lateral",              "dica":"Apoie no antebraço, quadril elevado",       "impacto":False,"yt":"https://www.youtube.com/watch?v=K2VljzCC16g"},
        {"nome":"Abdominal na polia alta",      "dica":"Ajoelhado, contraia o abdômen para baixo",  "impacto":False,"yt":"https://www.youtube.com/watch?v=AV5Ph6ZN3oA"},
    ],"Casa":[
        {"nome":"Prancha frontal",              "dica":"Mantenha o corpo reto, quadril não cai",    "impacto":False,"yt":"https://www.youtube.com/watch?v=pSHjTRCQxIw"},
        {"nome":"Abdominal crunch",             "dica":"Suba apenas as escápulas do chão",          "impacto":False,"yt":"https://www.youtube.com/watch?v=Xyd_fa5zoEU"},
        {"nome":"Bicicleta no ar",              "dica":"Cotovelo toca o joelho oposto",             "impacto":False,"yt":"https://www.youtube.com/watch?v=9FGilxCbdz8"},
        {"nome":"Leg raise deitado",            "dica":"Pernas retas, suba até 90° e desça",        "impacto":False,"yt":"https://www.youtube.com/watch?v=Wp4BlxcFTkE"},
    ]},
    "Gluteo":{"Academia":[
        {"nome":"Hip thrust com barra",         "dica":"Costas no banco, empurre o quadril para cima","impacto":False,"yt":"https://www.youtube.com/watch?v=xDmFkJxPzeM"},
        {"nome":"Abdução na máquina",           "dica":"Empurre as pernas para fora, segure 1s",   "impacto":False,"yt":"https://www.youtube.com/watch?v=H9-L3fWRMRM"},
        {"nome":"Kickback na polia",            "dica":"Chute para trás com a perna reta",         "impacto":False,"yt":"https://www.youtube.com/watch?v=GDdBqF55PpI"},
        {"nome":"Stiff romeno",                 "dica":"Desça a barra pela frente das pernas",      "impacto":False,"yt":"https://www.youtube.com/watch?v=1uDiW5--rAE"},
    ],"Casa":[
        {"nome":"Hip thrust no chão (ponte)",   "dica":"Costas no chão, empurre o quadril bem alto","impacto":False,"yt":"https://www.youtube.com/watch?v=xDmFkJxPzeM"},
        {"nome":"Kickback de quatro apoios",    "dica":"Chute a perna para trás e para cima",      "impacto":False,"yt":"https://www.youtube.com/watch?v=GDdBqF55PpI"},
        {"nome":"Fire hydrant",                 "dica":"De quatro, abra a perna para o lado",      "impacto":False,"yt":"https://www.youtube.com/watch?v=la7fw1yh8UA"},
        {"nome":"Ponte unilateral",             "dica":"Uma perna só no chão, outra estendida",    "impacto":False,"yt":"https://www.youtube.com/watch?v=xDmFkJxPzeM"},
    ]},
}

AQUECIMENTOS = ["Polichinelos — 1 min","Corrida estacionária — 2 min","Rotação de braços — 30s cada",
    "Agachamento sem peso — 15 reps","Jumping jacks — 1 min","Elevação de joelhos — 1 min","Mobilidade de ombros — 1 min"]
AQUEC_BAIXO  = ["Caminhada no lugar — 2 min","Rotação suave de ombros — 1 min","Rotação de tornozelos — 30s cada",
    "Agachamento parcial sem peso — 15 reps","Elevação leve de joelhos — 1 min","Alongamento de panturrilha — 30s cada"]
ALONGAMENTOS = ["Alongamento de peito na parede — 30s cada","Alongamento de quadríceps em pé — 30s cada",
    "Toque nos pés (posterior de coxa) — 30s","Alongamento de ombros (braço cruzado) — 30s cada",
    "Borboleta sentado (adutores) — 30s","Cat-cow (mobilidade de coluna) — 1 min","Criança (child's pose) — 30s"]
DICAS_OBJ = {
    "Hipertrofia (ganho de massa)":["Sobrecarga progressiva: aumente peso ou reps a cada semana","Consuma 1.6-2.2g de proteína por kg de peso corporal/dia","Durma 7-8 horas para maximizar a recuperação muscular"],
    "Emagrecimento / Definição":["Déficit calórico moderado (300-500 kcal abaixo da manutenção)","Inclua cardio HIIT 2-3x por semana nos dias de descanso","Alta ingestão de proteína para preservar massa muscular"],
    "Força máxima":["Trabalhe com cargas entre 85-95% do seu 1RM","Descanse 3-5 minutos entre séries para recuperação neural","Foque nos compostos: agachamento, supino, terra e desenvolvimento"],
    "Resistência muscular":["Use cargas leves a moderadas com muitas repetições (15-25)","Reduza o descanso entre séries para 30-60 segundos","Inclua circuitos para manter a frequência cardíaca elevada"],
    "Condicionamento físico":["Combine treino de força com cardio na mesma sessão","Varie os estímulos: corrida, bike, pular corda e funcional","Monitore sua frequência cardíaca para treinar nas zonas corretas"],
    "Reabilitação / Saúde geral":["Comece com cargas muito leves, aumente 10% por semana","Priorize amplitude de movimento e técnica perfeita","Inclua exercícios de mobilidade e equilíbrio em todas as sessões"],
}
NUTRI_OBJ = {
    "Hipertrofia (ganho de massa)":["🍗 Proteína: frango, ovos, whey, peixe — a cada 3-4h","🍚 Carboidratos: arroz, batata doce, aveia — pré e pós treino","🥑 Gorduras boas: azeite, castanhas, abacate","💧 Mínimo 3 litros de água por dia"],
    "Emagrecimento / Definição":["🥗 Vegetais e fibras para saciedade com poucas calorias","🍗 Proteína magra em TODAS as refeições","🚫 Evite açúcar refinado, refrigerantes e ultraprocessados","💧 Beba água antes das refeições"],
    "Força máxima":["🍗 Alta proteína: 2g por kg de peso corporal","🍚 Carboidratos complexos para energia nos treinos","⏰ Refeição rica em carbos 2h antes do treino","💊 Creatina 5g/dia pode auxiliar nos ganhos"],
    "Resistência muscular":["🍚 Carboidratos são seu combustível — não corte!","🍌 Frutas antes do treino para energia rápida","🍗 Proteína moderada para recuperação (1.4-1.6g/kg)","💧 Hidratação extra!"],
    "Condicionamento físico":["🍽️ Dieta balanceada: 40% carbs, 30% proteína, 30% gordura","🍎 Frutas e vegetais variados para micronutrientes","⏰ Coma 1-2h antes do treino, refeição leve após","💧 Mínimo 2.5L de água"],
    "Reabilitação / Saúde geral":["🐟 Anti-inflamatórios: peixes, cúrcuma, gengibre","🥛 Cálcio e vitamina D para saúde óssea","🥗 Antioxidantes: frutas vermelhas, vegetais coloridos","💧 Hidratação adequada"],
}
DIVISOES = {
    1:["Full Body — Todos os grupos"],
    2:["Superior: Peito, Costas, Ombros, Braços","Inferior: Pernas, Glúteos, Panturrilha, Core"],
    3:["Push: Peito, Ombros, Tríceps","Pull: Costas, Bíceps","Legs: Pernas, Glúteos, Panturrilha + Core"],
    4:["Peito + Tríceps","Costas + Bíceps","Pernas + Glúteos","Ombros + Core + Panturrilha"],
    5:["Peito","Costas","Pernas + Glúteos","Ombros + Panturrilha","Braços + Core"],
    6:["Peito + Tríceps","Costas + Bíceps","Pernas","Ombros + Core","Glúteos + Panturrilha","Full Body leve"],
    7:["Peito","Costas","Pernas","Ombros","Braços","Glúteos + Core + Panturrilha","Cardio + Mobilidade"],
}
FRASES = ["Modo monstro ativado. 🔥","Hora de superar seus limites. 💪","Cada rep te aproxima do objetivo. ⚡",
    "Foco, força e consistência. 🎯","O único treino ruim é o que não foi feito.","Consistência supera intensidade. 📈"]

# Frases do loading com emojis — exibidas em sequência durante a animação
LOADING_MSGS = [
    "Analisando sua composição corporal...",
    "Identificando grupos musculares prioritários...",
    "Calculando cargas ideais para seu perfil...",
    "Montando divisão semanal personalizada...",
    "Selecionando exercícios por objetivo...",
    "Ajustando intensidade ao seu nível...",
    "Aplicando filtro de segurança articular...",
    "Finalizando seu plano de treino...",
]

# ╔══════════════════════════════════════════════════════════╗
# ║                  LÓGICA DE TREINO                        ║
# ╚══════════════════════════════════════════════════════════╝
def calc_imc(peso,altura):
    try:
        p,a=float(peso),float(altura)/100; imc=p/(a*a)
        cat=("Abaixo do peso" if imc<18.5 else "Peso normal" if imc<25 else "Sobrepeso" if imc<30 else "Obesidade")
        return round(imc,1),cat
    except: return None,None

def _sr(obj,cond):
    cfg={"Hipertrofia (ganho de massa)":{"Iniciante (< 3 meses)":(3,"10-12"),"Iniciante avançado (3-6 meses)":(3,"10-12"),"Intermediário":(4,"8-12"),"Avançado":(4,"8-10"),"Atleta":(5,"6-10")},
         "Emagrecimento / Definição":{"Iniciante (< 3 meses)":(3,"12-15"),"Iniciante avançado (3-6 meses)":(3,"12-15"),"Intermediário":(3,"15-20"),"Avançado":(4,"12-15"),"Atleta":(4,"15-20")},
         "Força máxima":{"Iniciante (< 3 meses)":(3,"8-10"),"Iniciante avançado (3-6 meses)":(4,"6-8"),"Intermediário":(5,"4-6"),"Avançado":(5,"3-5"),"Atleta":(6,"1-5")},
         "Resistência muscular":{"Iniciante (< 3 meses)":(2,"15-20"),"Iniciante avançado (3-6 meses)":(3,"15-20"),"Intermediário":(3,"20-25"),"Avançado":(4,"20-30"),"Atleta":(4,"25-30")},
         "Condicionamento físico":{"Iniciante (< 3 meses)":(3,"12-15"),"Iniciante avançado (3-6 meses)":(3,"12-15"),"Intermediário":(3,"15-20"),"Avançado":(4,"12-15"),"Atleta":(4,"15-20")},
         "Reabilitação / Saúde geral":{"Iniciante (< 3 meses)":(2,"12-15"),"Iniciante avançado (3-6 meses)":(2,"12-15"),"Intermediário":(3,"12-15"),"Avançado":(3,"10-12"),"Atleta":(3,"10-15")}}
    return cfg.get(obj,{}).get(cond,(3,"10-12"))

def _carga(cmax,obj,cond):
    fo={"Hipertrofia (ganho de massa)":0.65,"Emagrecimento / Definição":0.45,"Força máxima":0.80,"Resistência muscular":0.35,"Condicionamento físico":0.50,"Reabilitação / Saúde geral":0.30}
    fn={"Iniciante (< 3 meses)":0.50,"Iniciante avançado (3-6 meses)":0.65,"Intermediário":0.80,"Avançado":0.95,"Atleta":1.0}
    try: return max(2,round(float(cmax)*fo.get(obj,0.5)*fn.get(cond,0.7)))
    except: return 10

def _desc(obj):
    return {"Hipertrofia (ganho de massa)":"60-90s","Emagrecimento / Definição":"30-45s","Força máxima":"2-4 min","Resistência muscular":"30-45s","Condicionamento físico":"45-60s","Reabilitação / Saúde geral":"60-90s"}.get(obj,"60s")

def _qtd(dur,n,cond):
    util=max(dur-10,10); total=max(1,util//5); perg=max(1,total//max(1,n))
    return min(perg,4 if cond in ["Avançado","Atleta"] else 3)

def gerar_dados(data):
    local,obj,cond=data["local"],data["objetivo"],data["condicionamento"]
    grupos=data["grupos"]; dur=int(data.get("duracao",60))
    iv,ic=calc_imc(data["peso"],data["altura"])
    restringir=ic in ("Sobrepeso","Obesidade")
    sr,rp=_sr(obj,cond); desc=_desc(obj); qtd=_qtd(dur,len(grupos),cond)
    exs={}
    for grupo in grupos:
        lista=EXERCICIOS.get(grupo,{}).get(local,[])
        if not lista: continue
        if restringir: lista=[e for e in lista if not e.get("impacto",False)]
        if not lista: continue
        q=min(qtd,len(lista))
        exs[grupo]=[]
        for ex in random.sample(lista,q):
            c=_carga(data["carga"],obj,cond)
            ci="Peso corporal" if local=="Casa" else f"~{max(2,c+random.randint(-3,5))} kg"
            exs[grupo].append({"nome":ex["nome"],"dica":ex["dica"],"series":sr,"reps":rp,"carga":ci,"descanso":desc,"yt":ex["yt"]})
    pool=AQUEC_BAIXO if restringir else AQUECIMENTOS
    return {"atleta":data,"imc_val":str(iv) if iv else "--","imc_cat":ic or "--","aviso_imc":restringir,
        "aquec":random.sample(pool,min(5,len(pool))),"exs":exs,
        "along":random.sample(ALONGAMENTOS,min(5,len(ALONGAMENTOS))),
        "div":DIVISOES.get(int(data["dias"]),DIVISOES[4]),
        "dicas":DICAS_OBJ.get(obj,[]),"nutri":NUTRI_OBJ.get(obj,[]),"frase":random.choice(FRASES)}

# ╔══════════════════════════════════════════════════════════╗
# ║           TELA DE LOADING ANIMADA (PRO)                  ║
# ╚══════════════════════════════════════════════════════════╝
class TelaLoading(ctk.CTkToplevel):
    """Tela de loading fullscreen animada com canvas personalizado."""

    def __init__(self, master, foto_path, on_done):
        super().__init__(master)
        self.on_done    = on_done
        self.foto_path  = foto_path
        self._running   = True
        self._angle     = 0
        self._progress  = 0.0
        self._msg_idx   = 0
        self._dots      = 0
        self._photo_img = None

        self.title("")
        self.geometry("700x580")
        self.resizable(False, False)
        self.configure(fg_color=C["bg"])
        self.grab_set()
        self.lift()
        self.overrideredirect(False)
        self.after(10, self._center)
        self._build()
        self._start_animation()

    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build(self):
        outer = ctk.CTkFrame(self, fg_color=C["bg"], corner_radius=0)
        outer.pack(fill="both", expand=True)

        # Topo com logo
        top = ctk.CTkFrame(outer, fg_color=C["bg2"], corner_radius=0, height=60)
        top.pack(fill="x")
        top.pack_propagate(False)
        ctk.CTkFrame(top, fg_color=C["green"], height=2, corner_radius=0).pack(fill="x", side="top")
        ctk.CTkLabel(top, text="⚡  ARNO AI", font=F["body_b"],
                     text_color=C["green"]).pack(side="left", padx=24, pady=18)
        ctk.CTkLabel(top, text="Analisando seu perfil...", font=F["small"],
                     text_color=C["text_dim"]).pack(side="right", padx=24)

        # Canvas central — animação
        self.canvas = tk.Canvas(outer, width=700, height=340,
                                bg=C["bg"], highlightthickness=0)
        self.canvas.pack(pady=(20, 0))

        # Foto miniatura (se tiver)
        self._load_foto_preview()

        # Mensagem de status
        self.lbl_msg = ctk.CTkLabel(outer, text=LOADING_MSGS[0],
                                    font=F["body"], text_color=C["text_soft"])
        self.lbl_msg.pack(pady=(16, 4))

        # Barra de progresso
        self.prog_bar = ctk.CTkProgressBar(outer, width=440, height=6,
                                           fg_color=C["bg3"],
                                           progress_color=C["green"],
                                           corner_radius=3)
        self.prog_bar.pack(pady=(4, 0))
        self.prog_bar.set(0)

        # Percentual
        self.lbl_pct = ctk.CTkLabel(outer, text="0%",
                                    font=F["small_b"], text_color=C["green"])
        self.lbl_pct.pack(pady=(6, 0))

    def _load_foto_preview(self):
        """Carrega a foto e exibe miniatura circular no canvas."""
        try:
            img = Image.open(self.foto_path).convert("RGBA")
            # Recorte circular
            size = 120
            img = img.resize((size, size), Image.LANCZOS)
            mask = Image.new("L", (size, size), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, size, size), fill=255)
            result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
            result.paste(img, mask=mask)
            self._photo_img = ImageTk.PhotoImage(result)
            # Desenha no canvas (centro)
            self.canvas.create_image(350, 170, image=self._photo_img)
        except Exception:
            pass

    def _start_animation(self):
        self._animate()
        # Avança progress e mensagens ao longo de 4 segundos
        total_ms = 4000
        steps = 80
        step_ms = total_ms // steps

        def advance(step=0):
            if not self._running: return
            self._progress = min(step / steps, 1.0)
            self.prog_bar.set(self._progress)
            pct = int(self._progress * 100)
            self.lbl_pct.configure(text=f"{pct}%")
            # Troca mensagem a cada ~12 steps
            idx = min(step // (steps // len(LOADING_MSGS)), len(LOADING_MSGS)-1)
            self.lbl_msg.configure(text=LOADING_MSGS[idx])
            if step < steps:
                self.after(step_ms, lambda: advance(step+1))
            else:
                # Concluído — espera 300ms e fecha
                self.after(300, self._concluir)

        self.after(200, lambda: advance(0))

    def _animate(self):
        """Desenha o spinner/scan animado no canvas."""
        if not self._running:
            return

        c = self.canvas
        c.delete("anim")

        cx, cy = 350, 170
        r_outer = 148
        r_inner = 130

        # Anel externo pulsante
        pulse = 0.5 + 0.5 * math.sin(math.radians(self._angle * 2))
        alpha_val = int(60 + 60 * pulse)
        ring_color = C["green"]

        # Arco girando (spinner)
        start = self._angle % 360
        c.create_arc(cx-r_outer, cy-r_outer, cx+r_outer, cy+r_outer,
                     start=start, extent=260,
                     outline=C["green_l"], width=3, style="arc", tags="anim")
        c.create_arc(cx-r_outer, cy-r_outer, cx+r_outer, cy+r_outer,
                     start=(start+270)%360, extent=60,
                     outline=C["green_dim"], width=2, style="arc", tags="anim")

        # Anel interno
        c.create_oval(cx-r_inner, cy-r_inner, cx+r_inner, cy+r_inner,
                      outline=C["bg3"], width=1, tags="anim")

        # Scan line horizontal animada (efeito AI)
        scan_y = cy - r_inner + ((self._angle * 2) % (r_inner * 2))
        scan_y = cy - r_inner + abs((self._angle * 2 % (r_inner * 2)) - r_inner)
        # Clip na área do círculo
        scan_x_offset = math.sqrt(max(0, r_inner**2 - (scan_y - cy)**2))
        if scan_x_offset > 10:
            c.create_line(cx - scan_x_offset + 6, scan_y,
                          cx + scan_x_offset - 6, scan_y,
                          fill=C["green_l"], width=1, tags="anim")
            # Gradiente fake — linhas mais finas acima
            for dy in range(1, 8):
                alpha_line = C["green_dim"]
                if scan_y - dy > cy - r_inner:
                    off2 = math.sqrt(max(0, r_inner**2 - (scan_y - dy - cy)**2))
                    if off2 > 10:
                        c.create_line(cx - off2 + 6, scan_y - dy,
                                      cx + off2 - 6, scan_y - dy,
                                      fill=C["bg5"], width=1, tags="anim")

        # Pontos girando na órbita
        for i in range(4):
            angle_dot = math.radians(self._angle + i * 90)
            dx = (r_outer + 12) * math.cos(angle_dot)
            dy = (r_outer + 12) * math.sin(angle_dot)
            r_dot = 3 if i % 2 == 0 else 2
            col_dot = C["green"] if i == 0 else C["green_dim"]
            c.create_oval(cx+dx-r_dot, cy+dy-r_dot,
                          cx+dx+r_dot, cy+dy+r_dot,
                          fill=col_dot, outline="", tags="anim")

        # Texto central (se não houver foto)
        if self._photo_img is None:
            c.create_text(cx, cy, text="ARNO\nAI",
                          font=("Segoe UI", 18, "bold"),
                          fill=C["green"], justify="center", tags="anim")

        self._angle = (self._angle + 3) % 360
        self.after(30, self._animate)  # ~33fps

    def _concluir(self):
        self._running = False
        self.destroy()
        self.on_done()


# ╔══════════════════════════════════════════════════════════╗
# ║               PAINEL DE RESULTADO (CARDS)                ║
# ╚══════════════════════════════════════════════════════════╝
class PainelResultado(ctk.CTkScrollableFrame):
    def __init__(self,master,**kw):
        super().__init__(master,fg_color=C["bg"],corner_radius=0,
            scrollbar_fg_color=C["bg2"],scrollbar_button_color=C["green"],
            scrollbar_button_hover_color=C["green_l"],**kw)
        self.grid_columnconfigure(0,weight=1)
        self._placeholder()

    def _placeholder(self):
        for w in self.winfo_children(): w.destroy()
        f=ctk.CTkFrame(self,fg_color="transparent")
        f.grid(row=0,column=0,pady=80)
        ib=ctk.CTkFrame(f,fg_color=C["bg3"],corner_radius=40,width=80,height=80)
        ib.pack_propagate(False); ib.pack(pady=(0,20))
        ctk.CTkLabel(ib,text="⚡",font=("Segoe UI",36),text_color=C["green"]).pack(expand=True)
        ctk.CTkLabel(f,text="Seu treino aparece aqui",font=F["title2"],text_color=C["text"]).pack()
        ctk.CTkLabel(f,text="Preencha os dados, tire sua foto e gere o treino",font=F["small"],text_color=C["text_dim"]).pack(pady=(6,0))
        sep=ctk.CTkFrame(f,fg_color=C["bg3"],height=1,width=280); sep.pack(pady=28)
        for item in ["  Análise corporal pela foto","  Exercícios com links do YouTube","  Filtro inteligente por IMC","  Divisão semanal personalizada"]:
            ctk.CTkLabel(f,text=item,font=F["body"],text_color=C["text_mid"],anchor="w").pack(anchor="w",pady=3)

    def renderizar(self,t,foto_path=None):
        for w in self.winfo_children(): w.destroy()
        self.grid_columnconfigure(0,weight=1)
        row=0
        PAD={"padx":20,"pady":5,"sticky":"ew"}

        def sp(h=12):
            nonlocal row
            ctk.CTkFrame(self,fg_color="transparent",height=h).grid(row=row,column=0); row+=1

        def section(emoji,titulo,sub=""):
            nonlocal row; sp(8)
            hf=ctk.CTkFrame(self,fg_color="transparent")
            hf.grid(row=row,column=0,sticky="ew",padx=24,pady=(14,4)); row+=1
            hf.grid_columnconfigure(1,weight=1)
            badge=ctk.CTkFrame(hf,fg_color=C["green"],corner_radius=10,width=38,height=38)
            badge.pack_propagate(False); badge.grid(row=0,column=0,rowspan=2,padx=(0,14))
            ctk.CTkLabel(badge,text=emoji,font=("Segoe UI",17),text_color="#000").grid(row=0,column=0,pady=6)
            ctk.CTkLabel(hf,text=titulo,font=F["header"],text_color=C["text"],anchor="w").grid(row=0,column=1,sticky="w")
            if sub: ctk.CTkLabel(hf,text=sub,font=F["tiny"],text_color=C["text_dim"],anchor="w").grid(row=1,column=1,sticky="w")
            ctk.CTkFrame(self,fg_color=C["bg3"],height=1).grid(row=row,column=0,sticky="ew",padx=24,pady=(4,10)); row+=1

        atleta=t["atleta"]

        # ── CARD HERO ──────────────────────────────────────────────────────────
        hero=ctk.CTkFrame(self,fg_color=C["bg3"],corner_radius=16)
        hero.grid(row=row,column=0,sticky="ew",padx=20,pady=(16,4)); row+=1
        hero.grid_columnconfigure(0,weight=1)
        ctk.CTkFrame(hero,fg_color=C["green"],height=3,corner_radius=0).grid(row=0,column=0,sticky="ew")

        hinn=ctk.CTkFrame(hero,fg_color="transparent")
        hinn.grid(row=1,column=0,sticky="ew",padx=20,pady=18)
        hinn.grid_columnconfigure(2,weight=1)

        # Foto miniatura circular (se houver)
        if foto_path and os.path.exists(foto_path):
            try:
                img=Image.open(foto_path).convert("RGBA")
                size=64
                img=img.resize((size,size),Image.LANCZOS)
                mask=Image.new("L",(size,size),0)
                draw=ImageDraw.Draw(mask)
                draw.ellipse((0,0,size,size),fill=255)
                result=Image.new("RGBA",(size,size),(0,0,0,0))
                result.paste(img,mask=mask)
                self._foto_tk=ImageTk.PhotoImage(result)
                foto_lbl=tk.Label(hinn,image=self._foto_tk,bg=C["bg3"],bd=0)
                foto_lbl.grid(row=0,column=0,rowspan=3,padx=(0,16))
            except Exception:
                self._make_avatar(hinn,atleta)
        else:
            self._make_avatar(hinn,atleta)

        # Separador
        ctk.CTkFrame(hinn,fg_color=C["bg5"],width=1).grid(row=0,column=1,rowspan=3,sticky="ns",padx=(0,14),pady=4)

        nome_d=atleta.get("nome") or "Atleta"
        ctk.CTkLabel(hinn,text=nome_d,font=F["title2"],text_color=C["text"]).grid(row=0,column=2,sticky="w")
        ctk.CTkLabel(hinn,text=f"{atleta['idade']} anos  ·  {atleta['altura']} cm  ·  {atleta['peso']} kg  ·  {atleta['sexo']}",
            font=F["small"],text_color=C["text_mid"]).grid(row=1,column=2,sticky="w",pady=(3,0))
        ctk.CTkLabel(hinn,text=t["frase"],font=F["tiny_i"],text_color=C["green_l"]).grid(row=2,column=2,sticky="w",pady=(5,0))

        if t.get("aviso_imc"):
            af=ctk.CTkFrame(hero,fg_color=C["warning_bg"],corner_radius=8)
            af.grid(row=2,column=0,sticky="ew",padx=14,pady=(0,8))
            ctk.CTkLabel(af,text="⚠  IMC elevado — exercícios de alto impacto substituídos para proteger suas articulações.",
                font=F["tiny"],text_color=C["warning"],wraplength=520,justify="left",anchor="w").grid(row=0,column=0,padx=12,pady=8,sticky="w")

        sf=ctk.CTkFrame(hero,fg_color=C["bg4"],corner_radius=10)
        sf.grid(row=3,column=0,sticky="ew",padx=14,pady=(0,14))
        imc_c={"Peso normal":C["success"],"Abaixo do peso":C["warning"],"Sobrepeso":C["warning"],"Obesidade":C["error"]}.get(t["imc_cat"],C["text_mid"])
        stats=[("IMC",t["imc_val"],imc_c),("Objetivo",atleta["objetivo"].split()[0],C["green_l"]),
               ("Local",atleta["local"],C["text_mid"]),("Dias/sem",atleta["dias"],C["text_mid"]),("Duração",f"{atleta['duracao']}min",C["text_mid"])]
        for col,(lbl,val,cor) in enumerate(stats):
            sf.grid_columnconfigure(col,weight=1)
            s=ctk.CTkFrame(sf,fg_color="transparent"); s.grid(row=0,column=col,padx=10,pady=12)
            ctk.CTkLabel(s,text=val,font=F["body_b"],text_color=cor).pack()
            ctk.CTkLabel(s,text=lbl,font=F["tiny"],text_color=C["text_dim"]).pack()

        # ── AQUECIMENTO ────────────────────────────────────────────────────────
        section("🔥","AQUECIMENTO","5-10 minutos antes do treino")
        ca=ctk.CTkFrame(self,fg_color=C["bg3"],corner_radius=12)
        ca.grid(row=row,column=0,sticky="ew",padx=20,pady=(0,4)); row+=1
        ca.grid_columnconfigure(0,weight=1)
        for i,aq in enumerate(t["aquec"]):
            it=ctk.CTkFrame(ca,fg_color=C["bg4"] if i%2==0 else "transparent",corner_radius=6)
            it.grid(row=i,column=0,sticky="ew",padx=8,pady=2)
            ctk.CTkLabel(it,text=f"  {i+1}",font=F["tiny_i"],text_color=C["green"],width=30).grid(row=0,column=0,padx=(6,0),pady=8)
            ctk.CTkLabel(it,text=aq,font=F["body"],text_color=C["text_soft"],anchor="w").grid(row=0,column=1,sticky="w",pady=8)

        # ── EXERCÍCIOS ──────────────────────────────────────────────────────────
        section("💪","TREINO PRINCIPAL",f"Nível: {atleta['condicionamento']}  ·  ~{atleta['duracao']} min")
        for grupo,exercicios in t["exs"].items():
            gh=ctk.CTkFrame(self,fg_color=C["bg3"],corner_radius=10)
            gh.grid(row=row,column=0,sticky="ew",padx=20,pady=(6,2)); row+=1
            dot=ctk.CTkFrame(gh,fg_color=C["green"],width=4,corner_radius=2)
            dot.pack(side="left",fill="y",padx=(12,10),pady=10)
            ctk.CTkLabel(gh,text=grupo.upper(),font=F["body_b"],text_color=C["text"]).pack(side="left",pady=10)
            ctk.CTkLabel(gh,text=f"{len(exercicios)} exercícios",font=F["tiny"],text_color=C["text_dim"]).pack(side="right",padx=14)

            for idx,ex in enumerate(exercicios):
                ce=ctk.CTkFrame(self,fg_color=C["bg3"],corner_radius=12)
                ce.grid(row=row,column=0,sticky="ew",padx=28,pady=(2,4)); row+=1
                ce.grid_columnconfigure(0,weight=1)

                tr=ctk.CTkFrame(ce,fg_color="transparent")
                tr.grid(row=0,column=0,sticky="ew",padx=14,pady=(14,6))
                tr.grid_columnconfigure(1,weight=1)

                nb=ctk.CTkFrame(tr,fg_color=C["green_dim"],corner_radius=8,width=28,height=28)
                nb.pack_propagate(False); nb.grid(row=0,column=0,padx=(0,12))
                ctk.CTkLabel(nb,text=str(idx+1),font=F["small_b"],text_color=C["green_l"]).grid(row=0,column=0)
                ctk.CTkLabel(tr,text=ex["nome"],font=F["body_b"],text_color=C["text"],anchor="w").grid(row=0,column=1,sticky="w")

                yt_url=ex["yt"]
                ctk.CTkButton(tr,text="▶  YouTube",font=F["tiny"],width=110,height=28,corner_radius=6,
                    fg_color=C["yt_bg"],hover_color=C["youtube_d"],text_color=C["youtube"],
                    border_color=C["youtube_d"],border_width=1,
                    command=lambda url=yt_url: webbrowser.open(url)
                ).grid(row=0,column=2,padx=(12,0))

                br=ctk.CTkFrame(ce,fg_color="transparent")
                br.grid(row=1,column=0,sticky="w",padx=14,pady=(0,6))
                for txt,cbg,ctxt in [(f"{ex['series']}× {ex['reps']} reps",C["bg4"],C["green_l"]),(ex["carga"],C["bg4"],C["text_mid"]),(f"⏱ {ex['descanso']}",C["bg4"],C["text_dim"])]:
                    b=ctk.CTkFrame(br,fg_color=cbg,corner_radius=6); b.pack(side="left",padx=(0,6))
                    ctk.CTkLabel(b,text=txt,font=F["tiny"],text_color=ctxt).pack(padx=10,pady=4)

                df=ctk.CTkFrame(ce,fg_color=C["bg4"],corner_radius=6)
                df.grid(row=2,column=0,sticky="ew",padx=14,pady=(0,14))
                ctk.CTkLabel(df,text=f"  💡  {ex['dica']}",font=F["tiny_i"],text_color=C["text_dim"],anchor="w",wraplength=500).grid(row=0,column=0,sticky="w",padx=6,pady=7)

        # ── VOLTA À CALMA ───────────────────────────────────────────────────────
        section("🧘","VOLTA À CALMA","Alongamento pós-treino — 5-10 min")
        cal=ctk.CTkFrame(self,fg_color=C["bg3"],corner_radius=12)
        cal.grid(row=row,column=0,sticky="ew",padx=20,pady=(0,4)); row+=1
        cal.grid_columnconfigure(0,weight=1)
        for i,al in enumerate(t["along"]):
            it=ctk.CTkFrame(cal,fg_color=C["bg4"] if i%2==0 else "transparent",corner_radius=6)
            it.grid(row=i,column=0,sticky="ew",padx=8,pady=2)
            ctk.CTkLabel(it,text=f"  {i+1}",font=F["tiny_i"],text_color=C["green_l"],width=30).grid(row=0,column=0,padx=(6,0),pady=8)
            ctk.CTkLabel(it,text=al,font=F["body"],text_color=C["text_soft"],anchor="w").grid(row=0,column=1,sticky="w",pady=8)

        # ── DIVISÃO SEMANAL ─────────────────────────────────────────────────────
        dias=int(atleta["dias"]); section("📅","DIVISÃO SEMANAL",f"{dias} dias por semana")
        cal_f=ctk.CTkFrame(self,fg_color="transparent")
        cal_f.grid(row=row,column=0,sticky="ew",padx=20,pady=(0,6)); row+=1
        cols=min(dias,4)
        for c in range(cols): cal_f.grid_columnconfigure(c,weight=1)
        for i,linha in enumerate(t["div"]):
            r2,c2=divmod(i,cols)
            cd=ctk.CTkFrame(cal_f,fg_color=C["bg3"],corner_radius=12)
            cd.grid(row=r2,column=c2,padx=4,pady=4,sticky="nsew"); cd.grid_columnconfigure(0,weight=1)
            ctk.CTkFrame(cd,fg_color=C["green"],height=3,corner_radius=0).grid(row=0,column=0,sticky="ew")
            ctk.CTkLabel(cd,text=f"DIA {i+1}",font=F["tiny"],text_color=C["green"]).grid(row=1,column=0,padx=12,pady=(10,3),sticky="w")
            ctk.CTkLabel(cd,text=linha,font=F["small"],text_color=C["text_soft"],wraplength=150,anchor="w",justify="left").grid(row=2,column=0,padx=12,pady=(0,12),sticky="w")

        # ── DICAS ───────────────────────────────────────────────────────────────
        section("⚡","DICAS PERSONALIZADAS",atleta["objetivo"])
        for i,d in enumerate(t["dicas"]):
            cd2=ctk.CTkFrame(self,fg_color=C["bg3"],corner_radius=10)
            cd2.grid(row=row,column=0,sticky="ew",padx=20,pady=3); row+=1
            cd2.grid_columnconfigure(1,weight=1)
            nb2=ctk.CTkFrame(cd2,fg_color=C["green_dim"],corner_radius=8,width=30,height=30)
            nb2.pack_propagate(False); nb2.grid(row=0,column=0,padx=(14,12),pady=12)
            ctk.CTkLabel(nb2,text=str(i+1),font=F["small_b"],text_color=C["green_l"]).grid(row=0,column=0)
            ctk.CTkLabel(cd2,text=d,font=F["body"],text_color=C["text_soft"],anchor="w",wraplength=540,justify="left").grid(row=0,column=1,sticky="w",pady=12,padx=(0,14))

        # ── NUTRIÇÃO ────────────────────────────────────────────────────────────
        section("🥗","NUTRIÇÃO BÁSICA","Para potencializar seus resultados")
        ng=ctk.CTkFrame(self,fg_color="transparent")
        ng.grid(row=row,column=0,sticky="ew",padx=20,pady=(0,6)); row+=1
        ng.grid_columnconfigure(0,weight=1); ng.grid_columnconfigure(1,weight=1)
        for i,n in enumerate(t["nutri"]):
            r3,c3=divmod(i,2)
            cn=ctk.CTkFrame(ng,fg_color=C["bg3"],corner_radius=10)
            cn.grid(row=r3,column=c3,padx=4,pady=4,sticky="nsew")
            ctk.CTkLabel(cn,text=n,font=F["small"],text_color=C["text_mid"],wraplength=210,anchor="w",justify="left").grid(row=0,column=0,padx=14,pady=12,sticky="w")

        # ── RODAPÉ ──────────────────────────────────────────────────────────────
        sp(8)
        cf=ctk.CTkFrame(self,fg_color=C["green"],corner_radius=14)
        cf.grid(row=row,column=0,sticky="ew",padx=20,pady=(4,28)); row+=1
        ctk.CTkLabel(cf,text=f"  Bora treinar, {atleta.get('nome') or 'Atleta'}! Consistência é a chave.  ⚡",
            font=F["body_b"],text_color="#000").grid(row=0,column=0,padx=18,pady=16,sticky="w")

    def _make_avatar(self,parent,atleta):
        av=ctk.CTkFrame(parent,fg_color=C["green"],corner_radius=32,width=64,height=64)
        av.pack_propagate(False); av.grid(row=0,column=0,rowspan=3,padx=(0,16))
        inits="".join(w[0].upper() for w in (atleta.get("nome") or "AT").split()[:2])
        ctk.CTkLabel(av,text=inits,font=F["body_b"],text_color="#000").grid(row=0,column=0,pady=16)


# ╔══════════════════════════════════════════════════════════╗
# ║               TELA DE LOGIN / CADASTRO                   ║
# ╚══════════════════════════════════════════════════════════╝
class TelaAuth(ctk.CTkToplevel):
    def __init__(self,master,on_ok):
        super().__init__(master)
        self.on_ok=on_ok; self._modo="login"; self._show_pw=False
        self.title("ARNO AI — Entrar"); self.geometry("460x700")
        self.resizable(False,False); self.configure(fg_color=C["bg"])
        self.grab_set(); self.lift(); self.focus_force()
        self.after(10,self._center); self._build()

    def _center(self):
        self.update_idletasks()
        w,h=self.winfo_width(),self.winfo_height()
        sw,sh=self.winfo_screenwidth(),self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build(self):
        for c in self.winfo_children(): c.destroy()
        self._show_pw=False
        outer=ctk.CTkFrame(self,fg_color=C["bg"],corner_radius=0)
        outer.pack(fill="both",expand=True)
        ctk.CTkFrame(outer,fg_color=C["green"],height=3,corner_radius=0).pack(fill="x")
        lf=ctk.CTkFrame(outer,fg_color="transparent"); lf.pack(pady=(32,6))
        ib=ctk.CTkFrame(lf,fg_color=C["green"],corner_radius=22,width=58,height=58)
        ib.pack_propagate(False); ib.pack()
        ctk.CTkLabel(ib,text="⚡",font=("Segoe UI",24),text_color="#000").pack(expand=True)
        ctk.CTkLabel(outer,text="ARNO AI",font=F["mega"],text_color=C["text"]).pack(pady=(10,0))
        ctk.CTkLabel(outer,text="Personal Trainer Inteligente",font=F["small"],text_color=C["text_dim"]).pack()
        tf=ctk.CTkFrame(outer,fg_color=C["bg3"],corner_radius=10)
        tf.pack(fill="x",padx=36,pady=(24,0))
        for txt,modo in [("Entrar","login"),("Cadastrar","cadastro")]:
            ativo=self._modo==modo
            ctk.CTkButton(tf,text=txt,font=F["body_b"],height=38,corner_radius=8,
                fg_color=C["green"] if ativo else "transparent",
                hover_color=C["green_d"] if ativo else C["bg4"],
                text_color="#000" if ativo else C["text_dim"],
                command=lambda m=modo: self._ir(m)
            ).pack(side="left",fill="x",expand=True,padx=3,pady=3)
        form=ctk.CTkFrame(outer,fg_color=C["bg3"],corner_radius=12)
        form.pack(fill="x",padx=36,pady=(12,0))
        def campo(lbl,attr,ph,show=""):
            ctk.CTkLabel(form,text=lbl,font=F["small"],text_color=C["text_dim"]).pack(anchor="w",padx=18,pady=(12,2))
            e=ctk.CTkEntry(form,placeholder_text=ph,show=show,fg_color=C["bg4"],border_color=C["border2"],
                text_color=C["text"],font=F["body"],height=44,corner_radius=10)
            e.pack(fill="x",padx=18,pady=(0,2)); setattr(self,attr,e)
        if self._modo=="cadastro": campo("Nome completo","e_nome","Ex: João Silva")
        campo("E-mail","e_email","seu@email.com")
        ctk.CTkLabel(form,text="Senha",font=F["small"],text_color=C["text_dim"]).pack(anchor="w",padx=18,pady=(12,2))
        rpw=ctk.CTkFrame(form,fg_color="transparent"); rpw.pack(fill="x",padx=18,pady=(0,4))
        rpw.grid_columnconfigure(0,weight=1)
        self.e_senha=ctk.CTkEntry(rpw,placeholder_text="Mínimo 6 caracteres",show="•",
            fg_color=C["bg4"],border_color=C["border2"],text_color=C["text"],font=F["body"],height=44,corner_radius=10)
        self.e_senha.grid(row=0,column=0,sticky="ew",padx=(0,8))
        ctk.CTkButton(rpw,text="👁",width=44,height=44,fg_color=C["bg4"],hover_color=C["bg5"],
            text_color=C["green"],font=F["body"],corner_radius=10,command=self._toggle_pw).grid(row=0,column=1)
        if self._modo=="cadastro": campo("Confirmar senha","e_senha2","Repita a senha",show="•")
        ctk.CTkFrame(form,fg_color="transparent",height=10).pack()
        self.msg_lbl=ctk.CTkLabel(outer,text="",font=F["small"],text_color=C["error"])
        self.msg_lbl.pack(pady=(10,0))
        lbl_btn="ENTRAR  ⚡" if self._modo=="login" else "CRIAR CONTA  ⚡"
        self.btn=ctk.CTkButton(outer,text=lbl_btn,font=F["btn_lg"],height=52,corner_radius=12,
            fg_color=C["green"],hover_color=C["green_d"],text_color="#000",command=self._acao)
        self.btn.pack(fill="x",padx=36,pady=(12,0))
        foot="Não tem conta? Cadastre-se" if self._modo=="login" else "Já tem conta? Entre"
        ctk.CTkLabel(outer,text=foot,font=F["small"],text_color=C["text_dim"]).pack(pady=(12,2))
        ctk.CTkLabel(outer,text="Seus dados ficam 100% locais no seu computador",font=F["tiny"],text_color=C["text_dim"]).pack(pady=(0,18))
        self.bind("<Return>",lambda e: self._acao())
        self.after(100,lambda: self.e_email.focus())

    def _ir(self,m): self._modo=m; self._build()
    def _toggle_pw(self):
        self._show_pw=not self._show_pw
        self.e_senha.configure(show="" if self._show_pw else "•")
    def _set_msg(self,t,c=None): self.msg_lbl.configure(text=t,text_color=c or C["error"])
    def _acao(self):
        if self._modo=="login": self._do_login()
        else: self._do_cad()
    def _do_login(self):
        em,pw=self.e_email.get().strip(),self.e_senha.get()
        if not em or not pw: self._set_msg("Preencha e-mail e senha."); return
        self.btn.configure(state="disabled",text="Entrando...")
        self.after(150,lambda: self._proc_login(em,pw))
    def _proc_login(self,em,pw):
        ok,msg,user=db_login(em,pw)
        if ok:
            self._set_msg("✅  "+msg,C["success"]); self.after(700,lambda: self._done(user))
        else:
            self._set_msg(msg); self.btn.configure(state="normal",text="ENTRAR  ⚡")
    def _do_cad(self):
        nome=self.e_nome.get().strip(); em=self.e_email.get().strip()
        pw=self.e_senha.get(); pw2=self.e_senha2.get()
        if not all([nome,em,pw,pw2]): self._set_msg("Preencha todos os campos."); return
        if pw!=pw2: self._set_msg("As senhas não coincidem."); return
        self.btn.configure(state="disabled",text="Criando conta...")
        self.after(150,lambda: self._proc_cad(nome,em,pw))
    def _proc_cad(self,nome,em,pw):
        ok,msg=db_cadastrar(nome,em,pw)
        if ok:
            self._set_msg("✅  "+msg,C["success"]); self.after(1000,lambda: self._ir("login"))
        else:
            self._set_msg(msg); self.btn.configure(state="normal",text="CRIAR CONTA  ⚡")
    def _done(self,user):
        self.destroy(); self.on_ok(user)


# ╔══════════════════════════════════════════════════════════╗
# ║                    APP PRINCIPAL                         ║
# ╚══════════════════════════════════════════════════════════╝
class ArnoAI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("ARNO AI — Personal Trainer Inteligente")
        self.geometry("1440x900"); self.minsize(1100,720)
        self.configure(fg_color=C["bg"])
        self._usuario=None; self._ultimo=None; self._foto_path=None

        self.v_nome=tk.StringVar(); self.v_idade=tk.StringVar(value="25")
        self.v_altura=tk.StringVar(value="175"); self.v_peso=tk.StringVar(value="75")
        self.v_sexo=tk.StringVar(value="Masculino")
        self.v_obj=tk.StringVar(value="Hipertrofia (ganho de massa)")
        self.v_cond=tk.StringVar(value="Intermediário")
        self.v_local=tk.StringVar(value="Academia")
        self.v_carga=tk.StringVar(value="40"); self.v_dias=tk.StringVar(value="4")
        self.v_dur=tk.StringVar(value="60"); self.gvars={}
        self._step=1  # 1 = dados, 2 = foto

        self._build()
        self.after(200,self._abrir_auth)

    # ── Auth ──────────────────────────────────────────────────────────────────
    def _abrir_auth(self):
        self.withdraw()
        a=TelaAuth(self,self._on_login)
        a.protocol("WM_DELETE_WINDOW",self.destroy)

    def _on_login(self,user):
        self._usuario=user; self.v_nome.set(user.get("nome",""))
        self._refresh_top(); self.deiconify(); self.lift(); self.focus_force()

    def _refresh_top(self):
        if hasattr(self,"lbl_user") and self._usuario:
            nome=self._usuario.get("nome","Atleta"); n=self._usuario.get("treinos",0)
            self.lbl_user.configure(text=f"Olá, {nome}  ·  {n} treino{'s' if n!=1 else ''}")

    def _logout(self):
        if messagebox.askyesno("Sair","Deseja sair da conta?"):
            self._usuario=None; self.withdraw(); self._abrir_auth()

    # ── Build UI ──────────────────────────────────────────────────────────────
    def _build(self):
        self._build_top()
        main=ctk.CTkFrame(self,fg_color=C["bg"],corner_radius=0)
        main.pack(fill="both",expand=True,padx=16,pady=(8,16))
        main.grid_columnconfigure(0,weight=0,minsize=480)
        main.grid_columnconfigure(1,weight=1)
        main.grid_rowconfigure(0,weight=1)
        self._build_left(main)
        self._build_right(main)

    def _build_top(self):
        tb=ctk.CTkFrame(self,fg_color=C["bg2"],corner_radius=0,height=52)
        tb.pack(fill="x"); tb.pack_propagate(False)
        ctk.CTkFrame(tb,fg_color=C["green"],height=2,corner_radius=0).pack(fill="x",side="top")
        inn=ctk.CTkFrame(tb,fg_color="transparent"); inn.pack(fill="both",expand=True,padx=20)
        lf=ctk.CTkFrame(inn,fg_color="transparent"); lf.pack(side="left")
        ctk.CTkLabel(lf,text="⚡",font=("Segoe UI",16),text_color=C["green"]).pack(side="left",padx=(0,6))
        ctk.CTkLabel(lf,text="ARNO AI",font=F["body_b"],text_color=C["text"]).pack(side="left")
        ctk.CTkLabel(lf,text="  Personal Trainer",font=F["tiny"],text_color=C["text_dim"]).pack(side="left",pady=18)
        ctk.CTkButton(inn,text="Sair",font=F["tiny"],width=60,height=26,
            fg_color="transparent",hover_color=C["bg4"],text_color=C["text_dim"],
            border_color=C["border2"],border_width=1,corner_radius=6,command=self._logout
        ).pack(side="right",pady=13)
        ctk.CTkButton(inn,text="📂  Histórico",font=F["small_b"],width=110,height=28,
            fg_color=C["green_dim"],hover_color=C["green_d"],text_color=C["green_l"],
            border_color=C["green_d"],border_width=1,corner_radius=6,command=self._abrir_historico
        ).pack(side="right",pady=13,padx=(0,8))
        ctk.CTkButton(inn,text="👤  Perfil",font=F["small_b"],width=90,height=28,
            fg_color=C["bg4"],hover_color=C["bg5"],text_color=C["text_mid"],
            border_color=C["border2"],border_width=1,corner_radius=6,command=self._abrir_perfil
        ).pack(side="right",pady=13,padx=(0,8))
        self.lbl_user=ctk.CTkLabel(inn,text="...",font=F["small"],text_color=C["text_mid"])
        self.lbl_user.pack(side="right",padx=14)

    # ── PAINEL ESQUERDO COM STEPS ─────────────────────────────────────────────
    def _build_left(self,parent):
        outer=ctk.CTkFrame(parent,fg_color=C["bg2"],corner_radius=16)
        outer.grid(row=0,column=0,sticky="nsew",padx=(0,10))
        outer.grid_rowconfigure(1,weight=1)
        outer.grid_columnconfigure(0,weight=1)

        # ── Steps indicator no topo ──────────────────────────────────────
        steps_frame=ctk.CTkFrame(outer,fg_color=C["bg3"],corner_radius=12)
        steps_frame.grid(row=0,column=0,sticky="ew",padx=16,pady=(16,8))
        steps_frame.grid_columnconfigure(0,weight=1)
        steps_frame.grid_columnconfigure(2,weight=1)

        # Step 1
        s1=ctk.CTkFrame(steps_frame,fg_color="transparent")
        s1.grid(row=0,column=0,padx=12,pady=12,sticky="w")
        self.step1_circle=ctk.CTkFrame(s1,fg_color=C["green"],corner_radius=16,width=32,height=32)
        self.step1_circle.pack_propagate(False); self.step1_circle.pack(side="left",padx=(0,10))
        self.step1_lbl=ctk.CTkLabel(self.step1_circle,text="1",font=F["step_num"],text_color="#000")
        self.step1_lbl.pack(expand=True)
        s1_txt=ctk.CTkFrame(s1,fg_color="transparent"); s1_txt.pack(side="left")
        ctk.CTkLabel(s1_txt,text="Seus Dados",font=F["small_b"],text_color=C["text"]).pack(anchor="w")
        ctk.CTkLabel(s1_txt,text="Informações pessoais",font=F["tiny"],text_color=C["text_dim"]).pack(anchor="w")

        # Linha conectora
        conn=ctk.CTkFrame(steps_frame,fg_color=C["bg5"],height=2,corner_radius=1)
        conn.grid(row=0,column=1,sticky="ew",padx=4)
        self.step_conn=conn

        # Step 2
        s2=ctk.CTkFrame(steps_frame,fg_color="transparent")
        s2.grid(row=0,column=2,padx=12,pady=12,sticky="e")
        self.step2_circle=ctk.CTkFrame(s2,fg_color=C["bg5"],corner_radius=16,width=32,height=32)
        self.step2_circle.pack_propagate(False); self.step2_circle.pack(side="left",padx=(0,10))
        self.step2_lbl=ctk.CTkLabel(self.step2_circle,text="2",font=F["step_num"],text_color=C["text_dim"])
        self.step2_lbl.pack(expand=True)
        s2_txt=ctk.CTkFrame(s2,fg_color="transparent"); s2_txt.pack(side="left")
        self.step2_title=ctk.CTkLabel(s2_txt,text="Sua Foto",font=F["small_b"],text_color=C["text_dim"])
        self.step2_title.pack(anchor="w")
        self.step2_sub=ctk.CTkLabel(s2_txt,text="Análise corporal",font=F["tiny"],text_color=C["text_dim"])
        self.step2_sub.pack(anchor="w")

        # ── Área de conteúdo que troca conforme o step ───────────────────
        self.content_area=ctk.CTkScrollableFrame(outer,fg_color=C["bg2"],corner_radius=14,
            scrollbar_fg_color=C["bg2"],scrollbar_button_color=C["green"],
            scrollbar_button_hover_color=C["green_l"],width=450)
        self.content_area.grid(row=1,column=0,sticky="nsew",padx=1,pady=(0,1))
        self.content_area.grid_columnconfigure(0,weight=1)

        self._render_step1()

    def _render_step1(self):
        """Renderiza o formulário de dados (Step 1)."""
        for w in self.content_area.winfo_children(): w.destroy()
        left=self.content_area; row=0

        # IMC card
        imc_f=ctk.CTkFrame(left,fg_color=C["bg3"],corner_radius=12)
        imc_f.grid(row=row,column=0,sticky="ew",padx=16,pady=(16,10)); row+=1
        imc_f.grid_columnconfigure(0,weight=1); imc_f.grid_columnconfigure(2,weight=2)
        self.imc_v=ctk.CTkLabel(imc_f,text="--",font=F["title"],text_color=C["green_l"])
        self.imc_v.grid(row=0,column=0,padx=16,pady=(14,0),sticky="w")
        ctk.CTkLabel(imc_f,text="IMC",font=F["tiny"],text_color=C["text_dim"]).grid(row=1,column=0,padx=16,pady=(0,14),sticky="w")
        ctk.CTkFrame(imc_f,fg_color=C["bg5"],width=1).grid(row=0,column=1,rowspan=2,sticky="ns",padx=6,pady=10)
        self.imc_c=ctk.CTkLabel(imc_f,text="Preencha altura e peso",font=F["small"],text_color=C["text_dim"],wraplength=170)
        self.imc_c.grid(row=0,column=2,rowspan=2,padx=14,pady=14,sticky="w")
        self.v_peso.trace_add("write",lambda *_: self._imc())
        self.v_altura.trace_add("write",lambda *_: self._imc())

        # Dados pessoais
        row=self._shdr(left,row,"👤","DADOS PESSOAIS","Informações básicas")
        self._lbl(left,row,"Nome (opcional)"); row+=1
        self._inp(left,row,self.v_nome,"Ex: João Silva"); row+=1

        trio=ctk.CTkFrame(left,fg_color="transparent")
        trio.grid(row=row,column=0,sticky="ew",padx=16,pady=(4,10)); row+=1
        for c in range(3): trio.grid_columnconfigure(c,weight=1)
        for i,(lbl,var,ph,suf) in enumerate([("Idade",self.v_idade,"25","anos"),("Altura",self.v_altura,"175","cm"),("Peso",self.v_peso,"75","kg")]):
            f=ctk.CTkFrame(trio,fg_color="transparent")
            f.grid(row=0,column=i,padx=(0 if i==0 else 6,0),sticky="ew")
            ctk.CTkLabel(f,text=f"{lbl} ({suf})",font=F["tiny"],text_color=C["text_dim"]).pack(anchor="w")
            ctk.CTkEntry(f,textvariable=var,placeholder_text=ph,fg_color=C["bg3"],border_color=C["border2"],
                text_color=C["text"],font=F["body"],height=42,corner_radius=10).pack(fill="x")

        self._lbl(left,row,"Sexo"); row+=1
        self._seg(left,row,self.v_sexo,["Masculino","Feminino","Outro"]); row+=1

        # Configuração
        row=self._shdr(left,row,"🏋️","CONFIGURAÇÃO DO TREINO","Personalize seu programa")
        self._lbl(left,row,"Objetivo principal"); row+=1
        self._opt(left,row,self.v_obj,["Hipertrofia (ganho de massa)","Emagrecimento / Definição","Força máxima","Resistência muscular","Condicionamento físico","Reabilitação / Saúde geral"]); row+=1
        self._lbl(left,row,"Nível de condicionamento"); row+=1
        self._opt(left,row,self.v_cond,["Iniciante (< 3 meses)","Iniciante avançado (3-6 meses)","Intermediário","Avançado","Atleta"]); row+=1
        self._lbl(left,row,"Local do treino"); row+=1
        self._seg(left,row,self.v_local,["Academia","Casa"]); row+=1

        triple=ctk.CTkFrame(left,fg_color="transparent")
        triple.grid(row=row,column=0,sticky="ew",padx=16,pady=(4,10)); row+=1
        for c in range(3): triple.grid_columnconfigure(c,weight=1)
        for i,(lbl,var,ph,suf) in enumerate([("Carga máx",self.v_carga,"40","kg"),("Dias",self.v_dias,"4","/sem"),("Duração",self.v_dur,"60","min")]):
            f=ctk.CTkFrame(triple,fg_color="transparent")
            f.grid(row=0,column=i,padx=(0 if i==0 else 6,0),sticky="ew")
            ctk.CTkLabel(f,text=f"{lbl} ({suf})",font=F["tiny"],text_color=C["text_dim"]).pack(anchor="w")
            ctk.CTkEntry(f,textvariable=var,placeholder_text=ph,fg_color=C["bg3"],border_color=C["border2"],
                text_color=C["text"],font=F["body"],height=42,corner_radius=10).pack(fill="x")

        # Grupos musculares
        row=self._shdr(left,row,"💪","GRUPOS MUSCULARES","Selecione os músculos alvo")
        gg=ctk.CTkFrame(left,fg_color=C["bg3"],corner_radius=12)
        gg.grid(row=row,column=0,sticky="ew",padx=16,pady=(4,6)); row+=1
        ig=ctk.CTkFrame(gg,fg_color="transparent"); ig.pack(fill="x",padx=14,pady=14)
        for c in range(3): ig.grid_columnconfigure(c,weight=1)
        grupos=[("Peito","Peito"),("Bíceps","Biceps"),("Tríceps","Triceps"),
                ("Ombros","Ombro"),("Costas","Costas"),("Pernas","Perna"),
                ("Panturrilha","Panturrilha"),("Core / Abs","Core/Abs"),("Glúteos","Gluteo")]
        for idx,(disp,key) in enumerate(grupos):
            var=tk.BooleanVar(value=True); self.gvars[key]=var
            r2,c2=divmod(idx,3)
            ctk.CTkCheckBox(ig,text=disp,variable=var,fg_color=C["green"],hover_color=C["green_d"],
                border_color=C["bg5"],checkmark_color="#000",text_color=C["text"],font=F["small"],
                corner_radius=4,height=32,border_width=2).grid(row=r2,column=c2,sticky="w",padx=8,pady=6)

        sel=ctk.CTkFrame(left,fg_color="transparent")
        sel.grid(row=row,column=0,sticky="ew",padx=16,pady=(2,8)); row+=1
        for txt,st in [("Selecionar todos",True),("Desmarcar todos",False)]:
            ctk.CTkButton(sel,text=txt,font=F["tiny"],height=28,corner_radius=6,
                fg_color=C["bg3"],hover_color=C["bg5"],text_color=C["text_mid"],
                command=lambda s=st: self._set_g(s)).pack(side="left",padx=(0,6))

        ctk.CTkFrame(left,fg_color="transparent",height=6).grid(row=row,column=0); row+=1

        # Botão PRÓXIMO (vai para o step 2)
        ctk.CTkButton(left,text="PRÓXIMO  →  Tirar Foto",font=F["btn_lg"],
            fg_color=C["green"],hover_color=C["green_d"],text_color="#000",
            height=58,corner_radius=14,command=self._ir_step2
        ).grid(row=row,column=0,sticky="ew",padx=16,pady=(4,24))

    def _render_step2(self):
        """Renderiza a tela de foto (Step 2)."""
        for w in self.content_area.winfo_children(): w.destroy()
        left=self.content_area; row=0

        # Header orientação
        ctk.CTkFrame(left,fg_color="transparent",height=16).grid(row=row,column=0); row+=1

        info_card=ctk.CTkFrame(left,fg_color=C["bg3"],corner_radius=14)
        info_card.grid(row=row,column=0,sticky="ew",padx=16,pady=(0,8)); row+=1
        info_card.grid_columnconfigure(0,weight=1)
        ctk.CTkFrame(info_card,fg_color=C["green"],height=3,corner_radius=0).grid(row=0,column=0,sticky="ew")

        inf=ctk.CTkFrame(info_card,fg_color="transparent")
        inf.grid(row=1,column=0,padx=20,pady=18,sticky="ew")
        ctk.CTkLabel(inf,text="📸  Como tirar a foto ideal",font=F["body_b"],text_color=C["text"]).pack(anchor="w")
        ctk.CTkLabel(inf,text="Para uma análise corporal precisa, siga as instruções:",
            font=F["small"],text_color=C["text_dim"]).pack(anchor="w",pady=(4,12))

        dicas_foto=[
            ("🧍","Foto em pé, corpo inteiro visível"),
            ("💡","Ambiente bem iluminado"),
            ("👕","Roupa leve (short, camiseta)"),
            ("📐","Fique de frente para a câmera"),
            ("📷","Peça para alguém tirar ou use suporte"),
        ]
        for emoji,txt in dicas_foto:
            d=ctk.CTkFrame(inf,fg_color=C["bg4"],corner_radius=8)
            d.pack(fill="x",pady=3)
            ctk.CTkLabel(d,text=emoji,font=("Segoe UI",14)).pack(side="left",padx=(12,8),pady=8)
            ctk.CTkLabel(d,text=txt,font=F["small"],text_color=C["text_soft"]).pack(side="left",pady=8)

        # Área de preview da foto
        ctk.CTkFrame(left,fg_color="transparent",height=8).grid(row=row,column=0); row+=1

        self.foto_preview_frame=ctk.CTkFrame(left,fg_color=C["bg3"],corner_radius=14)
        self.foto_preview_frame.grid(row=row,column=0,sticky="ew",padx=16,pady=(0,8)); row+=1
        self.foto_preview_frame.grid_columnconfigure(0,weight=1)

        self._render_foto_preview()

        # Botões de ação da foto
        btn_row=ctk.CTkFrame(left,fg_color="transparent")
        btn_row.grid(row=row,column=0,sticky="ew",padx=16,pady=(0,8)); row+=1
        btn_row.grid_columnconfigure(0,weight=1); btn_row.grid_columnconfigure(1,weight=1)

        ctk.CTkButton(btn_row,text="📁  Escolher Foto",font=F["btn"],
            fg_color=C["bg3"],hover_color=C["bg5"],text_color=C["text"],
            border_color=C["border2"],border_width=1,
            height=48,corner_radius=12,command=self._escolher_foto
        ).grid(row=0,column=0,padx=(0,6),sticky="ew")

        ctk.CTkButton(btn_row,text="📷  Câmera (Tirar Foto)",font=F["btn"],
            fg_color=C["bg3"],hover_color=C["bg5"],text_color=C["text"],
            border_color=C["border2"],border_width=1,
            height=48,corner_radius=12,command=self._tirar_foto
        ).grid(row=0,column=1,padx=(6,0),sticky="ew")

        ctk.CTkFrame(left,fg_color="transparent",height=6).grid(row=row,column=0); row+=1

        # Label status foto
        self.lbl_foto_status=ctk.CTkLabel(left,text="Nenhuma foto selecionada",
            font=F["small"],text_color=C["text_dim"])
        self.lbl_foto_status.grid(row=row,column=0,pady=(0,4)); row+=1
        if self._foto_path:
            nome_arq=os.path.basename(self._foto_path)
            self.lbl_foto_status.configure(text=f"✅  Foto: {nome_arq}",text_color=C["success"])

        ctk.CTkFrame(left,fg_color="transparent",height=8).grid(row=row,column=0); row+=1

        # Botão GERAR TREINO
        self.btn_gerar=ctk.CTkButton(left,text="⚡   GERAR MEU TREINO",font=F["btn_lg"],
            fg_color=C["green"],hover_color=C["green_d"],text_color="#000",
            height=62,corner_radius=14,command=self._gerar)
        self.btn_gerar.grid(row=row,column=0,sticky="ew",padx=16,pady=(4,8)); row+=1

        # Pular foto
        ctk.CTkButton(left,text="Continuar sem foto",font=F["small"],
            fg_color="transparent",hover_color=C["bg3"],text_color=C["text_dim"],
            border_color=C["border2"],border_width=1,height=34,corner_radius=10,
            command=self._gerar_sem_foto
        ).grid(row=row,column=0,sticky="ew",padx=16,pady=(0,8)); row+=1

        # Voltar ao step 1
        ctk.CTkButton(left,text="← Voltar e editar dados",font=F["tiny"],
            fg_color="transparent",hover_color=C["bg3"],text_color=C["text_dim"],
            height=30,corner_radius=8,command=self._ir_step1
        ).grid(row=row,column=0,pady=(0,20))

    def _render_foto_preview(self):
        """Renderiza preview da foto escolhida ou placeholder."""
        for w in self.foto_preview_frame.winfo_children(): w.destroy()
        if self._foto_path and os.path.exists(self._foto_path):
            try:
                img=Image.open(self._foto_path)
                # Mantém proporção, max 200px altura
                w_orig,h_orig=img.size
                target_h=200
                target_w=int(w_orig*(target_h/h_orig))
                target_w=min(target_w,360)
                img=img.resize((target_w,target_h),Image.LANCZOS)
                self._preview_tk=ImageTk.PhotoImage(img)
                container=ctk.CTkFrame(self.foto_preview_frame,fg_color="transparent")
                container.pack(pady=16)
                # Frame com borda verde
                border_f=ctk.CTkFrame(container,fg_color=C["green"],corner_radius=12,
                    width=target_w+4,height=target_h+4)
                border_f.pack_propagate(False); border_f.pack()
                tk.Label(border_f,image=self._preview_tk,bg=C["bg3"],bd=0).pack(padx=2,pady=2)
                ctk.CTkLabel(self.foto_preview_frame,text="✅  Foto carregada com sucesso!",
                    font=F["small_b"],text_color=C["success"]).pack(pady=(0,12))
                return
            except Exception: pass

        # Placeholder
        ph=ctk.CTkFrame(self.foto_preview_frame,fg_color=C["bg4"],corner_radius=12)
        ph.pack(fill="x",padx=16,pady=16)
        ctk.CTkLabel(ph,text="🧍",font=("Segoe UI",48)).pack(pady=(24,8))
        ctk.CTkLabel(ph,text="Nenhuma foto selecionada",font=F["body"],text_color=C["text_dim"]).pack()
        ctk.CTkLabel(ph,text="Clique em um dos botões abaixo para adicionar sua foto",
            font=F["small"],text_color=C["text_dim"]).pack(pady=(4,24))

    # ── Steps ─────────────────────────────────────────────────────────────────
    def _ir_step2(self):
        """Valida dados e avança para o step 2."""
        if not self._validar_dados(): return
        self._step=2
        # Atualiza visual dos steps
        self.step1_circle.configure(fg_color=C["green_d"])
        self.step1_lbl.configure(text="✓",text_color=C["text"])
        self.step_conn.configure(fg_color=C["green"])
        self.step2_circle.configure(fg_color=C["green"])
        self.step2_lbl.configure(text="2",text_color="#000")
        self.step2_title.configure(text_color=C["text"])
        self.step2_sub.configure(text_color=C["text_mid"])
        self._render_step2()

    def _ir_step1(self):
        self._step=1
        self.step1_circle.configure(fg_color=C["green"])
        self.step1_lbl.configure(text="1",text_color="#000")
        self.step_conn.configure(fg_color=C["bg5"])
        self.step2_circle.configure(fg_color=C["bg5"])
        self.step2_lbl.configure(text="2",text_color=C["text_dim"])
        self.step2_title.configure(text_color=C["text_dim"])
        self.step2_sub.configure(text_color=C["text_dim"])
        self._render_step1()

    # ── Foto ──────────────────────────────────────────────────────────────────
    def _escolher_foto(self):
        path=filedialog.askopenfilename(
            title="Selecione sua foto (corpo inteiro, em pé)",
            filetypes=[("Imagens","*.jpg *.jpeg *.png *.bmp *.webp"),("Todos","*.*")]
        )
        if path:
            self._foto_path=path
            self._render_foto_preview()
            if hasattr(self,"lbl_foto_status"):
                self.lbl_foto_status.configure(
                    text=f"✅  {os.path.basename(path)}",text_color=C["success"])

    def _tirar_foto(self):
        """Tenta abrir câmera; se não disponível, abre seletor de arquivo."""
        try:
            import cv2
            cap=cv2.VideoCapture(0)
            if not cap.isOpened(): raise RuntimeError("Câmera não encontrada")

            # Janela simples de captura
            win=ctk.CTkToplevel(self)
            win.title("Câmera — Pressione ESPAÇO para tirar foto")
            win.geometry("660x560"); win.grab_set(); win.lift()
            win.configure(fg_color=C["bg"])

            canvas=tk.Canvas(win,width=640,height=480,bg=C["bg"],highlightthickness=0)
            canvas.pack(pady=(10,5))
            lbl_inst=ctk.CTkLabel(win,text="Pressione  ESPAÇO  para capturar  |  ESC para cancelar",
                font=F["small"],text_color=C["text_mid"])
            lbl_inst.pack()

            self._cam_running=True
            self._cam_photo=None

            def update_frame():
                if not self._cam_running: return
                ret,frame=cap.read()
                if ret:
                    frame_rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
                    img=Image.fromarray(frame_rgb).resize((640,480))
                    imgtk=ImageTk.PhotoImage(image=img)
                    canvas._imgtk=imgtk
                    canvas.create_image(0,0,anchor="nw",image=imgtk)
                win.after(33,update_frame)

            def on_key(event):
                if event.keysym=="space":
                    ret,frame=cap.read()
                    if ret:
                        path="arno_foto_capturada.jpg"
                        cv2.imwrite(path,frame)
                        self._foto_path=os.path.abspath(path)
                        self._cam_running=False
                        cap.release()
                        win.destroy()
                        self._render_foto_preview()
                        if hasattr(self,"lbl_foto_status"):
                            self.lbl_foto_status.configure(text="✅  Foto capturada!",text_color=C["success"])
                elif event.keysym=="Escape":
                    self._cam_running=False
                    cap.release()
                    win.destroy()

            win.bind("<Key>",on_key)
            update_frame()

        except Exception:
            # Câmera não disponível → abre seletor
            messagebox.showinfo("Câmera","Câmera não disponível.\nSelecione uma foto do computador.")
            self._escolher_foto()

    def _gerar_sem_foto(self):
        """Gera treino sem foto."""
        self._foto_path=None
        self._gerar()

    # ── Build right ───────────────────────────────────────────────────────────
    def _build_right(self,parent):
        outer=ctk.CTkFrame(parent,fg_color=C["bg2"],corner_radius=16)
        outer.grid(row=0,column=1,sticky="nsew",padx=(10,0))
        right=ctk.CTkFrame(outer,fg_color=C["bg"],corner_radius=14)
        right.pack(fill="both",expand=True,padx=2,pady=2)
        right.grid_rowconfigure(1,weight=1); right.grid_columnconfigure(0,weight=1)

        hdr=ctk.CTkFrame(right,fg_color=C["bg2"],corner_radius=0,height=60)
        hdr.grid(row=0,column=0,sticky="ew"); hdr.grid_propagate(False)
        hi=ctk.CTkFrame(hdr,fg_color="transparent"); hi.pack(fill="both",expand=True,padx=22)
        ctk.CTkLabel(hi,text="📋  TREINO GERADO",font=F["header"],text_color=C["text"]).pack(side="left",pady=20)
        self.lbl_status=ctk.CTkLabel(hi,text="Pronto para gerar",font=F["small"],text_color=C["text_dim"])
        self.lbl_status.pack(side="right",pady=20)

        self.painel=PainelResultado(right)
        self.painel.grid(row=1,column=0,sticky="nsew")

        footer=ctk.CTkFrame(right,fg_color=C["bg2"],corner_radius=0,height=54)
        footer.grid(row=2,column=0,sticky="ew"); footer.grid_propagate(False)
        bf=ctk.CTkFrame(footer,fg_color="transparent"); bf.pack(side="right",padx=16,pady=10)
        self.btn_cp=ctk.CTkButton(bf,text="📋  Copiar",font=F["small"],width=110,
            fg_color=C["bg3"],hover_color=C["bg5"],text_color=C["text_mid"],
            border_color=C["border2"],border_width=1,height=34,corner_radius=8,command=self._copiar)
        self.btn_cp.pack(side="right",padx=(8,0))
        ctk.CTkButton(bf,text="📄  Exportar PDF",font=F["small"],width=130,
            fg_color=C["green_dim"],hover_color=C["green_d"],text_color=C["green_l"],
            border_color=C["green_d"],border_width=1,height=34,corner_radius=8,
            command=self._exportar_pdf
        ).pack(side="right",padx=(8,0))
        ctk.CTkButton(bf,text="🔄  Nova variação",font=F["small"],width=140,
            fg_color=C["bg3"],hover_color=C["bg5"],text_color=C["text_mid"],
            border_color=C["border2"],border_width=1,height=34,corner_radius=8,command=self._gerar
        ).pack(side="right")
        ctk.CTkButton(bf,text="← Recomeçar",font=F["small"],width=110,
            fg_color=C["bg3"],hover_color=C["bg5"],text_color=C["text_dim"],
            border_color=C["border2"],border_width=1,height=34,corner_radius=8,command=self._limpar
        ).pack(side="right",padx=(0,8))

    # ── Helpers ───────────────────────────────────────────────────────────────
    def _shdr(self,p,row,icon,title,sub):
        ctk.CTkFrame(p,fg_color="transparent",height=8).grid(row=row,column=0); row+=1
        ctk.CTkFrame(p,fg_color=C["bg3"],height=1).grid(row=row,column=0,sticky="ew",padx=16,pady=(0,10)); row+=1
        f=ctk.CTkFrame(p,fg_color="transparent")
        f.grid(row=row,column=0,sticky="ew",padx=16,pady=(0,6)); row+=1
        f.grid_columnconfigure(1,weight=1)
        ib=ctk.CTkFrame(f,fg_color=C["bg4"],corner_radius=8,width=36,height=36)
        ib.pack_propagate(False); ib.grid(row=0,column=0,rowspan=2,padx=(0,12))
        ctk.CTkLabel(ib,text=icon,font=("Segoe UI",15)).grid(row=0,column=0,padx=4)
        ctk.CTkLabel(f,text=title,font=F["body_b"],text_color=C["text"]).grid(row=0,column=1,sticky="w")
        ctk.CTkLabel(f,text=sub,font=F["tiny"],text_color=C["text_dim"]).grid(row=1,column=1,sticky="w")
        return row

    def _lbl(self,p,row,t):
        ctk.CTkLabel(p,text=t,font=F["small"],text_color=C["text_mid"]).grid(row=row,column=0,sticky="w",padx=18,pady=(8,2))
    def _inp(self,p,row,var,ph=""):
        ctk.CTkEntry(p,textvariable=var,placeholder_text=ph,fg_color=C["bg3"],border_color=C["border2"],
            text_color=C["text"],font=F["body"],height=42,corner_radius=10).grid(row=row,column=0,sticky="ew",padx=16,pady=(0,4))
    def _opt(self,p,row,var,values):
        ctk.CTkOptionMenu(p,variable=var,values=values,fg_color=C["bg3"],button_color=C["green"],
            button_hover_color=C["green_d"],dropdown_fg_color=C["bg3"],dropdown_hover_color=C["bg4"],
            text_color=C["text"],dropdown_text_color=C["text"],font=F["body"],height=42,corner_radius=10
        ).grid(row=row,column=0,sticky="ew",padx=16,pady=(0,4))
    def _seg(self,p,row,var,values):
        ctk.CTkSegmentedButton(p,variable=var,values=values,fg_color=C["bg3"],
            selected_color=C["green"],selected_hover_color=C["green_d"],
            unselected_color=C["bg3"],unselected_hover_color=C["bg4"],
            text_color=C["text"],font=F["small"],height=40,corner_radius=10
        ).grid(row=row,column=0,sticky="ew",padx=16,pady=(0,4))
    def _set_g(self,s):
        for v in self.gvars.values(): v.set(s)

    def _imc(self):
        try:
            p,a=float(self.v_peso.get()),float(self.v_altura.get())/100; imc=p/(a*a)
            if imc<18.5:   cat,cor="Abaixo do peso",C["warning"]
            elif imc<25.0: cat,cor="Peso normal",C["success"]
            elif imc<30.0: cat,cor="Sobrepeso",C["warning"]
            else:           cat,cor="Obesidade",C["error"]
            self.imc_v.configure(text=f"{imc:.1f}",text_color=cor)
            self.imc_c.configure(text=cat,text_color=cor)
        except:
            self.imc_v.configure(text="--",text_color=C["green_l"])
            self.imc_c.configure(text="Preencha altura e peso",text_color=C["text_dim"])

    def _validar_dados(self):
        for var,nome in [(self.v_idade,"Idade"),(self.v_altura,"Altura"),(self.v_peso,"Peso"),(self.v_carga,"Carga máxima")]:
            v=var.get().strip()
            if not v: messagebox.showerror("Campo obrigatório",f"Preencha: {nome}"); return False
            try: float(v)
            except: messagebox.showerror("Valor inválido",f"{nome} deve ser um número."); return False
        try:
            dias=int(self.v_dias.get())
            if not 1<=dias<=7: raise ValueError
        except: messagebox.showerror("Valor inválido","Dias deve ser entre 1 e 7."); return False
        grupos=[k for k,v in self.gvars.items() if v.get()]
        if not grupos: messagebox.showerror("Grupos musculares","Selecione ao menos um grupo."); return False
        return True

    def _gerar(self):
        if not self._validar_dados(): return
        data={"nome":self.v_nome.get().strip(),"idade":self.v_idade.get(),"altura":self.v_altura.get(),
              "peso":self.v_peso.get(),"sexo":self.v_sexo.get(),"objetivo":self.v_obj.get(),
              "condicionamento":self.v_cond.get(),"local":self.v_local.get(),"carga":self.v_carga.get(),
              "dias":self.v_dias.get(),"duracao":self.v_dur.get(),
              "grupos":[k for k,v in self.gvars.items() if v.get()]}

        # Abre tela de loading animada
        self.lbl_status.configure(text="Analisando...",text_color=C["green_l"])
        TelaLoading(self, self._foto_path or "", lambda: self._finalizar(data))

    def _finalizar(self,data):
        t=gerar_dados(data)
        self.painel.renderizar(t, foto_path=self._foto_path)
        self._ultimo=t
        self.lbl_status.configure(text="✅  Treino gerado!",text_color=C["success"])
        if self._usuario:
            db_inc(self._usuario["email"])
            db_salvar_historico(self._usuario["email"], t)
            self._usuario["treinos"]=self._usuario.get("treinos",0)+1
            self._refresh_top()

    def _limpar(self):
        self.painel._placeholder()
        self.lbl_status.configure(text="Pronto para gerar",text_color=C["text_dim"])
        self._ultimo=None; self._foto_path=None
        self._ir_step1()

    def _copiar(self):
        if not self._ultimo: messagebox.showinfo("Nada para copiar","Gere um treino primeiro!"); return
        t=self._ultimo; a=t["atleta"]
        ls=["="*58,"  ARNO AI — TREINO PERSONALIZADO","="*58,"",
            f"  Atleta : {a.get('nome') or 'Atleta'}",
            f"  Dados  : {a['idade']} anos | {a['altura']} cm | {a['peso']} kg | {a['sexo']}",
            f"  IMC    : {t['imc_val']} ({t['imc_cat']})",
            f"  Objetivo: {a['objetivo']}",
            f"  Nível  : {a['condicionamento']} | Local: {a['local']} | {a['dias']} dias/sem | {a['duracao']} min",
            "","-"*58,"  AQUECIMENTO","-"*58,""]
        for i,aq in enumerate(t["aquec"],1): ls.append(f"  {i}. {aq}")
        ls+=["","-"*58,"  TREINO PRINCIPAL","-"*58,""]
        for grupo,exs in t["exs"].items():
            ls+=[f"  ── {grupo.upper()} ──",""]
            for i,ex in enumerate(exs,1):
                ls+=[f"  {i}. {ex['nome']}",
                     f"     {ex['series']}× {ex['reps']} reps  |  Carga: {ex['carga']}  |  Descanso: {ex['descanso']}",
                     f"     Dica: {ex['dica']}",f"     Video: {ex['yt']}",""]
        ls+=["-"*58,"  DIVISÃO SEMANAL","-"*58,""]
        for i,d in enumerate(t["div"],1): ls.append(f"  Dia {i}: {d}")
        ls+=["","="*58,f"  Gerado por ARNO AI  |  {datetime.now().strftime('%d/%m/%Y %H:%M')}","="*58]
        self.clipboard_clear(); self.clipboard_append("\n".join(ls))
        self.btn_cp.configure(text="✅  Copiado!",text_color=C["success"])
        self.after(2500,lambda: self.btn_cp.configure(text="📋  Copiar",text_color=C["text_mid"]))

    def _abrir_historico(self):
        if not self._usuario:
            messagebox.showinfo("Histórico","Faça login para ver seu histórico."); return
        TelaHistorico(self, self._usuario["email"], on_recarregar=self._carregar_do_historico)

    def _abrir_perfil(self):
        if not self._usuario:
            messagebox.showinfo("Perfil","Faça login para acessar seu perfil."); return
        TelaPerfil(self, self._usuario, on_atualizar=self._on_perfil_atualizado)

    def _on_perfil_atualizado(self, user):
        self._usuario=user
        self._refresh_top()

    def _exportar_pdf(self):
        if not self._ultimo:
            messagebox.showinfo("Exportar PDF","Gere um treino primeiro!"); return
        caminho=filedialog.asksaveasfilename(
            title="Salvar treino como PDF",
            defaultextension=".pdf",
            filetypes=[("PDF","*.pdf"),("Todos","*.*")],
            initialfile=f"treino_arno_{datetime.now().strftime('%d%m%Y_%H%M')}.pdf"
        )
        if not caminho: return
        try:
            _gerar_pdf(self._ultimo, caminho)
            messagebox.showinfo("PDF Exportado",
                f"Treino salvo com sucesso!\n\n{caminho}")
        except Exception as e:
            messagebox.showerror("Erro ao gerar PDF",
                f"Nao foi possivel gerar o PDF.\n\nErro: {e}\n\nDica: pip install reportlab")

    def _carregar_do_historico(self, entrada):
        """Carrega um treino do histórico no painel de resultado."""
        # Reconstrói o objeto de treino a partir da entrada salva
        t = {
            "atleta":   entrada["atleta"],
            "imc_val":  entrada["imc_val"],
            "imc_cat":  entrada["imc_cat"],
            "aviso_imc":entrada.get("aviso_imc", False),
            "aquec":    entrada["aquec"],
            "exs":      entrada["exs"],
            "along":    entrada["along"],
            "div":      entrada["div"],
            "dicas":    entrada["dicas"],
            "nutri":    entrada["nutri"],
            "frase":    entrada["frase"],
        }
        self.painel.renderizar(t)
        self._ultimo = t
        self.lbl_status.configure(
            text=f"📂  Histórico: {entrada['data']} às {entrada['hora']}",
            text_color=C["green_l"])


# ╔══════════════════════════════════════════════════════════╗
# ║                  EXPORTAR PDF                            ║
# ╚══════════════════════════════════════════════════════════╝
def _gerar_pdf(t, caminho):
    """Gera um PDF profissional do treino usando reportlab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.enums import TA_LEFT, TA_CENTER

    doc = SimpleDocTemplate(caminho, pagesize=A4,
                            rightMargin=20*mm, leftMargin=20*mm,
                            topMargin=20*mm, bottomMargin=20*mm)
    story = []
    GREEN  = colors.HexColor("#16a34a")
    GREEN2 = colors.HexColor("#052e16")
    DARK   = colors.HexColor("#0f0f14")
    GRAY   = colors.HexColor("#ccccdd")
    WHITE  = colors.white

    styles = getSampleStyleSheet()
    sty_titulo = ParagraphStyle("titulo",fontSize=22,fontName="Helvetica-Bold",
                                textColor=WHITE,spaceAfter=2,leading=26)
    sty_sub    = ParagraphStyle("sub",fontSize=10,fontName="Helvetica",
                                textColor=GRAY,spaceAfter=8)
    sty_sec    = ParagraphStyle("sec",fontSize=12,fontName="Helvetica-Bold",
                                textColor=GREEN,spaceBefore=14,spaceAfter=4)
    sty_body   = ParagraphStyle("body",fontSize=9,fontName="Helvetica",
                                textColor=WHITE,leading=14,spaceAfter=3)
    sty_dica   = ParagraphStyle("dica",fontSize=8,fontName="Helvetica-Oblique",
                                textColor=GRAY,leading=12,spaceAfter=2)

    a = t["atleta"]

    # ── Cabeçalho ──────────────────────────────────────────────────────────
    header_data = [[
        Paragraph("⚡ ARNO AI", sty_titulo),
        Paragraph(f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}", sty_dica)
    ]]
    header_table = Table(header_data, colWidths=[120*mm, 50*mm])
    header_table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),DARK),
        ("LINEBELOW",(0,0),(-1,-1),2,GREEN),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("ALIGN",(1,0),(1,0),"RIGHT"),
        ("TOPPADDING",(0,0),(-1,-1),10),
        ("BOTTOMPADDING",(0,0),(-1,-1),10),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 8*mm))

    # ── Perfil ──────────────────────────────────────────────────────────────
    story.append(Paragraph("PERFIL DO ATLETA", sty_sec))
    story.append(HRFlowable(width="100%",thickness=1,color=GREEN))
    story.append(Spacer(1,3*mm))
    perfil_data = [
        ["Atleta",     a.get("nome") or "Atleta",       "IMC",      f"{t.get('imc_val','--')} ({t.get('imc_cat','--')})"],
        ["Idade",      f"{a.get('idade','?')} anos",    "Objetivo", a.get("objetivo","")],
        ["Altura",     f"{a.get('altura','?')} cm",     "Nível",    a.get("condicionamento","")],
        ["Peso",       f"{a.get('peso','?')} kg",       "Local",    a.get("local","")],
        ["Dias/sem",   a.get("dias","?"),                "Duração",  f"{a.get('duracao','?')} min"],
    ]
    pt = Table(perfil_data, colWidths=[28*mm,52*mm,28*mm,62*mm])
    pt.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),DARK),
        ("TEXTCOLOR",(0,0),(-1,-1),WHITE),
        ("FONTNAME",(0,0),(0,-1),"Helvetica-Bold"),
        ("FONTNAME",(2,0),(2,-1),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),8),
        ("TEXTCOLOR",(0,0),(0,-1),GREEN),
        ("TEXTCOLOR",(2,0),(2,-1),GREEN),
        ("ROWBACKGROUNDS",(0,0),(-1,-1),[DARK, colors.HexColor("#16161e")]),
        ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#2e2e3e")),
        ("TOPPADDING",(0,0),(-1,-1),5),
        ("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),6),
    ]))
    story.append(pt)
    story.append(Spacer(1,6*mm))

    # ── Aquecimento ─────────────────────────────────────────────────────────
    story.append(Paragraph("🔥  AQUECIMENTO  (5-10 min)", sty_sec))
    story.append(HRFlowable(width="100%",thickness=1,color=GREEN))
    story.append(Spacer(1,2*mm))
    for i,aq in enumerate(t.get("aquec",[]),1):
        story.append(Paragraph(f"{i}.  {aq}", sty_body))
    story.append(Spacer(1,4*mm))

    # ── Exercícios ──────────────────────────────────────────────────────────
    story.append(Paragraph("💪  TREINO PRINCIPAL", sty_sec))
    story.append(HRFlowable(width="100%",thickness=1,color=GREEN))
    story.append(Spacer(1,2*mm))
    for grupo, exercicios in t.get("exs",{}).items():
        story.append(Paragraph(f"▌  {grupo.upper()}", ParagraphStyle(
            "grp",fontSize=10,fontName="Helvetica-Bold",
            textColor=colors.HexColor("#4ade80"),spaceBefore=8,spaceAfter=3)))
        ex_data=[["#","Exercício","Séries","Carga","Descanso"]]
        for idx,ex in enumerate(exercicios,1):
            ex_data.append([
                str(idx), ex.get("nome",""),
                f"{ex.get('series','?')}× {ex.get('reps','?')}",
                ex.get("carga",""), ex.get("descanso","")
            ])
        et=Table(ex_data, colWidths=[8*mm,72*mm,28*mm,22*mm,28*mm])
        et.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),GREEN),
            ("TEXTCOLOR",(0,0),(-1,0),colors.HexColor("#000000")),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
            ("FONTSIZE",(0,0),(-1,-1),8),
            ("TEXTCOLOR",(0,1),(-1,-1),WHITE),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[DARK,colors.HexColor("#16161e")]),
            ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#2e2e3e")),
            ("TOPPADDING",(0,0),(-1,-1),4),
            ("BOTTOMPADDING",(0,0),(-1,-1),4),
            ("LEFTPADDING",(0,0),(-1,-1),5),
            ("ALIGN",(0,0),(0,-1),"CENTER"),
        ]))
        story.append(et)
        # Dicas
        for ex in exercicios:
            if ex.get("dica"):
                story.append(Paragraph(f"   💡 {ex['nome']}: {ex['dica']}", sty_dica))
        story.append(Spacer(1,2*mm))

    # ── Volta à Calma ───────────────────────────────────────────────────────
    story.append(Paragraph("🧘  VOLTA À CALMA  (5-10 min)", sty_sec))
    story.append(HRFlowable(width="100%",thickness=1,color=GREEN))
    story.append(Spacer(1,2*mm))
    for i,al in enumerate(t.get("along",[]),1):
        story.append(Paragraph(f"{i}.  {al}", sty_body))
    story.append(Spacer(1,4*mm))

    # ── Divisão Semanal ─────────────────────────────────────────────────────
    story.append(Paragraph("📅  DIVISÃO SEMANAL", sty_sec))
    story.append(HRFlowable(width="100%",thickness=1,color=GREEN))
    story.append(Spacer(1,2*mm))
    div = t.get("div",[])
    div_data=[]
    for i,d in enumerate(div,1):
        div_data.append([Paragraph(f"DIA {i}",ParagraphStyle("dn",fontSize=8,
            fontName="Helvetica-Bold",textColor=GREEN)),
            Paragraph(d,sty_body)])
    if div_data:
        dt=Table(div_data,colWidths=[20*mm,150*mm])
        dt.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),DARK),
            ("ROWBACKGROUNDS",(0,0),(-1,-1),[DARK,colors.HexColor("#16161e")]),
            ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#2e2e3e")),
            ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
            ("LEFTPADDING",(0,0),(-1,-1),6),
        ]))
        story.append(dt)
    story.append(Spacer(1,4*mm))

    # ── Dicas e Nutrição ────────────────────────────────────────────────────
    story.append(Paragraph("⚡  DICAS PERSONALIZADAS", sty_sec))
    story.append(HRFlowable(width="100%",thickness=1,color=GREEN))
    story.append(Spacer(1,2*mm))
    for i,d in enumerate(t.get("dicas",[]),1):
        story.append(Paragraph(f"{i}.  {d}", sty_body))
    story.append(Spacer(1,4*mm))

    story.append(Paragraph("🥗  NUTRIÇÃO BÁSICA", sty_sec))
    story.append(HRFlowable(width="100%",thickness=1,color=GREEN))
    story.append(Spacer(1,2*mm))
    for n in t.get("nutri",[]):
        story.append(Paragraph(f"•  {n}", sty_body))

    # ── Rodapé ──────────────────────────────────────────────────────────────
    story.append(Spacer(1,8*mm))
    story.append(HRFlowable(width="100%",thickness=1,color=GREEN))
    story.append(Paragraph(
        f"Bora treinar, {a.get('nome') or 'Atleta'}! Consistência é a chave.  ⚡  |  Gerado por ARNO AI",
        ParagraphStyle("rod",fontSize=8,fontName="Helvetica-Oblique",
                       textColor=GREEN,alignment=TA_CENTER,spaceBefore=4)))

    doc.build(story)


# ╔══════════════════════════════════════════════════════════╗
# ║                   TELA DE PERFIL                         ║
# ╚══════════════════════════════════════════════════════════╝
class TelaPerfil(ctk.CTkToplevel):
    """Tela de perfil: editar dados + recuperar senha + ver estatísticas."""

    def __init__(self, master, usuario, on_atualizar=None):
        super().__init__(master)
        self._usuario     = usuario
        self.on_atualizar = on_atualizar
        self._show_pw     = False
        self._aba         = "perfil"   # "perfil" | "stats" | "senha"

        self.title("ARNO AI — Meu Perfil")
        self.geometry("720x620")
        self.resizable(False, False)
        self.configure(fg_color=C["bg"])
        self.grab_set()
        self.lift()
        self.focus_force()
        self.after(10, self._center)
        self._build()

    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build(self):
        for w in self.winfo_children(): w.destroy()
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Header ──────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color=C["bg2"], corner_radius=0, height=56)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        ctk.CTkFrame(hdr, fg_color=C["green"], height=2, corner_radius=0).pack(fill="x", side="top")
        hi = ctk.CTkFrame(hdr, fg_color="transparent")
        hi.pack(fill="both", expand=True, padx=20)
        ctk.CTkLabel(hi, text="👤  MEU PERFIL",
                     font=F["header"], text_color=C["text"]).pack(side="left", pady=16)

        # Abas
        for lbl, aba in [("✏️  Editar Dados","perfil"),
                         ("📊  Estatísticas","stats"),
                         ("🔑  Alterar Senha","senha")]:
            ativo = self._aba == aba
            ctk.CTkButton(hi, text=lbl, font=F["small_b"],
                          width=130, height=28, corner_radius=6,
                          fg_color=C["green"] if ativo else C["bg4"],
                          hover_color=C["green_d"] if ativo else C["bg5"],
                          text_color="#000" if ativo else C["text_mid"],
                          command=lambda a=aba: self._mudar_aba(a)
                          ).pack(side="right", padx=(0,6), pady=14)

        # ── Conteúdo ─────────────────────────────────────────────────────────
        body = ctk.CTkScrollableFrame(self, fg_color=C["bg"], corner_radius=0,
                                      scrollbar_fg_color=C["bg"],
                                      scrollbar_button_color=C["green"])
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)

        if self._aba == "perfil":
            self._aba_perfil(body)
        elif self._aba == "stats":
            self._aba_stats(body)
        else:
            self._aba_senha(body)

    def _mudar_aba(self, aba):
        self._aba = aba
        self._build()

    # ── ABA EDITAR DADOS ─────────────────────────────────────────────────────
    def _aba_perfil(self, body):
        u = self._usuario
        ctk.CTkFrame(body, fg_color="transparent", height=20).grid(row=0, column=0)

        # Avatar grande
        av_f = ctk.CTkFrame(body, fg_color="transparent")
        av_f.grid(row=1, column=0, pady=(0, 6))
        av = ctk.CTkFrame(av_f, fg_color=C["green"], corner_radius=40, width=80, height=80)
        av.pack_propagate(False); av.pack()
        inits = "".join(w[0].upper() for w in (u.get("nome") or "AT").split()[:2])
        ctk.CTkLabel(av, text=inits, font=F["title"], text_color="#000").pack(expand=True)
        ctk.CTkLabel(body, text=f"Membro desde {u.get('criado_em','?')}",
                     font=F["tiny"], text_color=C["text_dim"]).grid(row=2, column=0, pady=(0,16))

        form = ctk.CTkFrame(body, fg_color=C["bg3"], corner_radius=14)
        form.grid(row=3, column=0, sticky="ew", padx=40, pady=(0,8))
        form.grid_columnconfigure(0, weight=1)

        def campo(parent, lbl, val, row_n, show=""):
            ctk.CTkLabel(parent, text=lbl, font=F["small"],
                         text_color=C["text_dim"]).grid(row=row_n*2, column=0,
                                                        sticky="w", padx=20, pady=(12,2))
            e = ctk.CTkEntry(parent, fg_color=C["bg4"], border_color=C["border2"],
                             text_color=C["text"], font=F["body"],
                             height=42, corner_radius=10, show=show)
            e.insert(0, val)
            e.grid(row=row_n*2+1, column=0, sticky="ew", padx=20, pady=(0,4))
            return e

        self.e_nome  = campo(form, "Nome completo",  u.get("nome",""),  0)
        self.e_email = campo(form, "E-mail",          u.get("email",""), 1)

        ctk.CTkLabel(form, text="Nova senha (deixe em branco para manter)",
                     font=F["small"], text_color=C["text_dim"]).grid(
            row=4, column=0, sticky="w", padx=20, pady=(12,2))
        pw_row = ctk.CTkFrame(form, fg_color="transparent")
        pw_row.grid(row=5, column=0, sticky="ew", padx=20, pady=(0,4))
        pw_row.grid_columnconfigure(0, weight=1)
        self.e_pw = ctk.CTkEntry(pw_row, placeholder_text="Nova senha (opcional)",
                                 show="•", fg_color=C["bg4"], border_color=C["border2"],
                                 text_color=C["text"], font=F["body"],
                                 height=42, corner_radius=10)
        self.e_pw.grid(row=0, column=0, sticky="ew", padx=(0,8))
        ctk.CTkButton(pw_row, text="👁", width=42, height=42,
                      fg_color=C["bg4"], hover_color=C["bg5"],
                      text_color=C["green"], font=F["body"], corner_radius=10,
                      command=self._toggle_pw).grid(row=0, column=1)
        ctk.CTkFrame(form, fg_color="transparent", height=10).grid(row=6, column=0)

        self.msg_p = ctk.CTkLabel(body, text="", font=F["small"], text_color=C["error"])
        self.msg_p.grid(row=4, column=0, pady=(4,0))

        ctk.CTkButton(body, text="💾  Salvar Alterações",
                      font=F["btn_lg"], height=48, corner_radius=12,
                      fg_color=C["green"], hover_color=C["green_d"],
                      text_color="#000", command=self._salvar_perfil
                      ).grid(row=5, column=0, sticky="ew", padx=40, pady=(8,24))

    def _toggle_pw(self):
        self._show_pw = not self._show_pw
        self.e_pw.configure(show="" if self._show_pw else "•")

    def _salvar_perfil(self):
        nome  = self.e_nome.get().strip()
        email = self.e_email.get().strip()
        pw    = self.e_pw.get() if hasattr(self,"e_pw") else ""
        ok, msg, u = db_atualizar_perfil(
            self._usuario["email"], nome, email, pw or None)
        if ok:
            self._usuario = u
            self.msg_p.configure(text="✅  "+msg, text_color=C["success"])
            if self.on_atualizar: self.on_atualizar(u)
            self.after(1500, self._build)
        else:
            self.msg_p.configure(text=msg, text_color=C["error"])

    # ── ABA ESTATÍSTICAS ─────────────────────────────────────────────────────
    def _aba_stats(self, body):
        stats = db_stats_usuario(self._usuario["email"])
        ctk.CTkFrame(body, fg_color="transparent", height=20).grid(row=0, column=0)

        if not stats:
            ph = ctk.CTkFrame(body, fg_color="transparent")
            ph.grid(row=1, column=0, pady=60)
            ctk.CTkLabel(ph, text="📊", font=("Segoe UI",42)).pack(pady=(0,12))
            ctk.CTkLabel(ph, text="Sem dados ainda",
                         font=F["body"], text_color=C["text_dim"]).pack()
            ctk.CTkLabel(ph, text="Gere alguns treinos para ver suas estatísticas!",
                         font=F["small"], text_color=C["text_dim"]).pack(pady=(4,0))
            return

        row = 1

        # ── Cards de métricas ──────────────────────────────────────────────
        metrics = [
            ("🏋️",  "Treinos Gerados",    str(stats["total"]),         C["green_l"]),
            ("🔥",  "Sequência Atual",    f"{stats['sequencia']} dias", C["warning"]),
            ("💪",  "Grupo Favorito",     stats["top_grupo"],           C["green_l"]),
            ("⚖️",  "Carga Média",        f"{stats['carga_media']} kg", C["text_mid"]),
            ("🎯",  "Objetivo Principal", stats["top_obj"].split()[0],  C["green_l"]),
            ("📍",  "Local Favorito",     stats["top_local"],           C["text_mid"]),
        ]

        grid_f = ctk.CTkFrame(body, fg_color="transparent")
        grid_f.grid(row=row, column=0, sticky="ew", padx=30, pady=(0,12)); row+=1
        for c in range(3): grid_f.grid_columnconfigure(c, weight=1)
        for i, (emoji, lbl, val, cor) in enumerate(metrics):
            r2, c2 = divmod(i, 3)
            card = ctk.CTkFrame(grid_f, fg_color=C["bg3"], corner_radius=12)
            card.grid(row=r2, column=c2, padx=5, pady=5, sticky="nsew")
            ctk.CTkLabel(card, text=emoji, font=("Segoe UI",22)).pack(pady=(14,4))
            ctk.CTkLabel(card, text=val, font=F["title2"], text_color=cor).pack()
            ctk.CTkLabel(card, text=lbl, font=F["tiny"],
                         text_color=C["text_dim"]).pack(pady=(2,14))

        # ── Grupos mais treinados ──────────────────────────────────────────
        grupos_count = stats.get("grupos_count", {})
        if grupos_count:
            ctk.CTkLabel(body, text="💪  Grupos mais treinados",
                         font=F["body_b"], text_color=C["text"]).grid(
                row=row, column=0, sticky="w", padx=34, pady=(8,6)); row+=1

            bar_frame = ctk.CTkFrame(body, fg_color="transparent")
            bar_frame.grid(row=row, column=0, sticky="ew", padx=30, pady=(0,12)); row+=1
            bar_frame.grid_columnconfigure(0, weight=1)

            max_val = max(grupos_count.values())
            sorted_g = sorted(grupos_count.items(), key=lambda x:-x[1])
            for gi, (g, cnt) in enumerate(sorted_g[:8]):
                pct = cnt / max_val
                bar_row = ctk.CTkFrame(bar_frame, fg_color="transparent")
                bar_row.grid(row=gi, column=0, sticky="ew", pady=3)
                bar_row.grid_columnconfigure(1, weight=1)

                ctk.CTkLabel(bar_row, text=g, font=F["small"],
                             text_color=C["text_soft"], width=90, anchor="w"
                             ).grid(row=0, column=0, padx=(0,10))

                bar_bg = ctk.CTkFrame(bar_row, fg_color=C["bg4"],
                                      height=20, corner_radius=4)
                bar_bg.grid(row=0, column=1, sticky="ew")
                bar_bg.grid_propagate(False)
                bar_bg.grid_columnconfigure(0, weight=1)

                bar_fill = ctk.CTkFrame(bar_bg, fg_color=C["green"],
                                        height=20, corner_radius=4)
                bar_fill.place(relx=0, rely=0, relwidth=pct, relheight=1)

                ctk.CTkLabel(bar_row, text=str(cnt), font=F["tiny"],
                             text_color=C["green_l"], width=24
                             ).grid(row=0, column=2, padx=(8,0))

        # ── Objetivos ──────────────────────────────────────────────────────
        obj_count = stats.get("obj_count", {})
        if obj_count:
            ctk.CTkLabel(body, text="🎯  Objetivos",
                         font=F["body_b"], text_color=C["text"]).grid(
                row=row, column=0, sticky="w", padx=34, pady=(8,6)); row+=1
            obj_f = ctk.CTkFrame(body, fg_color=C["bg3"], corner_radius=12)
            obj_f.grid(row=row, column=0, sticky="ew", padx=30, pady=(0,24)); row+=1
            for oi, (obj, cnt) in enumerate(sorted(obj_count.items(), key=lambda x:-x[1])):
                oi_row = ctk.CTkFrame(obj_f, fg_color=C["bg4"] if oi%2==0 else "transparent",
                                      corner_radius=6)
                oi_row.pack(fill="x", padx=8, pady=2)
                oi_row.grid_columnconfigure(0, weight=1)
                ctk.CTkLabel(oi_row, text=obj, font=F["small"],
                             text_color=C["text_soft"], anchor="w"
                             ).grid(row=0, column=0, sticky="w", padx=12, pady=6)
                ctk.CTkLabel(oi_row, text=f"{cnt}x", font=F["small_b"],
                             text_color=C["green_l"]
                             ).grid(row=0, column=1, padx=12)

    # ── ABA ALTERAR SENHA ────────────────────────────────────────────────────
    def _aba_senha(self, body):
        ctk.CTkFrame(body, fg_color="transparent", height=30).grid(row=0, column=0)

        icon_f = ctk.CTkFrame(body, fg_color="transparent")
        icon_f.grid(row=1, column=0, pady=(0,6))
        ib = ctk.CTkFrame(icon_f, fg_color=C["green_dim"], corner_radius=30, width=60, height=60)
        ib.pack_propagate(False); ib.pack()
        ctk.CTkLabel(ib, text="🔑", font=("Segoe UI",22)).pack(expand=True)

        ctk.CTkLabel(body, text="Esqueceu sua senha?",
                     font=F["title2"], text_color=C["text"]).grid(row=2, column=0, pady=(0,4))
        ctk.CTkLabel(body,
                     text="Digite seu e-mail para receber um código de recuperação.",
                     font=F["small"], text_color=C["text_dim"]).grid(row=3, column=0, pady=(0,20))

        form = ctk.CTkFrame(body, fg_color=C["bg3"], corner_radius=14)
        form.grid(row=4, column=0, sticky="ew", padx=60, pady=(0,8))
        form.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(form, text="E-mail cadastrado", font=F["small"],
                     text_color=C["text_dim"]).grid(row=0, column=0, sticky="w", padx=20, pady=(14,2))
        self.e_rec_email = ctk.CTkEntry(form, placeholder_text="seu@email.com",
                                        fg_color=C["bg4"], border_color=C["border2"],
                                        text_color=C["text"], font=F["body"],
                                        height=42, corner_radius=10)
        self.e_rec_email.insert(0, self._usuario.get("email",""))
        self.e_rec_email.grid(row=1, column=0, sticky="ew", padx=20, pady=(0,4))

        self.codigo_frame = ctk.CTkFrame(form, fg_color="transparent")
        self.codigo_frame.grid(row=2, column=0, sticky="ew")
        self.codigo_frame.grid_columnconfigure(0, weight=1)
        self._codigo_visivel = False

        ctk.CTkFrame(form, fg_color="transparent", height=8).grid(row=3, column=0)

        self.msg_s = ctk.CTkLabel(body, text="", font=F["small"], text_color=C["error"])
        self.msg_s.grid(row=5, column=0, pady=(4,0))

        self.btn_rec = ctk.CTkButton(body, text="📨  Enviar Código de Recuperação",
                                     font=F["btn_lg"], height=48, corner_radius=12,
                                     fg_color=C["green"], hover_color=C["green_d"],
                                     text_color="#000", command=self._enviar_codigo)
        self.btn_rec.grid(row=6, column=0, sticky="ew", padx=60, pady=(8,6))

        ctk.CTkLabel(body,
                     text="⚠  O código é exibido na tela (app desktop sem e-mail real).",
                     font=F["tiny_i"], text_color=C["text_dim"]).grid(
            row=7, column=0, pady=(0,24))

    def _enviar_codigo(self):
        email = self.e_rec_email.get().strip()
        ok, resultado = db_recuperar_senha(email)
        if not ok:
            self.msg_s.configure(text=resultado, text_color=C["error"]); return

        codigo = resultado
        self.msg_s.configure(text="✅  Código gerado! Insira abaixo.", text_color=C["success"])
        self.btn_rec.configure(state="disabled", text="Código enviado ✓")

        # Mostra campos de código + nova senha
        for w in self.codigo_frame.winfo_children(): w.destroy()
        f = self.codigo_frame

        ctk.CTkLabel(f, text=f"Código de verificação:  {codigo}",
                     font=F["body_b"], text_color=C["green_l"]).grid(
            row=0, column=0, padx=20, pady=(12,6), sticky="w")
        ctk.CTkLabel(f, text="Digite o código acima:", font=F["small"],
                     text_color=C["text_dim"]).grid(row=1, column=0, sticky="w", padx=20, pady=(4,2))
        self.e_codigo = ctk.CTkEntry(f, placeholder_text="000000",
                                     fg_color=C["bg4"], border_color=C["border2"],
                                     text_color=C["text"], font=F["body"],
                                     height=42, corner_radius=10)
        self.e_codigo.grid(row=2, column=0, sticky="ew", padx=20, pady=(0,4))

        ctk.CTkLabel(f, text="Nova senha:", font=F["small"],
                     text_color=C["text_dim"]).grid(row=3, column=0, sticky="w", padx=20, pady=(8,2))
        self.e_nova_pw = ctk.CTkEntry(f, placeholder_text="Mínimo 6 caracteres",
                                      show="•", fg_color=C["bg4"], border_color=C["border2"],
                                      text_color=C["text"], font=F["body"],
                                      height=42, corner_radius=10)
        self.e_nova_pw.grid(row=4, column=0, sticky="ew", padx=20, pady=(0,4))

        ctk.CTkButton(f, text="🔒  Redefinir Senha",
                      font=F["btn"], height=44, corner_radius=10,
                      fg_color=C["green"], hover_color=C["green_d"],
                      text_color="#000", command=lambda: self._redefinir(email)
                      ).grid(row=5, column=0, sticky="ew", padx=20, pady=(8,14))

    def _redefinir(self, email):
        codigo    = self.e_codigo.get().strip()
        nova_pw   = self.e_nova_pw.get()
        ok, msg   = db_redefinir_senha(email, codigo, nova_pw)
        if ok:
            self.msg_s.configure(text="✅  "+msg, text_color=C["success"])
            self.after(1500, self._build)
        else:
            self.msg_s.configure(text=msg, text_color=C["error"])


# ╔══════════════════════════════════════════════════════════╗
# ║                  TELA DE HISTÓRICO                       ║
# ╚══════════════════════════════════════════════════════════╝
class TelaHistorico(ctk.CTkToplevel):
    """Janela de histórico de treinos do usuário."""

    def __init__(self, master, email, on_recarregar=None):
        super().__init__(master)
        self.email          = email
        self.on_recarregar  = on_recarregar
        self._entrada_atual = None  # entrada sendo visualizada

        self.title("ARNO AI — Histórico de Treinos")
        self.geometry("1100x680")
        self.minsize(900, 560)
        self.configure(fg_color=C["bg"])
        self.grab_set()
        self.lift()
        self.focus_force()
        self.after(10, self._center)
        self._build()

    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

    def _build(self):
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # ── Header ──────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self, fg_color=C["bg2"], corner_radius=0, height=56)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.grid_propagate(False)
        ctk.CTkFrame(hdr, fg_color=C["green"], height=2, corner_radius=0).pack(fill="x", side="top")

        hi = ctk.CTkFrame(hdr, fg_color="transparent")
        hi.pack(fill="both", expand=True, padx=20)

        ctk.CTkLabel(hi, text="📂  HISTÓRICO DE TREINOS",
                     font=F["header"], text_color=C["text"]).pack(side="left", pady=16)

        # Botão limpar tudo
        ctk.CTkButton(hi, text="🗑  Limpar Tudo", font=F["tiny"],
                      width=110, height=26,
                      fg_color="transparent", hover_color=C["error_bg"],
                      text_color=C["error"], border_color=C["error"],
                      border_width=1, corner_radius=6,
                      command=self._limpar_tudo
                      ).pack(side="right", pady=14)

        self.lbl_count = ctk.CTkLabel(hi, text="",
                                      font=F["small"], text_color=C["text_dim"])
        self.lbl_count.pack(side="right", padx=12, pady=14)

        # ── Layout: lista esquerda + detalhe direita ─────────────────────────
        body = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        body.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=0, minsize=340)
        body.grid_columnconfigure(1, weight=1)

        # ── Painel esquerdo — lista de entradas ──────────────────────────────
        left_outer = ctk.CTkFrame(body, fg_color=C["bg2"], corner_radius=0)
        left_outer.grid(row=0, column=0, sticky="nsew")

        # Busca / filtro
        search_f = ctk.CTkFrame(left_outer, fg_color=C["bg3"], corner_radius=0, height=48)
        search_f.pack(fill="x")
        search_f.pack_propagate(False)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filtrar())
        ctk.CTkEntry(search_f, textvariable=self.search_var,
                     placeholder_text="🔍  Buscar treino...",
                     fg_color=C["bg4"], border_color=C["border2"],
                     text_color=C["text"], font=F["small"],
                     height=34, corner_radius=8
                     ).pack(fill="x", padx=12, pady=7)

        self.lista_frame = ctk.CTkScrollableFrame(
            left_outer, fg_color=C["bg2"], corner_radius=0,
            scrollbar_fg_color=C["bg2"],
            scrollbar_button_color=C["green"],
            scrollbar_button_hover_color=C["green_l"],
        )
        self.lista_frame.pack(fill="both", expand=True)
        self.lista_frame.grid_columnconfigure(0, weight=1)

        # ── Painel direito — detalhe ─────────────────────────────────────────
        right_outer = ctk.CTkFrame(body, fg_color=C["bg"], corner_radius=0)
        right_outer.grid(row=0, column=1, sticky="nsew")
        right_outer.grid_rowconfigure(0, weight=1)
        right_outer.grid_columnconfigure(0, weight=1)

        self.detalhe_frame = ctk.CTkScrollableFrame(
            right_outer, fg_color=C["bg"], corner_radius=0,
            scrollbar_fg_color=C["bg"],
            scrollbar_button_color=C["green"],
            scrollbar_button_hover_color=C["green_l"],
        )
        self.detalhe_frame.grid(row=0, column=0, sticky="nsew")
        self.detalhe_frame.grid_columnconfigure(0, weight=1)

        # Footer do detalhe
        det_footer = ctk.CTkFrame(right_outer, fg_color=C["bg2"],
                                  corner_radius=0, height=50)
        det_footer.grid(row=1, column=0, sticky="ew")
        det_footer.grid_propagate(False)

        bf = ctk.CTkFrame(det_footer, fg_color="transparent")
        bf.pack(side="right", padx=16, pady=10)

        self.btn_carregar = ctk.CTkButton(
            bf, text="⚡  Carregar este Treino",
            font=F["btn"], width=190, height=32,
            fg_color=C["green"], hover_color=C["green_d"],
            text_color="#000", corner_radius=8,
            command=self._carregar_selecionado, state="disabled"
        )
        self.btn_carregar.pack(side="right", padx=(8, 0))

        self.btn_del = ctk.CTkButton(
            bf, text="🗑  Deletar",
            font=F["small"], width=90, height=32,
            fg_color="transparent", hover_color=C["error_bg"],
            text_color=C["error"], border_color=C["error"],
            border_width=1, corner_radius=8,
            command=self._deletar_selecionado, state="disabled"
        )
        self.btn_del.pack(side="right")

        # Carrega dados
        self._entradas = db_carregar_historico(self.email)
        self._renderizar_lista(self._entradas)
        self._mostrar_placeholder_detalhe()

    # ── Lista ────────────────────────────────────────────────────────────────
    def _renderizar_lista(self, entradas):
        for w in self.lista_frame.winfo_children(): w.destroy()
        self.lbl_count.configure(
            text=f"{len(entradas)} treino{'s' if len(entradas)!=1 else ''}")

        if not entradas:
            empty = ctk.CTkFrame(self.lista_frame, fg_color="transparent")
            empty.grid(row=0, column=0, pady=60)
            ctk.CTkLabel(empty, text="📭", font=("Segoe UI", 36),
                         text_color=C["text_dim"]).pack(pady=(0, 12))
            ctk.CTkLabel(empty, text="Nenhum treino no histórico",
                         font=F["body"], text_color=C["text_dim"]).pack()
            ctk.CTkLabel(empty, text="Gere seu primeiro treino para começar!",
                         font=F["small"], text_color=C["text_dim"]).pack(pady=(4,0))
            return

        for idx, entrada in enumerate(entradas):
            self._card_lista(idx, entrada)

    def _card_lista(self, idx, entrada):
        atleta  = entrada.get("atleta", {})
        grupos  = entrada.get("grupos", [])
        n_exs   = entrada.get("total_exercicios", 0)
        obj_raw = atleta.get("objetivo", "")
        obj_short = obj_raw.split()[0] if obj_raw else "—"

        card = ctk.CTkFrame(self.lista_frame, fg_color=C["bg3"],
                            corner_radius=10, cursor="hand2")
        card.grid(row=idx, column=0, sticky="ew", padx=10, pady=4)
        card.grid_columnconfigure(0, weight=1)
        self._bind_card(card, entrada)

        # Faixa lateral verde
        ctk.CTkFrame(card, fg_color=C["green"], width=4,
                     corner_radius=2).grid(row=0, column=0,
                                           rowspan=3, sticky="ns",
                                           padx=(10, 0), pady=10)

        # Data e hora
        top_r = ctk.CTkFrame(card, fg_color="transparent")
        top_r.grid(row=0, column=1, sticky="ew", padx=(10, 12), pady=(10, 2))
        top_r.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(top_r, text=f"{entrada.get('data','?')}  {entrada.get('hora','')}",
                     font=F["small_b"], text_color=C["text"],
                     anchor="w").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(top_r, text=f"#{idx+1}",
                     font=F["tiny"], text_color=C["text_dim"]).grid(row=0, column=1, sticky="e")

        # Nome do atleta + objetivo
        ctk.CTkLabel(card,
                     text=f"{atleta.get('nome') or 'Atleta'}  ·  {obj_short}",
                     font=F["tiny"], text_color=C["text_mid"],
                     anchor="w").grid(row=1, column=1, sticky="w", padx=(10, 12))

        # Grupos como pills
        pill_frame = ctk.CTkFrame(card, fg_color="transparent")
        pill_frame.grid(row=2, column=1, sticky="w",
                        padx=(10, 12), pady=(4, 10))
        for g in grupos[:4]:
            b = ctk.CTkFrame(pill_frame, fg_color=C["green_dim"],
                             corner_radius=4)
            b.pack(side="left", padx=(0, 4))
            ctk.CTkLabel(b, text=g, font=F["tiny"],
                         text_color=C["green_l"]).pack(padx=6, pady=2)
        if len(grupos) > 4:
            b = ctk.CTkFrame(pill_frame, fg_color=C["bg4"], corner_radius=4)
            b.pack(side="left")
            ctk.CTkLabel(b, text=f"+{len(grupos)-4}",
                         font=F["tiny"], text_color=C["text_dim"]).pack(padx=6, pady=2)

        # Contador de exercícios
        ctk.CTkLabel(card, text=f"{n_exs} exercícios",
                     font=F["tiny"], text_color=C["text_dim"]).grid(
            row=2, column=2, padx=(0, 12), pady=(4, 10), sticky="e")

    def _bind_card(self, widget, entrada):
        """Bind clique recursivo em todos os filhos do card."""
        widget.bind("<Button-1>", lambda e, en=entrada: self._selecionar(en))
        for child in widget.winfo_children():
            self._bind_card(child, entrada)

    def _selecionar(self, entrada):
        self._entrada_atual = entrada
        self.btn_carregar.configure(state="normal")
        self.btn_del.configure(state="normal")
        self._mostrar_detalhe(entrada)

    # ── Detalhe ──────────────────────────────────────────────────────────────
    def _mostrar_placeholder_detalhe(self):
        for w in self.detalhe_frame.winfo_children(): w.destroy()
        ph = ctk.CTkFrame(self.detalhe_frame, fg_color="transparent")
        ph.grid(row=0, column=0, pady=80)
        ctk.CTkLabel(ph, text="👈", font=("Segoe UI", 40)).pack(pady=(0, 12))
        ctk.CTkLabel(ph, text="Selecione um treino na lista",
                     font=F["body"], text_color=C["text_dim"]).pack()
        ctk.CTkLabel(ph, text="para ver os detalhes completos",
                     font=F["small"], text_color=C["text_dim"]).pack(pady=(4, 0))

    def _mostrar_detalhe(self, entrada):
        for w in self.detalhe_frame.winfo_children(): w.destroy()
        df = self.detalhe_frame
        df.grid_columnconfigure(0, weight=1)
        row = 0

        def sp(h=10):
            nonlocal row
            ctk.CTkFrame(df, fg_color="transparent", height=h).grid(row=row, column=0); row+=1

        def sec(emoji, titulo, sub=""):
            nonlocal row
            sp(6)
            f = ctk.CTkFrame(df, fg_color="transparent")
            f.grid(row=row, column=0, sticky="ew", padx=20, pady=(10,2)); row+=1
            f.grid_columnconfigure(1, weight=1)
            badge = ctk.CTkFrame(f, fg_color=C["green"], corner_radius=8, width=32, height=32)
            badge.pack_propagate(False)
            badge.grid(row=0, column=0, rowspan=2, padx=(0, 10))
            ctk.CTkLabel(badge, text=emoji, font=("Segoe UI",14), text_color="#000").grid(row=0,column=0,pady=4)
            ctk.CTkLabel(f, text=titulo, font=F["header"], text_color=C["text"], anchor="w").grid(row=0,column=1,sticky="w")
            if sub: ctk.CTkLabel(f, text=sub, font=F["tiny"], text_color=C["text_dim"], anchor="w").grid(row=1,column=1,sticky="w")
            ctk.CTkFrame(df, fg_color=C["bg3"], height=1).grid(row=row,column=0,sticky="ew",padx=20,pady=(2,8)); row+=1

        atleta = entrada.get("atleta", {})
        sp(16)

        # ── Card Perfil ─────────────────────────────────────────────────────
        hero = ctk.CTkFrame(df, fg_color=C["bg3"], corner_radius=14)
        hero.grid(row=row, column=0, sticky="ew", padx=20, pady=(0,4)); row+=1
        hero.grid_columnconfigure(0, weight=1)
        ctk.CTkFrame(hero, fg_color=C["green"], height=3, corner_radius=0).grid(row=0,column=0,sticky="ew")

        hin = ctk.CTkFrame(hero, fg_color="transparent")
        hin.grid(row=1, column=0, sticky="ew", padx=18, pady=14)
        hin.grid_columnconfigure(1, weight=1)

        # Avatar
        av = ctk.CTkFrame(hin, fg_color=C["green"], corner_radius=22, width=44, height=44)
        av.pack_propagate(False); av.grid(row=0, column=0, rowspan=2, padx=(0,14))
        inits = "".join(w[0].upper() for w in (atleta.get("nome") or "AT").split()[:2])
        ctk.CTkLabel(av, text=inits, font=F["small_b"], text_color="#000").grid(row=0, column=0, pady=10)

        ctk.CTkLabel(hin, text=atleta.get("nome") or "Atleta",
                     font=F["body_b"], text_color=C["text"]).grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(hin,
                     text=f"{atleta.get('idade','?')} anos  ·  {atleta.get('altura','?')} cm  ·  {atleta.get('peso','?')} kg  ·  {atleta.get('sexo','?')}",
                     font=F["tiny"], text_color=C["text_mid"]).grid(row=1, column=1, sticky="w")

        # Tag data/hora
        ctk.CTkLabel(hin,
                     text=f"  📅 {entrada.get('data','?')} às {entrada.get('hora','')}",
                     font=F["tiny_i"], text_color=C["green_l"]).grid(row=2, column=1, sticky="w", pady=(4,0))

        # Stats
        sf = ctk.CTkFrame(hero, fg_color=C["bg4"], corner_radius=10)
        sf.grid(row=2, column=0, sticky="ew", padx=12, pady=(0,12))
        imc_c = {"Peso normal":C["success"],"Abaixo do peso":C["warning"],"Sobrepeso":C["warning"],"Obesidade":C["error"]}.get(entrada.get("imc_cat",""),C["text_mid"])
        stats_d = [
            ("IMC",     entrada.get("imc_val","--"),        imc_c),
            ("Objetivo",atleta.get("objetivo","").split()[0] if atleta.get("objetivo") else "—", C["green_l"]),
            ("Local",   atleta.get("local","—"),             C["text_mid"]),
            ("Dias/sem",atleta.get("dias","—"),              C["text_mid"]),
            ("Duração", f"{atleta.get('duracao','?')}min",  C["text_mid"]),
        ]
        for col,(lbl,val,cor) in enumerate(stats_d):
            sf.grid_columnconfigure(col, weight=1)
            s = ctk.CTkFrame(sf, fg_color="transparent")
            s.grid(row=0, column=col, padx=8, pady=10)
            ctk.CTkLabel(s, text=val, font=F["small_b"], text_color=cor).pack()
            ctk.CTkLabel(s, text=lbl, font=F["tiny"], text_color=C["text_dim"]).pack()

        # ── Exercícios ──────────────────────────────────────────────────────
        sec("💪", "EXERCÍCIOS", f"{entrada.get('total_exercicios',0)} no total")
        exs = entrada.get("exs", {})
        for grupo, exercicios in exs.items():
            gh = ctk.CTkFrame(df, fg_color=C["bg3"], corner_radius=8)
            gh.grid(row=row, column=0, sticky="ew", padx=20, pady=(4,2)); row+=1
            dot = ctk.CTkFrame(gh, fg_color=C["green"], width=4, corner_radius=2)
            dot.pack(side="left", fill="y", padx=(10,10), pady=8)
            ctk.CTkLabel(gh, text=grupo.upper(), font=F["small_b"], text_color=C["text"]).pack(side="left", pady=8)
            ctk.CTkLabel(gh, text=f"{len(exercicios)} ex.", font=F["tiny"], text_color=C["text_dim"]).pack(side="right", padx=12)

            for idx, ex in enumerate(exercicios):
                ce = ctk.CTkFrame(df, fg_color=C["bg3"], corner_radius=10)
                ce.grid(row=row, column=0, sticky="ew", padx=28, pady=(2,3)); row+=1
                ce.grid_columnconfigure(0, weight=1)

                tr = ctk.CTkFrame(ce, fg_color="transparent")
                tr.grid(row=0, column=0, sticky="ew", padx=12, pady=(10,4))
                tr.grid_columnconfigure(1, weight=1)

                nb = ctk.CTkFrame(tr, fg_color=C["green_dim"], corner_radius=6, width=24, height=24)
                nb.pack_propagate(False); nb.grid(row=0, column=0, padx=(0,10))
                ctk.CTkLabel(nb, text=str(idx+1), font=F["tiny"], text_color=C["green_l"]).grid(row=0,column=0)
                ctk.CTkLabel(tr, text=ex.get("nome",""), font=F["body_b"], text_color=C["text"], anchor="w").grid(row=0, column=1, sticky="w")

                # Botão YT
                yt_url = ex.get("yt","")
                if yt_url:
                    ctk.CTkButton(tr, text="▶", font=F["tiny"], width=28, height=24,
                                  fg_color=C["yt_bg"], hover_color=C["youtube_d"],
                                  text_color=C["youtube"], border_color=C["youtube_d"],
                                  border_width=1, corner_radius=4,
                                  command=lambda u=yt_url: webbrowser.open(u)
                                  ).grid(row=0, column=2, padx=(8,0))

                br = ctk.CTkFrame(ce, fg_color="transparent")
                br.grid(row=1, column=0, sticky="w", padx=12, pady=(0,4))
                for txt, cbg, ct2 in [
                    (f"{ex.get('series','?')}× {ex.get('reps','?')} reps", C["bg4"], C["green_l"]),
                    (ex.get("carga",""), C["bg4"], C["text_mid"]),
                    (f"⏱ {ex.get('descanso','')}", C["bg4"], C["text_dim"]),
                ]:
                    if txt.strip():
                        b = ctk.CTkFrame(br, fg_color=cbg, corner_radius=5)
                        b.pack(side="left", padx=(0,5))
                        ctk.CTkLabel(b, text=txt, font=F["tiny"], text_color=ct2).pack(padx=8, pady=3)

                if ex.get("dica"):
                    df2 = ctk.CTkFrame(ce, fg_color=C["bg4"], corner_radius=5)
                    df2.grid(row=2, column=0, sticky="ew", padx=12, pady=(0,10))
                    ctk.CTkLabel(df2, text=f"  💡 {ex['dica']}", font=F["tiny_i"],
                                 text_color=C["text_dim"], anchor="w", wraplength=460
                                 ).grid(row=0, column=0, sticky="w", padx=4, pady=5)

        # ── Divisão Semanal ─────────────────────────────────────────────────
        dias = int(atleta.get("dias", 4))
        sec("📅", "DIVISÃO SEMANAL", f"{dias} dias por semana")
        div_f = ctk.CTkFrame(df, fg_color="transparent")
        div_f.grid(row=row, column=0, sticky="ew", padx=20, pady=(0,4)); row+=1
        cols = min(dias, 4)
        for c in range(cols): div_f.grid_columnconfigure(c, weight=1)
        for i, linha in enumerate(entrada.get("div", [])):
            r2, c2 = divmod(i, cols)
            cd = ctk.CTkFrame(div_f, fg_color=C["bg3"], corner_radius=10)
            cd.grid(row=r2, column=c2, padx=4, pady=4, sticky="nsew")
            cd.grid_columnconfigure(0, weight=1)
            ctk.CTkFrame(cd, fg_color=C["green"], height=3, corner_radius=0).grid(row=0,column=0,sticky="ew")
            ctk.CTkLabel(cd, text=f"DIA {i+1}", font=F["tiny"], text_color=C["green"]).grid(row=1,column=0,padx=10,pady=(8,2),sticky="w")
            ctk.CTkLabel(cd, text=linha, font=F["small"], text_color=C["text_soft"],
                         wraplength=140, anchor="w", justify="left").grid(row=2,column=0,padx=10,pady=(0,10),sticky="w")

        # ── Dicas ────────────────────────────────────────────────────────────
        sec("⚡", "DICAS", atleta.get("objetivo",""))
        for i, d in enumerate(entrada.get("dicas", [])):
            cd2 = ctk.CTkFrame(df, fg_color=C["bg3"], corner_radius=8)
            cd2.grid(row=row, column=0, sticky="ew", padx=20, pady=2); row+=1
            cd2.grid_columnconfigure(1, weight=1)
            nb2 = ctk.CTkFrame(cd2, fg_color=C["green_dim"], corner_radius=6, width=24, height=24)
            nb2.pack_propagate(False); nb2.grid(row=0, column=0, padx=(12,10), pady=10)
            ctk.CTkLabel(nb2, text=str(i+1), font=F["tiny"], text_color=C["green_l"]).grid(row=0, column=0)
            ctk.CTkLabel(cd2, text=d, font=F["small"], text_color=C["text_soft"],
                         anchor="w", wraplength=460, justify="left").grid(row=0,column=1,sticky="w",pady=10,padx=(0,12))

        sp(24)

    # ── Ações ────────────────────────────────────────────────────────────────
    def _filtrar(self):
        q = self.search_var.get().strip().lower()
        if not q:
            self._renderizar_lista(self._entradas)
            return
        filtradas = [e for e in self._entradas
                     if q in (e.get("atleta",{}).get("nome","") or "").lower()
                     or q in (e.get("atleta",{}).get("objetivo","") or "").lower()
                     or any(q in g.lower() for g in e.get("grupos",[]))
                     or q in e.get("data","")]
        self._renderizar_lista(filtradas)

    def _carregar_selecionado(self):
        if not self._entrada_atual: return
        if self.on_recarregar:
            self.on_recarregar(self._entrada_atual)
        self.destroy()

    def _deletar_selecionado(self):
        if not self._entrada_atual: return
        if not messagebox.askyesno("Deletar", "Remover este treino do histórico?"):
            return
        db_deletar_historico(self.email, self._entrada_atual.get("id",""))
        self._entradas = db_carregar_historico(self.email)
        self._entrada_atual = None
        self.btn_carregar.configure(state="disabled")
        self.btn_del.configure(state="disabled")
        self._renderizar_lista(self._entradas)
        self._mostrar_placeholder_detalhe()

    def _limpar_tudo(self):
        if not self._entradas:
            messagebox.showinfo("Histórico","Histórico já está vazio."); return
        if not messagebox.askyesno("Limpar Tudo",
                                   f"Isso vai apagar todos os {len(self._entradas)} treinos do histórico.\n\nTem certeza?"):
            return
        db_limpar_historico(self.email)
        self._entradas = []
        self._entrada_atual = None
        self.btn_carregar.configure(state="disabled")
        self.btn_del.configure(state="disabled")
        self._renderizar_lista([])
        self._mostrar_placeholder_detalhe()


# ╔══════════════════════════════════════════════════════════╗
# ║                     ENTRY POINT                          ║
# ╚══════════════════════════════════════════════════════════╝
if __name__=="__main__":
    app=ArnoAI()
    app.mainloop()