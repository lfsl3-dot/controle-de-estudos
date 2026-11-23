"""Model da tabela auxiliar: materias."""


class MateriaModel:
    CAMPOS = "id,nome,descricao,criado_em"

    def __init__(self, cliente):
        self.cliente = cliente

    def listar(self, user_id: str) -> list[dict]:
        resp = (
            self.cliente.table("materias")
            .select(self.CAMPOS)
            .eq("user_id", user_id)
            .order("nome")
            .execute()
        )
        return resp.data or []

    def criar(self, user_id: str, nome: str, descricao: str) -> None:
        self.cliente.table("materias").insert(
            {"user_id": user_id, "nome": nome, "descricao": descricao or None}
        ).execute()

    def atualizar(self, user_id: str, materia_id: int, nome: str, descricao: str) -> None:
        (
            self.cliente.table("materias")
            .update({"nome": nome, "descricao": descricao or None})
            .eq("id", materia_id)
            .eq("user_id", user_id)
            .execute()
        )

    def excluir(self, user_id: str, materia_id: int) -> None:
        (
            self.cliente.table("materias")
            .delete()
            .eq("id", materia_id)
            .eq("user_id", user_id)
            .execute()
        )
