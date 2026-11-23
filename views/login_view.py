"""Tela de Login / Cadastro (primeira tela do sistema)."""
import flet as ft


class LoginView:
    def __init__(self, page: ft.Page, controller, ao_entrar):
        self.page = page
        self.controller = controller
        self.ao_entrar = ao_entrar
        self.modo_cadastro = False

        self.titulo = ft.Text("Entrar", size=24, weight=ft.FontWeight.BOLD)
        self.nome = ft.TextField(label="Nome", max_length=80, visible=False)
        self.email = ft.TextField(
            label="E-mail", keyboard_type=ft.KeyboardType.EMAIL, max_length=254, autofocus=True
        )
        self.senha = ft.TextField(
            label="Senha", password=True, can_reveal_password=True, max_length=72,
            on_submit=self._enviar,
        )
        self.confirmacao = ft.TextField(
            label="Confirme a senha", password=True, can_reveal_password=True,
            max_length=72, visible=False, on_submit=self._enviar,
        )
        self.mensagem = ft.Text("", color=ft.Colors.RED_700)
        self.botao = ft.Button(content="Entrar", icon=ft.Icons.LOGIN, on_click=self._enviar)
        self.alternar = ft.TextButton(
            content="Ainda não tem conta? Cadastre-se", on_click=self._alternar_modo
        )

    def build(self) -> ft.Control:
        return ft.Column(
            expand=True,
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Card(
                    content=ft.Container(
                        width=380,
                        padding=24,
                        content=ft.Column(
                            tight=True,
                            spacing=12,
                            controls=[
                                ft.Text("Controle de Estudos", size=14, color=ft.Colors.GREY_700),
                                self.titulo,
                                self.nome,
                                self.email,
                                self.senha,
                                self.confirmacao,
                                self.mensagem,
                                self.botao,
                                self.alternar,
                            ],
                        ),
                    )
                )
            ],
        )

    # ------------------------------------------------------------------
    def _mostrar(self, texto: str, erro: bool = True) -> None:
        self.mensagem.value = texto
        self.mensagem.color = ft.Colors.RED_700 if erro else ft.Colors.GREEN_700
        self.page.update()

    def _alternar_modo(self, e=None) -> None:
        self.modo_cadastro = not self.modo_cadastro
        cadastro = self.modo_cadastro
        self.titulo.value = "Criar conta" if cadastro else "Entrar"
        self.nome.visible = cadastro
        self.confirmacao.visible = cadastro
        self.botao.content = "Cadastrar" if cadastro else "Entrar"
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
