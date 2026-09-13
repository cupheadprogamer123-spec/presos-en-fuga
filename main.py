# -*- coding: utf-8 -*-
import os
import random
import itertools
import json

from kivy.app import App
from kivy.clock import Clock
from kivy.core.audio import SoundLoader
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.utils import get_color_from_hex


def col(h):
    return get_color_from_hex(h)


COLORES = {
    "azul": "#2980b9", "azul_h": "#3498db",
    "morado": "#8e44ad", "morado_h": "#9b59b6",
    "naranja": "#d35400", "naranja_h": "#e67e22",
    "verde_agua": "#16a085", "verde_agua_h": "#1abc9c",
    "verde": "#27ae60", "verde_h": "#2ecc71",
    "gris": "#7f8c8d", "gris_h": "#95a5a6",
    "rojo": "#e74c3c", "rojo_h": "#c0392b",
    "amarillo": "#f39c12", "amarillo_h": "#f1c40f",
    "oscuro": "#2c3e50", "oscuro2": "#34495e",
    "claro": "#ecf0f1", "blanco": "#ffffff", "negro": "#000000",
}


class BotonEstiloso(Button):
    def __init__(self, bg="#2980b9", bg_hover="#3498db", **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ""
        self.background_down = ""
        self.background_color = col(bg)
        self.color = (1, 1, 1, 1)
        self.bg_normal = col(bg)
        self.bg_hover = col(bg_hover)
        self.font_size = dp(16)
        self.bold = True
        self.size_hint_y = None
        self.height = dp(52)

    def on_press(self):
        self.background_color = self.bg_hover

    def on_release(self):
        self.background_color = self.bg_normal


class PantallaScroll(ScrollView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.do_scroll_x = False
        self.bar_width = dp(4)
        self.contenedor = BoxLayout(
            orientation="vertical", size_hint_y=None,
            padding=dp(12), spacing=dp(8),
        )
        self.contenedor.bind(minimum_height=self.contenedor.setter("height"))
        self.add_widget(self.contenedor)


class JuegoCodigoOculto(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)

        app = App.get_running_app()
        self.assets_dir = os.path.dirname(os.path.abspath(__file__))
        self.ARCHIVO_RECORDS = os.path.join(app.user_data_dir, "records.json")

        self.musica_activada = True
        self.efectos_activados = True
        self.sonidos = {}
        self.cargar_sonidos()
        self.reproducir_musica()

        self.tabla_records = self.cargar_records_desde_archivo()
        self.modo_juego = "PVP"
        self.dificultad_cpu = "Normal"
        self.dificultad_infinito = "Normal"
        self.dificultad_contrarreloj = "Normal"
        self.desbloqueado_detective = False
        self.desbloqueado_leyenda = False
        self.nombre_j1 = "Jugador 1"
        self.nombre_j2 = "Jugador 2"
        self.racha_actual = 0
        self.max_intentos_infinito = 15
        self.tiempo_restante = 900
        self.timer_event = None

        self.reiniciar_datos_partida()
        self.crear_menu_principal()

    def cargar_sonidos(self):
        archivos = {
            "musica": "L_theme.wav", "click": "click.wav",
            "victoria": "victoria.wav", "error": "error.wav",
        }
        for clave, nombre in archivos.items():
            ruta = os.path.join(self.assets_dir, nombre)
            self.sonidos[clave] = SoundLoader.load(ruta) if os.path.exists(ruta) else None
        if self.sonidos.get("musica"):
            self.sonidos["musica"].loop = True

    def reproducir_musica(self):
        s = self.sonidos.get("musica")
        if self.musica_activada and s:
            s.play()

    def detener_musica(self):
        s = self.sonidos.get("musica")
        if s:
            s.stop()

    def reproducir_efecto(self, clave):
        if not self.efectos_activados:
            return
        s = self.sonidos.get(clave)
        if s:
            s.play()

    def cargar_records_desde_archivo(self):
        if os.path.exists(self.ARCHIVO_RECORDS):
            try:
                with open(self.ARCHIVO_RECORDS, "r", encoding="utf-8") as f:
                    datos = json.load(f)
                    return [r for r in datos if r.get("nombre") not in
                            ["L", "Inspector Gadget", "Novato"]]
            except Exception as e:
                print("Error al cargar récords:", e)
        return []

    def guardar_records_en_archivo(self):
        try:
            with open(self.ARCHIVO_RECORDS, "w", encoding="utf-8") as f:
                json.dump(self.tabla_records, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print("Error al guardar récords:", e)

    def limpiar_ventana(self):
        self.detener_temporizador()
        self.clear_widgets()

    def crear_boton(self, text, command, bg="#2980b9", bg_hover="#3498db", disabled=False):
        b = BotonEstiloso(bg=bg, bg_hover=bg_hover, text=text)
        if disabled:
            b.disabled = True
            b.background_color = col(COLORES["gris"])
            b.bg_normal = col(COLORES["gris"])
            b.bg_hover = col(COLORES["gris"])
        else:
            b.bind(on_release=lambda *_: (self.reproducir_efecto("click"), command()))
        return b

    def mostrar_alerta(self, titulo, mensaje, callback_aceptar=None, tipo="info"):
        color_titulo = {
            "victoria": col(COLORES["verde"]),
            "error": col(COLORES["rojo"]),
            "info": col(COLORES["amarillo"]),
        }.get(tipo, col(COLORES["amarillo"]))

        contenido = BoxLayout(orientation="vertical", padding=dp(15), spacing=dp(12))
        contenido.add_widget(Label(
            text=titulo, font_size=dp(20), bold=True,
            color=color_titulo, size_hint_y=None, height=dp(40),
        ))
        scroll = ScrollView()
        lbl = Label(text=mensaje, font_size=dp(15), color=(1, 1, 1, 1),
                    halign="center", valign="middle", size_hint_y=None)
        lbl.bind(width=lambda *_: setattr(lbl, "text_size", (lbl.width, None)))
        lbl.bind(texture_size=lambda *_: setattr(lbl, "height", lbl.texture_size[1]))
        scroll.add_widget(lbl)
        contenido.add_widget(scroll)

        popup = Popup(
            title="", content=contenido,
            size_hint=(0.88, 0.65),
            background_color=col(COLORES["oscuro"]),
            separator_color=color_titulo,
            auto_dismiss=False,
        )

        def cerrar(*_):
            popup.dismiss()
            if callback_aceptar:
                callback_aceptar()

        contenido.add_widget(self.crear_boton(
            "Aceptar", cerrar, bg=COLORES["oscuro2"], bg_hover=COLORES["oscuro"]))
        popup.open()

    def mostrar_confirmacion(self, titulo, mensaje, funcion_si):
        contenido = BoxLayout(orientation="vertical", padding=dp(15), spacing=dp(12))
        contenido.add_widget(Label(
            text=titulo, font_size=dp(18), bold=True,
            color=col(COLORES["amarillo"]), size_hint_y=None, height=dp(40),
        ))
        contenido.add_widget(Label(text=mensaje, font_size=dp(14), color=(1, 1, 1, 1)))

        popup = Popup(
            title="", content=contenido,
            size_hint=(0.88, 0.55),
            background_color=col(COLORES["oscuro"]),
            separator_color=col(COLORES["amarillo"]),
            auto_dismiss=False,
        )
        fila = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(10))

        def si(*_):
            popup.dismiss()
            funcion_si()

        fila.add_widget(self.crear_boton("Sí", si, bg=COLORES["verde"], bg_hover=COLORES["verde_h"]))
        fila.add_widget(self.crear_boton("No", lambda *_: popup.dismiss(),
                                          bg=COLORES["rojo"], bg_hover=COLORES["rojo_h"]))
        contenido.add_widget(fila)
        popup.open()

    def detener_temporizador(self):
        if self.timer_event is not None:
            self.timer_event.cancel()
            self.timer_event = None

    def reiniciar_datos_partida(self):
        self.detener_temporizador()
        self.secreto_j1, self.secreto_j2 = [], []
        self.intentos_j1 = self.intentos_j2 = 0
        self.notas_j1 = {d: 0 for d in range(10)}
        self.notas_j2 = {d: 0 for d in range(10)}
        self.historial_j1, self.historial_j2 = [], []
        self.turno_actual = 1
        self.botones_notas = {}
        self.posibles_respuestas_cpu = [list(p) for p in itertools.permutations(range(10), 4)]

    def crear_menu_principal(self):
        self.limpiar_ventana()
        scroll = PantallaScroll()
        box = scroll.contenedor

        box.add_widget(Label(text="PRESOS EN FUGA", font_size=dp(28), bold=True,
                             color=col(COLORES["oscuro"]), size_hint_y=None, height=dp(50)))
        box.add_widget(Label(text="Selecciona un modo de juego:", font_size=dp(15),
                             color=col(COLORES["oscuro"]), size_hint_y=None, height=dp(30)))

        opciones = [
            ("Jugador vs Jugador", lambda: self.iniciar_modo("PVP"), COLORES["azul"], COLORES["azul_h"]),
            ("Jugador vs CPU", self.pantalla_dificultad_pvc, COLORES["morado"], COLORES["morado_h"]),
            ("Modo Infinito (Racha)", self.pantalla_dificultad_infinito, COLORES["naranja"], COLORES["naranja_h"]),
            ("Modo Contrarreloj", self.pantalla_dificultad_contrarreloj, COLORES["verde_agua"], COLORES["verde_agua_h"]),
            ("Cómo Jugar", self.pantalla_tutorial, COLORES["verde"], COLORES["verde_h"]),
            ("Opciones (Audio)", self.pantalla_opciones, COLORES["gris"], COLORES["gris_h"]),
        ]
        for texto, cmd, bg, bg_h in opciones:
            box.add_widget(self.crear_boton(texto, cmd, bg=bg, bg_hover=bg_h))

        box.add_widget(Label(text="TABLA DE MORTALES (MÁXIMA RACHA)",
                             font_size=dp(15), bold=True, color=col(COLORES["oscuro"]),
                             size_hint_y=None, height=dp(30)))
        records = sorted(self.tabla_records, key=lambda x: x["racha"], reverse=True)[:5]
        if not records:
            box.add_widget(Label(text="Ningún mortal ha registrado su marca aún.",
                                 font_size=dp(13), italic=True, color=col(COLORES["gris"]),
                                 size_hint_y=None, height=dp(30)))
        else:
            for i, rec in enumerate(records):
                medalla = "1." if i == 0 else ("2." if i == 1 else ("3." if i == 2 else "-"))
                txt = f"{medalla} #{i+1} {rec['nombre']} - {rec['racha']} Casos ({rec['dificultad']})"
                box.add_widget(Label(text=txt, font_size=dp(13), bold=True,
                                     color=col(COLORES["oscuro2"]),
                                     size_hint_y=None, height=dp(24)))
        self.add_widget(scroll)

    def pantalla_tutorial(self):
        self.limpiar_ventana()
        scroll = PantallaScroll()
        box = scroll.contenedor

        box.add_widget(Label(text="CÓMO JUGAR", font_size=dp(22), bold=True,
                             color=col(COLORES["oscuro"]), size_hint_y=None, height=dp(50)))
        texto = (
            "El objetivo es adivinar el código secreto de 4 dígitos únicos (del 0 al 9).\n\n"
            "Pistas recibidas tras cada intento:\n"
            "- Presos (Exactos): Dígitos correctos en la posición exacta.\n"
            "- Fugados (Desplazados): Dígitos correctos pero en posición incorrecta.\n\n"
            "Bloc de Notas:\n"
            "Toca un dígito para marcarlo en rojo (descartado) o verde (confirmado).\n\n"
            "Modos de Juego:\n"
            "- PvP: Enfréntate cara a cara. Cada jugador oculta su código.\n"
            "- vs CPU: Deduce el código de la máquina mientras ella deduce el tuyo.\n"
            "- Modo Infinito: Acumula victorias. Desbloquea rangos tras rachas >= 5.\n"
            "- Contrarreloj: Desarma la bomba antes de que el tiempo llegue a cero."
        )
        lbl = Label(text=texto, font_size=dp(13), color=col(COLORES["oscuro"]),
                    halign="left", valign="top", size_hint_y=None)
        lbl.bind(width=lambda *_: setattr(lbl, "text_size", (lbl.width - dp(10), None)))
        lbl.bind(texture_size=lambda *_: setattr(lbl, "height", lbl.texture_size[1] + dp(10)))
        box.add_widget(lbl)
        box.add_widget(self.crear_boton("Volver al Menú", self.crear_menu_principal,
                                         bg=COLORES["gris"], bg_hover=COLORES["gris_h"]))
        self.add_widget(scroll)

    def pantalla_opciones(self):
        self.limpiar_ventana()
        scroll = PantallaScroll()
        box = scroll.contenedor
        box.add_widget(Label(text="CONFIGURACIÓN DE AUDIO", font_size=dp(20), bold=True,
                             color=col(COLORES["oscuro"]), size_hint_y=None, height=dp(50)))

        txt_m = "Música: ACTIVADA" if self.musica_activada else "Música: DESACTIVADA"
        box.add_widget(self.crear_boton(
            txt_m, self.toggle_musica,
            bg=COLORES["verde"] if self.musica_activada else COLORES["rojo"],
            bg_hover=COLORES["verde_h"] if self.musica_activada else COLORES["rojo_h"]))

        txt_e = "Efectos: ACTIVADOS" if self.efectos_activados else "Efectos: DESACTIVADOS"
        box.add_widget(self.crear_boton(
            txt_e, self.toggle_efectos,
            bg=COLORES["verde"] if self.efectos_activados else COLORES["rojo"],
            bg_hover=COLORES["verde_h"] if self.efectos_activados else COLORES["rojo_h"]))

        box.add_widget(self.crear_boton("Volver", self.crear_menu_principal,
                                         bg=COLORES["gris"], bg_hover=COLORES["gris_h"]))
        self.add_widget(scroll)

    def toggle_musica(self):
        self.musica_activada = not self.musica_activada
        if self.musica_activada:
            self.reproducir_musica()
        else:
            self.detener_musica()
        self.pantalla_opciones()

    def toggle_efectos(self):
        self.efectos_activados = not self.efectos_activados
        self.pantalla_opciones()

    def pantalla_dificultad_pvc(self):
        self.limpiar_ventana()
        scroll = PantallaScroll()
        box = scroll.contenedor
        box.add_widget(Label(text="DIFICULTAD DE LA CPU", font_size=dp(20), bold=True,
                             color=col(COLORES["morado"]), size_hint_y=None, height=dp(50)))

        for txt, dif, bg, bgh in [
            ("Fácil (Aleatorio)", "Fácil", COLORES["verde"], COLORES["verde_h"]),
            ("Normal (Deducción Moderada)", "Normal", COLORES["amarillo"], COLORES["amarillo_h"]),
            ("Difícil (Implacable)", "Difícil", COLORES["rojo"], COLORES["rojo_h"]),
        ]:
            box.add_widget(self.crear_boton(
                txt, lambda d=dif: self.confirmar_dificultad_pvc(d), bg=bg, bg_hover=bgh))

        box.add_widget(self.crear_boton("Volver", self.crear_menu_principal,
                                         bg=COLORES["gris"], bg_hover=COLORES["gris_h"]))
        self.add_widget(scroll)

    def confirmar_dificultad_pvc(self, diff):
        self.dificultad_cpu = diff
        self.iniciar_modo("PVC")

    def pantalla_dificultad_infinito(self):
        self.limpiar_ventana()
        scroll = PantallaScroll()
        box = scroll.contenedor
        box.add_widget(Label(text="DIFICULTAD MODO INFINITO", font_size=dp(20), bold=True,
                             color=col(COLORES["naranja"]), size_hint_y=None, height=dp(50)))

        for txt, dif, n, bg, bgh in [
            ("Fácil (20 Intentos)", "Fácil", 20, COLORES["verde"], COLORES["verde_h"]),
            ("Normal (15 Intentos)", "Normal", 15, COLORES["amarillo"], COLORES["amarillo_h"]),
            ("Difícil (8 Intentos)", "Difícil", 8, COLORES["rojo"], COLORES["rojo_h"]),
        ]:
            box.add_widget(self.crear_boton(
                txt, lambda d=dif, i=n: self.confirmar_dificultad_infinito(d, i),
                bg=bg, bg_hover=bgh))

        box.add_widget(self.crear_boton("Volver", self.crear_menu_principal,
                                         bg=COLORES["gris"], bg_hover=COLORES["gris_h"]))
        self.add_widget(scroll)

    def confirmar_dificultad_infinito(self, diff, intentos):
        self.dificultad_infinito = diff
        self.max_intentos_infinito = intentos
        self.iniciar_modo("INFINITO")

    def pantalla_dificultad_contrarreloj(self):
        self.limpiar_ventana()
        scroll = PantallaScroll()
        box = scroll.contenedor
        box.add_widget(Label(text="DIFICULTAD CONTRARRELOJ", font_size=dp(20), bold=True,
                             color=col(COLORES["verde_agua"]), size_hint_y=None, height=dp(50)))

        for txt, dif, seg, bg, bgh in [
            ("Fácil (20 Minutos)", "Fácil", 1200, COLORES["verde"], COLORES["verde_h"]),
            ("Normal (15 Minutos)", "Normal", 900, COLORES["amarillo"], COLORES["amarillo_h"]),
            ("Difícil (10 Minutos)", "Difícil", 600, COLORES["rojo"], COLORES["rojo_h"]),
            ("Extremo (5 Minutos)", "Extremo", 300, COLORES["morado"], COLORES["morado_h"]),
        ]:
            box.add_widget(self.crear_boton(
                txt, lambda d=dif, s=seg: self.confirmar_dificultad_contrarreloj(d, s),
                bg=bg, bg_hover=bgh))

        box.add_widget(self.crear_boton("Volver", self.crear_menu_principal,
                                         bg=COLORES["gris"], bg_hover=COLORES["gris_h"]))
        self.add_widget(scroll)

    def confirmar_dificultad_contrarreloj(self, diff, tiempo):
        self.dificultad_contrarreloj = diff
        self.tiempo_restante = tiempo
        self.iniciar_modo("CONTRARRELOJ")

    def iniciar_modo(self, modo):
        self.modo_juego = modo
        self.reiniciar_datos_partida()

        if modo == "PVP":
            self.nombre_j1, self.nombre_j2 = "Jugador 1", "Jugador 2"
            self.crear_pantalla_nombres_pvp()
        elif modo == "PVC":
            self.nombre_j1 = "Jugador 1"
            self.nombre_j2 = f"CPU ({self.dificultad_cpu})"
            self.crear_pantalla_registro_pvc()
        elif modo == "INFINITO":
            self.racha_actual = 0
            self.nombre_j1 = "Detective"
            self.iniciar_nivel_infinito()
        elif modo == "CONTRARRELOJ":
            self.nombre_j1, self.nombre_j2 = "Agente", "Bomba de Tiempo"
            digitos = list(range(10))
            random.shuffle(digitos)
            self.secreto_j2 = digitos[:4]
            self.crear_pantalla_juego()

    def _entry(self, hint="", password=False):
        return TextInput(
            text=hint, multiline=False, password=password,
            halign="center", font_size=dp(20),
            size_hint_y=None, height=dp(50),
            input_filter="int" if password else None,
            input_type="number" if password else "text",
        )

    def _validar_secreto(self, texto):
        return len(texto) == 4 and texto.isdigit() and len(set(texto)) == 4

    def crear_pantalla_nombres_pvp(self):
        self.limpiar_ventana()
        scroll = PantallaScroll()
        box = scroll.contenedor
        box.add_widget(Label(text="MODO 2 JUGADORES", font_size=dp(20), bold=True,
                             color=col(COLORES["oscuro"]), size_hint_y=None, height=dp(50)))
        box.add_widget(Label(text="Nombre Jugador 1:", font_size=dp(14),
                             color=col(COLORES["oscuro"]), size_hint_y=None, height=dp(30)))
        self.entry_nombre_j1 = self._entry("Jugador 1")
        box.add_widget(self.entry_nombre_j1)
        box.add_widget(Label(text="Nombre Jugador 2:", font_size=dp(14),
                             color=col(COLORES["oscuro"]), size_hint_y=None, height=dp(30)))
        self.entry_nombre_j2 = self._entry("Jugador 2")
        box.add_widget(self.entry_nombre_j2)
        box.add_widget(self.crear_boton("Continuar", self.guardar_nombres_pvp,
                                         bg=COLORES["verde"], bg_hover=COLORES["verde_h"]))
        self.add_widget(scroll)

    def guardar_nombres_pvp(self):
        n1 = (self.entry_nombre_j1.text or "").strip()
        n2 = (self.entry_nombre_j2.text or "").strip()
        self.nombre_j1 = n1 if n1 and n1 != "Jugador 1" else "Jugador 1"
        self.nombre_j2 = n2 if n2 and n2 != "Jugador 2" else "Jugador 2"
        self.crear_pantalla_ingreso_j1()

    def crear_pantalla_ingreso_j1(self):
        self.limpiar_ventana()
        scroll = PantallaScroll()
        box = scroll.contenedor
        box.add_widget(Label(text=self.nombre_j1.upper(), font_size=dp(22), bold=True,
                             color=col(COLORES["oscuro"]), size_hint_y=None, height=dp(50)))
        box.add_widget(Label(text="Ingresa tu número secreto de 4 dígitos:",
                             font_size=dp(15), color=col(COLORES["oscuro"]),
                             size_hint_y=None, height=dp(30)))
        self.entry_secreto = self._entry(password=True)
        box.add_widget(self.entry_secreto)
        box.add_widget(self.crear_boton(f"Guardar y Turno de {self.nombre_j2}",
                                         self.guardar_secreto_j1,
                                         bg=COLORES["verde"], bg_hover=COLORES["verde_h"]))
        self.add_widget(scroll)

    def guardar_secreto_j1(self):
        texto = (self.entry_secreto.text or "").strip()
        if not self._validar_secreto(texto):
            self.mostrar_alerta("Error", "Debes ingresar exactamente 4 dígitos distintos.",
                                 tipo="error")
            return
        self.secreto_j1 = [int(d) for d in texto]
        self.crear_pantalla_ingreso_j2()

    def crear_pantalla_ingreso_j2(self):
        self.limpiar_ventana()
        scroll = PantallaScroll()
        box = scroll.contenedor
        box.add_widget(Label(text=self.nombre_j2.upper(), font_size=dp(22), bold=True,
                             color=col(COLORES["oscuro"]), size_hint_y=None, height=dp(50)))
        box.add_widget(Label(text="Ingresa tu número secreto de 4 dígitos:",
                             font_size=dp(15), color=col(COLORES["oscuro"]),
                             size_hint_y=None, height=dp(30)))
        self.entry_secreto = self._entry(password=True)
        box.add_widget(self.entry_secreto)
        box.add_widget(self.crear_boton("Guardar e Iniciar Juego", self.guardar_secreto_j2,
                                         bg=COLORES["verde"], bg_hover=COLORES["verde_h"]))
        self.add_widget(scroll)

    def guardar_secreto_j2(self):
        texto = (self.entry_secreto.text or "").strip()
        if not self._validar_secreto(texto):
            self.mostrar_alerta("Error", "Debes ingresar exactamente 4 dígitos distintos.",
                                 tipo="error")
            return
        self.secreto_j2 = [int(d) for d in texto]
        self.mostrar_pantalla_transicion()

    def crear_pantalla_registro_pvc(self):
        self.limpiar_ventana()
        scroll = PantallaScroll()
        box = scroll.contenedor
        box.add_widget(Label(text=f"DUELO CONTRA LA CPU ({self.dificultad_cpu.upper()})",
                             font_size=dp(18), bold=True, color=col(COLORES["morado"]),
                             size_hint_y=None, height=dp(50)))
        box.add_widget(Label(text="Tu Nombre:", font_size=dp(14),
                             color=col(COLORES["oscuro"]), size_hint_y=None, height=dp(30)))
        self.entry_nombre_j1 = self._entry("Jugador 1")
        box.add_widget(self.entry_nombre_j1)
        box.add_widget(Label(text="Tu número secreto (4 dígitos):", font_size=dp(14),
                             color=col(COLORES["oscuro"]), size_hint_y=None, height=dp(30)))
        self.entry_secreto = self._entry(password=True)
        box.add_widget(self.entry_secreto)
        box.add_widget(self.crear_boton("¡Iniciar Duelo!", self.guardar_pvc_y_comenzar,
                                         bg=COLORES["morado"], bg_hover=COLORES["morado_h"]))
        self.add_widget(scroll)

    def guardar_pvc_y_comenzar(self):
        n1 = (self.entry_nombre_j1.text or "").strip()
        texto = (self.entry_secreto.text or "").strip()
        if not self._validar_secreto(texto):
            self.mostrar_alerta("Error", "Debes ingresar exactamente 4 dígitos distintos.",
                                 tipo="error")
            return
        self.nombre_j1 = n1 if n1 and n1 != "Jugador 1" else "Jugador 1"
        self.secreto_j1 = [int(d) for d in texto]
        digitos = list(range(10))
        random.shuffle(digitos)
        self.secreto_j2 = digitos[:4]
        self.crear_pantalla_juego()

    def iniciar_nivel_infinito(self):
        self.reiniciar_datos_partida()
        digitos = list(range(10))
        random.shuffle(digitos)
        self.secreto_j2 = digitos[:4]
        self.crear_pantalla_juego()

    def mostrar_pantalla_transicion(self):
        self.limpiar_ventana()
        scroll = PantallaScroll()
        box = scroll.contenedor
        nombre_actual = self.nombre_j1 if self.turno_actual == 1 else self.nombre_j2
        box.add_widget(Label(text=f"¡Turno de {nombre_actual}!", font_size=dp(22), bold=True,
                             color=col(COLORES["oscuro"]), size_hint_y=None, height=dp(50)))
        box.add_widget(Label(text="Pásale el control al otro jugador\ny presiona el botón "
                                  "cuando estés listo.",
                             font_size=dp(15), color=col(COLORES["oscuro"]),
                             size_hint_y=None, height=dp(60)))
        box.add_widget(self.crear_boton("¡Estoy listo!", self.crear_pantalla_juego,
                                         bg=COLORES["azul"], bg_hover=COLORES["azul_h"]))
        self.add_widget(scroll)

    def confirmar_volver_menu(self):
        self.mostrar_confirmacion(
            "¿Abandonar partida?",
            "Si vuelves al menú principal perderás el progreso actual.",
            self.crear_menu_principal)

    def crear_pantalla_juego(self):
        self.limpiar_ventana()
        nombre_actual = self.nombre_j1 if self.turno_actual == 1 else self.nombre_j2

        top = BoxLayout(size_hint_y=None, height=dp(50), padding=dp(8), spacing=dp(8))
        if self.modo_juego == "INFINITO":
            top.add_widget(Label(
                text=f"CASO #{self.racha_actual + 1} ({self.dificultad_infinito}) | "
                     f"Racha: {self.racha_actual}",
                font_size=dp(14), bold=True, color=col(COLORES["naranja"])))
        elif self.modo_juego == "CONTRARRELOJ":
            mins, secs = self.tiempo_restante // 60, self.tiempo_restante % 60
            self.lbl_timer = Label(
                text=f"Tiempo: {mins:02d}:{secs:02d} ({self.dificultad_contrarreloj})",
                font_size=dp(14), bold=True, color=col(COLORES["rojo"]))
            top.add_widget(self.lbl_timer)
            self.actualizar_temporizador()
        else:
            top.add_widget(Label(text=f"TURNO: {nombre_actual.upper()}",
                                 font_size=dp(14), bold=True, color=col(COLORES["oscuro"])))

        btn_menu = BotonEstiloso(text="Menú", bg=COLORES["rojo"], bg_hover=COLORES["rojo_h"])
        btn_menu.width = dp(80)
        btn_menu.size_hint_x = None
        btn_menu.height = dp(40)
        btn_menu.bind(on_release=lambda *_: self.confirmar_volver_menu())
        top.add_widget(btn_menu)
        self.add_widget(top)

        if self.modo_juego == "INFINITO":
            intentos_restantes = self.max_intentos_infinito - self.intentos_j1
            self.lbl_intentos_infinito = Label(
                text=f"Intentos Restantes: {intentos_restantes} / {self.max_intentos_infinito}",
                font_size=dp(13), bold=True, color=col(COLORES["rojo"]),
                size_hint_y=None, height=dp(28))
            self.add_widget(self.lbl_intentos_infinito)

        bloc_label = Label(text="Bloc de Notas (toca para marcar)",
                           font_size=dp(13
