"""Tela de Login / Cadastro (primeira tela do sistema)."""
import flet as ft


class LoginView:
    def __init__(self, page: ft.Page, controller, ao_entrar):
        self.page = page
        self.controller = controller
        self.ao_entrar = ao_entrar
        self.modo_cadastro = False

        self.titulo = ft.Text("Bem-vindo de volta", size=26, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900)
        self.nome = ft.TextField(label="Nome", max_length=80, visible=False, prefix_icon=ft.Icons.PERSON_OUTLINE, border_radius=12)
        self.email = ft.TextField(label="E-mail", keyboard_type=ft.KeyboardType.EMAIL, max_length=254, autofocus=True, prefix_icon=ft.Icons.MAIL_OUTLINE, border_radius=12)
        self.senha = ft.TextField(label="Senha", password=True, can_reveal_password=True, max_length=72, prefix_icon=ft.Icons.LOCK_OUTLINE, border_radius=12, on_submit=self._enviar)
        self.confirmacao = ft.TextField(label="Confirme a senha", password=True, can_reveal_password=True, max_length=72, visible=False, prefix_icon=ft.Icons.VERIFIED_USER_OUTLINE, border_radius=12, on_submit=self._enviar)
        self.mensagem = ft.Text("", color=ft.Colors.RED_700)
        self.botao = ft.Button(content="Entrar", icon=ft.Icons.LOGIN, height=46, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12), bgcolor=ft.Colors.INDIGO_600, color=ft.Colors.WHITE), on_click=self._enviar)
        self.alternar = ft.TextButton(content="Ainda não tem conta? Cadastre-se", style=ft.ButtonStyle(color=ft.Colors.INDIGO_700), on_click=self._alternar_modo)

    def build(self) -> ft.Control:
        return ft.Container(
            expand=True,
            gradient=ft.LinearGradient(begin=ft.alignment.top_left, end=ft.alignment.bottom_right, colors=[ft.Colors.INDIGO_50, ft.Colors.BLUE_50, ft.Colors.WHITE]),
            alignment=ft.alignment.center,
            padding=24,
            content=ft.Card(
                elevation=12,
                surface_tint_color=ft.Colors.TRANSPARENT,
                shape=ft.RoundedRectangleBorder(radius=20),
                content=ft.Container(
                    width=410,
                    padding=32,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=20,
                    content=ft.Column(
                        tight=True,
                        spacing=13,
                        controls=[
                            ft.Container(width=52, height=52, border_radius=16, gradient=ft.LinearGradient(begin=ft.alignment.top_left, end=ft.alignment.bottom_right, colors=[ft.Colors.INDIGO_600, ft.Colors.BLUE_500]), alignment=ft.alignment.center, content=ft.Icon(ft.Icons.MENU_BOOK, color=ft.Colors.WHITE, size=28)),
                            ft.Text("Controle de Estudos", size=14, weight=ft.FontWeight.W_600, color=ft.Colors.INDIGO_600),
                            self.titulo,
                            ft.Text("Organize matérias, estudos e seu progresso.", size=13, color=ft.Colors.GREY_600),
                            ft.Container(height=4),
                            self.nome,
                            self.email,
                            self.senha,
                            self.confirmacao,
                            self.mensagem,
                            self.botao,
                            ft.Container(alignment=ft.alignment.center, content=self.alternar),
                        ],
                    ),
                ),
            ),
        )

    # ------------------------------------------------------------------
    def _mostrar(self, texto: str, erro: bool = True) -> None:
        self.mensagem.value = texto
        self.mensagem.color = ft.Colors.RED_700 if erro else ft.Colors.GREEN_700
        self.page.update()

    def _alternar_modo(self, e=None) -> None:
        self.modo_cadastro = not self.modo_cadastro
        cadastro = self.modo_cadastro
        self.titulo.value = "Criar sua conta" if cadastro else "Bem-vindo de volta"
        self.nome.visible = cadastro
        self.confirmacao.visible = cadastro
        self.botao.content = "Criar conta" if cadastro else "Entrar"
        self.alternar.content = "Já tenho conta. Entrar" if cadastro else "Ainda não tem conta? Cadastre-se"
        self.mensagem.value = ""
        self.page.update()

    def _enviar(self, e=None) -> None:
        self.botao.disabled = True
        self.mensagem.value = ""
        self.page.update()
        try:
            if self.modo_cadastro:
                ok, msg, _ = self.controller.cadastrar(
                    self.nome.value, self.email.value, self.senha.value, self.confirmacao.value
                )
                self.senha.value = ""
                self.confirmacao.value = ""
                if ok:
                    self._alternar_modo()
                self._mostrar(msg, erro=not ok)
            else:
                ok, msg, _ = self.controller.entrar(self.email.value, self.senha.value)
                self.senha.value = ""
                if ok:
                    self.ao_entrar()
                    return
                self._mostrar(msg, erro=True)
        finally:
            self.botao.disabled = False
            self.page.update()
