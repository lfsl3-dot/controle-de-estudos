-- =====================================================================
-- Controle de Estudos - banco de dados (Supabase / PostgreSQL)
-- Execute este arquivo inteiro no SQL Editor do Supabase.
-- Tabelas: perfis -> materias -> estudos (todas ligadas ao usuario do login)
-- =====================================================================

-- ---------- 1) PERFIS (dados basicos de quem usa o sistema) ----------
create table if not exists public.perfis (
    id         uuid primary key default gen_random_uuid(),
    user_id    uuid not null unique references auth.users(id) on delete cascade,
    nome       text not null check (char_length(nome) between 2 and 80),
    criado_em  timestamptz not null default now()
);

-- ---------- 2) MATERIAS (tabela auxiliar: classifica os estudos) ----------
create table if not exists public.materias (
    id         bigint generated always as identity primary key,
    user_id    uuid not null default auth.uid() references auth.users(id) on delete cascade,
    nome       text not null check (char_length(nome) between 2 and 60),
    descricao  text check (descricao is null or char_length(descricao) <= 200),
    criado_em  timestamptz not null default now()
);

-- ---------- 3) ESTUDOS (tabela principal: CRUD do sistema) ----------
create table if not exists public.estudos (
    id          bigint generated always as identity primary key,
    user_id     uuid not null default auth.uid() references auth.users(id) on delete cascade,
    materia_id  bigint not null references public.materias(id) on delete cascade,
    titulo      text not null check (char_length(titulo) between 3 and 80),
    status      text not null default 'pendente'
                check (status in ('pendente', 'em_andamento', 'concluido')),
    duracao_min integer not null default 30 check (duracao_min between 1 and 600),
    criado_em   timestamptz not null default now()
);

create index if not exists idx_materias_user on public.materias(user_id);
create index if not exists idx_estudos_user on public.estudos(user_id);
create index if not exists idx_estudos_materia on public.estudos(materia_id);

-- ---------- Cria o perfil automaticamente quando alguem se cadastra ----------
create or replace function public.criar_perfil_novo_usuario()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
    nome_informado text;
begin
    nome_informado := trim(coalesce(new.raw_user_meta_data->>'nome', ''));
    if char_length(nome_informado) < 2 then
        nome_informado := 'Estudante';
    end if;
    insert into public.perfis (user_id, nome)
    values (new.id, left(nome_informado, 80));
    return new;
end;
$$;

drop trigger if exists ao_criar_usuario on auth.users;
create trigger ao_criar_usuario
    after insert on auth.users
    for each row execute function public.criar_perfil_novo_usuario();

-- =====================================================================
-- SEGURANCA: RLS (Row Level Security) ativado em TODAS as tabelas
-- Cada usuario so enxerga/altera os proprios registros (auth.uid() = user_id)
-- =====================================================================
alter table public.perfis   enable row level security;
alter table public.materias enable row level security;
alter table public.estudos  enable row level security;

-- Quem nao esta logado (role anon) nao tem acesso nenhum as tabelas
revoke all on public.perfis, public.materias, public.estudos from anon;
grant select, insert, update, delete on public.perfis, public.materias, public.estudos to authenticated;

-- ---------- Politicas: PERFIS ----------
drop policy if exists "perfis_select_proprio" on public.perfis;
drop policy if exists "perfis_insert_proprio" on public.perfis;
drop policy if exists "perfis_update_proprio" on public.perfis;
drop policy if exists "perfis_delete_proprio" on public.perfis;

create policy "perfis_select_proprio" on public.perfis for select to authenticated
    using (auth.uid() = user_id);
create policy "perfis_insert_proprio" on public.perfis for insert to authenticated
    with check (auth.uid() = user_id);
create policy "perfis_update_proprio" on public.perfis for update to authenticated
    using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "perfis_delete_proprio" on public.perfis for delete to authenticated
    using (auth.uid() = user_id);

-- ---------- Politicas: MATERIAS ----------
drop policy if exists "materias_select_proprio" on public.materias;
drop policy if exists "materias_insert_proprio" on public.materias;
drop policy if exists "materias_update_proprio" on public.materias;
drop policy if exists "materias_delete_proprio" on public.materias;

create policy "materias_select_proprio" on public.materias for select to authenticated
    using (auth.uid() = user_id);
create policy "materias_insert_proprio" on public.materias for insert to authenticated
    with check (auth.uid() = user_id);
create policy "materias_update_proprio" on public.materias for update to authenticated
    using (auth.uid() = user_id) with check (auth.uid() = user_id);
create policy "materias_delete_proprio" on public.materias for delete to authenticated
    using (auth.uid() = user_id);

-- ---------- Politicas: ESTUDOS ----------
-- Alem de conferir o dono do estudo, confere se a materia escolhida tambem
-- pertence ao usuario (impede ligar um estudo a materia de outra pessoa).
drop policy if exists "estudos_select_proprio" on public.estudos;
drop policy if exists "estudos_insert_proprio" on public.estudos;
drop policy if exists "estudos_update_proprio" on public.estudos;
drop policy if exists "estudos_delete_proprio" on public.estudos;

create policy "estudos_select_proprio" on public.estudos for select to authenticated
    using (auth.uid() = user_id);
create policy "estudos_insert_proprio" on public.estudos for insert to authenticated
    with check (
        auth.uid() = user_id
        and exists (select 1 from public.materias m
                    where m.id = materia_id and m.user_id = auth.uid())
    );
create policy "estudos_update_proprio" on public.estudos for update to authenticated
    using (auth.uid() = user_id)
    with check (
        auth.uid() = user_id
        and exists (select 1 from public.materias m
                    where m.id = materia_id and m.user_id = auth.uid())
    );
create policy "estudos_delete_proprio" on public.estudos for delete to authenticated
    using (auth.uid() = user_id);

-- ---------- Conferencia (use na gravacao do video) ----------
-- select tablename, rowsecurity from pg_tables where schemaname = 'public';
-- select tablename, policyname, cmd from pg_policies where schemaname = 'public';
