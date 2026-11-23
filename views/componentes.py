"""Pecas reutilizaveis das telas (avisos e confirmacoes)."""
import flet as ft


def mostrar_aviso(page: ft.Page, mensagem: str, erro: bool = False) -> None:
    """Aviso simples (SnackBar) verde para sucesso e vermelho para erro."""
    page.show_dialog(
        ft.SnackBar(
            content=ft.Text(mensagem),
            bgcolor=ft.Colors.RED_700 if erro else ft.Colors.GREEN_700,
        )
    )


def confirmar(page: ft.Page, titulo: str, mensagem: str, ao_confirmar,
              texto_botao: str = "Excluir") -> None:
    """Janela de confirmacao antes de uma acao perigosa (ex.: excluir)."""

    def cancelar(e):
        page.pop_dialog()

    def confirmado(e):
        page.pop_dialog()
        ao_confirmar()

    page.show_dialog(
        ft.AlertDialog(
            modal=True,
            title=ft.Text(titulo),
            content=ft.Text(mensagem),
            actions=[
                ft.TextButton(content="Cancelar", on_click=cancelar),
                ft.TextButton(
                    content=texto_botao,
                    on_click=confirmado,
                    style=ft.ButtonStyle(color=ft.Colors.RED_700),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
    )
