"""Model de autenticacao e perfil (Supabase Auth + tabela perfis)."""


class UsuarioModel:
    def __init__(self, cliente):
        self.cliente = cliente

    # ---- Supabase Auth (nenhuma senha e guardada por nos) ----
    def cadastrar(self, nome: str, email: str, senha: str):
        return self.cliente.auth.sign_up(
            {"email": email, "password": senha, "options": {"data": {"nome": nome}}}
        )

    def entrar(self, email: str, senha: str):
        return self.cliente.auth.sign_in_with_password({"email": email, "password": senha})

    def sair(self) -> None:
        # scope local: encerra apenas esta sessao, nao as de outros dispositivos
        try:
            self.cliente.auth.sign_out({"scope": "local"})
        except TypeError:
            self.cliente.auth.sign_out()

    def sessao_ativa(self) -> bool:
        return self.cliente.auth.get_session() is not None

    # ---- Tabela perfis ----
    def buscar_perfil(self, user_id: str) -> dict | None:
        resp = (
            self.cliente.table("perfis")
            .select("id,user_id,nome,criado_em")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        return (resp.data or [None])[0]

    def atualizar_nome(self, user_id: str, nome: str) -> None:
        self.cliente.table("perfis").update({"nome": nome}).eq("user_id", user_id).execute()
