"""Pecas reutilizaveis das telas (avisos e confirmacoes)."""
import flet as ft


def mostrar_aviso(page: ft.Page, mensagem: str, erro: bool = False) -> None:
    """Aviso simples e moderno com cor de sucesso ou erro."""
    page.show_dialog(
        ft.SnackBar(
            content=ft.Row(
                tight=True,
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.ERROR_OUTLINE if erro else ft.Icons.CHECK_CIRCLE_OUTLINE, color=ft.Colors.WHITE),
                    ft.Text(mensagem, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
                ],
            ),
            bgcolor=ft.Colors.RED_700 if erro else ft.Colors.GREEN_700,
            behavior=ft.SnackBarBehavior.FLOATING,
            shape=ft.RoundedRectangleBorder(radius=12),
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
