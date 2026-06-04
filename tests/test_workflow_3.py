import httpx
import os

url = "http://localhost:5678/webhook/wfInformeDiario3/webhook/trigger-informe"

print(f"Probando Workflow 3 (Informe Diario Ejecutivo) enviando POST a {url}...")
try:
    res = httpx.post(url, timeout=20.0)
    print(f"Codigo de estado: {res.status_code}")
    print(f"Respuesta: {res.text}")
    
    # Check if informes.jsonl exists
    filepath = "informes.jsonl"
    if os.path.exists(filepath):
        print("\nArchivo 'informes.jsonl' encontrado con exito. Ultimas lineas:")
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines[-2:]:
                print(line.strip())
    elif os.path.exists("../informes.jsonl"):
        print("\nArchivo 'informes.jsonl' encontrado con exito. Ultimas lineas:")
        with open("../informes.jsonl", "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines[-2:]:
                print(line.strip())
    else:
        print("\nAdvertencia: No se encontro el archivo 'informes.jsonl'.")
except Exception as e:
    print(f"Error: {e}")
