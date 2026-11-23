"""Conexao com o Supabase.

As credenciais vem SEMPRE de variaveis de ambiente (arquivo .env no computador,
painel de variaveis na hospedagem). Nada de chave escrita no codigo.
"""
import base64
import json
import os

from dotenv import load_dotenv

load_dotenv()


class ConfiguracaoError(Exception):
    """Variaveis de ambiente ausentes ou invalidas."""


def _chave_e_privilegiada(chave: str) -> bool:
    """Detecta chaves secretas/service_role, que jamais podem ser usadas aqui."""
    if chave.startswith("sb_secret_"):
        return True
    partes = chave.split(".")
    if len(partes) == 3:  # formato antigo (JWT): olhamos o campo "role"
        try:
            carga = partes[1] + "=" * (-len(partes[1]) % 4)
            dados = json.loads(base64.urlsafe_b64decode(carga))
            return dados.get("role") == "service_role"
        except Exception:
            return False
    return False


def ler_configuracao() -> tuple[str, str]:
    url = os.environ.get("SUPABASE_URL", "").strip()
    chave = os.environ.get("SUPABASE_KEY", "").strip()

    if not url or not chave:
        raise ConfiguracaoError("Variaveis de ambiente do Supabase nao configuradas.")
    if _chave_e_privilegiada(chave):
        raise ConfiguracaoError("Use apenas a chave publica (publishable/anon).")

    # A URL deve ser a base do projeto, sem /rest/v1/
    url = url.split("/rest/v1")[0].rstrip("/")
    return url, chave


def criar_cliente():
    """Cria um cliente Supabase NOVO.

    Importante: cada sessao de usuario recebe o seu proprio cliente. Se varios
    usuarios dividissem o mesmo cliente, um poderia herdar o login do outro.
    """
    from supabase import create_client  # importado aqui para facilitar testes

    url, chave = ler_configuracao()
    return create_client(url, chave)
