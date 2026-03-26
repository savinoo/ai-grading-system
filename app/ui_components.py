
import streamlit as st


def setup_page():
    st.set_page_config(page_title="AI Grading System (TCC)", layout="wide", page_icon="📝")

def render_custom_css():
    st.markdown("""
<style>
    /* Estilo Global */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 95% !important;
    }

    /* Cards de Métricas */
    .stMetric {
        background: white;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        color: #333 !important;
        transition: transform 0.2s;
    }
    .stMetric:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .stMetric > div:first-child {
        color: #666 !important;
        font-size: 14px !important;
        font-weight: 500;
    }
    .stMetric > div:last-child {
        color: #2c3e50 !important;
        font-size: 28px !important;
        font-weight: 700 !important;
    }

    /* Estilo dos Expanders de Questão */
    .streamlit-expanderHeader {
        background-color: #f8f9fa;
        border-radius: 5px;
        font-weight: 600;
        color: #495057;
    }

    /* Destaque para notas */
    .grade-badge-pass {
        background-color: #d4edda;
        color: #155724;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    .grade-badge-fail {
        background-color: #f8d7da;
        color: #721c24;
        padding: 4px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

def render_student_report(student_data):
    """Renderiza o relatório detalhado de um aluno (Drill-Down)"""
    st.info(f"Visualizando prova de **{student_data['name']}**")

    # Lista de Questões em Cards Expansíveis
    for idx, q_res in enumerate(student_data['details']):
        # Define cor do header baseado na nota da questão
        q_grade = q_res['grade']
        icon = "✅" if q_grade >= 6 else "❌"

        with st.expander(f"{icon} Questão {idx+1} | Nota: {q_grade:.1f} | {q_res['question_text'][:60]}..."):

            # Layout em 2 colunas dentro do card da questão
            c_left, c_right = st.columns([1, 1], gap="medium")

            with c_left:
                st.markdown("#### 📝 Resposta do Aluno")
                st.markdown(f"> *{q_res['answer_text']}*")

                st.markdown("#### 📌 Enunciado Completo")
                st.caption(q_res['question_text'])

            with c_right:
                st.markdown(f"#### 🔍 Correção Detalhada (Nota: {q_grade:.1f})")

                full_state = q_res['state']
                c1 = full_state.get('correction_1')
                c2 = full_state.get('correction_2')
                arb = full_state.get('correction_arbiter')

                # Tabs para Deep Dive
                t_overview, t_rag, t_agents, t_arbiter = st.tabs(["📝 Resultado", "📚 Contexto (RAG)", "🤖 Agentes (Thinking)", "⚖️ Árbitro"])

                with t_overview:
                    if q_res.get('divergence'):
                        st.error("⚠️ **Divergência Detectada!**")
                        st.markdown("A IA detectou desacordo entre corretores e acionou o Árbitro.")
                    else:
                        st.success("**Consenso Atingido**")

                    final_corr = arb or c2 or c1
                    if final_corr:
                        st.info(f"**Feedback ao Aluno:**\n\n{final_corr.feedback_text}")

                with t_rag:
                        rag_ctx = full_state.get('rag_contexts', []) or []
                        st.markdown(f"**{len(rag_ctx)} Trechos recuperados do material:**")
                        for r in rag_ctx:
                            with st.popover(f"Chunk (Score: {r.relevance_score:.2f})"):
                                st.write(r.content)

                with t_agents:
                        col_a1, col_a2 = st.columns(2)
                        with col_a1:
                            st.markdown("##### 🤖 Corretor 1")
                            if c1:
                                st.metric("Nota C1", c1.total_score)
                                with st.popover("Ver Raciocínio (Chain-of-Thought)"):
                                    st.write(c1.reasoning_chain)
                            else:
                                st.warning("Não executou.")

                        with col_a2:
                            st.markdown("##### 🤖 Corretor 2")
                            if c2:
                                st.metric("Nota C2", c2.total_score)
                                with st.popover("Ver Raciocínio (Chain-of-Thought)"):
                                    st.write(c2.reasoning_chain)
                            else:
                                st.warning("Não executou.")

                with t_arbiter:
                        if arb:
                            st.markdown("##### 👨‍⚖️ Intervenção do Árbitro")
                            st.metric("Nota Árbitro", arb.total_score)
                            st.markdown("**Veredito:**")
                            st.write(arb.feedback_text)
                            st.markdown("**Raciocínio de Desempate:**")
                            st.write(arb.reasoning_chain)
                        else:
                            st.caption("O árbitro não foi acionado para esta questão (sem divergência).")

def render_global_kpis(df_res):
    col_kpi1, col_kpi2, col_kpi3 = st.columns(3)

    avg_grade = df_res['grade'].mean()
    max_grade = df_res['grade'].max()
    pass_rate = (df_res['grade'] >= 6.0).mean()

    col_kpi1.metric("Média Geral", f"{avg_grade:.1f}", delta=f"{avg_grade-6.0:.1f} vs Meta" if avg_grade >=6 else f"{avg_grade-6.0:.1f}")
    col_kpi2.metric("Maior Nota", f"{max_grade:.1f}")
    col_kpi3.metric("Aprovação", f"{pass_rate*100:.0f}%")

def render_class_ranking(df_res):
    st.dataframe(
        df_res[['name', 'grade']].sort_values('grade', ascending=False),
        use_container_width=True,
        column_config={
            "name": st.column_config.TextColumn("Aluno", width="medium"),
            "grade": st.column_config.ProgressColumn(
                "Nota Final",
                help="Nota média das questões (0-10)",
                format="%.1f",
                min_value=0,
                max_value=10,
            ),
        },
        hide_index=True,
    )
