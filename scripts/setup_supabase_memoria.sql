-- LIBERTUS: Tabela de memória disciplinada de sessões
-- Executar no Supabase Dashboard > SQL Editor

CREATE TABLE IF NOT EXISTS libertus_memoria (
  id          BIGSERIAL PRIMARY KEY,
  tipo        TEXT NOT NULL CHECK (tipo IN ('decisao','erro','preferencia','aprendizado','pentest','objetivo','reflexao')),
  titulo      TEXT NOT NULL,
  conteudo    TEXT NOT NULL,
  sessao_id   TEXT,
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  tags        TEXT[] DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_libertus_memoria_tipo    ON libertus_memoria(tipo);
CREATE INDEX IF NOT EXISTS idx_libertus_memoria_created ON libertus_memoria(created_at DESC);

-- Row Level Security (opcional mas recomendado)
ALTER TABLE libertus_memoria ENABLE ROW LEVEL SECURITY;

-- Permite acesso via service_role key (o que usamos)
CREATE POLICY "service_role_all" ON libertus_memoria
  FOR ALL TO service_role USING (true) WITH CHECK (true);

-- Permite acesso via anon key com token
CREATE POLICY "anon_read_insert" ON libertus_memoria
  FOR ALL TO anon USING (true) WITH CHECK (true);
