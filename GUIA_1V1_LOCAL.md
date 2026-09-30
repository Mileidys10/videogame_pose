# Guía Oficial: Modo 1v1 Local en VideoGame Pose Combat

> **Modalidad**: 2 Jugadores en la misma computadora y en la misma pantalla.
> **Dispositivo**: 1 sola cámara web (o el mismo teclado en modo simulador).
> **Gobernanza**: Estándar Google Cloud OKF v0.2.

---

## 1. ¿Se puede jugar 1v1 Local en la misma PC?

**SÍ, rotundamente SÍ.** El juego está diseñado desde su núcleo arquitectónico para soportar **combates 1v1 locales** cara a cara frente a un solo monitor.

A diferencia del modo multijugador LAN (donde cada amigo usa su propia laptop), en el **Modo 1v1 Local**:
* Se utiliza **una sola cámara web**.
* Ambos amigos se paran lado a lado frente a la pantalla.
* La visión artificial rastrea a ambos peleadores simultáneamente en tiempo real.
* La pantalla dividida virtual proyecta los efectos de combate (Kamehamehas, Hadokens, Choques de Rayos, Escudos y Daño) directamente entre ambos.

---

## 2. ¿Cómo detecta la cámara a los dos jugadores?

El juego implementa dos motores de visión artificial de última generación para 1v1 local:

### Opción A: Motor Ultralytics YOLOv8-Pose (Recomendado)
* **Cómo funciona**: La red neuronal procesa el fotograma completo en un solo pase ultrarrápido y detecta a todas las personas presentes.
* **Asignación Automática**: El sistema ordena a los jugadores por su coordenada horizontal ($X$):
  * La persona situada a la **IZQUIERDA** es asignada como **Jugador 1 (Azul)**.
  * La persona situada a la **DERECHA** es asignada como **Jugador 2 (Rojo)**.

### Opción B: Motor Google MediaPipe (División Espacial ROI)
* **Cómo funciona**: Divide el campo de visión de la cámara en dos cuadrantes verticales (50% izquierdo y 50% derecho).
* Cada cuadrante tiene su propio rastreador esquelético de 33 puntos con suavizado temporal *Lerp*.

---

## 3. Disposición Física y Espacio Recomendado

Para la mejor experiencia de combate físico, sigue estas pautas:

```
               +--------------------------------------+
               |          MONITOR / PANTALLA          |
               +--------------------------------------+
                                  |
                              [ WEBCAM ]
                                  |
                                  |  (1.8 - 2.5 metros)
                                  v
           +-----------------+         +-----------------+
           |   JUGADOR 1     |         |   JUGADOR 2     |
           |  (Lado Izq)     |         |  (Lado Der)     |
           |     (P1)        |         |     (P2)        |
           +-----------------+         +-----------------+
```

1. **Distancia**: Sitúense a una distancia de entre **1.8 y 2.5 metros** de la cámara.
2. **Separación**: Dejen unos **50 cm de espacio** entre ustedes para no golpearse al lanzar puñetazos o hacer gestos amplios.
3. **Encuadre**: La cámara debe capturar desde la cintura o caderas hasta por encima de la cabeza con los brazos extendidos.
4. **Iluminación**: Asegúrense de tener luz frontal o de techo. Eviten pararse directamente frente a una ventana soleada (contraluz).

---

## 4. Dinámicas de Combate en 1v1 Local

| Acción Corporal | Postura Física | Efecto en Combate | Costo Ki |
| :--- | :--- | :--- | :--- |
| **KAMEHAMEHA** | Manos juntas orientadas al rival | Dispara rayo continuo (40 HP/s de daño) | 12 Ki/s |
| **ESCUDO (SHIELD)** | Antebrazos verticales cubriendo el pecho | Mitiga el 85% de daño frontal | 0 Ki |
| **CARGA DE KI** | Codos flexionados hacia atrás, puños en cintura | Recarga Ki a +15 Ki/s con aura brillante | 0 Ki |
| **GOLPE MELEE** | Estocada recta de puño hacia adelante | 18 HP de daño a corta distancia | 0 Ki |
| **UPPERCUT** | Puño vertical ascendente sobre el mentón | 24 HP \| **ROMPE ESCUDOS** + Aturde 1.2s | 0 Ki |
| **BALANZA 67** | Una mano muy arriba y otra muy abajo (Balanza) | **Paraliza al rival por 2.0s** + Carga +35 Ki | 0 Ki |
| **HADOKEN** | Ambas palmas abiertas empujando al frente | Esfera balística veloz (24 HP de impacto) | 20 Ki |
| **GENKIDAMA** | Ambos brazos extendidos arriba al cielo | Esfera colosal en área (45 HP) | 25+ Ki |
| **DODGE ROLL** | Inclinación lateral de hombros > 25° | Inmunidad total a ataques por 0.4s | 0 Ki |
| **BRAZOS CRUZADOS** | Brazos en 'X' sobre el pecho | Bufo de poder: **Ataques +30% de daño** por 8s | 0 Ki |

### ¡El Épico Choque de Poderes (Beam Struggle)!
Si el Jugador 1 y el Jugador 2 lanzan el **Kamehameha al mismo tiempo**, los dos rayos colisionan en el medio de la pantalla.
Aparecerá el aviso de **BEAM STRUGGLE**: ¡ambos deben bombear sus brazos y puños a máxima velocidad! El que genere más intensidad empujará el rayo y detonará una explosión colosal sobre su rival.

---

## 5. Modo Simulador de Teclado 1v1 (Misma Pantalla)

Si quieren jugar en la misma computadora pero no tienen cámara web conectada, pueden usar el modo simulador con el teclado compartido:

| Movimiento | Teclas Jugador 1 (Izquierda) | Teclas Jugador 2 (Derecha) | Numpad (P2 Alternativo) |
| :--- | :---: | :---: | :---: |
| **Kamehameha** | `1` | `8` | `KP 1` |
| **Escudo** | `2` | `9` | `KP 2` |
| **Cargar Ki** | `3` | `0` | `KP 3` |
| **Reposo (Idle)** | `4` | `-` | `KP 4` |
| **Golpe Melee** | `5` | `=` | `KP 5` |
| **Uppercut (Rompe Escudo)** | `6` | `[` | `KP 6` |
| **Meme de la Balanza 67** | `7` | `]` | `KP 7` |
| **Hadoken** | `U` | `J` | `KP 8` |
| **Genkidama** | `I` | `K` | `KP 9` |
| **Dodge Roll (Esquiva)** | `O` | `L` | `KP 0` |
| **Brazos Cruzados (+30% Daño)** | `P` | `;` | `KP .` |

---

## 6. Cómo Iniciar una Partida 1v1 Local

### Método Rápido (1 Clic)
Haz doble clic en:
👉 **`INICIAR_1V1_LOCAL.bat`**
Elige la opción `[1]` para cámara web o `[3]` para teclado.

### Método por Terminal
```bash
# 1v1 Local con YOLOv8 (Recomendado)
python main.py --mode local --players 2 --backend yolo

# 1v1 Local con MediaPipe
python main.py --mode local --players 2 --backend mediapipe

# 1v1 Local en el Teclado (Sin cámara)
python main.py --mode local --players 2 --backend mock
```
