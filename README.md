# Motor de Trazado de Rayos Discreto (Ray Tracing Engine)

Simulación de lentes gravitacionales y telemetría óptica usando 5 técnicas de Matemática Discreta:
Grafos y Dijkstra, Máquinas de Estado Finito, Composición de Funciones, Código Hamming(7,4) y Lógica de Predicados.

## Estructura

- `backend_engine.py`: núcleo lógico (Hamming, autómata, grafo, Dijkstra, predicado).
- `gui_visualizer.py`: interfaz gráfica con matplotlib.
- `main.py`: menú interactivo y punto de entrada.
- `requirements.txt`: dependencias.

## Requisitos

- Python 3.9 o superior
- En Linux, si la ventana no abre: `sudo apt install python3-tk`

## Instalación y ejecución

1. Clonar el repositorio:

   ```
   git clone <URL_DEL_REPOSITORIO>
   cd <CARPETA_DEL_PROYECTO>
   ```

2. (Opcional) Crear y activar un entorno virtual:

   ```
   python -m venv venv
   source venv/bin/activate        # Linux / macOS
   venv\Scripts\activate           # Windows
   ```

3. Instalar dependencias:

   ```
   pip install -r requirements.txt
   ```

4. Ejecutar:

   ```
   python main.py
   ```

## Uso del menú

1. **Simulación predeterminada**: traza la luz de (0,10) a (19,10) rodeando el agujero negro.
2. **Bit Flip**: invierte un bit de la trama Hamming y muestra cómo se autocorrige.
3. **Modificar r_s**: usa el deslizador de la ventana para ver cómo cambia la curvatura en tiempo real.

En la ventana también puedes mover el deslizador "Bit Flip" (0 = sin fallo, 1 a 7 = posición del bit invertido).
