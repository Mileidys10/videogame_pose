# Manual Oficial de Movimientos y Poses Biomecanicas
## VideoGame Pose Combat (Guía Técnica y Biomecánica)

Bienvenido al manual oficial de combate de **VideoGame Pose Combat**. Este documento describe con precision milimetrica como ejecutar cada postura corporal frente a la camara web, que efecto mecanico produce en el motor del juego y que ventajas tacticas ofrece en el combate.

---

## 1. Consejos de Calibracion y Espacio de Juego

Para garantizar una deteccion del 100% por los modelos de vision (YOLOv8-Pose o MediaPipe Tasks):

1. **Distancia a la Camara**: Ubicate entre **1.8 y 2.5 metros** del lente. Tu camara debe capturar desde tu cintura hasta por encima de tu cabeza con los brazos extendidos.
2. **Iluminacion**: Asegurate de tener una fuente de luz frontal o cenital. Evita ventanas brillantes o luces fuertes directamente a tus espaldas (contraluz).
3. **Fondo y Vestimenta**: Ropa con contraste respecto al fondo de tu habitacion mejora la precision de los keypoints en articulaciones.
4. **Guia Rapida en Partida**: En cualquier momento dentro del juego puedes presionar la tecla **'H'** o **'TAB'** para activar o desactivar la lista de movimientos en pantalla sin pausar el combate.

---

## 2. Catalogo Detallado de Movimientos de Combate

---

### 1. REPOSO / GUARDIA NEUTRA (IDLE)
* **Objetivo**: Postura base mientras evalua el proximo movimiento del oponente.
* **Como hacer la pose**:
  - Relaja los brazos pegados a los costados del cuerpo o sobre la cintura.
  - Mirada al frente hacia la pantalla.
* **Efecto en el juego**:
  - Sin consumo de Ki ni tiempo de recarga.
  - Permite recuperar estabilidad biomecanica.
* **Diagrama de Postura**:
```
     [ O ]        (Cabeza mirando al frente)
    /  |     |   |   |      (Brazos relajados a los lados)
      / ```
* **Tecla en Simulador**: `4` (P1) | `-` (P2)

---

### 2. KAMEHAMEHA / RAYO LASER CONTINUO (KAMEHAMEHA)
* **Objetivo**: Ataque energetico a distancia prolongado.
* **Como hacer la pose**:
  - Junta firmemente ambas muñecas/palmas a la altura del pecho.
  - Proyecta los brazos hacia adelante o lateralmente en direccion al rival.
* **Efecto en el juego**:
  - Consume **12 Ki por segundo**.
  - Emite un haz continuo de plasma incandescente que daña 40 HP/s al rival.
  - **Choque de Rayos (Beam Struggle)**: Si ambos jugadores lanzan el Kamehameha simultaneamente de frente, los rayos colisionan en un choque energetico central donde el jugador con mayor Ki desplaza el punto de contacto hacia el oponente.
* **Diagrama de Postura**:
```
     [ O ]
      / \ ====>  [HAZ DE PLASMA CONTINUO] ====>
    (o=o)         (Manos unidas proyectadas al frente)
      / \
```
* **Tecla en Simulador**: `1` (P1) | `8` (P2)

---

### 3. BLOQUEO / ESCUDO DEFENSIVO (SHIELD)
* **Objetivo**: Protegerse de ataques de proyectiles y rayos laser.
* **Como hacer la pose**:
  - Levanta ambos antebrazos frente al rostro y pecho en guardia alta de boxeo.
  - Las muñecas deben estar juntas o paralelas protegiendo el torso.
* **Efecto en el juego**:
  - Despliega una cupula dorada de alta energia.
  - **Mitiga el 85% del daño** de rayos laser, Hadokens y golpes melee normales.
  - **ADVERTENCIA**: Es vulnerable al golpe **UPPERCUT**, el cual destruye el escudo inmediatamente.
* **Diagrama de Postura**:
```
     [ O ]
     [|||]        (Antebrazos verticales cubriendo el pecho)
      / \
```
* **Tecla en Simulador**: `2` (P1) | `9` (P2)

---

### 4. CARGA DE ENERGIA KI (CHARGE_KI)
* **Objetivo**: Recargar rapidamente la reserva de energia para ataques especiales.
* **Como hacer la pose**:
  - Flexiona los brazos manteniendo los puños cerca de las caderas.
  - Abre los codos hacia afuera con fuerza (postura clasica de Saiyajin).
* **Efecto en el juego**:
  - Recarga **15 Ki por segundo**.
  - Genera un aura pulsante y chispas de plasma al pie del combatiente.
* **Diagrama de Postura**:
```
     [ O ]
     < | >        (Codos fuertemente abiertos hacia afuera)
     (o) (o)      (Puños en la cintura)
      / \
```
* **Tecla en Simulador**: `3` (P1) | `0` (P2)

---

### 5. GOLPE MELEE DIRECTO (PUNCH)
* **Objetivo**: Daño rapido y retroceso a corta distancia.
* **Como hacer la pose**:
  - Extiende completamente un brazo hacia adelante (estocada recta de puño).
  - Mantén el otro brazo recogido cerca del torso.
* **Efecto en el juego**:
  - Causa **18 HP de daño instantaneo** si el oponente esta a corta distancia (distancia <= 0.22).
  - Empuja al oponente hacia atras (*knockback*).
  - Cooldown rapido: **0.45 segundos**.
* **Diagrama de Postura**:
```
     [ O ]
   --[ | ]=====> [PUÑETAZO EXTENDIDO]
      / \
```
* **Tecla en Simulador**: `5` (P1) | `=` (P2)

---

### 6. GANCHO ASCENDENTE ROMPE-ESCUDOS (UPPERCUT)
* **Objetivo**: Romper escudos defensivos y castigar bloqueos rivales.
* **Como hacer la pose**:
  - Lanza un puño verticalmente hacia arriba por el centro del cuerpo, superando la altura de tu nariz.
  - El otro brazo permanece abajo o en el pecho.
* **Efecto en el juego**:
  - **Rompe escudos de inmediato**: Si el oponente esta bloqueando con escudo, el escudo colapsa, recibe **24 HP de daño** y sufre **0.45s de aturdimiento**.
  - Si el oponente no bloquea, causa **20 HP de daño**, lo eleva verticalmente y genera chispas doradas.
  - Cooldown: **1.2 segundos**.
* **Diagrama de Postura**:
```
       ^  (Puño ascendente sobre la nariz)
       |
     [ O ]
     ( | )
      / \
```
* **Tecla en Simulador**: `6` (P1) | `[` (P2)

---

### 7. BALANZA LAMELO BALL / PROVOCACION (SIXTY_SEVEN)
* **Objetivo**: Paralizar y desorientar al oponente.
* **Como hacer la pose**:
  - Separa ampliamente ambos brazos a los costados.
  - Levanta una mano muy alto (sobre la cabeza) y baja la otra mano bien abajo (cerca del muslo), simulando una balanza desequilibrada (meme de LaMelo Ball).
* **Efecto en el juego**:
  - Provoca al rival y dispara una lluvia de 25 particulas doradas en pantalla.
  - **Aturdimiento**: Paraliza temporalmente al oponente durante **2.0 segundos**, dejandolo indefenso ante un ataque cargado.
  - Cooldown: **10.0 segundos**.
* **Diagrama de Postura**:
```
   \             (Mano izquierda muy alta)
    \   [ O ]
        |   /
        |  /      (Mano derecha muy baja)
       / \
```
* **Tecla en Simulador**: `7` (P1) | `]` (P2)

---

### 8. DISPARO HADOKEN / ESFERA DE PLASMA (HADOKEN)
* **Objetivo**: Proyectil rapido y balistico a larga distancia.
* **Como hacer la pose**:
  - Extiende ambos brazos al frente a nivel del pecho con las palmas abiertas hacia el adversario.
* **Efecto en el juego**:
  - Consume **20 Ki**.
  - Dispara una bola de plasma a gran velocidad (1.8x velocidad normal).
  - Causa **24 HP de daño** al impactar directamente al oponente.
  - Cooldown: **1.0 segundo**.
* **Diagrama de Postura**:
```
     [ O ]
     [ | ] ===== (O) [ESFERA BALISTICA VELOZ] =====>
      / \
```
* **Tecla en Simulador**: `U` (P1) | `J` (P2)

---

### 9. GENKIDAMA COLOSAL (SPIRIT_BOMB)
* **Objetivo**: Ataque supremo de maxima destruccion en area.
* **Como hacer la pose**:
  - Alza ambos brazos hacia el cielo completamente extendidos por encima de la cabeza y separados lateralmente.
  - Manten la postura durante al menos 1 segundo mientras la esfera se condensa sobre ti.
  - Baja los brazos para liberar y lanzar la esfera.
* **Efecto en el juego**:
  - Requiere un minimo de **25 Ki**.
  - Mientras mantienes los brazos arriba, la esfera acumula energia y crece visualmente con arcos electricos.
  - Al soltarla, cae sobre la posicion del oponente causando **45 HP de daño devastador**, onda expansiva de 30 particulas y sacudida sismica de pantalla (*Trauma Shake*).
  - Cooldown: **4.0 segundos**.
* **Diagrama de Postura**:
```
    \   (o)   /    (Genkidama colosal sobre la cabeza)
     \ [ O ] /
       | | |
        / \
```
* **Tecla en Simulador**: `I` (P1) | `K` (P2)

---

### 10. EVASION ACROBATICA / ESQUIVA (DODGE_ROLL)
* **Objetivo**: Inmunidad total temporal contra proyectiles y ataques.
* **Como hacer la pose**:
  - Inclina tu torso y la linea de tus hombros bruscamente hacia un costado (angulo de inclinacion mayor a 25 grados respecto a la horizontal).
* **Efecto en el juego**:
  - Tu personaje realiza un dash acrobatico hacia atras.
  - **Invulnerabilidad Total**: Durante **0.4 segundos**, tu luchador recibe **0 de daño** de rayos laser, proyectiles Hadoken, golpes melee o Genkidamas.
  - Cooldown: **1.6 segundos**.
* **Diagrama de Postura**:
```
        [ O ]       (Inclinacion lateral de hombros > 25°)
       / /
      / /
     / /
```
* **Tecla en Simulador**: `O` (P1) | `L` (P2)

---

### 11. BRAZOS CRUZADOS / BUFO DE DAÑO (TAUNT_CROSS)
* **Objetivo**: Multiplicar el poder destructivo de tus siguientes golpes.
* **Como hacer la pose**:
  - Cruza con firmeza ambos antebrazos sobre tu pecho formando una "X", con cada mano tocando el hombro opuesto.
* **Efecto en el juego**:
  - Desata un estallido de aura carmesi y otorga un **bufo de daño de +30% durante 8.0 segundos**.
  - Ejemplo: Tu golpe Melee pasa de 18 HP a 23.4 HP; tu Hadoken pasa de 24 HP a 31.2 HP; tu Genkidama supera los 58 HP.
  - Cooldown: **10.0 segundos**.
* **Diagrama de Postura**:
```
     [ O ]
     < X >        (Brazos cruzados en X tocando hombros opuestos)
      / \
```
* **Tecla en Simulador**: `P` (P1) | `;` (P2)

---

## 3. Matriz Resumen de Movimientos

| Gesto Biomecanico | Accion Fisica Clave | Costo Ki | Cooldown | Dano / Efecto Primario | Tecla Simulador |
| :--- | :--- | :---: | :---: | :--- | :---: |
| **IDLE** | Brazos relajados al costado | 0 | 0.0s | Estado neutro | `4` / `-` |
| **KAMEHAMEHA** | Manos juntas proyectadas al frente | 12 Ki/s | 0.0s | Rayo continuo 40 HP/s + Beam Struggle | `1` / `8` |
| **SHIELD** | Antebrazos en vertical cubriendo rostro | 0 | 0.0s | Mitiga el 85% de daño | `2` / `9` |
| **CHARGE_KI** | Codos abiertos, puños en cintura | 0 | 0.0s | Recarga +15 Ki/s con aura | `3` / `0` |
| **PUNCH** | Estocada recta de un puño al frente | 0 | 0.45s | 18 HP daño rapido + Knockback | `5` / `=` |
| **UPPERCUT** | Puño vertical sobre la nariz | 0 | 1.2s | 24 HP + Rompe escudos + Aturdimiento | `6` / `[` |
| **SIXTY_SEVEN** | Balanza: 1 mano alta y 1 mano baja | 0 | 10.0s | Paraliza al oponente por 2.0s | `7` / `]` |
| **HADOKEN** | Ambas palmas extendidas al pecho | 20 Ki | 1.0s | 24 HP en esfera balistica rapida | `U` / `J` |
| **SPIRIT_BOMB** | Brazos alzados al cielo sobre cabeza | 25+ Ki | 4.0s | 45 HP daño masivo en area + Shake | `I` / `K` |
| **DODGE_ROLL** | Inclinacion lateral hombros >25° | 0 | 1.6s | Invulnerabilidad total 0.4s | `O` / `L` |
| **TAUNT_CROSS** | Brazos cruzados en X en el pecho | 0 | 10.0s | +30% daño de ataque por 8 segundos | `P` / `;` |

---

## 4. Guia Tactica y Combos Recomendados

1. **Combo "Ruptura y Castigo"**:
   - Cuando veas al rival ponerse en escudo dorado (`SHIELD`), acercate y lanza de inmediato un **UPPERCUT** (`6`).
   - El escudo se quebrara dejando al oponente aturdido por 0.45s.
   - Sigue inmediatamente con un **PUNCH** (`5`) para maximizar el daño y empujarlo.

2. **Combo "Poder Maximo" (Bufo + Genkidama)**:
   - Cruza los brazos en **TAUNT_CROSS** (`P`) para activar el bufo de +30%.
   - Si tienes Ki suficiente, levanta los brazos para convocar la **SPIRIT_BOMB** (`I`).
   - El daño resultante superara los 58 HP, quitando mas de media barra de vida al rival en un solo golpe.

3. **Evasion de Rayos o Hadokens**:
   - Si el oponente dispara un rayo continuo o un Hadoken directo y no tienes Ki para contratacar, inclina tus hombros hacia el costado para activar **DODGE_ROLL** (`O`).
   - El ataque pasara de largo atravesandote sin infligir ningun daño.

4. **Choque de Rayos (Beam Struggle)**:
   - Si ves venir un Kamehameha, ponte de frente y une tus manos para lanzar tu propio Kamehameha.
   - Los dos rayos colisionaran en el medio. Para ganar el choque y empujar el haz hacia el rival, entra al combate con tu barra de Ki cargada previamente usando **CHARGE_KI** (`3`).

---

## 5. Teclas Especiales del Sistema

* **'H' o 'TAB'**: Alterna la visualizacion de la guia de movimientos en pantalla durante la partida.
* **'R'**: Reinicia el combate actual y restablece las barras de salud y asaltos.
* **'ESC' o 'Q'**: Cierra y sale limpiamente del juego liberando camara y sockets.

---
*Desarrollado con arquitectura de software limpia y visión artificial en tiempo real.*
