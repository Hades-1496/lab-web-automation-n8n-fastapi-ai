import httpx

url = "http://localhost:5678/webhook/wfFeedbackAnalis2/webhook/feedback"
headers = {
    "x-api-key": "mi-secreto-super-seguro-2024"
}

# Test 1: Calificacion < 3 (Debe crear ticket)
payload1 = {
    "usuario_id": 42,
    "mensaje": "La aplicación tarda muchísimo en cargar la pantalla principal",
    "calificacion": 2
}

print(f"Probando Workflow 2 (Feedback Calificación 2) enviando POST a {url}...")
try:
    res1 = httpx.post(url, json=payload1, headers=headers, timeout=10.0)
    print(f"Test 1 - Codigo de estado: {res1.status_code}")
    print(f"Test 1 - Respuesta: {res1.text}")
except Exception as e:
    print(f"Test 1 - Error: {e}")

print("-" * 60)

# Test 2: Calificacion >= 3 (No debe crear ticket)
payload2 = {
    "usuario_id": 1,
    "mensaje": "Excelente aplicación, muy intuitiva",
    "calificacion": 5
}

print(f"Probando Workflow 2 (Feedback Calificación 5) enviando POST a {url}...")
try:
    res2 = httpx.post(url, json=payload2, headers=headers, timeout=10.0)
    print(f"Test 2 - Codigo de estado: {res2.status_code}")
    print(f"Test 2 - Respuesta: {res2.text}")
except Exception as e:
    print(f"Test 2 - Error: {e}")
