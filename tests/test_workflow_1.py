import httpx

url = "http://localhost:5678/webhook/wfTareaUrgente01/webhook/evento-tarea"
payload = {
    "evento": "tarea_creada",
    "tarea": { "id": 1, "titulo": "Presentación cliente importante", "prioridad": "alta" }
}

print(f"Probando Workflow 1 (Tarea Urgente) enviando POST a {url}...")
try:
    res = httpx.post(url, json=payload, timeout=10.0)
    print(f"Codigo de estado: {res.status_code}")
    print(f"Respuesta: {res.text}")
except Exception as e:
    print(f"Error: {e}")
