
## 🐳 Despliegue con Docker (Sin Instalar Dependencias)

Puedes compilar y ejecutar el servidor de juego o el entorno de pruebas de visión artificial directamente en un contenedor **Docker** sin necesidad de instalar OpenCV, MediaPipe ni paquetes de C++:

```bash
# 1. Iniciar el Servidor de Combate LAN (Puerto UDP 9999)
docker compose up --build -d

# 2. Ver logs en tiempo real del servidor
docker compose logs -f server

# 3. Ejecutar una partida de simulación autónoma (IA vs IA / Mock)
docker compose run --rm ai-match
```

### 🎮 1. Modo 1v1 Local (Misma Pantalla / 1 Sola Cámara)
¡Juega cara a cara con tu amigo en la misma computadora!
* **Doble clic en `INICIAR_1V1_LOCAL.bat`**.
* La cámara web detecta automáticamente a los 2 jugadores (P1 a la izquierda, P2 a la derecha).
* O jueguen en el mismo teclado con el simulador 1v1.
* Consulta todos los detalles en [GUIA_1V1_LOCAL.md](GUIA_1V1_LOCAL.md).

\n# VideoGame Pose - Combate Multi-Jugador por Vision Artificial

Videojuego de combate en tiempo real donde los jugadores controlan a sus avatares realizando posturas corporales frente a la camara web o simulador de teclado bajo el estandar oficial Google Cloud OKF v0.2.

---

## 1. Como Jugar en 2 PCs (Tu Amigo y Tu) - Paso a Paso

El juego cuenta con lanzadores automaticos de 1 clic para que tu y tu amigo jueguen sin configurar rutas ni comandos complicados:

### Paso 1: Pasarle el juego a tu amigo
1. Pasa la carpeta completa `videogame_pose` a tu amigo (en un archivo `.zip`, por USB, Google Drive o GitHub).
2. Tu amigo descomprime la carpeta en su computadora.
3. Tu amigo hace doble clic en el archivo:
   ```
   INSTALAR_DEPENDENCIAS.bat
   ```
   *(Este script instala automaticamente Python virtualenv y las librerias necesarias sin tocar nada mas).*

### Paso 2: Tu eres el HOST (PC 1 - Servidor)
1. En tu computadora, haz doble clic en:
   ```
   INICIAR_HOST.bat
   ```
2. La consola te mostrara tu direccion IP en color verde, por ejemplo:
   ```
   Tus direcciones IP detectadas para compartir con tu amigo:
     --> 192.168.1.14  (Interfaz: Wi-Fi)
   ```
3. Dile esa direccion IP a tu amigo (ejemplo: `192.168.1.14`).
4. Tu juego se abrira como Jugador 1 (Neon Cyan) esperando a que tu amigo se conecte.

### Paso 3: Tu Amigo es el CLIENTE (PC 2 - Jugador 2)
1. En su computadora, tu amigo hace doble clic en:
   ```
   INICIAR_CLIENTE.bat
   ```
2. La ventana le pedira que escriba tu IP:
   ```
   Ingresa la direccion IP del PC Host: 192.168.1.14
   ```
3. Escribe tu IP y presiona `ENTER`.
4. El juego conectara inmediatamente a tu partida a 60 FPS: tu estaras a la izquierda (P1) y tu amigo a la derecha (P2).

> **Jugar a distancia (Diferentes Casas por Internet)**: Consulta el manual completo [`GUIA_MULTIJUGADOR_LAN.md`](GUIA_MULTIJUGADOR_LAN.md) para conectarse gratis a traves de Radmin VPN o Hamachi con IPs virtuales `26.X.X.X` sin configurar routers.

---

## 2. Movimientos y Poses de Combate

Consulta el manual detallado con posturas corporales paso a paso, costos de Ki, combos tacticos y diagramas ASCII en [`GUIA_DE_MOVIMIENTOS.md`](GUIA_DE_MOVIMIENTOS.md).
Tambien puedes presionar la tecla **'H'** o **'TAB'** dentro del juego para abrir el overlay transparente de movimientos en pantalla sin pausar la partida.

| Movimiento | Postura Fisica Clave | Costo Ki | Cooldown | Dano / Efecto Principal | Tecla Teclado |
| :--- | :--- | :---: | :---: | :--- | :---: |
| **IDLE** | Brazos relajados al costado | 0 | 0.0s | Postura neutra | `4` / `-` |
| **KAMEHAMEHA** | Manos juntas proyectadas al frente | 12 Ki/s | 0.0s | Rayo continuo 40 HP/s + Choque | `1` / `8` |
| **SHIELD** | Antebrazos en vertical cubriendo rostro | 0 | 0.0s | Mitiga el 85% de dano | `2` / `9` |
| **CHARGE_KI** | Codos abiertos, punos en cintura | 0 | 0.0s | Recarga +15 Ki/s con aura | `3` / `0` |
| **PUNCH** | Estocada recta de un puno al frente | 0 | 0.45s | 18 HP dano rapido + Knockback | `5` / `=` |
| **UPPERCUT** | Puno vertical sobre la nariz | 0 | 1.2s | 24 HP + **Rompe escudos** | `6` / `[` |
| **SIXTY_SEVEN** | Balanza: 1 mano alta y 1 mano baja | 0 | 10.0s | Paraliza al oponente por 2.0s | `7` / `]` |
| **HADOKEN** | Ambas palmas extendidas al pecho | 20 Ki | 1.0s | 24 HP en esfera balistica rapida | `U` / `J` |
| **SPIRIT_BOMB** | Brazos alzados al cielo sobre cabeza | 25+ Ki | 4.0s | 45 HP dano masivo en area + Shake | `I` / `K` |
| **DODGE_ROLL** | Inclinacion lateral hombros >25 deg | 0 | 1.6s | **Inmunidad total por 0.4s** | `O` / `L` |
| **TAUNT_CROSS** | Brazos cruzados en X en el pecho | 0 | 10.0s | **+30% dano de ataque (8s)** | `P` / `;` |

---

## 3. Modos de Ejecucion por Linea de Comandos (Opcional)

Si prefieres ejecutar desde consola en lugar de los archivos `.bat`:

```bash
# 1. Modo Multijugador LAN - Servidor (PC 1):
python main.py --mode host --port 9999 --backend yolo

# 2. Modo Multijugador LAN - Cliente (PC 2):
python main.py --mode client --host 192.168.1.14 --port 9999 --backend yolo

# 3. Modo 1 Jugador contra Inteligencia Artificial (Nivel Dificil):
python main.py --mode single --difficulty hard --backend yolo

# 4. Modo Simulador de Teclado (Si alguna PC no tiene camara web):
python main.py --mode host --port 9999 --backend mock
python main.py --mode client --host 192.168.1.14 --port 9999 --backend mock

# 5. Ejecutar la suite completa de 43 pruebas automatizadas:
python -m unittest discover -s tests -v
```

---

## 4. Teclas Especiales y Controles

* **'H' o 'TAB'**: Abrir / cerrar Guia de Movimientos en pantalla.
* **'R'**: Reiniciar combate / nueva partida (disponible para el Host).
* **'ESC' o 'Q'**: Salir del juego limpiamente.

---
*Desarrollado por Mileidys Agamez Ospino • Visión Artificial, Pygame-CE y Arquitectura Limpia.*
