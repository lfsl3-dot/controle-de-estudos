"""Controle de Estudos - Flet + MVC + Supabase.

Ponto de entrada: monta a tela de login e a tela principal.
Cada sessao de navegador recebe o seu proprio Controller (e cliente Supabase).
"""
import logging
import os
import socket

import flet as ft

from controllers.app_controller import AppController
from views.componentes import mostrar_aviso
from views.login_view import LoginView
from views.principal_view import PrincipalView

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__) 


def _porta_disponivel(porta: int) -> bool:
    """Retorna True se a porta estiver livre para uso."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.bind(("0.0.0.0", porta))
            return True
        except OSError:
            return False


def _resolver_porta() -> int:
    """Usa PORT da hospedagem; se estiver ocupada, tenta uma porta livre."""
    porta = int(os.environ.get("PORT", 8080))
    if porta and _porta_disponivel(porta):
        return porta

    for tentativa in range(porta + 1, porta + 21):
        if _porta_disponivel(tentativa):
            logger.warning("Porta %s ocupada; usando %s em vez disso.", porta, tentativa)
            return tentativa

    if _porta_disponivel(8000):
        logger.warning("Nenhuma porta da faixa solicitada está livre; usando 8000.")
        return 8000

    raise RuntimeError("Não foi possível encontrar uma porta livre para iniciar o Flet.")


def main(page: ft.Page):
    page.title = "Controle de Estudos"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.bgcolor = ft.Colors.SURFACE
    page.fonts = {"Inter": "https://fonts.gstatic.com/s/inter/v18/UcCO3FwrK3iLTcviYwY.woff2"}
    page.theme = ft.Theme(font_family="Inter", color_scheme_seed=ft.Colors.INDIGO)

    try:
        controller = AppController()
    except Exception:
        logger.exception("Falha ao iniciar o sistema (confira as variaveis de ambiente)")
        page.add(
            ft.Container(
                expand=True,
                alignment=ft.alignment.center,
                bgcolor=ft.Colors.SURFACE,
                content=ft.Text("Sistema indisponível no momento. Tente novamente mais tarde."),
            )
        )
        return

    def mostrar_login(aviso: str | None = None) -> None:
        page.appbar = None
        page.controls.clear()
        page.add(LoginView(page, controller, ao_entrar=mostrar_principal).build())
        page.update()
        if aviso:
            mostrar_aviso(page, aviso, erro=True)

    def sair(e=None) -> None:
        controller.sair()
        mostrar_login()

    def mostrar_principal() -> None:
        if controller.usuario_atual is None:
            mostrar_login()
            return

        nome = controller.usuario_atual.get("nome") or controller.usuario_atual["email"]
        page.appbar = ft.AppBar(
            bgcolor=ft.Colors.WHITE,
            surface_tint_color=ft.Colors.TRANSPARENT,
            title=ft.Row(
                tight=True,
                controls=[
                    ft.Container(
                        width=38,
                        height=38,
                        border_radius=12,
                        gradient=ft.LinearGradient(
                            begin=ft.alignment.top_left,
                            end=ft.alignment.bottom_right,
                            colors=[ft.Colors.INDIGO_600, ft.Colors.BLUE_500],
                        ),
                        alignment=ft.alignment.center,
                        content=ft.Icon(ft.Icons.MENU_BOOK, color=ft.Colors.WHITE, size=20),
                    ),
                    ft.Text("Controle de Estudos", weight=ft.FontWeight.BOLD, size=18),
                ],
            ),
            center_title=False,
            actions=[
                ft.Container(
                    border=ft.border.all(1, ft.Colors.INDIGO_100),
                    border_radius=20,
                    bgcolor=ft.Colors.INDIGO_50,
                    padding=ft.padding.symmetric(horizontal=12, vertical=8),
                    content=ft.Row(
                        tight=True,
                        spacing=6,
                        controls=[
                            ft.Icon(ft.Icons.PERSON_OUTLINE, size=16, color=ft.Colors.INDIGO_700),
                            ft.Text(nome, size=13, weight=ft.FontWeight.W_600, color=ft.Colors.INDIGO_900),
                        ],
                    ),
                ),
                ft.IconButton(icon=ft.Icons.LOGOUT_ROUNDED, tooltip="Sair", on_click=sair),
                ft.Container(width=8),
            ],
        )
        page.controls.clear()
        page.add(PrincipalView(page, controller, ao_sessao_perdida=mostrar_login).build())
        page.update()

    mostrar_login()


if __name__ == "__main__":
    porta = _resolver_porta()
    logger.info("Iniciando Flet na porta %s", porta)
    ft.run(main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=porta)
