import streamlit as st
import asyncio
import os
import json
import pandas as pd
import random
import time
import sys

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Custom Modules ---
from src.utils.logging_config import setup_logging
from src.utils.helpers import run_async, save_uploaded_file, safe_gather
from app.persistence import save_persistence_data, load_persistence_data
from app.ui_components import (
    setup_page, render_custom_css, render_student_report, 
    render_global_kpis, render_class_ranking
)
from app.analytics_ui import (
    render_student_profile_card, render_class_analytics_dashboard, 
    render_analytics_selector
)
from src.workflow.graph import build_grading_workflow
from src.rag.chunking import process_and_index_pdf
from src.rag.retriever import search_context
from src.domain.schemas import ExamQuestion, EvaluationCriterion, QuestionMetadata, StudentAnswer
from src.domain.analytics_schemas import SubmissionRecord
from src.config.settings import settings
from src.agents.mock_generator import MockDataGeneratorAgent
from src.analytics import StudentTracker, ClassAnalyzer
from src.memory import get_knowledge_base
# from langchain_openai import ChatOpenAI # SUBSTITUIDO PELO FACTORY
from src.infrastructure.llm_factory import get_chat_model
from src.infrastructure.vector_db import get_vector_store
from src.infrastructure.langsmith_config import initialize_langsmith, is_langsmith_enabled

# --- Initialization ---
setup_logging()
initialize_langsmith()  # Inicializa LangSmith tracing
from src.infrastructure.dspy_config import configure_dspy
configure_dspy()
# Usando temperatura 1 para criatividade na geração de dados (Questões e Respostas)
# Usa o factory para suportar Gemini ou OpenAI transparentemente
llm_creation = get_chat_model(temperature=1)
mock_agent = MockDataGeneratorAgent(llm_creation)

# Analytics initialization
tracker = StudentTracker()
kb = get_knowledge_base()
analyzer = ClassAnalyzer()

setup_page()
render_custom_css()
load_persistence_data()

# --- Workflow Logic ---

async def run_correction_pipeline(inputs, status_container=None):
    """Executa o LangGraph de forma assíncrona, com streaming de eventos reais"""
    workflow = build_grading_workflow()
    
    if status_container:
        final_state = inputs.copy()
        async for output in workflow.astream(inputs):
            for key, value in output.items():
                if isinstance(value, dict):
                    final_state.update(value)
                
                # Feedback visual
                if key == "retrieve_context":
                    count = len(value.get('rag_context', []))
                    status_container.write(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;📚 RAG: {count} trechos recuperados.")
                elif key == "corrector_1":
                     res = value.get('individual_corrections', [])[0]
                     status_container.write(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;🤖 Corretor 1: Nota {res.total_score:.1f}")
                elif key == "corrector_2":
                     res = value.get('individual_corrections', [])[0]
                     status_container.write(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;🤖 Corretor 2: Nota {res.total_score:.1f}")
                elif key == "check_divergence":
                     is_div = value.get('divergence_detected', False)
                     if is_div:
                         status_container.write(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;⚠️ Divergência! Acionando Árbitro...")
                     else:
                         status_container.write(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;✨ Consenso atingido.")
                elif key == "arbiter":
                     res = value.get('individual_corrections', [])[-1]
                     status_container.write(f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;👨‍⚖️ Árbitro: Nota final {res.total_score:.1f}")
                     
        return final_state
    else:
        return await workflow.ainvoke(inputs)

def get_rag_status_info():
    try:
        vs = get_vector_store()
        count = vs._collection.count()
        return count, vs
    except:
        return 0, None

# --- SIDEBAR & SETUP ---
with st.sidebar:
    st.title("⚙️ Painel de Controle")
    operation_mode = st.radio(
        "Modo de Operação", 
        ["Single Student (Debug)", "Batch Processing (Turma)", "📊 Analytics Dashboard"],
        index=1
    )
    st.divider()
    
    # LangSmith Status
    st.header("📊 Observabilidade")
    st.caption(f"LLM model: {settings.MODEL_NAME}")
    if is_langsmith_enabled():
        st.success("✓ LangSmith Ativo", icon="🔍")
        st.caption(f"Projeto: {settings.LANGSMITH_PROJECT_NAME}")
        if st.button("Ver Dashboard", key="langsmith_dashboard"):
            st.info(f"[Abra em novo navegador](https://smith.langchain.com)", icon="🔗")
    else:
        st.warning("⚠️ LangSmith Desativado", icon="🔍")
        st.caption("Configure LANGSMITH_API_KEY para habilitar")
    
    st.divider()
    
    st.header("📚 Base de Conhecimento")
    doc_count, vs = get_rag_status_info()
    st.caption(f"Status VectorDB: {doc_count} docs indexados")
    
    uploaded_file = st.file_uploader("Upload de Material (PDF)", type="pdf")
    if 'global_discipline' not in st.session_state: st.session_state['global_discipline'] = "História"
    discipline = st.text_input("Disciplina", key="global_discipline")
    topic = "Revolução Industrial"
    
    if uploaded_file and st.button("Indexar Material"):
        with st.spinner("Processando..."):
            path = save_uploaded_file(uploaded_file)
            count = process_and_index_pdf(path, discipline, topic)
            st.success(f"Adicionado {count} chunks!")
            time.sleep(1)
            st.rerun()

    if doc_count > 0 and st.button("🗑️ Limpar Banco de Dados"):
         if vs:
            try:
                all_ids = vs._collection.get()['ids']
                if all_ids: vs._collection.delete(ids=all_ids)
                st.success("Limpo!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")

    st.divider()
    st.header("Parâmetros")
    divergence_threshold = st.slider("Limiar de Divergência", 0.5, 5.0, 1.5, 0.5)
    settings.DIVERGENCE_THRESHOLD = divergence_threshold

# --- PAGES ---

if operation_mode == "Single Student (Debug)":
    st.title("🔬 Modo Debug: Correção Individual")
    
    tab1, tab2, tab3 = st.tabs(["1. Configuração", "2. Execução", "3. Auditoria"])
    
    with tab1:
        col_q, col_a = st.columns(2)
        with col_q:
            q_text = st.text_area("Enunciado", "Explique a diferença entre Árvores B e B+.")
            default_rubric = [{"name": "Precisão", "description": "Conceito correto", "weight": 6, "max_score": 6}, {"name": "Clareza", "description": "Texto claro", "weight": 4, "max_score": 4}]
            rubric_json = st.text_area("Rubrica (JSON)", json.dumps(default_rubric, indent=2))
        with col_a:
            student_text = st.text_area("Resposta do Aluno", "Árvores B armazenam dados nos nós...")
            
        if st.button("Carregar Dados", key="single_load"):
            try:
                rubric_objs = [EvaluationCriterion(**r) for r in json.loads(rubric_json)]
                st.session_state['single_input'] = {
                    "question": ExamQuestion(id="Q1", statement=q_text, rubric=rubric_objs, metadata=QuestionMetadata(discipline=discipline, topic=topic)),
                    "student_answer": StudentAnswer(student_id="ALUNO_01", question_id="Q1", text=student_text),
                    "rag_context": [], "individual_corrections": [], "divergence_detected": False, "divergence_value": 0.0, "final_grade": None
                }
                st.success("Pronto para executar!")
            except Exception as e: st.error(f"Erro: {e}")

    with tab2:
        if 'single_input' in st.session_state and st.button("▶️ Executar", key="single_exec"):
            with st.spinner("Processando..."):
                final_state = run_async(run_correction_pipeline(st.session_state['single_input']))
                st.session_state['single_result'] = final_state
                st.success("Feito!")
        
        if 'single_result' in st.session_state:
            res = st.session_state['single_result']
            st.metric("Nota Final", f"{res['final_grade']:.2f}")
            with st.expander("Detalhes da Correção"):
                st.json(res)

    with tab3:
        st.info("Funcionalidade detalhada disponível no modo Batch.")

elif operation_mode == "Batch Processing (Turma)":
    # --- MODO 2: BATCH PROCESSING ---
    st.title("🎓 Modo Turma: Correção em Escala")
    st.markdown("Gerencie a correção automática de dezenas de alunos simultaneamente.")
    
    batch_mode = st.radio("Fonte da Prova", ["Simulação Completa (IA)", "Configuração Manual (Texto/JSON)"], horizontal=True)

    # A. CONFIG MANUAL
    if batch_mode == "Configuração Manual (Texto/JSON)":
        with st.expander("📝 1. Configuração da Prova e Gabarito", expanded=True):
            if st.checkbox("🤖 Usar Assistente de Criação (AI)"):
                c1, c2, c3 = st.columns([3, 2, 1])
                with c1: gen_topic = st.text_input("Tópico", f"{discipline}: {topic}")
                with c2: gen_diff = st.selectbox("Dificuldade", ["Easy", "Medium", "Hard"], index=1)
                with c3:
                    st.write("") 
                    if st.button("✨ Criar"):
                        with st.spinner("Criando..."):
                             q_obj = run_async(mock_agent.generate_exam_question(gen_topic, discipline, gen_diff))
                             st.session_state['q_input_val'] = q_obj.statement
                             st.session_state['r_input_val'] = json.dumps([r.model_dump() for r in q_obj.rubric], indent=2)
                             st.rerun()
            
            # Defaults
            if 'q_input_val' not in st.session_state: st.session_state['q_input_val'] = "Discuta o impacto..."
            if 'r_input_val' not in st.session_state: st.session_state['r_input_val'] = json.dumps([{"name": "Geral", "description": "...", "weight":10, "max_score":10}])
            
            c1, c2 = st.columns(2)
            c1.text_area("Enunciado", key="q_input_val", height=200)
            c2.text_area("Rubrica (JSON)", key="r_input_val", height=200)

    # B. SIMULAÇÂO & EXECUÇÃO
    col_load1 = st.container()
    
    if batch_mode == "Simulação Completa (IA)":
        with col_load1:
            st.subheader("👥 Simulação e Fluxo")
            
            sim_topic = st.text_input("Tópico Geral", value="Geral")
            c_qtd1, c_qtd2 = st.columns(2)
            qt_mock_questions = c_qtd1.number_input("Qtd Questões", 1, 10, 5) 
            qt_mock_students = c_qtd2.number_input("Qtd Alunos", 1, 50, 5)
            
            col_s1, col_s2 = st.columns(2)
            
            # STEP 1: GENERATE
            with col_s1:
                if st.button("1️⃣ Gerar Questões (IA)"):
                    with st.spinner(f"Gerando {qt_mock_questions} questões..."):
                        # Clean old state
                        for key in ['batch_all_mock_answers', 'exam_results']:
                            if key in st.session_state: del st.session_state[key]
                        
                        questions = run_async(mock_agent.generate_exam_questions(sim_topic, discipline, "Medium", count=qt_mock_questions))
                        st.session_state['exam_questions'] = questions
                        save_persistence_data()
                        st.rerun()

            if 'exam_questions' in st.session_state:
                st.success(f"{len(st.session_state['exam_questions'])} questões geradas.")
                
                with st.expander("👁️ Visualizar Prova", expanded=True):
                    # Rubric Table
                    first_q = st.session_state['exam_questions'][0]
                    rubric_data = [{"Critério": r.name, "Descrição": r.description, "Peso": r.weight} for r in first_q.rubric]
                    st.markdown("### 📋 Rubrica de Avaliação (Global)")
                    
                    md_table = "| Critério | Descrição | Peso |\n|---|---|---|\n"
                    for r in rubric_data: md_table += f"| {r['Critério']} | {r['Descrição']} | {r['Peso']} |\n"
                    st.markdown(md_table)
                    
                    st.divider()
                    st.markdown("### 📝 Questões")
                    for i, q in enumerate(st.session_state['exam_questions']):
                        st.markdown(f"**{i+1}.** {q.statement}")

                # STEP 2: SIMULATE ANSWERS
                with col_s2:
                    if st.button("2️⃣ Simular Respostas"):
                        status_container = st.status("✍️ Alunos realizando a prova...", expanded=True)
                        try:
                            questions = st.session_state['exam_questions']
                            profiles = ["excellent", "average", "average", "poor", "average"]
                            students_list = []
                            for i in range(qt_mock_students):
                                qual = profiles[i % len(profiles)]
                                students_list.append({"id": 200 + i, "name": f"Aluno {i+1} ({qual.title()})", "quality": qual})
                            st.session_state['batch_students_list'] = students_list
                            
                            all_mock_answers = {q.id: {} for q in questions} 
                            gen_bar = status_container.progress(0)
                            
                            # ESTRATÉGIA HÍBRIDA: Loop por Questão -> Paralelismo por Turma
                            # Isso restaura o log visual ("Questão X de Y...") mas mantém velocidade
                            
                            for q_idx, q in enumerate(questions):
                                status_container.write(f"📝 **Questão {q_idx+1}/{len(questions)}:** Simulando respostas da turma...")
                                
                                # Cria tasks apenas para ESTA questão (Todos os alunos ao mesmo tempo)
                                tasks = []
                                for s in students_list:
                                    # Lógica probabilística de desempenho: O aluno não é estático
                                    # Um aluno ruim pode acertar, e um bom pode errar.
                                    base_quality = s['quality']
                                    
                                    if base_quality == "poor":
                                        # 60% Errado, 30% Médio, 10% Bom (Sorte?)
                                        weights = [0.6, 0.3, 0.1]
                                    elif base_quality == "excellent":
                                        # 10% Ruim (Nervosismo), 20% Médio, 70% Excelente
                                        weights = [0.1, 0.2, 0.7]
                                    else: # average
                                        # 20% Ruim, 60% Médio, 20% Bom
                                        weights = [0.2, 0.6, 0.2]
                                    
                                    actual_quality = random.choices(
                                        ["poor", "average", "excellent"], 
                                        weights=weights, 
                                        k=1
                                    )[0]
                                    
                                    tasks.append(mock_agent.generate_student_answer(q, actual_quality, s['name']))
                                
                                # Executa o lote da questão
                                async def run_question_batch():
                                    return await safe_gather(*tasks)
                                
                                batch_answers = run_async(run_question_batch())
                                
                                # Salva resultados
                                for s_idx, ans in enumerate(batch_answers):
                                    s_id = students_list[s_idx]['id']
                                    all_mock_answers[q.id][s_id] = ans
                                
                                gen_bar.progress((q_idx + 1) / len(questions))
                            
                            st.session_state['batch_all_mock_answers'] = all_mock_answers
                            save_persistence_data()
                            status_container.update(label="✅ Respostas Entregues!", state="complete", expanded=False)
                            st.rerun()
                        except Exception as e:
                            status_container.update(label="Erro", state="error")
                            st.error(str(e))

            # STEP 3: CORRECT
            if 'batch_all_mock_answers' in st.session_state:
                st.markdown("---")
                # Preview Answers
                with st.expander("👀 Ver Respostas (Preview)"):
                    stud_map = {s['id']: s['name'] for s in st.session_state.get('batch_students_list', [])}
                    for q in st.session_state['exam_questions']:
                        st.markdown(f"#### {q.statement}")
                        answers = st.session_state['batch_all_mock_answers'].get(q.id, {})
                        for s_id, ans in answers.items():
                             st.markdown(f"**{stud_map.get(s_id, s_id)}:** {ans.text}")
                             st.caption("---")
                
                if st.button("3️⃣ Iniciar Correção Automática"):
                     status_container = st.status("🧑‍🏫 Corrigindo...", expanded=True)
                     try:
                        questions = st.session_state['exam_questions']
                        all_mock_answers = st.session_state['batch_all_mock_answers']
                        students_list = st.session_state.get('batch_students_list', [])
                        
                        students_results_map = {s['id']: {"id": s['id'], "name": s['name'], "total_grade": 0, "results": []} for s in students_list}
                        corr_bar = status_container.progress(0)
                        
                        for q_idx, q in enumerate(questions):
                            status_container.write(f"Corrigindo Q{q_idx+1}...")
                            rag_context = search_context(q.statement, q.metadata.discipline, q.metadata.topic)
                            
                            # Prepare inputs
                            inputs_by_student = {}
                            for s in students_list:
                                if s['id'] in all_mock_answers[q.id]:
                                    ans = all_mock_answers[q.id][s['id']]
                                    inputs_by_student[s['id']] = {
                                        "question": q, "student_answer": ans, "rag_context": rag_context,
                                        "individual_corrections": []
                                    }
                            
                            # Execute Batch
                            if inputs_by_student:
                                # [MODIFICAÇÃO] Chunking para evitar Rate Limit (Gemini 429)
                                # Processa em lotes de 3 alunos por vez (3 * 2 corretores = 6 calls simultâneos)
                                tasks = [run_correction_pipeline(inp, None) for inp in inputs_by_student.values()]
                                
                                async def process_q_batch():
                                    results = []
                                    chunk_size = int(os.getenv("BATCH_CHUNK_SIZE", "4"))
                                    total = len(tasks)
                                    
                                    for i in range(0, total, chunk_size):
                                        chunk = tasks[i : i + chunk_size]
                                        status_container.write(f"Corrigindo Q{q_idx+1}: Lote {i//chunk_size + 1}/{(total//chunk_size)+1}...")
                                        chunk_results = await safe_gather(*chunk)
                                        results.extend(chunk_results)
                                        # Optional cooldown between chunks (avoid 429s)
                                        cooldown = float(os.getenv("BATCH_COOLDOWN_SLEEP", "0.0"))
                                        if cooldown > 0:
                                            await asyncio.sleep(cooldown)
                                    return results
                                
                                batch_results = run_async(process_q_batch())
                                
                                # Aggregate
                                for i, (s_id, inp) in enumerate(inputs_by_student.items()):
                                    final_state = batch_results[i]
                                    students_results_map[s_id]["results"].append({
                                        "question_id": q.id, "question_text": q.statement,
                                        "answer_text": inp['student_answer'].text,
                                        "grade": final_state.get('final_grade', 0),
                                        "divergence": final_state.get('divergence_detected', False),
                                        "state": final_state
                                    })
                                    students_results_map[s_id]["total_grade"] += final_state.get('final_grade', 0)
                                    
                                    # **NEW**: Track this submission in analytics
                                    from datetime import datetime
                                    
                                    # Extract criterion scores from corrections
                                    criterion_scores = {}
                                    if final_state.get('individual_corrections'):
                                        last_correction = final_state['individual_corrections'][-1]
                                        if hasattr(last_correction, 'criterion_scores'):
                                            for crit in last_correction.criterion_scores:
                                                criterion_scores[crit.criterion_name] = crit.score
                                    
                                    submission_record = SubmissionRecord(
                                        submission_id=f"SUB_{s_id}_{q.id}_{datetime.now().timestamp()}",
                                        question_id=q.id,
                                        question_text=q.statement,
                                        student_answer=inp['student_answer'].text,
                                        grade=final_state.get('final_grade', 0),
                                        max_score=10.0,
                                        criterion_scores=criterion_scores,
                                        divergence_detected=final_state.get('divergence_detected', False),
                                        timestamp=datetime.now()
                                    )
                                    
                                    # Update student profile
                                    student_name = next(
                                        (s['name'] for s in students_list if s['id'] == s_id),
                                        f"Student_{s_id}"
                                    )
                                    
                                    profile = tracker.add_submission(
                                        student_id=str(s_id),
                                        student_name=student_name,
                                        submission=submission_record
                                    )
                                    
                                    # Persist to knowledge base
                                    kb.add_or_update(profile)
                            
                            corr_bar.progress((q_idx + 1) / len(questions))
                            
                        # Finalize
                        generated_batch_results = []
                        for s_id, s_data in students_results_map.items():
                             generated_batch_results.append({
                                 "id": s_id, "name": s_data["name"],
                                 "grade": s_data["total_grade"] / len(questions),
                                 "details": s_data["results"]
                             })
                        st.session_state['exam_results'] = generated_batch_results
                        save_persistence_data()
                        status_container.update(label="Concluído!", state="complete", expanded=False)
                        st.rerun()

                     except Exception as e:
                         status_container.update(label="Erro", state="error")
                         st.error(f"Stack trace: {e}")

    # C. RESULTS DASHBOARD
    if 'exam_results' in st.session_state:
        st.markdown("---")
        st.header("📊 Painel de Resultados")
        results = st.session_state['exam_results']
        df_res = pd.DataFrame(results)
        
        render_global_kpis(df_res)
        st.subheader("🏆 Classificação")
        render_class_ranking(df_res)
        
        st.markdown("---")
        st.subheader("📑 Boletim Individual")
        
        col_sel, col_stats = st.columns([1, 2])
        student_names = [r['name'] for r in results]
        selected_name = col_sel.selectbox("Selecione Aluno", student_names)
        
        if selected_name:
            student_data = next(r for r in results if r['name'] == selected_name)
            render_student_report(student_data)

elif operation_mode == "📊 Analytics Dashboard":
    # --- MODO 3: ANALYTICS DASHBOARD ---
    st.title("📊 Professor Assistant - Analytics Dashboard")
    st.markdown("Análise pedagógica avançada com tracking de alunos e insights de turma.")
    
    # Load all profiles from knowledge base
    all_profiles = kb.get_all()
    
    if not all_profiles:
        st.warning("⚠️ Nenhum dado disponível ainda. Execute correções em modo Batch primeiro para gerar analytics.")
        st.info("💡 **Como usar:** Execute correções de uma turma, e os dados de tracking serão salvos automaticamente.")
    else:
        # Tabs for different analytics views
        tab_overview, tab_student, tab_class = st.tabs([
            "📋 Visão Geral",
            "👤 Perfil do Aluno", 
            "🏫 Análise da Turma"
        ])
        
        with tab_overview:
            st.subheader("Resumo Geral")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total de Alunos Rastreados", len(all_profiles))
            
            with col2:
                total_submissions = sum(len(p.submissions_history) for p in all_profiles)
                st.metric("Total de Submissões", total_submissions)
            
            with col3:
                all_grades = [s.grade for p in all_profiles for s in p.submissions_history]
                avg_grade = sum(all_grades) / len(all_grades) if all_grades else 0
                st.metric("Média Global", f"{avg_grade:.2f}")
            
            st.divider()
            
            # Trend summary
            st.subheader("📈 Resumo de Tendências")
            trend_counts = {
                "improving": 0,
                "stable": 0,
                "declining": 0,
                "insufficient_data": 0
            }
            
            for profile in all_profiles:
                trend_counts[profile.trend] += 1
            
            col_imp, col_stab, col_dec, col_insuf = st.columns(4)
            
            with col_imp:
                st.metric("📈 Melhorando", trend_counts["improving"])
            
            with col_stab:
                st.metric("➡️ Estável", trend_counts["stable"])
            
            with col_dec:
                st.metric("📉 Piorando", trend_counts["declining"])
            
            with col_insuf:
                st.metric("❓ Dados Insuficientes", trend_counts["insufficient_data"])
        
        with tab_student:
            st.subheader("Análise Individual de Aluno")
            
            selected_profile = render_analytics_selector(all_profiles)
            
            if selected_profile:
                render_student_profile_card(selected_profile)
        
        with tab_class:
            st.subheader("Análise da Turma")
            
            # Generate class insights
            insights = analyzer.analyze_class(
                class_id="current_class",
                student_profiles=all_profiles
            )
            
            render_class_analytics_dashboard(insights, all_profiles)

