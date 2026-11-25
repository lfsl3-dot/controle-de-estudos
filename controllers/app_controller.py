"""Controller: regras do sistema, controle de sessao e validacao.

Todas as acoes devolvem uma tupla (ok, mensagem, dados), para a View apenas
mostrar o resultado. Detalhes tecnicos de erros ficam no log do servidor e
NUNCA aparecem na tela do usuario (rotina 5 do guia de seguranca).
"""
import functools
import logging
import time

from controllers import validacao as v
from models.conexao import criar_cliente
from models.estudo_model import EstudoModel
from models.materia_model import MateriaModel
from models.usuario_model import UsuarioModel

logger = logging.getLogger(__name__)

MSG_LOGIN_INVALIDO = "E-mail ou senha inválidos."
MSG_ERRO_GENERICO = "Não foi possível concluir a operação agora. Tente novamente."
MSG_SESSAO_EXPIRADA = "Sua sessão expirou. Entre novamente."
MAX_FALHAS_LOGIN = 5
SEGUNDOS_BLOQUEIO = 30
MAX_CADASTROS = 5
SEGUNDOS_CADASTRO_BLOQUEIO = 60
MAX_MUTACOES = 20
SEGUNDOS_MUTACOES = 10


def requer_login(metodo):
    """Bloqueia a execucao se nao houver usuario autenticado (rotina 3)."""

    @functools.wraps(metodo)
    def interno(self, *args, **kwargs):
        if not self.sessao_ativa():
            self.usuario_atual = None
            return False, MSG_SESSAO_EXPIRADA, None
        if metodo.__name__.startswith(("criar_", "atualizar_", "excluir_")):
            agora = time.monotonic()
            if agora < self._bloqueado_mutacao_ate:
                return False, "Muitas operações. Aguarde alguns segundos e tente de novo.", None
            self._mutacoes += 1
            if self._mutacoes >= MAX_MUTACOES:
                self._bloqueado_mutacao_ate = agora + SEGUNDOS_MUTACOES
                self._mutacoes = 0
                return False, "Muitas operações. Aguarde alguns segundos e tente de novo.", None
        return metodo(self, *args, **kwargs)

    return interno


class AppController:
    def __init__(self, cliente=None):
        # um cliente por sessao de usuario (evita misturar logins)
        self.cliente = cliente or criar_cliente()
        self.usuarios = UsuarioModel(self.cliente)
        self.materias = MateriaModel(self.cliente)
        self.estudos = EstudoModel(self.cliente)
        self.usuario_atual: dict | None = None
        self._falhas_login = 0
        self._bloqueado_ate = 0.0
        self._cadastros = 0
        self._bloqueado_cadastro_ate = 0.0
        self._mutacoes = 0
        self._bloqueado_mutacao_ate = 0.0

    # ------------------------------------------------------------------
    # Sessao
    # ------------------------------------------------------------------
    def sessao_ativa(self) -> bool:
        if self.usuario_atual is None:
            return False
        try:
            return self.usuarios.sessao_ativa()
        except Exception:
            logger.exception("Falha ao verificar a sessao")
            return False

    def _registrar_falha(self) -> None:
        self._falhas_login += 1
        if self._falhas_login >= MAX_FALHAS_LOGIN:
            self._bloqueado_ate = time.monotonic() + SEGUNDOS_BLOQUEIO
            self._falhas_login = 0

    def entrar(self, email, senha):
        if time.monotonic() < self._bloqueado_ate:
            return False, "Muitas tentativas. Aguarde alguns segundos e tente de novo.", None
        if not v.limpar(email) or not senha:
            return False, "Preencha o e-mail e a senha.", None
        # formato de e-mail invalido tambem recebe a mensagem generica
        if v.validar_email(email) is not None or len(senha) > 72:
            self._registrar_falha()
            return False, MSG_LOGIN_INVALIDO, None
        try:
            resposta = self.usuarios.entrar(v.limpar(email).lower(), senha)
            usuario = resposta.user
            if usuario is None or resposta.session is None:
                raise ValueError("login sem sessao")
        except Exception:
            self._registrar_falha()
            return False, MSG_LOGIN_INVALIDO, None  # sempre a mesma frase

        self._falhas_login = 0
        self.usuario_atual = {"id": str(usuario.id), "email": usuario.email, "nome": ""}
        try:
            perfil = self.usuarios.buscar_perfil(self.usuario_atual["id"])
            self.usuario_atual["nome"] = (perfil or {}).get("nome", "")
        except Exception:
            logger.exception("Falha ao carregar o perfil")
        return True, "Login realizado com sucesso.", self.usuario_atual

    def cadastrar(self, nome, email, senha, confirmacao):
        if time.monotonic() < self._bloqueado_cadastro_ate:
            return False, "Muitos cadastros. Aguarde alguns segundos e tente de novo.", None
        nome_limpo, erro = v.validar_texto(nome, "nome", 2, 80)
        if erro:
            return False, erro, None
        erro = v.validar_email(email)
        if erro:
            return False, erro, None
        erro = v.validar_senha_cadastro(senha)
        if erro:
            return False, erro, None
        if senha != confirmacao:
            return False, "A confirmação da senha não confere.", None
        try:
            self.usuarios.cadastrar(nome_limpo, v.limpar(email).lower(), senha)
        except Exception:
            logger.exception("Falha no cadastro")
            self._cadastros += 1
            if self._cadastros >= MAX_CADASTROS:
                self._bloqueado_cadastro_ate = time.monotonic() + SEGUNDOS_CADASTRO_BLOQUEIO
                self._cadastros = 0
            return False, "Não foi possível concluir o cadastro. Revise os dados e tente de novo.", None
        self._cadastros = 0
        return True, "Cadastro realizado! Se pedirem, confirme seu e-mail. Depois, entre no sistema.", None

    def sair(self) -> None:
        """Logout: encerra a sessao no Supabase e apaga os dados da memoria."""
        try:
            self.usuarios.sair()
        except Exception:
            logger.exception("Falha ao encerrar a sessao")
        self.usuario_atual = None

    # ------------------------------------------------------------------
    # Perfil
    # ------------------------------------------------------------------
    @requer_login
    def atualizar_perfil(self, nome):
        nome_limpo, erro = v.validar_texto(nome, "nome", 2, 80)
        if erro:
            return False, erro, None
        try:
            self.usuarios.atualizar_nome(self.usuario_atual["id"], nome_limpo)
            self.usuario_atual["nome"] = nome_limpo
        except Exception:
            logger.exception("Falha ao atualizar o perfil")
            return False, MSG_ERRO_GENERICO, None
        return True, "Perfil atualizado!", nome_limpo

    # ------------------------------------------------------------------
    # Materias (tabela auxiliar)
    # ------------------------------------------------------------------
    @requer_login
    def listar_materias(self):
        try:
            return True, "", self.materias.listar(self.usuario_atual["id"])
        except Exception:
            logger.exception("Falha ao listar materias")
            return False, MSG_ERRO_GENERICO, None

    def _validar_materia(self, nome, descricao):
        nome_limpo, erro = v.validar_texto(nome, "nome", 2, 60)
        if erro:
            return None, None, erro
        desc_limpa, erro = v.validar_texto(descricao, "descrição", 0, 200, obrigatorio=False)
        if erro:
            return None, None, erro
        return nome_limpo, desc_limpa, None

    @requer_login
    def criar_materia(self, nome, descricao):
        nome_limpo, desc_limpa, erro = self._validar_materia(nome, descricao)
        if erro:
            return False, erro, None
        try:
            self.materias.criar(self.usuario_atual["id"], nome_limpo, desc_limpa)
        except Exception:
            logger.exception("Falha ao criar materia")
            return False, MSG_ERRO_GENERICO, None
        return True, "Matéria cadastrada!", None

    @requer_login
    def atualizar_materia(self, materia_id, nome, descricao):
        mid, erro = v.validar_id(materia_id, "matéria")
        if erro:
            return False, erro, None
        nome_limpo, desc_limpa, erro = self._validar_materia(nome, descricao)
        if erro:
            return False, erro, None
        try:
            self.materias.atualizar(self.usuario_atual["id"], mid, nome_limpo, desc_limpa)
        except Exception:
            logger.exception("Falha ao atualizar materia")
            return False, MSG_ERRO_GENERICO, None
        return True, "Matéria atualizada!", None

    @requer_login
    def excluir_materia(self, materia_id):
        mid, erro = v.validar_id(materia_id, "matéria")
        if erro:
            return False, erro, None
        try:
            self.materias.excluir(self.usuario_atual["id"], mid)
        except Exception:
            logger.exception("Falha ao excluir materia")
            return False, MSG_ERRO_GENERICO, None
        return True, "Matéria excluída.", None

    # ------------------------------------------------------------------
    # Estudos (tabela principal)
    # ------------------------------------------------------------------
    @requer_login
    def listar_estudos(self):
        try:
            estudos = self.estudos.listar(self.usuario_atual["id"])
        except Exception:
            logger.exception("Falha ao listar estudos")
            return False, MSG_ERRO_GENERICO, None
        for estudo in estudos:
            estudo["materia_nome"] = (estudo.get("materias") or {}).get("nome", "-")
        return True, "", estudos

    def _validar_estudo(self, titulo, materia_id, status, duracao):
        titulo_limpo, erro = v.validar_texto(titulo, "título", 3, 80)
        if erro:
            return None, erro
        mid, erro = v.validar_id(materia_id, "matéria")
        if erro:
            return None, erro
        erro = v.validar_status(status)
        if erro:
            return None, erro
        minutos, erro = v.validar_inteiro(duracao, "duração", 1, 600)
        if erro:
            return None, erro
        return (titulo_limpo, mid, status, minutos), None

    @requer_login
    def criar_estudo(self, titulo, materia_id, status, duracao):
        dados, erro = self._validar_estudo(titulo, materia_id, status, duracao)
        if erro:
            return False, erro, None
        titulo_limpo, mid, status, minutos = dados
        try:
            self.estudos.criar(self.usuario_atual["id"], mid, titulo_limpo, status, minutos)
        except Exception:
            logger.exception("Falha ao criar estudo")
            return False, MSG_ERRO_GENERICO, None
        return True, "Estudo cadastrado!", None

    @requer_login
    def atualizar_estudo(self, estudo_id, titulo, materia_id, status, duracao):
        eid, erro = v.validar_id(estudo_id, "estudo")
        if erro:
            return False, erro, None
        dados, erro = self._validar_estudo(titulo, materia_id, status, duracao)
        if erro:
            return False, erro, None
        titulo_limpo, mid, status, minutos = dados
        try:
            self.estudos.atualizar(self.usuario_atual["id"], eid, mid, titulo_limpo, status, minutos)
        except Exception:
            logger.exception("Falha ao atualizar estudo")
            return False, MSG_ERRO_GENERICO, None
        return True, "Estudo atualizado!", None

    @requer_login
    def excluir_estudo(self, estudo_id):
        eid, erro = v.validar_id(estudo_id, "estudo")
        if erro:
            return False, erro, None
        try:
            self.estudos.excluir(self.usuario_atual["id"], eid)
        except Exception:
            logger.exception("Falha ao excluir estudo")
            return False, MSG_ERRO_GENERICO, None
        return True, "Estudo excluído.", None

    @staticmethod
    def resumo(estudos: list[dict]) -> dict:
        """Contagem por status e total de minutos (usado no painel inicial)."""
        resultado = {"pendente": 0, "em_andamento": 0, "concluido": 0, "minutos": 0}
        for estudo in estudos:
            if estudo.get("status") in resultado:
                resultado[estudo["status"]] += 1
            resultado["minutos"] += int(estudo.get("duracao_min") or 0)
        return resultado
