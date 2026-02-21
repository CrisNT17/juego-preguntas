# main.py - Versión para la Pico (después del reinicio)
import network
import socket
import ujson
import time
import _thread
from machine import Pin

# ========== CONFIGURACIÓN ==========
WIFI_SSID = "NOMBRE_DE_TU_WIFI"
WIFI_PASS = "TU_CONTRASEÑA"
GITHUB_TOKEN = "ghp_tu_token_aqui"
GITHUB_REPO = "CrisNT17/juego-preguntas"
GITHUB_USER = "CrisNT17"

# ========== PINES ==========
led_j1 = Pin(0, Pin.OUT)
led_j2 = Pin(1, Pin.OUT)
led_listo = Pin(2, Pin.OUT)
btn_j1 = Pin(4, Pin.IN, Pin.PULL_UP)
btn_j2 = Pin(5, Pin.IN, Pin.PULL_UP)
btn_reset = Pin(6, Pin.IN, Pin.PULL_UP)

# ========== ESTADO ==========
puntaje_j1 = 0
puntaje_j2 = 0
ultimo_presiono = None
led_j1_state = False
led_j2_state = False

# ========== WIFI ==========
def conectar_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(WIFI_SSID, WIFI_PASS)
    for i in range(20):
        if wlan.isconnected():
            return wlan.ifconfig()[0]
        time.sleep(0.5)
    return None

ip = conectar_wifi()
print(f"✅ IP: {ip}")

# ========== API ==========
def manejar(cliente, addr):
    global puntaje_j1, puntaje_j2, ultimo_presiono, led_j1_state, led_j2_state
    
    try:
        req = cliente.recv(1024).decode()
        
        if 'GET /api/estado' in req:
            estado = {
                "puntaje_j1": puntaje_j1,
                "puntaje_j2": puntaje_j2,
                "led_j1": led_j1_state,
                "led_j2": led_j2_state,
                "ultimo_presiono": ultimo_presiono,
                "estadisticas": {"modo": "ONLINE", "tamanio": 0}
            }
            cliente.send('HTTP/1.0 200 OK\r\nContent-type: application/json\r\n\r\n')
            cliente.send(ujson.dumps(estado))
            
        elif 'POST /api/aprobar' in req:
            if ultimo_presiono == 1:
                puntaje_j1 += 1
            elif ultimo_presiono == 2:
                puntaje_j2 += 1
            ultimo_presiono = None
            led_j1_state = led_j2_state = False
            led_j1.off()
            led_j2.off()
            cliente.send('HTTP/1.0 200 OK\r\n\r\nOK')
            
        elif 'GET /referee' in req:
            cliente.send('HTTP/1.0 302 Found\r\nLocation: https://raw.githubusercontent.com/CrisNT17/juego-preguntas/main/paginas/referee.html\r\n\r\n')
        
        cliente.close()
    except:
        cliente.close()

# ========== BOTONES ==========
def monitorear():
    global ultimo_presiono, led_j1_state, led_j2_state
    u1 = u2 = ur = 1
    while True:
        b1 = btn_j1.value()
        b2 = btn_j2.value()
        r = btn_reset.value()
        
        if b1 == 0 and u1 == 1:
            ultimo_presiono = 1
            led_j1_state = True
            led_j1.on()
        if b2 == 0 and u2 == 1:
            ultimo_presiono = 2
            led_j2_state = True
            led_j2.on()
        if r == 0 and ur == 1:
            led_j1_state = led_j2_state = False
            led_j1.off()
            led_j2.off()
            led_listo.on()
        
        u1, u2, ur = b1, b2, r
        time.sleep(0.05)

# ========== SERVIDOR ==========
_thread.start_new_thread(monitorear, ())
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
server = socket.socket()
server.bind(addr)
server.listen(5)

print(f"🚀 Servidor en http://{ip}")
while True:
    try:
        c, a = server.accept()
        manejar(c, a)
    except:
        time.sleep(0.01)