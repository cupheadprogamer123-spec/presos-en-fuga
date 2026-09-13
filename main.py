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
                           font_size=dp(13), bold=True, color=col(COLORES["oscuro"]),
                           size_hint_y=None, height=dp(26))
        self.add_widget(bloc_label)

        grid = GridLayout(cols=5, size_hint_y=None, height=dp(120),
                          spacing=dp(6), padding=dp(6))
        self.botones_notas = {}
        notas_actuales = self.notas_j1 if self.turno_actual == 1 else self.notas_j2
        for num in range(10):
            estado = notas_actuales[num]
            bg_col, fg_col = self.obtener_colores_nota(estado)
            b = Button(text=str(num), font_size=dp(20), bold=True,
                       background_normal="", background_down="",
                       background_color=col(bg_col), color=col(fg_col))
            b.bind(on_release=lambda inst, n=num: self.rotar_estado_nota(n))
            self.botones_notas[num] = b
            grid.add_widget(b)
        self.add_widget(grid)

        fila_intento = BoxLayout(size_hint_y=None, height=dp(60),
                                 padding=dp(8), spacing=dp(8))
        fila_intento.add_widget(Label(text="Intento:", font_size=dp(15), bold=True,
                                       color=col(COLORES["oscuro"]), size_hint_x=None,
                                       width=dp(80)))
        self.entry_intento = TextInput(
            multiline=False, input_filter="int", input_type="number",
            halign="center", font_size=dp(22),
            size_hint_x=None, width=dp(120))
        fila_intento.add_widget(self.entry_intento)

        self.btn_probar = BotonEstiloso(text="Probar", bg=COLORES["verde"],
                                        bg_hover=COLORES["verde_h"])
        self.btn_probar.bind(on_release=lambda *_: self.procesar_intento())
        fila_intento.add_widget(self.btn_probar)

        siguiente = self.nombre_j2 if self.turno_actual == 1 else self.nombre_j1
        self.btn_pasar_turno = BotonEstiloso(
            text=f"Pasar a {siguiente}", bg=COLORES["azul"], bg_hover=COLORES["azul_h"])
        self.btn_pasar_turno.bind(on_release=lambda *_: self.confirmar_cambio_turno())
        self.btn_pasar_turno.opacity = 0
        self.btn_pasar_turno.disabled = True
        fila_intento.add_widget(self.btn_pasar_turno)

        self.add_widget(fila_intento)

        self.add_widget(Label(text="Historial de Intentos", font_size=dp(13), bold=True,
                              color=col(COLORES["oscuro"]),
                              size_hint_y=None, height=dp(26)))
        scroll_hist = ScrollView()
        self.historial_layout = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=dp(2), padding=dp(4))
        self.historial_layout.bind(minimum_height=self.historial_layout.setter("height"))
        scroll_hist.add_widget(self.historial_layout)
        self.add_widget(scroll_hist)

        self.actualizar_vista_historial()

    def actualizar_vista_historial(self):
        self.historial_layout.clear_widgets()
        if self.modo_juego == "PVC":
            combinado = []
            for item in self.historial_j1:
                combinado.append((item[3],
                    f"J1 {self.nombre_j1}: {item[0]} -> {item[1]}P | {item[2]}F"))
            for item in self.historial_j2:
                combinado.append((item[3],
                    f"CPU: {item[0]} -> {item[1]}P | {item[2]}F"))
            combinado.sort(key=lambda x: x[0])
            for _, txt in combinado:
                self.historial_layout.add_widget(self._label_hist(txt))
        else:
            historial = self.historial_j1 if self.turno_actual == 1 else self.historial_j2
            for intento_txt, exactos, desplazados, num_intento in historial:
                txt = f"N°{num_intento} {intento_txt} -> {exactos}P | {desplazados}F"
                self.historial_layout.add_widget(self._label_hist(txt))

    def _label_hist(self, txt):
        return Label(text=txt, font_size=dp(13), bold=True,
                     color=col(COLORES["oscuro2"]), halign="left", valign="middle",
                     size_hint_y=None, height=dp(26))

    def obtener_colores_nota(self, estado):
        if estado == 0:
            return "#f0f0f0", "#000000"
        elif estado == 1:
            return "#e74c3c", "#ffffff"
        else:
            return "#27ae60", "#ffffff"

    def rotar_estado_nota(self, num):
        self.reproducir_efecto("click")
        notas_actuales = self.notas_j1 if self.turno_actual == 1 else self.notas_j2
        nuevo = (notas_actuales[num] + 1) % 3
        notas_actuales[num] = nuevo
        bg_col, fg_col = self.obtener_colores_nota(nuevo)
        self.botones_notas[num].background_color = col(bg_col)
        self.botones_notas[num].color = col(fg_col)

    def actualizar_temporizador(self, *args):
        if self.modo_juego != "CONTRARRELOJ":
            return
        if self.tiempo_restante > 0:
            self.tiempo_restante -= 1
            mins, secs = self.tiempo_restante // 60, self.tiempo_restante % 60
            if hasattr(self, "lbl_timer"):
                self.lbl_timer.text = f"Tiempo: {mins:02d}:{secs:02d} ({self.dificultad_contrarreloj})"
            self.timer_event = Clock.schedule_once(self.actualizar_temporizador, 1)
        else:
            self.detener_temporizador()
            self.reproducir_efecto("error")
            secreto_txt = "".join(map(str, self.secreto_j2))
            self.mostrar_alerta("¡TIEMPO AGOTADO!",
                f"¡La bomba explotó!\nEl código secreto era: {secreto_txt}",
                callback_aceptar=self.crear_menu_principal, tipo="error")

    def evaluar_intento(self, intento, secreto):
        exactos = desplazados = 0
        for i in range(4):
            if intento[i] == secreto[i]:
                exactos += 1
            elif intento[i] in secreto:
                desplazados += 1
        return exactos, desplazados

    def procesar_intento(self):
        texto = (self.entry_intento.text or "").strip()
        if not self._validar_secreto(texto):
            self.mostrar_alerta("Error", "Debes ingresar exactamente 4 dígitos distintos.",
                                 tipo="error")
            return
        intento_num = [int(d) for d in texto]

        if self.turno_actual == 1:
            self.intentos_j1 += 1
            exactos, desplazados = self.evaluar_intento(intento_num, self.secreto_j2)
            self.historial_j1.append((texto, exactos, desplazados, self.intentos_j1))
            self.entry_intento.text = ""
            self.actualizar_vista_historial()

            if exactos == 4:
                self.declarar_victoria(self.nombre_j1)
                return

            if self.modo_juego == "PVP":
                self.btn_probar.disabled = True
                self.btn_probar.opacity = 0
                self.btn_pasar_turno.disabled = False
                self.btn_pasar_turno.opacity = 1
            elif self.modo_juego == "PVC":
                self.ejecutar_turno_cpu()
            elif self.modo_juego == "INFINITO":
                if self.intentos_j1 >= self.max_intentos_infinito:
                    self.racha_actual = 0
                    secreto_txt = "".join(map(str, self.secreto_j2))
                    self.mostrar_alerta("¡SIN INTENTOS!",
                        f"Te has quedado sin intentos. Tu racha vuelve a 0.\n"
                        f"El código era: {secreto_txt}",
                        callback_aceptar=self.crear_menu_principal, tipo="error")
                else:
                    self.lbl_intentos_infinito.text = (
                        f"Intentos Restantes: "
                        f"{self.max_intentos_infinito - self.intentos_j1} / "
                        f"{self.max_intentos_infinito}")
        else:
            self.intentos_j2 += 1
            exactos, desplazados = self.evaluar_intento(intento_num, self.secreto_j1)
            self.historial_j2.append((texto, exactos, desplazados, self.intentos_j2))
            self.entry_intento.text = ""
            self.actualizar_vista_historial()

            if exactos == 4:
                self.declarar_victoria(self.nombre_j2)
                return

            self.btn_probar.disabled = True
            self.btn_probar.opacity = 0
            self.btn_pasar_turno.disabled = False
            self.btn_pasar_turno.opacity = 1

    def ejecutar_turno_cpu(self):
        self.intentos_j2 += 1
        if self.dificultad_cpu == "Fácil" or not self.posibles_respuestas_cpu:
            intento_cpu = random.sample(range(10), 4)
        else:
            intento_cpu = random.choice(self.posibles_respuestas_cpu)

        exactos, desplazados = self.evaluar_intento(intento_cpu, self.secreto_j1)
        intento_str = "".join(map(str, intento_cpu))

        if self.dificultad_cpu in ["Normal", "Difícil"]:
            self.posibles_respuestas_cpu = [
                c for c in self.posibles_respuestas_cpu
                if self.evaluar_intento(c, intento_cpu) == (exactos, desplazados)
            ]

        self.historial_j2.append((intento_str, exactos, desplazados, self.intentos_j2))

        msg = (f"La CPU probó el código: {intento_str}\n\n"
               f"Resultado:\n- {exactos} Presos\n- {desplazados} Fugados")

        def al_cerrar():
            self.actualizar_vista_historial()
            if exactos == 4:
                self.declarar_victoria(self.nombre_j2)

        self.mostrar_alerta("Turno de la CPU", msg, callback_aceptar=al_cerrar, tipo="info")

    def confirmar_cambio_turno(self):
        self.turno_actual = 2 if self.turno_actual == 1 else 1
        self.mostrar_pantalla_transicion()

    def declarar_victoria(self, ganador):
        self.detener_temporizador()
        self.reproducir_efecto("victoria")

        if self.modo_juego == "INFINITO":
            self.racha_actual += 1
            if self.dificultad_infinito == "Difícil" and self.racha_actual >= 5:
                self.desbloqueado_detective = True
            elif self.dificultad_infinito == "Detective" and self.racha_actual >= 5:
                self.desbloqueado_leyenda = True

            self.mostrar_alerta("¡CASO RESUELTO!",
                f"¡Felicidades! Has resuelto el caso.\nRacha actual: {self.racha_actual}",
                callback_aceptar=self.iniciar_nivel_infinito, tipo="victoria")
            self.registrar_record(self.nombre_j1, self.racha_actual, self.dificultad_infinito)
        else:
            self.mostrar_alerta("¡VICTORIA!",
                f"¡{ganador} ha descifrado el código secreto y ha ganado la partida!",
                callback_aceptar=self.crear_menu_principal, tipo="victoria")

    def registrar_record(self, nombre, racha, dif):
        for rec in self.tabla_records:
            if rec["nombre"] == nombre and rec["dificultad"] == dif:
                if racha > rec["racha"]:
                    rec["racha"] = racha
                self.guardar_records_en_archivo()
                return
        self.tabla_records.append({"nombre": nombre, "racha": racha, "dificultad": dif})
        self.guardar_records_en_archivo()


class PresosEnFugaApp(App):
    def build(self):
        self.title = "Presos en Fuga"
        return JuegoCodigoOculto()


if __name__ == "__main__":
    PresosEnFugaApp().run()
