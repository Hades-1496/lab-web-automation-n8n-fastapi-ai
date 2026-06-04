import os
import json
import httpx
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Sistema de Automatización API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock database of users
usuarios_db = {
    42: {"nombre": "Juan Pérez", "email": "juan.perez@example.com", "plan": "premium"},
    1: {"nombre": "Ana Gómez", "email": "ana.gomez@example.com", "plan": "basic"},
    2: {"nombre": "Carlos Rodríguez", "email": "carlos.rod@example.com", "plan": "pro"},
}

class TareaEntrada(BaseModel):
    titulo: str
    prioridad: str
    descripcion: Optional[str] = ""

class Tarea(BaseModel):
    id: int
    titulo: str
    prioridad: str
    descripcion: Optional[str] = ""
    completada: bool = False

# In-memory tasks database
tareas_db: List[Tarea] = [
    Tarea(id=1, titulo="Presentación cliente", prioridad="alta", descripcion="Preparar diapositivas para la demo", completada=False),
    Tarea(id=2, titulo="Revisar logs de producción", prioridad="media", descripcion="Buscar errores 500 del lunes", completada=True),
    Tarea(id=3, titulo="Actualizar dependencias", prioridad="baja", descripcion="Actualizar npm y pip", completada=False),
]
tarea_id_counter = 4

def guardar_en_db(tarea: TareaEntrada) -> Tarea:
    global tarea_id_counter
    nueva = Tarea(
        id=tarea_id_counter,
        titulo=tarea.titulo,
        prioridad=tarea.prioridad,
        descripcion=tarea.descripcion,
        completada=False
    )
    tareas_db.append(nueva)
    tarea_id_counter += 1
    return nueva

async def notificar_n8n(webhook_url: str, payload: dict):
    if not webhook_url:
        return
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(webhook_url, json=payload)
    except Exception:
        pass  # N8N no debe bloquear la respuesta principal

@app.post("/tareas", status_code=201)
async def crear_tarea(tarea: TareaEntrada, background_tasks: BackgroundTasks):
    nueva = guardar_en_db(tarea)
    webhook_url = os.getenv("N8N_WEBHOOK_TAREAS", "")
    if webhook_url:
        background_tasks.add_task(
            notificar_n8n,
            webhook_url,
            {"evento": "tarea_creada", "tarea": nueva.dict()}
        )
    return {"ok": True, "data": nueva}

@app.get("/tareas")
async def listar_tareas(completada: Optional[bool] = None):
    if completada is not None:
        return [t for t in tareas_db if t.completada == completada]
    return tareas_db

@app.get("/usuarios/{usuario_id}")
async def obtener_usuario(usuario_id: int):
    if usuario_id not in usuarios_db:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuarios_db[usuario_id]

class ChatInput(BaseModel):
    mensaje: str
    session_id: Optional[str] = "default"

@app.post("/api/chat")
async def chat(body: ChatInput):
    prompt = body.mensaje.strip()
    
    # Check if Groq API key is present and we can call Groq
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key and groq_api_key != "tu_clave_real_de_groq_aqui":
        try:
            url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {groq_api_key}",
                "Content-Type": "application/json"
            }
            model = os.getenv("GROQ_MODEL", "llama3-8b-8192")
            
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "Eres un asistente de IA experto que responde en español. Si el usuario te pide que devuelvas JSON, devuelve únicamente el JSON válido sin markdown ni texto extra."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2
            }
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.post(url, json=payload, headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    ai_content = data["choices"][0]["message"]["content"].strip()
                    
                    # Try to parse the content as JSON if it looks like one
                    if "Devuelve JSON" in prompt or "sentimiento" in prompt or ai_content.startswith("{"):
                        try:
                            clean_content = ai_content
                            if clean_content.startswith("```json"):
                                clean_content = clean_content.split("```json")[1].split("```")[0].strip()
                            elif clean_content.startswith("```"):
                                clean_content = clean_content.split("```")[1].split("```")[0].strip()
                            parsed_json = json.loads(clean_content)
                            return parsed_json
                        except Exception:
                            pass
                    
                    return {"respuesta": ai_content}
        except Exception as e:
            print(f"Error calling Groq: {e}")
            pass
            
    # Mock fallback logic
    lower_prompt = prompt.lower()
    
    # Case 1: Tarea urgente (Workflow 1)
    if "tarea urgente" in lower_prompt or "consejo breve" in lower_prompt:
        titulo = "esta tarea"
        if "'" in prompt:
            parts = prompt.split("'")
            if len(parts) >= 2:
                titulo = parts[1]
        elif '"' in prompt:
            parts = prompt.split('"')
            if len(parts) >= 2:
                titulo = parts[1]
                
        respuesta = f"Consejo de IA para '{titulo}': Organiza tu día priorizando esta actividad en tu bloque de mayor energía. Evita multitareas y define un entregable claro para las próximas 2 horas."
        return {"respuesta": respuesta}
        
    # Case 2: Feedback (Workflow 2)
    elif "feedback" in lower_prompt or "analiza este feedback" in lower_prompt:
        sentimiento = "positivo"
        problema = "Ninguno"
        accion = "Agradecer feedback"
        
        # Simple rule-based heuristics to determine sentiment
        if "calificación: 1/5" in lower_prompt or "calificación: 2/5" in lower_prompt or "tarda mucho" in lower_prompt or "no funciona" in lower_prompt or "malo" in lower_prompt or "error" in lower_prompt:
            sentimiento = "negativo"
            problema = "Lentitud o errores en la aplicación"
            accion = "Escalar a soporte de nivel 2 y abrir ticket de alta prioridad"
        elif "calificación: 3/5" in lower_prompt:
            sentimiento = "neutral"
            problema = "Aspectos mejorables en la experiencia de usuario"
            accion = "Revisar comentarios de mejora en la próxima iteración"
            
        return {
            "sentimiento": sentimiento,
            "problema_principal": problema,
            "accion": accion
        }
        
    # Case 3: Informe diario (Workflow 3)
    elif "informe diario" in lower_prompt or "informe diario ejecutivo" in lower_prompt:
        total_tareas = "varias"
        if "tareas pendientes:" in prompt:
            # try to parse total tasks count
            try:
                total_tareas = prompt.split("Tareas pendientes:")[1].split(".")[0].strip()
            except Exception:
                pass
            
        respuesta = (
            f"Informe Ejecutivo Diario:\n\n"
            f"1. Se registran actualmente {total_tareas} tareas pendientes en el sistema. Es crucial abordar primero las tareas marcadas con prioridad alta para evitar bloqueos operativos.\n\n"
            f"2. El rendimiento general del equipo se mantiene estable, pero se observa una acumulación de tickets de soporte que requieren revisión de infraestructura.\n\n"
            f"3. Recomendación de acción: Asignar un recurso técnico dedicado durante la mañana para resolver los problemas de rendimiento reportados por clientes premium."
        )
        return {"informe": respuesta}
        
    # Default fallback
    return {"respuesta": f"He recibido tu mensaje: '{prompt}'. Estoy procesándolo."}

@app.get("/health")
async def health():
    n8n_tasks_url = os.getenv("N8N_WEBHOOK_TAREAS", "")
    n8n_feedback_url = os.getenv("N8N_WEBHOOK_FEEDBACK", "")
    
    n8n_reachable = False
    details = {}
    
    for name, url in [("tareas", n8n_tasks_url), ("feedback", n8n_feedback_url)]:
        if url:
            try:
                async with httpx.AsyncClient(timeout=1.0) as client:
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    root_url = f"{parsed.scheme}://{parsed.netloc}/"
                    res = await client.get(root_url)
                    if res.status_code < 500:
                        n8n_reachable = True
                        details[name] = "reachable"
                    else:
                        details[name] = f"error status {res.status_code}"
            except Exception as e:
                details[name] = f"unreachable: {str(e)}"
        else:
            details[name] = "not_configured"
            
    status_str = "ok" if n8n_reachable or not (n8n_tasks_url or n8n_feedback_url) else "degraded"
    return {
        "status": status_str,
        "n8n_reachable": n8n_reachable,
        "details": details
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
