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
    page.padding = 20

    # Falha de configuracao: avisa de forma simples (detalhes so no log do servidor)
    try:
        controller = AppController()
    except Exception:
        logger.exception("Falha ao iniciar o sistema (confira as variaveis de ambiente)")
        page.add(ft.Text("Sistema indisponível no momento. Tente novamente mais tarde."))
        return

    def mostrar_login(aviso: str | None = None) -> None:
        page.appbar = None
        page.controls.clear()
        page.add(LoginView(page, controller, ao_entrar=mostrar_principal).build())
        page.update()
        if aviso:
            mostrar_aviso(page, aviso, erro=True)

    def sair(e=None) -> None:
        controller.sair()  # sign_out no Supabase + apaga o usuario da memoria
        mostrar_login()

    def mostrar_principal() -> None:
        # Bloqueio de tela interna sem login (rotina 3)
        if controller.usuario_atual is None:
            mostrar_login()
            return
        page.appbar = ft.AppBar(
            title=ft.Text("Controle de Estudos"),
            center_title=False,
            actions=[
                ft.Text(controller.usuario_atual.get("nome") or controller.usuario_atual["email"]),
                ft.IconButton(icon=ft.Icons.LOGOUT, tooltip="Sair", on_click=sair),
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
