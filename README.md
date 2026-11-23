# Controle de Estudos — Flet + MVC + Supabase

Sistema web individual (tema livre: **controle de estudos**) para o Trabalho Prático Final.
O usuário cadastra **matérias** e registra seus **estudos** (título, matéria, status e duração).

## Estrutura (padrão MVC)

```
main.py                    # ponto de entrada (login -> tela principal) e porta da hospedagem
models/                    # M: acesso ao Supabase (nenhuma regra de tela)
  conexao.py               #    lê o .env, recusa chave service_role, cria o cliente
  usuario_model.py         #    Supabase Auth (sign_up / sign_in / sign_out) + tabela perfis
  materia_model.py         #    CRUD da tabela materias
  estudo_model.py          #    CRUD da tabela estudos
controllers/               # C: regras, validação e controle de sessão
  validacao.py             #    validação das entradas
  app_controller.py        #    login, bloqueio sem sessão, mensagens seguras, CRUD
views/                     # V: telas Flet (nada de banco aqui)
  login_view.py            #    login / cadastro
  principal_view.py        #    estudos, matérias e perfil
  componentes.py           #    avisos e confirmação de exclusão
database/schema.sql        # tabelas, chaves estrangeiras, trigger e políticas RLS
tests/                     # testes automáticos (rodam sem internet)
```

## Banco de dados (3 tabelas relacionadas)

| Tabela | Função | Chaves |
|---|---|---|
| `perfis` | dados de quem usa o sistema | `user_id` → `auth.users` |
| `materias` | classifica os estudos | `user_id` → `auth.users` |
| `estudos` | itens centrais (CRUD) | `user_id` → `auth.users`, `materia_id` → `materias` |

## Como configurar (passo a passo)

### 1. Supabase
1. Crie um projeto em supabase.com.
2. **SQL Editor** → cole todo o conteúdo de `database/schema.sql` → **Run**.
3. **Project Settings → API Keys**: copie a **URL do projeto** (sem `/rest/v1/`) e a **Publishable key**
   (antiga `anon`). **Nunca** use a `service_role`/secret.
4. **Authentication → Sign In / Providers → Email**: para testar mais rápido você pode desativar
   *Confirm email*. Se deixar ativado, o usuário precisa confirmar o e-mail antes de entrar.

### 2. Rodar no seu computador
```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt    # precisa do Flet 1.0 ou mais novo
cp .env.example .env               # depois edite o .env com a URL e a chave publica
python main.py                     # abre em http://localhost:8080
```
> Use um ambiente virtual **novo** para este projeto: o Flet 1.0 tem uma API diferente das versões
> antigas (0.2x) usadas em outras atividades.

### 3. Testes automáticos
```bash
python -m unittest discover -s tests -t . -v
```

### 4. GitHub (sem vazar chaves)
```bash
git init
git add .
git status                         # confira: o arquivo .env NAO pode aparecer na lista
git commit -m "Controle de Estudos"
```
Se alguma chave já foi enviada ao GitHub por engano, gere uma chave nova no Supabase e apague a antiga.

### 5. Hospedagem (escolha uma)
- **Render**: *New → Web Service* ligado ao repositório. Build: `pip install -r requirements.txt` ·
  Start: `python main.py` · em *Environment Variables* cadastre `SUPABASE_URL` e `SUPABASE_KEY`.
- **Hugging Face Spaces**: crie um Space com SDK **Docker**, envie o código e o `Dockerfile` (sem `.env`).
  No `README.md` do Space coloque no topo:
  ```
  ---
  title: Controle de Estudos
  sdk: docker
  app_port: 7860
  ---
  ```
  Em *Settings → Variables and secrets* cadastre `SUPABASE_URL` e `SUPABASE_KEY` como *Secrets*.
- **Koyeb**: ligue o repositório, comando de inicialização `python main.py` e cadastre as duas variáveis.

O `main.py` já lê a porta da variável `PORT`, como o enunciado pede.

## Segurança (as 5 rotinas do guia)

| Rotina | Onde está |
|---|---|
| 1. Chaves protegidas | `.env` no `.gitignore`; `models/conexao.py` lê variáveis de ambiente, recusa chave `service_role`/secret e remove `/rest/v1/` da URL |
| 2. RLS em todas as tabelas | `database/schema.sql`: RLS ligado + políticas de SELECT/INSERT/UPDATE/DELETE com `auth.uid() = user_id`; o INSERT/UPDATE de `estudos` também confere se a matéria é do usuário; o papel `anon` não tem acesso |
| 3. Telas bloqueadas sem login | `@requer_login` no Controller (toda função de cadastro/edição/exclusão) e `mostrar_principal()` no `main.py` |
| 4. Validação de entradas | `controllers/validacao.py` + `try/except` no Controller (campos vazios, tamanhos, números, status, ids) |
| 5. Mensagens seguras | login sempre responde "E-mail ou senha inválidos."; erros técnicos só vão para o log do servidor |

Extras: cada sessão de navegador usa o seu próprio cliente Supabase (para um usuário não herdar o login do
outro), logout com `scope: local`, limite de tentativas de login (5 erros = 30 s de espera) e
confirmação antes de excluir.

### Teste de segurança recomendado
1. Crie duas contas (A e B). Cadastre matérias e estudos na A, saia e entre na B: a B não pode ver nada da A.
2. Teste a API sem login (deve voltar vazio ou erro, nunca os dados):
   ```bash
   curl "https://SEUPROJETO.supabase.co/rest/v1/estudos?select=*" \
        -H "apikey: SUA_CHAVE_PUBLICA"
   ```
3. No Supabase, confira o RLS: `select tablename, rowsecurity from pg_tables where schemaname = 'public';`
   (as 3 tabelas devem aparecer com `true`).
