"""Tela principal (so abre com usuario autenticado): estudos, materias e perfil."""
import flet as ft

from controllers.validacao import ROTULOS_STATUS
from views.componentes import confirmar, mostrar_aviso

COR_STATUS = {
    "pendente": ft.Colors.ORANGE_700,
    "em_andamento": ft.Colors.BLUE_700,
    "concluido": ft.Colors.GREEN_700,
}


def _data_br(texto: str | None) -> str:
    """Converte 2026-11-13T10:00:00+00:00 em 13/11/2026."""
    try:
        ano, mes, dia = (texto or "")[:10].split("-")
        return f"{dia}/{mes}/{ano}"
    except ValueError:
        return ""


class PrincipalView:
    def __init__(self, page: ft.Page, controller, ao_sessao_perdida, ao_sair=None):
        self.page = page
        self.controller = controller
        self.ao_sessao_perdida = ao_sessao_perdida
        self.ao_sair = ao_sair
        self.secao = "estudos"
        self.menu = ft.Row(spacing=8, wrap=True)
        self.area = ft.Column(expand=True, scroll=ft.ScrollMode.AUTO, spacing=14)
        self.raiz = ft.Column(
            expand=True,
            spacing=12,
            controls=[self.menu, ft.Container(height=1, bgcolor=ft.Colors.INDIGO_50), self.area],
        )

    def build(self) -> ft.Control:
        self._atualizar(atualizar_pagina=False)
        return ft.Container(
            expand=True,
            bgcolor=ft.Colors.SURFACE,
            padding=ft.Padding.symmetric(horizontal=24, vertical=18),
            alignment=ft.Alignment.TOP_CENTER,
            content=ft.Container(expand=True, width=1100, content=self.raiz),
        )

    # ------------------------------------------------------------------
    # Navegacao e utilitarios
    # ------------------------------------------------------------------
    def _atualizar(self, atualizar_pagina: bool = True) -> None:
        self._montar_menu()
        self.area.controls.clear()
        if self.secao == "estudos":
            self._montar_estudos()
        elif self.secao == "materias":
            self._montar_materias()
        else:
            self._montar_perfil()
        if atualizar_pagina:
            self.page.update()

    def _ir_para(self, secao: str) -> None:
        self.secao = secao
        self._atualizar()

    def _montar_menu(self) -> None:
        self.menu.controls.clear()
        opcoes = [
            ("estudos", "Estudos", ft.Icons.MENU_BOOK_OUTLINED),
            ("materias", "Matérias", ft.Icons.FOLDER_OUTLINED),
            ("perfil", "Meu perfil", ft.Icons.PERSON_OUTLINED),
        ]
        for chave, rotulo, icone in opcoes:
            ativa = chave == self.secao
            self.menu.controls.append(
                ft.Container(
                    border_radius=12,
                    bgcolor=ft.Colors.INDIGO_600 if ativa else ft.Colors.WHITE,
                    border=ft.Border.all(1, ft.Colors.INDIGO_200 if ativa else ft.Colors.GREY_300),
                    padding=ft.Padding.symmetric(horizontal=14, vertical=8),
                    ink=True,
                    on_click=lambda e, c=chave: self._ir_para(c),
                    content=ft.Row(
                        tight=True,
                        spacing=7,
                        controls=[
                            ft.Icon(icone, size=18, color=ft.Colors.WHITE if ativa else ft.Colors.INDIGO_700),
                            ft.Text(rotulo, weight=ft.FontWeight.W_600, size=13, color=ft.Colors.WHITE if ativa else ft.Colors.INDIGO_900),
                        ],
                    ),
                )
            )

    def _falha(self, mensagem: str) -> None:
        """Mostra o erro; se a sessao acabou, volta para o login."""
        if self.controller.usuario_atual is None:
            self.ao_sessao_perdida(mensagem)
        else:
            mostrar_aviso(self.page, mensagem, erro=True)

    # ------------------------------------------------------------------
    # Secao: ESTUDOS
    # ------------------------------------------------------------------
    def _montar_estudos(self) -> None:
        ok, msg, estudos = self.controller.listar_estudos()
        if not ok:
            self._falha(msg)
            return
        ok, msg, materias = self.controller.listar_materias()
        if not ok:
            self._falha(msg)
            return

        resumo = self.controller.resumo(estudos)
        self.area.controls.append(
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Column(tight=True, spacing=2, controls=[ft.Text("Meus estudos", size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900), ft.Text("Acompanhe sua rotina de estudos", size=13, color=ft.Colors.GREY_600)]),
                    ft.Button(content="Novo estudo", icon=ft.Icons.ADD_ROUNDED, height=42, disabled=not materias, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=12), bgcolor=ft.Colors.INDIGO_600, color=ft.Colors.WHITE), on_click=lambda e: self._abrir_form_estudo(materias)),
                ],
            )
        )
        if not materias:
            self.area.controls.append(ft.Container(padding=12, border_radius=12, bgcolor=ft.Colors.ORANGE_50, border=ft.Border.all(1, ft.Colors.ORANGE_100), content=ft.Row(spacing=8, controls=[ft.Icon(ft.Icons.INFO_OUTLINE, color=ft.Colors.ORANGE_800, size=18), ft.Text("Cadastre uma matéria na aba “Matérias” antes de criar seus estudos.", color=ft.Colors.ORANGE_900, size=13)])))
        self.area.controls.append(
            ft.Row(wrap=True, spacing=10, controls=[
                self._bloco_resumo(resumo["pendente"], "Pendentes", ft.Colors.ORANGE),
                self._bloco_resumo(resumo["em_andamento"], "Em andamento", ft.Colors.BLUE),
                self._bloco_resumo(resumo["concluido"], "Concluídos", ft.Colors.GREEN),
                self._bloco_resumo(resumo["minutos"], "Minutos planejados", ft.Colors.INDIGO),
            ])
        )
        if not estudos:
            self.area.controls.append(ft.Container(padding=20, border_radius=14, bgcolor=ft.Colors.WHITE, border=ft.Border.all(1, ft.Colors.GREY_200), alignment=ft.Alignment.CENTER, content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, tight=True, controls=[ft.Icon(ft.Icons.MENU_BOOK_OUTLINED, size=38, color=ft.Colors.INDIGO_300), ft.Text("Nenhum estudo cadastrado ainda", weight=ft.FontWeight.W_600, color=ft.Colors.GREY_700)])))
        for estudo in estudos:
            self.area.controls.append(self._cartao_estudo(estudo, materias))

    @staticmethod
    def _bloco_resumo(valor, rotulo: str, cor) -> ft.Control:
        return ft.Container(
            width=210,
            padding=14,
            border_radius=14,
            bgcolor=ft.Colors.WHITE,
            border=ft.Border.all(1, ft.Colors.GREY_200),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Column(tight=True, spacing=2, controls=[ft.Text(str(valor), size=24, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_900), ft.Text(rotulo, size=12, color=ft.Colors.GREY_600)]),
                    ft.Container(width=38, height=38, border_radius=12, bgcolor=cor if False else ft.Colors.INDIGO_50, alignment=ft.Alignment.CENTER, content=ft.Icon(ft.Icons.TRENDING_UP_ROUNDED, color=ft.Colors.INDIGO_600, size=20)),
                ],
            ),
        )

    def _cartao_estudo(self, estudo: dict, materias: list[dict]) -> ft.Control:
        status = estudo.get("status", "")
        return ft.Card(
            content=ft.Container(
                padding=12,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Column(
                            expand=True,
                            spacing=2,
                            controls=[
                                ft.Text(estudo["titulo"], size=16, weight=ft.FontWeight.BOLD),
                                ft.Text(
                                    f'{estudo["materia_nome"]} • {estudo["duracao_min"]} min'
                                    f' • {_data_br(estudo.get("criado_em"))}',
                                    color=ft.Colors.GREY_700,
                                ),
                                ft.Text(
                                    ROTULOS_STATUS.get(status, status),
                                    size=12,
                                    weight=ft.FontWeight.BOLD,
                                    color=COR_STATUS.get(status, ft.Colors.GREY_700),
                                ),
                            ],
                        ),
                        ft.Row(
                            spacing=0,
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.EDIT,
                                    tooltip="Editar",
                                    on_click=lambda e, est=estudo: self._abrir_form_estudo(materias, est),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DELETE,
                                    icon_color=ft.Colors.RED_700,
                                    tooltip="Excluir",
                                    on_click=lambda e, est=estudo: self._pedir_exclusao_estudo(est),
                                ),
                            ],
                        ),
                    ],
                ),
            )
        )

    def _abrir_form_estudo(self, materias: list[dict], estudo: dict | None = None) -> None:
        editando = estudo is not None
        titulo = ft.TextField(
            label="Título", value=estudo["titulo"] if editando else "", max_length=80, autofocus=True
        )
        materia = ft.Dropdown(
            label="Matéria",
            width=340,
            value=str(estudo["materia_id"]) if editando else None,
            options=[ft.DropdownOption(key=str(m["id"]), text=m["nome"]) for m in materias],
        )
        status = ft.Dropdown(
            label="Status",
            width=340,
            value=estudo["status"] if editando else "pendente",
            options=[ft.DropdownOption(key=k, text=t) for k, t in ROTULOS_STATUS.items()],
        )
        duracao = ft.TextField(
            label="Duração (minutos)",
            value=str(estudo["duracao_min"]) if editando else "30",
            keyboard_type=ft.KeyboardType.NUMBER,
            max_length=3,
        )
        erro = ft.Text("", color=ft.Colors.RED_700)

        def salvar(e):
            if editando:
                ok, msg, _ = self.controller.atualizar_estudo(
                    estudo["id"], titulo.value, materia.value, status.value, duracao.value
                )
            else:
                ok, msg, _ = self.controller.criar_estudo(
                    titulo.value, materia.value, status.value, duracao.value
                )
            if ok:
                self.page.pop_dialog()
                self._atualizar()
                mostrar_aviso(self.page, msg)
            elif self.controller.usuario_atual is None:
                self.page.pop_dialog()
                self.ao_sessao_perdida(msg)
            else:
                erro.value = msg  # aviso simples dentro do formulario
                self.page.update()

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Editar estudo" if editando else "Novo estudo"),
                content=ft.Column(
                    tight=True, width=380, spacing=12,
                    controls=[titulo, materia, status, duracao, erro],
                ),
                actions=[
                    ft.TextButton(content="Cancelar", on_click=lambda e: self.page.pop_dialog()),
                    ft.Button(content="Salvar", icon=ft.Icons.SAVE, on_click=salvar),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    def _pedir_exclusao_estudo(self, estudo: dict) -> None:
        confirmar(
            self.page,
            "Excluir estudo",
            f'Deseja realmente excluir "{estudo["titulo"]}"? Essa ação não pode ser desfeita.',
            lambda: self._excluir_estudo(estudo["id"]),
        )

    def _excluir_estudo(self, estudo_id: int) -> None:
        ok, msg, _ = self.controller.excluir_estudo(estudo_id)
        if ok:
            self._atualizar()
            mostrar_aviso(self.page, msg)
        else:
            self._falha(msg)

    # ------------------------------------------------------------------
    # Secao: MATERIAS
    # ------------------------------------------------------------------
    def _montar_materias(self) -> None:
        ok, msg, materias = self.controller.listar_materias()
        if not ok:
            self._falha(msg)
            return
        self.area.controls.append(
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text("Minhas matérias", size=22, weight=ft.FontWeight.BOLD),
                    ft.Button(
                        content="Nova matéria",
                        icon=ft.Icons.ADD,
                        on_click=lambda e: self._abrir_form_materia(),
                    ),
                ],
            )
        )
        if not materias:
            self.area.controls.append(ft.Text("Nenhuma matéria cadastrada ainda."))
        for materia in materias:
            self.area.controls.append(
                ft.Card(
                    content=ft.Container(
                        padding=12,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            vertical_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Column(
                                    expand=True,
                                    spacing=2,
                                    controls=[
                                        ft.Text(materia["nome"], size=16, weight=ft.FontWeight.BOLD),
                                        ft.Text(
                                            materia.get("descricao") or "Sem descrição",
                                            color=ft.Colors.GREY_700,
                                        ),
                                    ],
                                ),
                                ft.Row(
                                    spacing=0,
                                    controls=[
                                        ft.IconButton(
                                            icon=ft.Icons.EDIT,
                                            tooltip="Editar",
                                            on_click=lambda e, m=materia: self._abrir_form_materia(m),
                                        ),
                                        ft.IconButton(
                                            icon=ft.Icons.DELETE,
                                            icon_color=ft.Colors.RED_700,
                                            tooltip="Excluir",
                                            on_click=lambda e, m=materia: self._pedir_exclusao_materia(m),
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    )
                )
            )

    def _abrir_form_materia(self, materia: dict | None = None) -> None:
        editando = materia is not None
        nome = ft.TextField(
            label="Nome da matéria", value=materia["nome"] if editando else "",
            max_length=60, autofocus=True,
        )
        descricao = ft.TextField(
            label="Descrição (opcional)",
            value=(materia.get("descricao") or "") if editando else "",
            max_length=200,
        )
        erro = ft.Text("", color=ft.Colors.RED_700)

        def salvar(e):
            if editando:
                ok, msg, _ = self.controller.atualizar_materia(materia["id"], nome.value, descricao.value)
            else:
                ok, msg, _ = self.controller.criar_materia(nome.value, descricao.value)
            if ok:
                self.page.pop_dialog()
                self._atualizar()
                mostrar_aviso(self.page, msg)
            elif self.controller.usuario_atual is None:
                self.page.pop_dialog()
                self.ao_sessao_perdida(msg)
            else:
                erro.value = msg
                self.page.update()

        self.page.show_dialog(
            ft.AlertDialog(
                modal=True,
                title=ft.Text("Editar matéria" if editando else "Nova matéria"),
                content=ft.Column(
                    tight=True, width=380, spacing=12, controls=[nome, descricao, erro]
                ),
                actions=[
                    ft.TextButton(content="Cancelar", on_click=lambda e: self.page.pop_dialog()),
                    ft.Button(content="Salvar", icon=ft.Icons.SAVE, on_click=salvar),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
        )

    def _pedir_exclusao_materia(self, materia: dict) -> None:
        confirmar(
            self.page,
            "Excluir matéria",
            f'Excluir "{materia["nome"]}"? Todos os estudos dessa matéria também serão apagados.',
            lambda: self._excluir_materia(materia["id"]),
        )

    def _excluir_materia(self, materia_id: int) -> None:
        ok, msg, _ = self.controller.excluir_materia(materia_id)
        if ok:
            self._atualizar()
            mostrar_aviso(self.page, msg)
        else:
            self._falha(msg)

    # ------------------------------------------------------------------
    # Secao: PERFIL
    # ------------------------------------------------------------------
    def _montar_perfil(self) -> None:
        usuario = self.controller.usuario_atual or {}
        nome = ft.TextField(label="Nome", value=usuario.get("nome", ""), max_length=80, width=340)
        erro = ft.Text("", color=ft.Colors.RED_700)

        def salvar(e):
            ok, msg, _ = self.controller.atualizar_perfil(nome.value)
            if ok:
                erro.value = ""
                self.page.update()
                mostrar_aviso(self.page, msg)
            elif self.controller.usuario_atual is None:
                self.ao_sessao_perdida(msg)
            else:
                erro.value = msg
                self.page.update()

        self.area.controls.extend(
            [
                ft.Text("Meu perfil", size=22, weight=ft.FontWeight.BOLD),
                ft.Text(f'E-mail: {usuario.get("email", "")}', color=ft.Colors.GREY_700),
                nome,
                erro,
                ft.Button(content="Salvar nome", icon=ft.Icons.SAVE, on_click=salvar),
            ]
        )
