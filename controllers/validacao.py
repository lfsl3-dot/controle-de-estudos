# -*- coding: utf-8 -*-

"""Validacao das entradas do usuario (rotina 4 do guia de seguranca).

Funcoes simples e sem dependencia de Flet/Supabase: recebem o texto digitado e
devolvem o valor limpo ou uma mensagem de erro amigavel.
"""
import re

STATUS_VALIDOS = ("pendente", "em_andamento", "concluido")
ROTULOS_STATUS = {
    "pendente": "Pendente",
    "em_andamento": "Em andamento",
    "concluido": "Concluído",
}

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def limpar(texto) -> str:
    """Remove espacos nas pontas e garante que o valor seja texto."""
    return str(texto).strip() if texto is not None else ""


def _tem_caractere_de_controle(texto: str) -> bool:
    return any(ord(c) < 32 or ord(c) == 127 for c in texto)


def validar_email(email) -> str | None:
    """Retorna None se valido, ou a mensagem de erro."""
    valor = limpar(email)
    if not valor:
        return "Informe o e-mail."
    if len(valor) > 254 or _tem_caractere_de_controle(valor) or not _EMAIL_RE.match(valor):
        return "Informe um e-mail válido."
    return None


def validar_senha_cadastro(senha) -> str | None:
    if senha is None or not (8 <= len(senha) <= 72):
        return "A senha deve ter entre 8 e 72 caracteres."
    if not any(c.isalpha() for c in senha) or not any(c.isdigit() for c in senha):
        return "A senha deve conter letras e números."
    return None


def validar_texto(valor, rotulo: str, minimo: int, maximo: int,
                  obrigatorio: bool = True) -> tuple[str, str | None]:
    """Valida um texto de uma linha. Retorna (texto_limpo, erro)."""
    texto = limpar(valor)
    if not texto:
        if obrigatorio:
            return "", f"Preencha o campo {rotulo}."
        return "", None
    if _tem_caractere_de_controle(texto):
        return texto, f"O campo {rotulo} contém caracteres inválidos."
    if len(texto) < minimo or len(texto) > maximo:
        return texto, f"O campo {rotulo} deve ter entre {minimo} e {maximo} caracteres."
    return texto, None


def validar_inteiro(valor, rotulo: str, minimo: int, maximo: int) -> tuple[int | None, str | None]:
    """Converte para inteiro com try/except. Retorna (numero, erro)."""
    try:
        numero = int(limpar(valor))
    except (ValueError, TypeError):
        return None, f"O campo {rotulo} precisa ser um número inteiro."
    if numero < minimo or numero > maximo:
        return None, f"O campo {rotulo} deve estar entre {minimo} e {maximo}."
    return numero, None


def validar_status(status) -> str | None:
    return None if status in STATUS_VALIDOS else "Escolha um status válido."


def validar_id(valor, rotulo: str = "registro") -> tuple[int | None, str | None]:
    try:
        numero = int(valor)
    except (ValueError, TypeError):
        return None, f"Selecione um {rotulo} válido."
    if numero <= 0:
        return None, f"Selecione um {rotulo} válido."
    return numero, None
