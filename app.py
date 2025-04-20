import scratchattach as sa
import requests
import random
import time

# ——— Configuración de codificación ———
Aa = list("qwertyuiopasdfghjklñzxcvbnm;:,. 1234567890!\"·$%&/()='¡?¿ç+`´")
once = [str(i) for i in range(11, 11 + len(Aa))]

# ——— Constantes de control ———
BOT_USERNAME    = "Logise"   # Tu usuario de Scratch
RESPONSE_PREFIX = "123"      # Prefijo para mensajes de IA

# ——— Funciones de transformación ———
def encode(texto: str) -> str:
    s = ""
    for ch in texto:
        if ch in Aa:
            s += once[Aa.index(ch)]
        else:
            s += once[-1]
    return s

def decode(codigo: str) -> str:
    s = ""
    for i in range(0, len(codigo), 2):
        chunk = codigo[i:i+2]
        if chunk in once:
            idx = once.index(chunk)
            s += Aa[idx] if idx < len(Aa) else " "
        else:
            s += " "
    return s

def quitar_acentos(texto: str) -> str:
    reps = {
        "á":"a","é":"e","í":"i","ó":"o","ú":"u",
        "Á":"A","É":"E","Í":"I","Ó":"O","Ú":"U",
        "ñ":"n","Ñ":"N"
    }
    for orig, repl in reps.items():
        texto = texto.replace(orig, repl)
    return texto

# ——— Llamada a la IA con reintentos 429 ———
def ai_with_context(historial: list) -> str:
    url = "https://text.pollinations.ai/openai"
    headers = {"Content-Type": "application/json"}
    payload = {"model": "openai", "messages": historial, "seed": random.randint(2, 100000)}

    while True:
        r = requests.post(url, json=payload, headers=headers)
        if r.status_code == 200:
            response = r.json()["choices"][0]["message"]["content"]
            return response.lower()
        elif r.status_code == 429:
            print("🕒 429 Too Many Requests, reintentando en 1 s…")
            time.sleep(1)
        else:
            print(f"Error {r.status_code}: {r.text}")
            return "hubo un error al procesar tu mensaje."

# ——— set_var seguro con manejo de event stream ———
def set_var_seguro(cloud, var: str, valor: str, intentos: int = 5, espera: float = 0.5) -> bool:
    cloud.set_var(var, valor)
    time.sleep(1)
    cloud.set_var(var, valor)
    return True

# ——— Inicialización de sesión Scratch ———
session = sa.login("Logise", "Animatronicos6500Animatronicos6500")
cloud = session.connect_scratch_cloud("1143950579")
events = cloud.events()

# ——— Memoria en RAM por user_id ———
memoria_usuarios = {}
print("ok!")
@events.event
def on_set(activity):
    # 1) Solo nos interesa 'response' y no nuestro propio bot
    if activity.var != "response" or activity.username == BOT_USERNAME:
        return
    # 2) Ignorar valores que ya vienen con el prefijo de IA
    if activity.value.startswith(RESPONSE_PREFIX):
        return

    raw   = activity.value
    user_id = raw[:3]    # primeros 3 dígitos = ID de usuario
    body     = raw[3:]    # resto = mensaje codificado

    entrada = decode(body)
    print(f"[{user_id}] dice → «{entrada}»")

    # 3) Guardar en historial bajo user_id
    memoria_usuarios.setdefault(user_id, []).append({
        "role":    "user",
        "content": entrada
    })

    # 4) Llamar a la IA con todo el historial de ese user_id
    respuesta = ai_with_context(memoria_usuarios[user_id])
    respuesta = quitar_acentos(respuesta)
    print(f"[IA] responde → «{respuesta}»")

    # 5) Guardar respuesta en historial
    memoria_usuarios[user_id].append({
        "role":    "assistant",
        "content": respuesta
    })

    # 6) Preparar y enviar la respuesta codificada con prefijo
    limit = 250
    cuerpo = encode(respuesta)
    max_body = limit - len(RESPONSE_PREFIX)
    if len(cuerpo) > max_body:
        cuerpo = cuerpo[: max_body - (max_body % 2)]
    full = RESPONSE_PREFIX + cuerpo

    set_var_seguro(cloud, "response", full)
    set_var_seguro(cloud, "ai", random.randint(0, 100))

# ——— Iniciar escucha de eventos ———
events.start()
