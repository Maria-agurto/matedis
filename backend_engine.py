"""
Núcleo lógico del Motor de Trazado de Rayos Discreto.

Integra cinco técnicas de Matemática Discreta:
1. Teoría de Grafos y Dijkstra (malla espacial y geodésica discreta).
2. Máquina de Estado Finito determinista (ciclo de vida del fotón).
3. Composición de funciones (peso del espacio y atenuación de color).
4. Código Hamming(7,4) (corrección de errores de telemetría).
5. Lógica de predicados (validación del renderizado del píxel).
"""

import heapq
import math
from dataclasses import dataclass,field
from functools import reduce

PROPAGANDO="PROPAGANDO"
DESVIADO="DESVIADO"
ATRAPADO_HORIZONTE="ATRAPADO_HORIZONTE"
IMPACTO_SENSOR="IMPACTO_SENSOR"

COLOR_BASE=(255,200,80)


def componer(*funciones):
    """
    Composición de funciones: componer(f,g,h)(x) equivale a (f∘g∘h)(x)=f(g(h(x))).
    Se aplica primero la función más a la derecha.
    """
    def compuesta(valor):
        return reduce(lambda acumulado,funcion:funcion(acumulado),reversed(funciones),valor)
    return compuesta


class HammingCodecColor:
    """
    Codec Hamming(7,4) para proteger nibbles de intensidad de color.

    Disposición de la trama de 7 bits (posiciones 1 a 7):
    [p1,p2,d1,p3,d2,d3,d4]
    """

    POSICIONES_DATOS=(2,4,5,6)

    @staticmethod
    def entero_a_nibble(valor):
        """Convierte un entero de 0 a 15 en una lista de 4 bits (MSB primero)."""
        if not 0<=valor<=15:
            raise ValueError("El valor debe estar entre 0 y 15 para formar un nibble.")
        return [(valor>>3)&1,(valor>>2)&1,(valor>>1)&1,valor&1]

    @staticmethod
    def nibble_a_entero(bits):
        """Convierte una lista de 4 bits (MSB primero) en un entero de 0 a 15."""
        d1,d2,d3,d4=bits
        return d1*8+d2*4+d3*2+d4

    @staticmethod
    def extraer_datos(trama_7bits):
        """Extrae los 4 bits de datos de una trama de 7 bits."""
        return [trama_7bits[i] for i in HammingCodecColor.POSICIONES_DATOS]

    @staticmethod
    def encode(data_4bits):
        """Codifica 4 bits de datos y devuelve la trama Hamming(7,4) de 7 bits."""
        if len(data_4bits)!=4 or any(bit not in (0,1) for bit in data_4bits):
            raise ValueError("Se requieren exactamente 4 bits (0 o 1).")
        d1,d2,d3,d4=data_4bits
        p1=(d1+d2+d4)%2
        p2=(d1+d3+d4)%2
        p3=(d2+d3+d4)%2
        return [p1,p2,d1,p3,d2,d3,d4]

    @staticmethod
    def corregir_trama(code_7bits):
        """
        Calcula el síndrome y corrige un bit alterado.
        Devuelve (trama_corregida_de_7_bits,sindrome). Un síndrome 0 indica trama sin errores.
        """
        if len(code_7bits)!=7 or any(bit not in (0,1) for bit in code_7bits):
            raise ValueError("Se requieren exactamente 7 bits (0 o 1).")
        c1,c2,c3,c4,c5,c6,c7=code_7bits
        s1=(c1+c3+c5+c7)%2
        s2=(c2+c3+c6+c7)%2
        s3=(c4+c5+c6+c7)%2
        sindrome=s1*1+s2*2+s3*4
        corregida=list(code_7bits)
        if sindrome!=0:
            corregida[sindrome-1]^=1
        return corregida,sindrome

    @staticmethod
    def decode_and_correct(code_7bits):
        """Decodifica una trama de 7 bits corrigiendo un error simple. Devuelve (datos_4bits,sindrome)."""
        corregida,sindrome=HammingCodecColor.corregir_trama(code_7bits)
        return HammingCodecColor.extraer_datos(corregida),sindrome

    @staticmethod
    def inyectar_errores(trama_7bits,posiciones):
        """Invierte los bits en las posiciones indicadas (base 1) simulando ruido de radiación."""
        alterada=list(trama_7bits)
        for posicion in posiciones:
            if not 1<=posicion<=7:
                raise ValueError("La posición del bit debe estar entre 1 y 7.")
            alterada[posicion-1]^=1
        return alterada


class FotonAutomata:
    """
    Autómata finito determinista M=(Q,Σ,δ,q0,F) del ciclo de vida de un fotón.

    Q={PROPAGANDO,DESVIADO,ATRAPADO_HORIZONTE,IMPACTO_SENSOR}
    q0=PROPAGANDO
    F={ATRAPADO_HORIZONTE,IMPACTO_SENSOR} (estados absorbentes)
    """

    ESTADOS=(PROPAGANDO,DESVIADO,ATRAPADO_HORIZONTE,IMPACTO_SENSOR)
    ESTADOS_FINALES=(ATRAPADO_HORIZONTE,IMPACTO_SENSOR)

    def __init__(self,r_s):
        if r_s<=0:
            raise ValueError("El radio de Schwarzschild debe ser positivo.")
        self.r_s=r_s
        self.estado=PROPAGANDO
        self.historial=[]

    def actualizar_estado(self,r_actual,impacto_sensor=False):
        """
        Función de transición δ. Evalúa la distancia r_actual respecto a r_s:
        r<=r_s -> ATRAPADO_HORIZONTE; impacto -> IMPACTO_SENSOR;
        r<=2*r_s -> DESVIADO; en otro caso -> PROPAGANDO.
        Los estados finales no cambian una vez alcanzados.
        """
        if self.estado in self.ESTADOS_FINALES:
            return self.estado
        if r_actual<=self.r_s:
            self.estado=ATRAPADO_HORIZONTE
        elif impacto_sensor:
            self.estado=IMPACTO_SENSOR
        elif r_actual<=2.0*self.r_s:
            self.estado=DESVIADO
        else:
            self.estado=PROPAGANDO
        self.historial.append(self.estado)
        return self.estado

    def recorrer_trayectoria(self,radios,llego_al_sensor):
        """
        Alimenta el autómata con la secuencia de radios de la trayectoria.
        El último nodo se procesa con impacto en sensor si el rayo llegó a su destino.
        Devuelve el historial de estados.
        """
        total=len(radios)
        for indice,radio in enumerate(radios):
            es_ultimo=indice==total-1
            self.actualizar_estado(radio,impacto_sensor=llego_al_sensor and es_ultimo)
        return list(self.historial)

    def forzar_captura(self):
        """Marca el fotón como atrapado cuando no existe ninguna ruta posible hacia el sensor."""
        self.estado=ATRAPADO_HORIZONTE
        self.historial.append(self.estado)
        return self.estado


@dataclass
class ResultadoSimulacion:
    """Resultado completo de una simulación de trazado de rayos."""

    origen:tuple
    destino:tuple
    costo_optico:float
    camino:list
    radios:list
    historial_estados:list
    estado_final:str
    cruzo_horizonte:bool
    renderiza:bool
    factor_atenuacion:float
    bits_originales:list
    trama_enviada:list
    trama_recibida:list
    trama_corregida:list
    sindrome:int
    bits_recuperados:list
    recuperacion_exitosa:bool
    posiciones_flip:tuple
    color_emitido:tuple
    color_sin_correccion:tuple
    color_restaurado:tuple
    posiciones_alteradas:list=field(default_factory=list)

    def secuencia_estados(self):
        """Devuelve los estados visitados sin repeticiones consecutivas."""
        secuencia=[]
        for estado in self.historial_estados:
            if not secuencia or secuencia[-1]!=estado:
                secuencia.append(estado)
        return secuencia


class RayTracingEngineDiscreto:
    """Motor de trazado de rayos sobre una rejilla 2D modelada como grafo ponderado."""

    def __init__(self,ancho=20,alto=20,r_s=3.0,conectividad=8):
        if ancho<3 or alto<3:
            raise ValueError("La rejilla debe medir al menos 3x3.")
        if r_s<=0:
            raise ValueError("El radio de Schwarzschild debe ser positivo.")
        if conectividad not in (4,8):
            raise ValueError("La conectividad debe ser 4 u 8.")
        self.ancho=ancho
        self.alto=alto
        self.r_s=r_s
        self.conectividad=conectividad
        self.centro_x=ancho//2
        self.centro_y=alto//2
        self.pesos={}
        self.grafo={}
        self.construir_malla_espacial()

    def obtener_distancia_centro(self,x,y):
        """Función h: distancia euclídea del píxel (x,y) al centro de masa."""
        return math.sqrt((x-self.centro_x)**2+(y-self.centro_y)**2)

    def _peso_radial(self,r):
        """Función g: costo de paso en función del radio. Infinito dentro del horizonte."""
        if r<=self.r_s:
            return float("inf")
        return 1.0+(self.r_s/(r-self.r_s+0.1))**2

    def evaluar_peso_paso(self,x,y):
        """Peso del nodo (x,y) como composición g∘h: 1.0+(r_s/(r-r_s+0.1))^2, o inf si r<=r_s."""
        radio_nodo=lambda punto:self.obtener_distancia_centro(punto[0],punto[1])
        return componer(self._peso_radial,radio_nodo)((x,y))

    def factor_atenuacion(self,nodo):
        """
        Composición (f∘g∘h)(nodo) para la atenuación de color por Redshift:
        h=distancia al centro, g=peso del espacio, f=inverso del peso (en el intervalo [0,1]).
        """
        h=lambda punto:self.obtener_distancia_centro(punto[0],punto[1])
        g=self._peso_radial
        f=lambda peso:0.0 if math.isinf(peso) else 1.0/peso
        return componer(f,g,h)(nodo)

    @staticmethod
    def atenuar_color(color_rgb,factor):
        """Aplica el factor de atenuación a cada canal RGB, acotado a [0,255]."""
        return tuple(max(0,min(255,round(canal*factor))) for canal in color_rgb)

    def _vecinos_relativos(self):
        """Desplazamientos de vecindad según la conectividad configurada."""
        ortogonales=[(-1,0),(1,0),(0,-1),(0,1)]
        diagonales=[(-1,-1),(-1,1),(1,-1),(1,1)]
        return ortogonales+(diagonales if self.conectividad==8 else [])

    def construir_malla_espacial(self):
        """
        Construye el grafo dirigido ponderado G=(V,E,W). Cada píxel es un nodo y
        el peso de una arista es el costo del nodo destino (multiplicado por √2 en diagonales).
        """
        self.pesos={}
        self.grafo={}
        for x in range(self.ancho):
            for y in range(self.alto):
                self.pesos[(x,y)]=self.evaluar_peso_paso(x,y)
        for x in range(self.ancho):
            for y in range(self.alto):
                nodo=(x,y)
                self.grafo[nodo]=[]
                for dx,dy in self._vecinos_relativos():
                    nx,ny=x+dx,y+dy
                    if 0<=nx<self.ancho and 0<=ny<self.alto:
                        escala=math.sqrt(2) if dx!=0 and dy!=0 else 1.0
                        self.grafo[nodo].append(((nx,ny),self.pesos[(nx,ny)]*escala))

    def trazar_geodesica_dijkstra(self,origen,destino):
        """
        Algoritmo de Dijkstra con cola de prioridad (heapq).
        Devuelve (costo_total,camino). Si no existe ruta devuelve (inf,[]).
        """
        if origen not in self.grafo or destino not in self.grafo:
            raise ValueError("Origen o destino fuera de la rejilla.")
        if math.isinf(self.pesos[origen]):
            return float("inf"),[]
        dist={nodo:float("inf") for nodo in self.grafo}
        dist[origen]=0.0
        padre={}
        cola=[(0.0,origen)]
        while cola:
            d_act,u=heapq.heappop(cola)
            if u==destino:
                break
            if d_act>dist[u]:
                continue
            for v,peso in self.grafo[u]:
                if math.isinf(peso):
                    continue
                nueva=dist[u]+peso
                if nueva<dist[v]:
                    dist[v]=nueva
                    padre[v]=u
                    heapq.heappush(cola,(nueva,v))
        if origen!=destino and destino not in padre:
            return float("inf"),[]
        camino=[destino]
        while camino[-1]!=origen:
            camino.append(padre[camino[-1]])
        camino.reverse()
        return dist[destino],camino

    def evaluar_predicado_renderizado(self,estado,cruzo_horizonte):
        """Predicado RenderizarPíxel(p) ⟺ (Estado(p)=IMPACTO_SENSOR) ∧ ¬CruzóHorizonte(p)."""
        return (estado==IMPACTO_SENSOR) and not cruzo_horizonte

    def simular(self,origen,destino,color_base=COLOR_BASE,posiciones_flip=()):
        """
        Ejecuta el pipeline completo: geodésica, autómata, predicado y telemetría Hamming.
        posiciones_flip contiene las posiciones (1 a 7) de la trama que serán invertidas por radiación.
        """
        costo,camino=self.trazar_geodesica_dijkstra(origen,destino)
        automata=FotonAutomata(self.r_s)
        if camino:
            radios=[self.obtener_distancia_centro(x,y) for x,y in camino]
            llego=camino[-1]==destino
            automata.recorrer_trayectoria(radios,llego)
            cruzo=any(radio<=self.r_s for radio in radios)
            nodo_critico=min(camino,key=lambda nodo:self.obtener_distancia_centro(nodo[0],nodo[1]))
            factor=self.factor_atenuacion(nodo_critico)
        else:
            radios=[]
            automata.forzar_captura()
            cruzo=True
            factor=0.0
        renderiza=self.evaluar_predicado_renderizado(automata.estado,cruzo)

        nibble=round(factor*15)
        bits_originales=HammingCodecColor.entero_a_nibble(nibble)
        trama_enviada=HammingCodecColor.encode(bits_originales)
        trama_recibida=HammingCodecColor.inyectar_errores(trama_enviada,posiciones_flip)
        trama_corregida,sindrome=HammingCodecColor.corregir_trama(trama_recibida)
        bits_recuperados=HammingCodecColor.extraer_datos(trama_corregida)
        bits_sin_correccion=HammingCodecColor.extraer_datos(trama_recibida)

        nivel_emitido=nibble/15
        nivel_sin_correccion=HammingCodecColor.nibble_a_entero(bits_sin_correccion)/15
        nivel_restaurado=HammingCodecColor.nibble_a_entero(bits_recuperados)/15

        return ResultadoSimulacion(
            origen=origen,
            destino=destino,
            costo_optico=costo,
            camino=camino,
            radios=radios,
            historial_estados=list(automata.historial),
            estado_final=automata.estado,
            cruzo_horizonte=cruzo,
            renderiza=renderiza,
            factor_atenuacion=factor,
            bits_originales=bits_originales,
            trama_enviada=trama_enviada,
            trama_recibida=trama_recibida,
            trama_corregida=trama_corregida,
            sindrome=sindrome,
            bits_recuperados=bits_recuperados,
            recuperacion_exitosa=bits_recuperados==bits_originales,
            posiciones_flip=tuple(posiciones_flip),
            color_emitido=self.atenuar_color(color_base,nivel_emitido),
            color_sin_correccion=self.atenuar_color(color_base,nivel_sin_correccion),
            color_restaurado=self.atenuar_color(color_base,nivel_restaurado),
            posiciones_alteradas=[i+1 for i in range(7) if trama_enviada[i]!=trama_recibida[i]],
        )
