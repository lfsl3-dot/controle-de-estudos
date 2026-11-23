# Roteiro do vídeo (5 a 10 minutos)

Grave a tela e explique **com a sua voz**, com as suas palavras. Use este roteiro só como guia de tempo.

| Tempo | O que mostrar | O que falar |
|---|---|---|
| 0:00–0:45 | Tela de login | Seu nome, o tema escolhido (controle de estudos) e o problema que ele resolve. |
| 0:45–3:30 | Sistema funcionando no link público | Cadastro de conta, login, criar matéria, criar estudo, editar, excluir (mostre a confirmação) e sair. Mostre que as 3 tabelas são usadas. |
| 3:30–5:30 | Pastas no VS Code | **models/**: conversa com o Supabase. **controllers/**: regras, validação e controle de sessão. **views/**: telas Flet. **main.py**: liga tudo e lê a porta. Mostre um `try/except` e o `@requer_login`. |
| 5:30–7:30 | Painel do Supabase | Tabela `perfis`, `materias` e `estudos`, as chaves estrangeiras (`user_id` e `materia_id`) e as políticas RLS (`auth.uid() = user_id`). |
| 7:30–9:00 | Código e painel | Segurança: `.env` no `.gitignore`, só chave pública, RLS, validação, mensagem genérica no login e telas bloqueadas sem sessão. |
| 9:00–9:45 | Painel da hospedagem | Qual plataforma usou, onde cadastrou `SUPABASE_URL` e `SUPABASE_KEY`, e o comando de início. |

Dica: antes de gravar, peça para alguém testar o sistema sem a sua ajuda e anote o que confundiu.
