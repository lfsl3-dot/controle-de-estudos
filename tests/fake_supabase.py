"""Supabase de mentira (em memoria) so para testar o Controller sem internet.

Simula o essencial: login, sessao e o RLS (cada usuario so enxerga os proprios
registros). O RLS de verdade e o do arquivo database/schema.sql.
"""
import itertools
from types import SimpleNamespace

_ids = itertools.count(1)


class Resposta:
    def __init__(self, data):
        self.data = data


class AuthFalsa:
    def __init__(self, banco):
        self.banco = banco
        self.usuario_id = None

    def sign_up(self, dados):
        email = dados["email"]
        uid = f"uid-{len(self.banco.usuarios) + 1}"
        self.banco.usuarios[email] = {"senha": dados["password"], "id": uid}
        nome = dados.get("options", {}).get("data", {}).get("nome", "Estudante")
        self.banco.tabelas["perfis"].append({"id": next(_ids), "user_id": uid, "nome": nome, "criado_em": "2026-01-01"})
        return SimpleNamespace(user=SimpleNamespace(id=uid, email=email), session=None)

    def sign_in_with_password(self, dados):
        usuario = self.banco.usuarios.get(dados["email"])
        if not usuario or usuario["senha"] != dados["password"]:
            raise Exception("Invalid login credentials")
        self.usuario_id = usuario["id"]
        return SimpleNamespace(user=SimpleNamespace(id=usuario["id"], email=dados["email"]), session=object())

    def get_session(self):
        return object() if self.usuario_id else None

    def sign_out(self, opcoes=None):
        self.usuario_id = None


class ConsultaFalsa:
    def __init__(self, cliente, tabela):
        self.cliente, self.tabela = cliente, tabela
        self.acao, self.carga, self.filtros, self.coluna_ordem, self.desc, self.colunas = "select", None, [], None, False, "*"

    def select(self, colunas="*"):
        self.acao, self.colunas = "select", colunas
        return self

    def insert(self, dados):
        self.acao, self.carga = "insert", dados
        return self

    def update(self, dados):
        self.acao, self.carga = "update", dados
        return self

    def delete(self):
        self.acao = "delete"
        return self

    def eq(self, coluna, valor):
        self.filtros.append((coluna, valor))
        return self

    def order(self, coluna, desc=False):
        self.coluna_ordem, self.desc = coluna, desc
        return self

    def limit(self, n):
        return self

    def execute(self):
        banco = self.cliente.banco
        if banco.falhar_com:
            raise Exception(banco.falhar_com)
        uid = self.cliente.auth.usuario_id
        if uid is None:
            raise Exception("permission denied for table (anon)")  # RLS: anon bloqueado
        linhas = banco.tabelas[self.tabela]
        # RLS: so as linhas do proprio usuario
        visiveis = [l for l in linhas if l["user_id"] == uid]
        alvo = [l for l in visiveis if all(l.get(c) == v for c, v in self.filtros)]
        if self.acao == "insert":
            if self.carga["user_id"] != uid:
                raise Exception("new row violates row-level security policy")
            nova = {"id": next(_ids), "criado_em": "2026-11-13T10:00:00", **self.carga}
            linhas.append(nova)
            return Resposta([nova])
        if self.acao == "update":
            for l in alvo:
                l.update(self.carga)
            return Resposta(alvo)
        if self.acao == "delete":
            for l in alvo:
                linhas.remove(l)
            return Resposta(alvo)
        resultado = [dict(l) for l in alvo]
        if self.tabela == "estudos" and "materias(nome)" in self.colunas:
            for r in resultado:
                m = next((x for x in banco.tabelas["materias"] if x["id"] == r["materia_id"]), None)
                r["materias"] = {"nome": m["nome"]} if m else None
        if self.coluna_ordem:
            resultado.sort(key=lambda r: r.get(self.coluna_ordem) or "", reverse=self.desc)
        return Resposta(resultado)


class BancoFalso:
    def __init__(self):
        self.usuarios = {}
        self.tabelas = {"perfis": [], "materias": [], "estudos": []}
        self.falhar_com = None


class ClienteFalso:
    """Um cliente por sessao, todos apontando para o mesmo banco."""

    def __init__(self, banco):
        self.banco = banco
        self.auth = AuthFalsa(banco)

    def table(self, nome):
        return ConsultaFalsa(self, nome)
