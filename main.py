"""
Punto de entrada del Motor de Trazado de Rayos Discreto.
Menú interactivo por consola que lanza la interfaz gráfica.
"""

from backend_engine import RayTracingEngineDiscreto
from gui_visualizer import VisualizadorGUI

ANCHO=20
ALTO=20
R_S_DEFECTO=3.0
ORIGEN=(0,ALTO//2)
DESTINO=(ANCHO-1,ALTO//2)


def leer_numero(mensaje,minimo,maximo,defecto,tipo=float):
    """Lee un número validado por consola. Enter devuelve el valor por defecto."""
    while True:
        texto=input(mensaje).strip()
        if texto=="":
            return defecto
        try:
            valor=tipo(texto)
        except ValueError:
            print("Entrada no válida, intenta de nuevo.")
            continue
        if minimo<=valor<=maximo:
            return valor
        print(f"El valor debe estar entre {minimo} y {maximo}.")


def imprimir_reporte(resultado,r_s):
    """Muestra en consola el resumen de la simulación."""
    print("\n"+"="*60)
    print(" RESULTADO DE LA SIMULACIÓN")
    print("="*60)
    print(f"Radio de Schwarzschild: {r_s:.1f} píxeles")
    print(f"Origen: {resultado.origen}  ->  Sensor: {resultado.destino}")
    if resultado.camino:
        print(f"Nodos en la geodésica: {len(resultado.camino)}")
        print(f"Costo óptico (retardo gravitacional): {resultado.costo_optico:.2f}")
        print(f"Aproximación mínima al centro: {min(resultado.radios):.2f} px")
    else:
        print("No existe ruta posible: el fotón es absorbido por el horizonte.")
    print(f"Secuencia de estados: {' -> '.join(resultado.secuencia_estados())}")
    print(f"Estado final del autómata: {resultado.estado_final}")
    print(f"Píxel renderizado: {'SÍ' if resultado.renderiza else 'NO'}")
    print("\n--- Telemetría Hamming(7,4) ---")
    print(f"Bits de intensidad emitidos: {resultado.bits_originales}")
    print(f"Trama enviada:  {resultado.trama_enviada}")
    print(f"Trama recibida: {resultado.trama_recibida}")
    if resultado.posiciones_alteradas:
        print(f"Bits alterados por radiación (posiciones): {resultado.posiciones_alteradas}")
    print(f"Síndrome: {resultado.sindrome}")
    print(f"Bits restaurados: {resultado.bits_recuperados}")
    print(f"¿Imagen sin distorsión?: {'SÍ' if resultado.recuperacion_exitosa else 'NO'}")
    print("="*60+"\n")


def ejecutar_simulacion(r_s=R_S_DEFECTO,posicion_flip=0):
    """Ejecuta la simulación, imprime el reporte y abre la ventana gráfica."""
    motor=RayTracingEngineDiscreto(ANCHO,ALTO,r_s)
    posiciones=(posicion_flip,) if posicion_flip else ()
    resultado=motor.simular(ORIGEN,DESTINO,posiciones_flip=posiciones)
    imprimir_reporte(resultado,r_s)
    print("Abriendo ventana gráfica (ciérrala para volver al menú)...")
    VisualizadorGUI(ANCHO,ALTO,r_s,ORIGEN,DESTINO,posicion_flip).mostrar()


def opcion_simulacion_predeterminada():
    """Opción 1: simulación estándar sin fallos."""
    ejecutar_simulacion()


def opcion_bit_flip():
    """Opción 2: Bit Flip voluntario para demostrar la autocorrección de Hamming."""
    posicion=leer_numero("Posición del bit a invertir (1 a 7) [3]: ",1,7,3,int)
    ejecutar_simulacion(posicion_flip=posicion)


def opcion_modificar_radio():
    """Opción 3: modificar r_s; la ventana incluye un deslizador para verlo en tiempo real."""
    r_s=leer_numero(
        f"Radio de Schwarzschild inicial ({VisualizadorGUI.RS_MIN} a {VisualizadorGUI.RS_MAX}) [{R_S_DEFECTO}]: ",
        VisualizadorGUI.RS_MIN,
        VisualizadorGUI.RS_MAX,
        R_S_DEFECTO,
        float,
    )
    print("Usa el deslizador 'Radio r_s' de la ventana para cambiar la curvatura en tiempo real.")
    ejecutar_simulacion(r_s=r_s)


def mostrar_menu():
    """Imprime el menú principal."""
    print("\n==========================================================")
    print(" MOTOR DE TRAZADO DE RAYOS DISCRETO - LENTE GRAVITACIONAL ")
    print("==========================================================")
    print(" 1. Ejecutar simulación predeterminada")
    print(" 2. Simular fallo por radiación (Bit Flip) y autocorrección Hamming")
    print(" 3. Modificar el radio de Schwarzschild (r_s) en tiempo real")
    print(" 4. Salir")


def main():
    """Bucle principal del menú."""
    acciones={
        "1":opcion_simulacion_predeterminada,
        "2":opcion_bit_flip,
        "3":opcion_modificar_radio,
    }
    while True:
        mostrar_menu()
        eleccion=input("Elige una opción: ").strip()
        if eleccion=="4":
            print("Hasta luego.")
            break
        accion=acciones.get(eleccion)
        if accion is None:
            print("Opción no válida.")
            continue
        accion()


if __name__=="__main__":
    main()
