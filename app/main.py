"""
Streamlit Observability App — Interface visual para o pipeline de correção CorretumAI.

Rastreabilidade completa: exibe cada etapa do pipeline (RAG, Corretor 1, Corretor 2,
Divergência, Árbitro) em tempo real com feedback visual.

Adaptado da branch main para a arquitetura da branch tcc.
"""
import asyncio
import json
import os
import sys
import time

import pandas as pd
import streamlit as st

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.persistence import load_persistence_data, save_persistence_data
from app.ui_components import (
    render_class_ranking,
    render_custom_css,
    render_global_kpis,
    render_student_report,
    setup_page,
)
from src.core.settings import settings
from src.core.langsmith_config import initialize_langsmith, is_langsmith_enabled
from src.core.llm_handler import get_chat_model
from src.core.vector_db_handler import get_vector_store
from src.domain.ai.schemas import EvaluationCriterion, ExamQuestion, QuestionMetadata, StudentAnswer
from src.domain.ai.workflow.graph import get_grading_graph
from src.services.rag.retrieval_service import RetrievalService


# --- Initialization ---
setup_page()
render_custom_css()
initialize_langsmith()
load_persistence_data()

retrieval_service = RetrievalService()


# --- Helpers ---
def run_async(coro):
    """Run async coroutine from sync context (Streamlit)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
    except RuntimeError:
        pass
    return asyncio.run(coro)


# --- Workflow Logic ---
async def run_correction_pipeline(inputs, status_container=None):
    """Executa o LangGraph de forma assíncrona, com streaming de eventos reais."""
    workflow = get_grading_graph()

    if status_container:
        final_state = dict(inputs)
        async for output in workflow.astream(inputs):
            for key, value in output.items():
                if isinstance(value, dict):
                    final_state.update(value)

                # Feedback visual por etapa
                if key == "retrieve_context":
                    contexts = value.get('rag_contexts', [])
                    count = len(contexts) if contexts else 0
                    status_container.write(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;📚 RAG: {count} trechos recuperados.")

                elif key == "examiner_1":
                    c1 = value.get('correction_1')
                    if c1:
                        status_container.write(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;🤖 Corretor 1: Nota {c1.total_score:.1f}")

                elif key == "examiner_2":
                    c2 = value.get('correction_2')
                    if c2:
                        status_container.write(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;🤖 Corretor 2: Nota {c2.total_score:.1f}")

                elif key == "divergence_check":
                    is_div = value.get('divergence_detected', False)
                    if is_div:
                        diff = value.get('divergence_value', 0)
                        status_container.write(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;⚠️ Divergência ({diff:.1f} pts)! Acionando Árbitro...")
                    else:
                        status_container.write("&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;✨ Consenso atingido.")

                elif key == "arbiter":
                    arb = value.get('correction_arbiter')
                    if arb:
                        status_container.write(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;👨‍⚖️ Árbitro: Nota {arb.total_score:.1f}")

                elif key == "finalize":
                    score = value.get('final_score')
                    if score is not None:
                        status_container.write(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;✅ Nota Final: {score:.1f}")

        return final_state
    else:
        return await workflow.ainvoke(inputs)


def get_rag_status_info():
    """Retorna contagem de documentos no VectorDB."""
    try:
        vs = get_vector_store()
        count = vs._collection.count()
        return count, vs
    except Exception:
        return 0, None


# --- SIDEBAR & SETUP ---
with st.sidebar:
    st.title("⚙️ Painel de Controle")
    operation_mode = st.radio(
        "Modo de Operação",
        ["Single Student (Debug)", "Batch Processing (Turma)"],
        index=0
    )
    st.divider()

    # LangSmith Status
    st.header("📊 Observabilidade")
    model_name = getattr(settings, 'LLM_MODEL_NAME', 'unknown')
    st.caption(f"LLM: {settings.LLM_PROVIDER} / {model_name}")
    if is_langsmith_enabled():
        st.success("✓ LangSmith Ativo", icon="🔍")
        st.caption(f"Projeto: {settings.LANGSMITH_PROJECT_NAME}")
        if st.button("Ver Dashboard", key="langsmith_dashboard"):
            st.info("[Abra em novo navegador](https://smith.langchain.com)", icon="🔗")
    else:
        st.warning("⚠️ LangSmith Desativado", icon="🔍")
        st.caption("Configure LANGSMITH_API_KEY para habilitar")

    st.divider()

    st.header("📚 Base de Conhecimento")
    doc_count, vs = get_rag_status_info()
    st.caption(f"Status VectorDB: {doc_count} docs indexados")

    if doc_count > 0 and st.button("🗑️ Limpar Banco de Dados"):
        if vs:
            try:
                all_ids = vs._collection.get()['ids']
                if all_ids:
                    vs._collection.delete(ids=all_ids)
                st.success("Limpo!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")

    st.divider()
    st.header("Parâmetros")
    divergence_threshold = st.slider("Limiar de Divergência", 0.5, 5.0, 2.0, 0.5)
    st.session_state["divergence_threshold"] = divergence_threshold


# --- PAGES ---

if operation_mode == "Single Student (Debug)":
    st.title("🔬 Modo Debug: Correção Individual")
    st.markdown("Rastreabilidade completa de cada etapa do pipeline de correção.")

    tab1, tab2, tab3 = st.tabs(["1. Configuração", "2. Execução", "3. Auditoria"])

    with tab1:
        if 'global_discipline' not in st.session_state:
            st.session_state['global_discipline'] = "Banco de Dados"

        discipline = st.text_input("Disciplina", key="global_discipline")
        topic = st.text_input("Tópico", value="Geral")

        col_q, col_a = st.columns(2)
        with col_q:
            q_text = st.text_area("Enunciado", "Explique a diferença entre Árvores B e B+.")
            default_rubric = [
                {"name": "Precisão Conceitual", "description": "Correção dos conceitos apresentados", "weight": 6, "max_score": 6},
                {"name": "Clareza", "description": "Organização e clareza do texto", "weight": 4, "max_score": 4}
            ]
            rubric_json = st.text_area("Rubrica (JSON)", json.dumps(default_rubric, indent=2, ensure_ascii=False))
        with col_a:
            student_text = st.text_area("Resposta do Aluno", "Árvores B armazenam dados em todos os nós, enquanto B+ armazenam apenas nas folhas...")

        if st.button("Carregar Dados", key="single_load"):
            try:
                rubric_objs = [EvaluationCriterion(**r) for r in json.loads(rubric_json)]
                st.session_state['single_input'] = {
                    "question": ExamQuestion(
                        id="Q1",
                        statement=q_text,
                        rubric=rubric_objs,
                        metadata=QuestionMetadata(discipline=discipline, topic=topic)
                    ),
                    "student_answer": StudentAnswer(
                        student_id="ALUNO_01",
                        question_id="Q1",
                        text=student_text
                    ),
                    "rag_contexts": [],
                    "correction_1": None,
                    "correction_2": None,
                    "correction_arbiter": None,
                    "divergence_detected": False,
                    "divergence_value": 0.0,
                    "all_corrections": [],
                    "final_score": None,
                }
                st.success("Pronto para executar!")
            except Exception as e:
                st.error(f"Erro na configuração: {e}")

    with tab2:
        if 'single_input' in st.session_state and st.button("▶️ Executar Pipeline", key="single_exec"):
            status_container = st.status("🧑‍🏫 Executando pipeline de correção...", expanded=True)
            try:
                final_state = run_async(run_correction_pipeline(
                    st.session_state['single_input'],
                    status_container
                ))
                st.session_state['single_result'] = final_state
                status_container.update(label="✅ Correção concluída!", state="complete")
            except Exception as e:
                status_container.update(label="❌ Erro na execução", state="error")
                st.error(f"Erro: {e}")

        if 'single_result' in st.session_state:
            res = st.session_state['single_result']
            final_score = res.get('final_score', 0)

            st.metric("Nota Final", f"{final_score:.2f}" if final_score else "N/A")

            with st.expander("📋 Detalhes da Correção", expanded=True):
                # Corretor 1
                c1 = res.get('correction_1')
                c2 = res.get('correction_2')
                arb = res.get('correction_arbiter')

                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    st.markdown("##### 🤖 Corretor 1")
                    if c1:
                        st.metric("Nota", f"{c1.total_score:.1f}")
                        st.markdown(f"**Feedback:** {c1.feedback_text}")
                        with st.popover("Ver Raciocínio (Chain-of-Thought)"):
                            st.write(c1.reasoning_chain)
                        if c1.criterion_scores:
                            st.markdown("**Notas por critério:**")
                            for cs in c1.criterion_scores:
                                st.caption(f"• {cs.criterion}: {cs.score}/{cs.max_score}")
                    else:
                        st.warning("Não executou.")

                with col_c2:
                    st.markdown("##### 🤖 Corretor 2")
                    if c2:
                        st.metric("Nota", f"{c2.total_score:.1f}")
                        st.markdown(f"**Feedback:** {c2.feedback_text}")
                        with st.popover("Ver Raciocínio (Chain-of-Thought)"):
                            st.write(c2.reasoning_chain)
                        if c2.criterion_scores:
                            st.markdown("**Notas por critério:**")
                            for cs in c2.criterion_scores:
                                st.caption(f"• {cs.criterion}: {cs.score}/{cs.max_score}")
                    else:
                        st.warning("Não executou.")

                # Divergência
                if res.get('divergence_detected'):
                    st.error(f"⚠️ Divergência detectada: {res.get('divergence_value', 0):.1f} pontos")
                else:
                    st.success("✨ Consenso atingido entre corretores")

                # Árbitro
                if arb:
                    st.markdown("##### 👨‍⚖️ Árbitro")
                    st.metric("Nota Árbitro", f"{arb.total_score:.1f}")
                    st.markdown(f"**Veredito:** {arb.feedback_text}")
                    with st.popover("Ver Raciocínio de Desempate"):
                        st.write(arb.reasoning_chain)

            with st.expander("📚 Contexto RAG"):
                rag_ctx = res.get('rag_contexts', [])
                if rag_ctx:
                    st.markdown(f"**{len(rag_ctx)} trechos recuperados do material:**")
                    for r in rag_ctx:
                        with st.popover(f"Chunk (Score: {r.relevance_score:.2f})"):
                            st.write(r.content)
                else:
                    st.caption("Nenhum contexto RAG utilizado.")

            with st.expander("🔍 Estado Completo (Debug JSON)"):
                # Serialize for display
                debug_data = {
                    "final_score": res.get('final_score'),
                    "divergence_detected": res.get('divergence_detected'),
                    "divergence_value": res.get('divergence_value'),
                    "correction_1": res['correction_1'].model_dump() if res.get('correction_1') else None,
                    "correction_2": res['correction_2'].model_dump() if res.get('correction_2') else None,
                    "correction_arbiter": res['correction_arbiter'].model_dump() if res.get('correction_arbiter') else None,
                    "rag_contexts_count": len(res.get('rag_contexts', []) or []),
                }
                st.json(debug_data)

    with tab3:
        st.markdown("""
        ### Pipeline de Correção — Etapas

        | # | Etapa | Node | O que faz |
        |---|-------|------|-----------|
        | 1 | **RAG** | `retrieve_context` | Busca trechos relevantes do material didático |
        | 2 | **Corretor 1** | `examiner_1` | Avaliação independente por critério |
        | 3 | **Corretor 2** | `examiner_2` | Segunda avaliação independente |
        | 4 | **Divergência** | `divergence_check` | Compara notas C1 vs C2 (limiar configurável) |
        | 5 | **Árbitro** | `arbiter` | Acionado se divergência > limiar |
        | 6 | **Consenso** | `finalize` | Média do par mais próximo (C1, C2, C3) |

        **Limiar atual:** `DIVERGENCE_THRESHOLD = {threshold}`

        Cada etapa é exibida em tempo real na aba "Execução".
        """.format(threshold=st.session_state.get('divergence_threshold', 2.0)))


elif operation_mode == "Batch Processing (Turma)":
    st.title("🎓 Modo Turma: Correção em Escala")
    st.markdown("Gerencie a correção automática de dezenas de respostas simultaneamente.")
    st.info("💡 O modo batch utiliza o mesmo pipeline com rastreabilidade completa. "
            "Cada resposta passa por RAG → C1 → C2 → Divergência → Árbitro (se necessário).")

    st.warning("⚠️ Funcionalidade em desenvolvimento para a branch TCC. "
               "Use o modo Single Student para rastreabilidade completa.")
