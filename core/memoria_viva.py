"""
LIBERTUS - Memória Viva
========================
Relevância que respira: sobe com uso, decai com tempo.
Substitui o campo estático `relevancia` pelo dinâmico `peso_vivo`.

Uso:
    from memoria_viva import MemoriaViva
    mv = MemoriaViva()

    # Buscar memórias relevantes para um contexto
    memorias = mv.buscar("como fazer scan de portas")

    # Depois de usar: registrar se foi útil
    mv.foi_util(memoria_id, contexto="scan nmap")
    mv.foi_inutil(memoria_id, contexto="scan nmap")

    # Rodar decaimento (chamar 1x por dia ou por sessão)
    mv.decair()

    # Ver estado de saúde da memória
    mv.status()
"""

import os
from datetime import datetime
from supabase import create_client, Client


class MemoriaViva:
    def __init__(self):
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("SUPABASE_URL e SUPABASE_KEY precisam estar no ambiente")
        self.db: Client = create_client(url, key)

    # ------------------------------------------------------------------
    # BUSCA: retorna memórias ordenadas por peso_vivo (não mais relevancia)
    # ------------------------------------------------------------------
    def buscar(self, query: str = None, tipo: str = None, projeto: str = None,
               limite: int = 10, peso_minimo: float = 1.0) -> list[dict]:
        """
        Busca memórias vivas. Filtra por peso mínimo, ordena por peso_vivo DESC.
        """
        q = self.db.table("libertus_memoria").select(
            "id, tipo, titulo, conteudo, tags, projeto, "
            "peso_vivo, vezes_usada, vezes_util, ultimo_acesso"
        ).gte("peso_vivo", peso_minimo).order("peso_vivo", desc=True)

        if tipo:
            q = q.eq("tipo", tipo)
        if projeto:
            q = q.eq("projeto", projeto)

        resultado = q.limit(limite).execute()
        memorias = resultado.data or []

        # Filtro por texto no título/conteúdo (simples, sem embedding)
        if query:
            query_lower = query.lower()
            memorias = [
                m for m in memorias
                if query_lower in (m.get("titulo") or "").lower()
                or query_lower in (m.get("conteudo") or "").lower()
            ]

        return memorias

    # ------------------------------------------------------------------
    # FEEDBACK: registrar se a memória foi útil ou não
    # ------------------------------------------------------------------
    def foi_util(self, memoria_id: str, contexto: str = None) -> float:
        """Memória ajudou → peso sobe +1.5 (max 10)"""
        return self._registrar_uso(memoria_id, foi_util=True, contexto=contexto)

    def foi_inutil(self, memoria_id: str, contexto: str = None) -> float:
        """Memória não ajudou → peso cai -0.5 (min 0.1)"""
        return self._registrar_uso(memoria_id, foi_util=False, contexto=contexto)

    def _registrar_uso(self, memoria_id: str, foi_util: bool,
                       contexto: str = None) -> float:
        """Chama a função SQL que ajusta o peso e loga o uso."""
        result = self.db.rpc("libertus_registrar_uso", {
            "p_memoria_id": memoria_id,
            "p_foi_util": foi_util,
            "p_contexto": contexto
        }).execute()
        novo_peso = result.data
        emoji = "📈" if foi_util else "📉"
        label = "ÚTIL" if foi_util else "INÚTIL"
        print(f"  {emoji} Memória [{memoria_id[:8]}...] marcada como {label} → peso: {novo_peso:.2f}")
        return novo_peso

    # ------------------------------------------------------------------
    # DECAIMENTO: chamar uma vez por sessão ou dia
    # ------------------------------------------------------------------
    def decair(self) -> int:
        """
        Aplica decaimento natural: -0.1 por dia de inatividade.
        Retorna quantas memórias foram afetadas.
        """
        result = self.db.rpc("libertus_decaimento").execute()
        count = result.data or 0
        print(f"  🍂 Decaimento aplicado: {count} memórias afetadas")
        return count

    # ------------------------------------------------------------------
    # STATUS: diagnóstico da saúde da memória
    # ------------------------------------------------------------------
    def status(self):
        """Imprime relatório de saúde da memória do LIBERTUS."""
        # Top memórias
        top = self.db.table("libertus_memoria_top").select("*").limit(5).execute()
        print("\n🧠 TOP MEMÓRIAS MAIS VIVAS:")
        for m in (top.data or []):
            taxa = m.get('taxa_utilidade_pct', 0)
            print(f"  [{m['peso_vivo']:.1f}] {m['titulo'][:50]} "
                  f"(usada {m['vezes_usada']}x, {taxa}% útil)")

        # Memórias morrendo
        morrendo = self.db.table("libertus_memoria_morrendo").select("*").limit(5).execute()
        if morrendo.data:
            print("\n💀 MEMÓRIAS MORRENDO (peso < 2.0):")
            for m in morrendo.data:
                dias = int(m.get('dias_sem_acesso') or 0)
                print(f"  [{m['peso_vivo']:.1f}] {m['titulo'][:50]} "
                      f"({dias} dias sem acesso)")

        # Contagem geral
        total = self.db.table("libertus_memoria").select("id", count="exact").execute()
        print(f"\n📊 Total de memórias: {total.count}")

    # ------------------------------------------------------------------
    # INTEGRAÇÃO COM RESPOSTAS: wrapper para usar no fluxo principal
    # ------------------------------------------------------------------
    def buscar_e_rastrear(self, query: str, tipo: str = None,
                          projeto: str = None, limite: int = 5) -> list[dict]:
        """
        Busca memórias E já as marca internamente como "acessadas"
        (atualiza ultimo_acesso sem mudar o peso ainda — o peso muda
        só depois que o usuário/sistema confirmar se foi útil).
        """
        memorias = self.buscar(query, tipo, projeto, limite)
        if memorias:
            ids = [m["id"] for m in memorias]
            # Atualiza ultimo_acesso para evitar decaimento injusto
            self.db.table("libertus_memoria").update({
                "ultimo_acesso": datetime.utcnow().isoformat()
            }).in_("id", ids).execute()
        return memorias


# ------------------------------------------------------------------
# INTEGRAÇÃO DIRETA NO LIBERTUS: patch no fluxo de busca de memória
# ------------------------------------------------------------------
def patch_libertus(libertus_instance):
    """
    Injeta MemoriaViva no LIBERTUS existente sem reescrever nada.
    Chame isso no __init__ do libertus.py:

        from memoria_viva import patch_libertus
        patch_libertus(self)

    Depois use:
        memorias = self.mv.buscar_e_rastrear("scan de portas")
        # ... usa as memórias na resposta ...
        self.mv.foi_util(memorias[0]["id"], contexto="scan nmap")
    """
    mv = MemoriaViva()
    libertus_instance.mv = mv
    print("🧬 Memória Viva ativa no LIBERTUS")
    return mv


# ------------------------------------------------------------------
# DEMO / TESTE STANDALONE
# ------------------------------------------------------------------
if __name__ == "__main__":
    print("=== LIBERTUS: Memória Viva - Diagnóstico ===\n")
    mv = MemoriaViva()

    # Rodar decaimento
    mv.decair()

    # Ver status
    mv.status()

    # Exemplo de busca
    print("\n🔍 Buscando memórias sobre 'pentest'...")
    memorias = mv.buscar("pentest", limite=3)
    for m in memorias:
        print(f"  [{m['peso_vivo']:.1f}] {m['titulo']}")
