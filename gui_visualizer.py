"""
Interfaz gráfica del Motor de Trazado de Rayos Discreto.

Muestra la rejilla, el agujero negro, la geodésica calculada con Dijkstra y un panel
de telemetría con el estado del autómata, el predicado lógico y la corrección Hamming.
Incluye controles interactivos para r_s y para inyectar un Bit Flip en tiempo real.
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle,Rectangle
from matplotlib.widgets import Button,Slider

from backend_engine import (
    ATRAPADO_HORIZONTE,
    DESVIADO,
    IMPACTO_SENSOR,
    RayTracingEngineDiscreto,
)

COLORES_ESTADO={
    IMPACTO_SENSOR:"#2e7d32",
    ATRAPADO_HORIZONTE:"#c62828",
    DESVIADO:"#ef6c00",
}

ETIQUETAS_TRAMA=("p1","p2","d1","p3","d2","d3","d4")


def suavizar_trayectoria(puntos,ventana=5):
    """Suaviza la poligonal de nodos con media móvil para dibujar la curva continua de la luz."""
    if len(puntos)<3:
        return puntos
    mitad=ventana//2
    relleno=np.pad(puntos,((mitad,mitad),(0,0)),mode="edge")
    nucleo=np.ones(ventana)/ventana
    suave=np.column_stack([np.convolve(relleno[:,i],nucleo,mode="valid") for i in range(2)])
    suave[0]=puntos[0]
    suave[-1]=puntos[-1]
    return suave


class VisualizadorGUI:
    """Ventana interactiva basada en matplotlib."""

    RS_MIN=1.0
    RS_MAX=8.0

    def __init__(self,ancho=20,alto=20,r_s=3.0,origen=None,destino=None,posicion_flip=0):
        self.ancho=ancho
        self.alto=alto
        self.r_s=min(max(r_s,self.RS_MIN),self.RS_MAX)
        self.origen=origen if origen is not None else (0,alto//2)
        self.destino=destino if destino is not None else (ancho-1,alto//2)
        self.posicion_flip=posicion_flip
        self.fig=None
        self.ax_malla=None
        self.ax_info=None
        self.slider_rs=None
        self.slider_flip=None
        self.boton_reset=None

    def mostrar(self):
        """Construye la ventana, dibuja la simulación inicial y entra al bucle de eventos."""
        self.fig=plt.figure(figsize=(14,8))
        self.fig.suptitle("Motor de Trazado de Rayos Discreto - Lente Gravitacional",fontsize=13,fontweight="bold")
        self.ax_malla=self.fig.add_axes([0.04,0.22,0.54,0.70])
        self.ax_info=self.fig.add_axes([0.61,0.10,0.37,0.82])

        ax_rs=self.fig.add_axes([0.14,0.12,0.38,0.03])
        ax_flip=self.fig.add_axes([0.14,0.06,0.38,0.03])
        ax_reset=self.fig.add_axes([0.14,0.01,0.12,0.04])

        self.slider_rs=Slider(ax_rs,"Radio r_s",self.RS_MIN,self.RS_MAX,valinit=self.r_s,valstep=0.1)
        self.slider_flip=Slider(ax_flip,"Bit Flip (0=ninguno)",0,7,valinit=self.posicion_flip,valstep=1)
        self.boton_reset=Button(ax_reset,"Restablecer")

        self.slider_rs.on_changed(self._al_cambiar_controles)
        self.slider_flip.on_changed(self._al_cambiar_controles)
        self.boton_reset.on_clicked(self._al_restablecer)

        self.dibujar()
        plt.show()

    def _al_cambiar_controles(self,_valor):
        """Recalcula y redibuja cada vez que se mueve un control."""
        self.r_s=float(self.slider_rs.val)
        self.posicion_flip=int(self.slider_flip.val)
        self.dibujar()

    def _al_restablecer(self,_evento):
        """Devuelve los controles a sus valores iniciales."""
        self.slider_rs.reset()
        self.slider_flip.reset()

    def dibujar(self):
        """Ejecuta la simulación con los parámetros actuales y actualiza ambos paneles."""
        motor=RayTracingEngineDiscreto(self.ancho,self.alto,self.r_s)
        posiciones=(self.posicion_flip,) if self.posicion_flip else ()
        resultado=motor.simular(self.origen,self.destino,posiciones_flip=posiciones)
        self._dibujar_malla(motor,resultado)
        self._dibujar_panel(resultado)
        self.fig.canvas.draw_idle()

    def _dibujar_malla(self,motor,resultado):
        """Dibuja la rejilla, el agujero negro, la geodésica y los nodos recorridos."""
        ax=self.ax_malla
        ax.clear()
        ax.set_xlim(-0.5,self.ancho-0.5)
        ax.set_ylim(-0.5,self.alto-0.5)
        ax.set_aspect("equal")
        ax.set_xticks(range(self.ancho))
        ax.set_yticks(range(self.alto))
        ax.tick_params(labelsize=6)
        ax.grid(True,color="#cfd8dc",linewidth=0.5)
        ax.set_title(f"Rejilla {self.ancho}x{self.alto}  |  r_s={self.r_s:.1f} px",fontsize=10)

        xs,ys=np.meshgrid(np.arange(self.ancho),np.arange(self.alto),indexing="ij")
        radios=np.sqrt((xs-motor.centro_x)**2+(ys-motor.centro_y)**2)
        dentro=radios<=self.r_s
        ax.scatter(xs[~dentro],ys[~dentro],s=6,color="#90a4ae",zorder=1)
        ax.scatter(xs[dentro],ys[dentro],s=6,color="#37474f",zorder=1)

        centro=(motor.centro_x,motor.centro_y)
        ax.add_patch(Circle(centro,2.0*self.r_s,fill=False,linestyle=":",edgecolor="#7e57c2",linewidth=1.2,zorder=2))
        ax.add_patch(Circle(centro,1.5*self.r_s,fill=False,linestyle="--",edgecolor="#ff7043",linewidth=1.2,zorder=2))
        ax.add_patch(Circle(centro,self.r_s,facecolor="black",edgecolor="#ffb300",linewidth=2,zorder=3))
        ax.plot([],[],color="#ffb300",linewidth=2,label="Horizonte de sucesos (r_s)")
        ax.plot([],[],color="#ff7043",linestyle="--",label="Esfera de fotones (1.5 r_s)")
        ax.plot([],[],color="#7e57c2",linestyle=":",label="Zona de desvío (2 r_s)")

        if resultado.camino:
            puntos=np.array(resultado.camino,dtype=float)
            suave=suavizar_trayectoria(puntos)
            ax.plot(suave[:,0],suave[:,1],color="#00acc1",linewidth=2.8,zorder=4,label="Geodésica (Dijkstra)")
            ax.scatter(puntos[:,0],puntos[:,1],s=30,color="#ff9800",edgecolor="black",linewidth=0.5,zorder=5,label="Nodos recorridos")

        ax.scatter([self.origen[0]],[self.origen[1]],s=130,color="#43a047",edgecolor="black",zorder=6,label="Emisor")
        if resultado.renderiza:
            ax.scatter([self.destino[0]],[self.destino[1]],s=330,marker="*",color="#ffd600",edgecolor="black",zorder=7,label="Impacto en sensor")
        else:
            ax.scatter([self.destino[0]],[self.destino[1]],s=130,marker="X",color="#e53935",edgecolor="black",zorder=7,label="Sensor sin impacto")
        ax.legend(loc="upper center",bbox_to_anchor=(0.5,-0.06),ncol=3,fontsize=7,frameon=False)

    def _dibujar_trama(self,ax,y,titulo,trama,rojos=(),verdes=()):
        """Dibuja una trama de 7 bits resaltando en rojo los bits alterados y en verde los corregidos."""
        ax.text(0.04,y+0.07,titulo,fontsize=9,fontweight="bold",va="bottom")
        for indice,bit in enumerate(trama):
            posicion=indice+1
            x0=0.04+indice*0.134
            if posicion in rojos:
                fondo,borde,grosor="#ffcdd2","#c62828",2.5
            elif posicion in verdes:
                fondo,borde,grosor="#c8e6c9","#2e7d32",2.5
            else:
                fondo,borde,grosor="#eceff1","#455a64",1.0
            ax.add_patch(Rectangle((x0,y),0.11,0.055,facecolor=fondo,edgecolor=borde,linewidth=grosor))
            ax.text(x0+0.055,y+0.0275,str(bit),ha="center",va="center",fontsize=11,fontweight="bold")
            ax.text(x0+0.055,y-0.012,ETIQUETAS_TRAMA[indice],ha="center",va="top",fontsize=6,color="#78909c")

    def _dibujar_muestra_color(self,ax,x,etiqueta,color_rgb):
        """Dibuja un recuadro con el color RGB resultante."""
        normalizado=tuple(canal/255 for canal in color_rgb)
        ax.add_patch(Rectangle((x,0.03),0.2,0.07,facecolor=normalizado,edgecolor="black",linewidth=1))
        ax.text(x+0.1,0.015,etiqueta,ha="center",va="top",fontsize=7)

    def _dibujar_panel(self,resultado):
        """Dibuja el panel de telemetría: autómata, predicado lógico y corrección Hamming."""
        ax=self.ax_info
        ax.clear()
        ax.set_xlim(0,1)
        ax.set_ylim(0,1)
        ax.axis("off")
        ax.add_patch(Rectangle((0,0),1,1,facecolor="#fafafa",edgecolor="#b0bec5",linewidth=1.2))

        ax.text(0.5,0.965,"PANEL DE TELEMETRÍA",ha="center",va="center",fontsize=11,fontweight="bold")

        color_estado=COLORES_ESTADO.get(resultado.estado_final,"#1565c0")
        ax.text(0.04,0.91,"Estado final del autómata:",fontsize=9,va="center")
        ax.text(0.96,0.91,resultado.estado_final,fontsize=10,fontweight="bold",color=color_estado,ha="right",va="center")
        secuencia=" → ".join(resultado.secuencia_estados()) if resultado.historial_estados else "sin trayectoria"
        ax.text(0.04,0.865,f"Secuencia: {secuencia}",fontsize=7,color="#455a64",va="center")

        texto_render="SÍ" if resultado.renderiza else "NO"
        color_render="#2e7d32" if resultado.renderiza else "#c62828"
        ax.text(0.04,0.80,"Píxel Renderizado:",fontsize=9,va="center")
        ax.text(0.96,0.80,texto_render,fontsize=11,fontweight="bold",color=color_render,ha="right",va="center")
        ax.text(0.04,0.765,"(Estado=IMPACTO_SENSOR) ∧ ¬CruzóHorizonte",fontsize=7,color="#455a64",va="center")
        costo=f"{resultado.costo_optico:.2f}" if resultado.camino else "∞"
        ax.text(0.04,0.73,f"Costo óptico: {costo}   |   Atenuación: {resultado.factor_atenuacion:.2f}",fontsize=7.5,color="#455a64",va="center")

        ax.text(0.04,0.675,"Telemetría Hamming(7,4)",fontsize=10,fontweight="bold",va="center")
        ax.text(0.04,0.64,f"Nibble de intensidad: {resultado.bits_originales}",fontsize=8,va="center")

        alterados=tuple(resultado.posiciones_alteradas)
        verdes=(resultado.sindrome,) if resultado.sindrome and resultado.recuperacion_exitosa else ()
        self._dibujar_trama(ax,0.52,"Trama enviada",resultado.trama_enviada)
        self._dibujar_trama(ax,0.39,"Trama recibida (con ruido)",resultado.trama_recibida,rojos=alterados)
        self._dibujar_trama(ax,0.26,"Trama corregida",resultado.trama_corregida,verdes=verdes)

        if not alterados:
            diagnostico="Síndrome 0: no se detectaron errores."
            color_diag="#455a64"
        elif resultado.recuperacion_exitosa:
            diagnostico=f"Síndrome {resultado.sindrome}: bit {resultado.sindrome} corregido. Datos restaurados."
            color_diag="#2e7d32"
        else:
            diagnostico=f"Síndrome {resultado.sindrome}: error múltiple, Hamming(7,4) no lo puede corregir."
            color_diag="#c62828"
        ax.text(0.04,0.20,diagnostico,fontsize=8,color=color_diag,fontweight="bold",va="center")
        ax.text(0.04,0.17,f"Datos restaurados: {resultado.bits_recuperados}   ¿Igual al original?: {'SÍ' if resultado.recuperacion_exitosa else 'NO'}",fontsize=7.5,va="center")

        self._dibujar_muestra_color(ax,0.04,"Emitido",resultado.color_emitido)
        self._dibujar_muestra_color(ax,0.40,"Recibido sin Hamming",resultado.color_sin_correccion)
        self._dibujar_muestra_color(ax,0.76,"Restaurado",resultado.color_restaurado)
