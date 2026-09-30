# Guia Oficial Multijugador LAN y Remoto (2 PCs)
## VideoGame Pose Combat (Gobernanza Google Cloud OKF v0.2)

Esta guia explica paso a paso y de forma infalible como jugar **VideoGame Pose Combat** entre dos computadoras separadas, donde una persona actua como **HOST (Servidor / Jugador 1)** y la otra como **CLIENTE (Jugador 2)**, ya sea en la misma red Wi-Fi o a traves de Internet.

---

## 1. Como Preparar y Pasar la Aplicacion a tu Amigo

1. Toma la carpeta completa `videogame_pose` y comprimela en un archivo `.zip` (o enviasela por Google Drive, USB, o clonandola desde tu repositorio de GitHub).
2. Tu amigo debe descomprimir la carpeta en cualquier ubicacion de su PC (por ejemplo, en el Escritorio o en Documentos).
3. **Paso unico de instalacion para tu amigo**:
   - Tu amigo solo debe hacer doble clic en el archivo:
     ```
     INSTALAR_DEPENDENCIAS.bat
     ```
   - Este script verifica que tenga Python instalado, crea automaticamente el entorno virtual `.venv` y descarga las librerias (`pygame-ce`, `opencv-python`, `ultralytics`, `numpy`).

---

## 2. Escenario A: Jugando en la Misma Red Wi-Fi / Casa (LAN Directa)

Este es el metodo mas facil y con menor latencia (< 5ms de ping).

### Paso a Paso para el HOST (PC 1 - Tu):
1. Asegurate de que ambas computadoras esten conectadas a la misma red Wi-Fi o por cable Ethernet al mismo router.
2. En tu PC, haz doble clic en:
   ```
   INICIAR_HOST.bat
   ```
3. La ventana negra mostrara en letras verdes tu direccion IP local, por ejemplo:
   ```
   Tus direcciones IP detectadas para compartir con tu amigo:
     --> 192.168.1.14 (Interfaz: Wi-Fi)
   ```
4. Copia esa direccion (ej. `192.168.1.14`) y pasasela a tu amigo por chat o diciendosela directamente.
5. El juego se abrira en modo Host esperando a que tu amigo se conecte.

### Paso a Paso para el CLIENTE (PC 2 - Tu Amigo):
1. En su PC, tu amigo hace doble clic en:
   ```
   INICIAR_CLIENTE.bat
   ```
2. La consola le pedira:
   ```
   Ingresa la direccion IP del PC Host:
   ```
3. Tu amigo escribe tu IP (por ejemplo `192.168.1.14`) y presiona `ENTER`.
4. El juego conectara inmediatamente con tu partida. Veras en pantalla a ambos jugadores sincronizados a 60 FPS: tu como P1 a la izquierda y tu amigo como P2 a la derecha.

---

## 3. Escenario B: Jugando a Distancia por Internet (Distintas Casas / Redes)

Si tu amigo esta en otra casa o ciudad, no podra usar la IP `192.168.X.X` directamente porque los routers bloquean conexiones entrantes no autorizadas. Hay dos metodos muy sencillos:

### Opcion Recomendada: Usar Radmin VPN (Gratis y sin configurar router)
1. Tanto tu como tu amigo descargan e instalan **Radmin VPN** (gratuito) desde `https://www.radmin-vpn.com/`.
2. Uno de los dos crea una red en Radmin VPN (por ejemplo, nombre: `CombatePoses` y una contraseña).
3. El otro se une a esa red ingresando el nombre y la contraseña.
4. Radmin VPN les asignara una IP virtual que empieza por `26.X.X.X` (por ejemplo `26.45.20.112`).
5. **Para jugar**:
   - Tu abres `INICIAR_HOST.bat`.
   - Le das tu IP de Radmin VPN (la que empieza por `26.X.X.X`) a tu amigo.
   - Tu amigo abre `INICIAR_CLIENTE.bat` y escribe esa IP `26.X.X.X`.
   - Se conectan al instante como si estuvieran en la misma habitacion.

---

## 4. Configuracion del Firewall de Windows (Si la conexion falla)

En raras ocasiones, el Firewall de Windows en el PC del Host puede bloquear los paquetes entrantes. Para permitir el juego:

1. Abre el menu Inicio, escribe **Firewall de Windows Defender con seguridad avanzada** y presiona `ENTER`.
2. En la columna izquierda, haz clic en **Reglas de entrada**.
3. En la columna derecha, haz clic en **Nueva regla...**:
   - Tipo de regla: **Puerto** -> Siguiente.
   - Protocolo: Selecciona **UDP**.
   - Puertos especificos: Escribe **9999** -> Siguiente.
   - Accion: **Permitir la conexion** -> Siguiente.
   - Perfil: Marca Dominio, Privado y Publico -> Siguiente.
   - Nombre: Escribe `VideoGame Pose Combat UDP` -> Finalizar.

---

## 5. Tabla de Comandos Manuales por Consola (Para Usuarios Avanzados)

Si prefieres ejecutar desde PowerShell o la terminal en lugar de los archivos `.bat`:

```bash
# HOST (Tu PC):
python main.py --mode host --port 9999 --backend yolo

# CLIENTE (PC de tu Amigo):
python main.py --mode client --host 192.168.1.14 --port 9999 --backend yolo

# MODO SIN CAMARA (Si alguno no tiene camara web y prefiere teclado):
python main.py --mode host --port 9999 --backend mock
python main.py --mode client --host 192.168.1.14 --port 9999 --backend mock
```

---

## 6. Solucion de Problemas Frecuentes (FAQ)

* **¿Que pasa si mi amigo presiona una tecla o hace un gesto y yo no lo veo?**
  - Verifica que el Host este corriendo antes de que el Cliente abra `INICIAR_CLIENTE.bat`.
  - Prueba hacer un ping desde la consola de tu amigo hacia tu IP: `ping 192.168.1.14`. Si dice "Tiempo de espera agotado", el Firewall del Host esta bloqueando la conexion (revisa la Seccion 4).
* **¿Que pasa si una de las PCs no tiene camara web?**
  - No hay problema. El que no tenga camara puede ejecutar con `--backend mock` o el script automatico hara el fallback a teclado si no detecta camara. Podra controlar a su luchador con las teclas `1` a `7` y `U`, `I`, `O`, `P`.
* **¿Como reiniciar la partida entre asaltos?**
  - El Host puede presionar la tecla **'R'** en cualquier momento para reiniciar el combate y restaurar la vida de ambos.

---
*Manual oficial de red de la Fabrica de Software Google Cloud OKF v0.2.*
