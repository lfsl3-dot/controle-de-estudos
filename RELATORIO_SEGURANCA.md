# Relatório de Segurança e Interface

Data: 25/11/2026

## Resultado geral

- Testes automatizados: **20 aprovados**.
- Isolamento entre contas A e B: aprovado.
- Sessões sem login: bloqueadas pelo Controller.
- Proteção contra erro técnico exposto na tela: aprovada.
- Chaves privilegiadas: recusadas pela configuração.
- Consulta anônima às tabelas `perfis`, `materias` e `estudos`: negada pelo Supabase.
- Proteção de limite de tentativas: aprovada.
- Limite defensivo de mutações repetidas: aprovado após correção de um limite que podia permitir a operação no limite.

## Interface interna alterada

- Nova barra lateral com navegação para Estudos, Materias e Perfil.
- Informações do usuário apresentadas em cartão próprio.
- Botão de saída integrado à barra lateral.
- Área principal ampliada e separada visualmente por fundo neutro.
- Tema global com barra lateral indigo e identidade visual consistente.

## Cabeçalhos HTTP encontrados

A aplicação retornou os seguintes controles:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Permissions-Policy` para câmera, microfone, geolocalização e pagamento
- `Cross-Origin-Opener-Policy: same-origin`
- `Cross-Origin-Embedder-Policy: require-corp`
- `Cache-Control: no-store, max-age=0`
- `Content-Security-Policy`

## Falhas encontradas e corrigidas

1. **Erro de API do Flet**: a versão 1.0.1 utilizava `openapi_prefix`, argumento removido pelo FastAPI moderno. Corrigido com camada de compatibilidade.
2. **Erro de Pydantic/Supabase**: versões incompatíveis poderiam causar falha ao iniciar. Corrigido com dependências alinhadas no `requirements.txt`.
3. **Erro visual ao iniciar**: `ft.padding.all/symmetric` não existia nesta versão do Flet. Substituído por controles compatíveis.
4. **CSP bloqueava recursos necessários do Flet**: política ampliada apenas para os domínios necessários do runtime Flutter/Flet.
5. **Limite de mutações permitia uma operação no threshold**: corrigido para bloquear a operação que atingisse o limite.

## Falha de hospedagem no Render

- **Erro observado:** `module 'flet.controls.alignment' has no attribute 'center'`.
- **Correção:** adicionados aliases compatíveis para chamadas antigas de `alignment.center()` e `Alignment.center()`.
- **Runtime:** criado `runtime.txt` fixando Python 3.11.9 para alinhar o Render ao ambiente testado.
- **Dependências:** Flet 1.0.1, Flet Web 1.0.1 e FastAPI 0.115.12 permanecem fixados em `requirements.txt`.

## Modificações aplicadas nesta revisão

- Remoção defensiva dos cabeçalhos `Access-Control-Allow-Origin` e `Access-Control-Allow-Credentials` das respostas HTTP.
- Rotas protegidas continuam dependentes da sessão do Supabase e das políticas RLS.
- A desativação de `/openapi.json`, `/docs` e `/redoc` foi revertida porque afetava o funcionamento interno do Flet nesta versão. Esses endpoints não expõem dados do banco sem sessão.

## Observações

- Cabeçalhos CORS permissivos não substituem RLS, mas foram removidos por não serem necessários para esta aplicação local.
- Não é seguro nem legítimo "contragolpear" o dispositivo de um atacante. A proteção adequada é bloquear, limitar, registrar e isolar a tentativa, além de usar CDN/WAF e monitoramento.

## Recomendações para produção

- Publicar com HTTPS obrigatório e confirmar HSTS no proxy externo.
- Configurar rate limiting real por IP e por conta no servidor/WAF.
- Habilitar MFA no Supabase para contas administrativas.
- Revisar logs de autenticação e configurar alertas.
- Validar periodicamente RLS no painel SQL do Supabase.
- Manter segredo somente no painel da hospedagem e nunca no código ou no Dockerfile.
