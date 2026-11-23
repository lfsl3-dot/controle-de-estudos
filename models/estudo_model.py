"""Model da tabela principal: estudos (CRUD completo)."""


class EstudoModel:
    CAMPOS = "id,titulo,status,duracao_min,criado_em,materia_id,materias(nome)"

    def __init__(self, cliente):
        self.cliente = cliente

    def listar(self, user_id: str) -> list[dict]:
        resp = (
            self.cliente.table("estudos")
            .select(self.CAMPOS)
            .eq("user_id", user_id)
            .order("criado_em", desc=True)
            .execute()
        )
        return resp.data or []

    def criar(self, user_id: str, materia_id: int, titulo: str, status: str, duracao_min: int) -> None:
        self.cliente.table("estudos").insert(
            {
                "user_id": user_id,
                "materia_id": materia_id,
                "titulo": titulo,
                "status": status,
                "duracao_min": duracao_min,
            }
        ).execute()

    def atualizar(self, user_id: str, estudo_id: int, materia_id: int, titulo: str,
                  status: str, duracao_min: int) -> None:
        (
            self.cliente.table("estudos")
            .update(
                {
                    "materia_id": materia_id,
                    "titulo": titulo,
                    "status": status,
                    "duracao_min": duracao_min,
                }
            )
            .eq("id", estudo_id)
            .eq("user_id", user_id)
            .execute()
        )

    def excluir(self, user_id: str, estudo_id: int) -> None:
        (
            self.cliente.table("estudos")
            .delete()
            .eq("id", estudo_id)
            .eq("user_id", user_id)
            .execute()
        )
