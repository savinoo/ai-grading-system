import asyncio
import json
import logging
import os
import random
import sys
import time

import pandas as pd
import streamlit as st

# Configure logging to console with timestamps for debugging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
_perf_log = logging.getLogger("perf")

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Custom Modules (adapted for tcc architecture) ---
from app.analytics_ui import render_analytics_selector, render_class_analytics_dashboard, render_plagiarism_dashboard, render_student_profile_card
from app.api_client import get_api_client
from app.experiment_store import get_experiment_store
from app.persistence import load_persistence_data, save_persistence_data
from app.ui_components import (
    render_class_ranking,
    render_custom_css,
    render_global_kpis,
    render_student_report,
    setup_page,
)
from src.agents.mock_generator import MockDataGeneratorAgent
from src.analytics import ClassAnalyzer, StudentTracker
from src.core.settings import settings
from src.domain.analytics_schemas import SubmissionRecord
from src.domain.ai.schemas import EvaluationCriterion, ExamQuestion, QuestionMetadata, StudentAnswer
from src.core.langsmith_config import initialize_langsmith, is_langsmith_enabled
from src.core.llm_handler import get_chat_model
from src.core.vector_db_handler import get_vector_store
from src.memory import get_knowledge_base
from src.services.rag.chunking_service import ChunkingService
from src.services.rag.retrieval_service import RetrievalService
from src.utils.helpers import run_async, safe_gather, save_uploaded_file
from src.core.logging_config import get_logger
from src.domain.ai.workflow.graph import get_grading_graph

# --- Initialization (cached to avoid re-creation on every Streamlit rerun) ---
logger = get_logger("streamlit")

@st.cache_resource
def _init_langsmith():
    initialize_langsmith()
    return True

@st.cache_resource
def _init_llm():
    return get_chat_model(temperature=1)

@st.cache_resource
def _init_mock_agent():
    return MockDataGeneratorAgent(_init_llm())

@st.cache_resource
def _init_retrieval():
    return RetrievalService()

@st.cache_resource
def _init_tracker():
    return StudentTracker()

@st.cache_resource
def _init_kb():
    return get_knowledge_base()

@st.cache_resource
def _init_analyzer():
    return ClassAnalyzer()

_t0 = time.time()
_init_langsmith()
_perf_log.info(f"[INIT] langsmith: {time.time()-_t0:.2f}s")

_t0 = time.time()
mock_agent = _init_mock_agent()
_perf_log.info(f"[INIT] mock_agent (LLM x2): {time.time()-_t0:.2f}s")

_t0 = time.time()
retrieval_service = _init_retrieval()
_perf_log.info(f"[INIT] retrieval_service (VectorDB): {time.time()-_t0:.2f}s")

_t0 = time.time()
tracker = _init_tracker()
kb = _init_kb()
analyzer = _init_analyzer()
exp_store = get_experiment_store()
_perf_log.info(f"[INIT] analytics (tracker+kb+analyzer+exp_store): {time.time()-_t0:.2f}s")

setup_page()
render_custom_css()
load_persistence_data()
_perf_log.info("[INIT] === Streamlit ready ===")

# --- Workflow Logic ---

async def run_correction_pipeline(inputs, status_container=None):
    """Executa o LangGraph de forma assíncrona, com streaming de eventos reais"""
    workflow = get_grading_graph()

    if status_container:
        final_state = dict(inputs)
        async for output in workflow.astream(inputs):
            for key, value in output.items():
                if isinstance(value, dict):
                    final_state.update(value)

                # Feedback visual (node names from tcc graph)
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
        ["Single Student (Debug)", "Batch Processing (Turma)", "📊 Analytics Dashboard", "🔗 End-to-End (Backend API)"],
        index=1
    )
    st.divider()

    # LangSmith Status
    st.header("📊 Observabilidade")
    st.caption(f"LLM: {settings.LLM_PROVIDER} / {settings.LLM_MODEL_NAME}")
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

    uploaded_file = st.file_uploader("Upload de Material (PDF)", type="pdf")
    if 'global_discipline' not in st.session_state: st.session_state['global_discipline'] = "História"
    discipline = st.text_input("Disciplina", key="global_discipline")
    topic = "Revolução Industrial"

    if uploaded_file and st.button("Indexar Material"):
        with st.spinner("Processando e indexando..."):
            path = save_uploaded_file(uploaded_file)
            chunking = ChunkingService()
            chunks = run_async(chunking.process_pdf(path))
            if chunks:
                vs_instance = get_vector_store()
                vs_instance.add_documents(chunks)
                st.success(f"Indexado {len(chunks)} chunks no VectorDB!")
            else:
                st.warning("Nenhum chunk extraído do PDF.")
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
    divergence_threshold = st.slider("Limiar de Divergência", 0.5, 5.0, 2.0, 0.5)
    st.session_state["divergence_threshold"] = divergence_threshold

    # RAG toggle (Condição A vs B do TCC)
    rag_enabled = st.toggle("RAG Ativado (Condição A)", value=True,
                            help="Desative para Condição B (sem RAG)")
    st.session_state["rag_enabled"] = rag_enabled
    if rag_enabled:
        st.caption(f"Condição A: RAG ativo (top_k={getattr(settings, 'RAG_TOP_K', 4)})")
    else:
        st.caption("Condição B: RAG desativado (top_k=0)")

    # Experiment history
    st.divider()
    st.header("📦 Experimentos")
    experiments = exp_store.list_experiments()
    if experiments:
        st.caption(f"{len(experiments)} experimento(s) salvo(s)")
        for exp in experiments[:5]:
            col_info, col_btn = st.columns([3, 1])
            col_info.caption(f"#{exp['id']} — {exp.get('llm_model', '?')} | {exp.get('num_questions', '?')}Q {exp.get('num_students', '?')}A | {exp.get('status', '?')}")
            if col_btn.button("📥", key=f"export_{exp['id']}", help="Exportar JSON"):
                export_path = f"tcc/results/experiment_{exp['id']}.json"
                exp_store.export_experiment(exp['id'], export_path)
                st.success(f"Exportado: {export_path}")
    else:
        st.caption("Nenhum experimento ainda")

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
                    "rag_contexts": [], "correction_1": None, "correction_2": None, "correction_arbiter": None, "divergence_detected": False, "divergence_value": 0.0, "all_corrections": [], "final_score": None
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
            st.metric("Nota Final", f"{res.get('final_score', 0):.2f}")
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
                with c2: gen_diff = st.selectbox("Dificuldade", ["fácil", "médio", "difícil"], index=1)
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

            # ─── Reutilizar experimento anterior (TCC: mesmas questões/respostas pra Condição B) ───
            prev_experiments = exp_store.list_experiments()
            completed_exps = [e for e in prev_experiments if e.get('status') == 'completed']

            if completed_exps:
                with st.expander("🔄 Reutilizar questões/respostas de experimento anterior", expanded=False):
                    st.caption("Use isso para rodar a Condição B com os mesmos dados da Condição A")
                    exp_options = {f"#{e['id']} — {e.get('llm_model', '?')} | {e.get('num_questions', '?')}Q {e.get('num_students', '?')}A ({e.get('discipline', '?')})": e['id'] for e in completed_exps[:10]}
                    selected_exp_label = st.selectbox("Selecione o experimento", list(exp_options.keys()))
                    selected_exp_id = exp_options[selected_exp_label]

                    col_load_q, col_load_qa = st.columns(2)

                    if col_load_q.button("📋 Carregar só questões", key="load_q"):
                        prev_questions = exp_store.load_questions(selected_exp_id)
                        if prev_questions:
                            from src.domain.ai.schemas import ExamQuestion, EvaluationCriterion, QuestionMetadata
                            loaded_qs = []
                            for pq in prev_questions:
                                rubric = json.loads(pq['rubric_json']) if pq.get('rubric_json') else []
                                rubric_objs = [EvaluationCriterion(**r) for r in rubric]
                                loaded_qs.append(ExamQuestion(
                                    id=pq['question_uuid'],
                                    statement=pq['statement'],
                                    total_points=pq.get('total_points', 10.0),
                                    rubric=rubric_objs,
                                    metadata=QuestionMetadata(
                                        discipline=pq.get('discipline', ''),
                                        topic=pq.get('topic', ''),
                                        difficulty_level=pq.get('difficulty')
                                    )
                                ))
                            st.session_state['exam_questions'] = loaded_qs
                            for key in ['batch_all_mock_answers', 'exam_results']:
                                if key in st.session_state: del st.session_state[key]
                            st.success(f"{len(loaded_qs)} questões carregadas do experimento #{selected_exp_id}")
                        else:
                            st.warning("Nenhuma questão encontrada neste experimento")

                    if col_load_qa.button("📋 Carregar questões + respostas", key="load_qa"):
                        prev_questions = exp_store.load_questions(selected_exp_id)
                        prev_answers = exp_store.load_answers(selected_exp_id)
                        prev_students = exp_store.load_students(selected_exp_id)
                        if prev_questions and prev_answers:
                            from src.domain.ai.schemas import ExamQuestion, EvaluationCriterion, QuestionMetadata, StudentAnswer
                            import uuid as _uuid
                            # Load questions
                            loaded_qs = []
                            for pq in prev_questions:
                                rubric = json.loads(pq['rubric_json']) if pq.get('rubric_json') else []
                                rubric_objs = [EvaluationCriterion(**r) for r in rubric]
                                loaded_qs.append(ExamQuestion(
                                    id=pq['question_uuid'],
                                    statement=pq['statement'],
                                    total_points=pq.get('total_points', 10.0),
                                    rubric=rubric_objs,
                                    metadata=QuestionMetadata(
                                        discipline=pq.get('discipline', ''),
                                        topic=pq.get('topic', ''),
                                        difficulty_level=pq.get('difficulty')
                                    )
                                ))
                            st.session_state['exam_questions'] = loaded_qs

                            # Load students
                            students_list = [
                                {"id": ps['student_id'], "name": ps['student_name'], "quality": ps.get('quality_profile')}
                                for ps in prev_students
                            ]
                            st.session_state['batch_students_list'] = students_list

                            # Load answers (reconstruct nested dict)
                            all_mock_answers = {str(q.id): {} for q in loaded_qs}
                            for pa in prev_answers:
                                q_uuid = pa['question_uuid']
                                s_id = pa['student_id']
                                if q_uuid not in all_mock_answers:
                                    all_mock_answers[q_uuid] = {}
                                all_mock_answers[q_uuid][s_id] = StudentAnswer(
                                    student_id=_uuid.UUID(s_id) if len(s_id) > 10 else s_id,
                                    question_id=_uuid.UUID(q_uuid),
                                    text=pa['answer_text']
                                )
                            st.session_state['batch_all_mock_answers'] = all_mock_answers

                            if 'exam_results' in st.session_state:
                                del st.session_state['exam_results']

                            st.success(f"Carregado do exp #{selected_exp_id}: {len(loaded_qs)} questões, {len(prev_students)} alunos, {len(prev_answers)} respostas")
                            st.info("Agora clique em '3️⃣ Iniciar Correção Automática' para corrigir com a condição atual (RAG on/off)")
                        else:
                            st.warning("Dados incompletos neste experimento")

            sim_topic = st.text_input("Tópico Geral", value="Geral")
            c_qtd1, c_qtd2 = st.columns(2)
            qt_mock_questions = c_qtd1.number_input("Qtd Questões", 1, 10, 3)
            qt_mock_students = c_qtd2.number_input("Qtd Alunos", 1, 50, 4)

            col_s1, col_s2 = st.columns(2)

            # STEP 1: GENERATE
            with col_s1:
                if st.button("1️⃣ Gerar Questões (IA)", disabled='_generating' in st.session_state):
                    st.session_state['_generating'] = True
                    with st.spinner(f"Gerando {qt_mock_questions} questões..."):
                        # Clean old state
                        for key in ['batch_all_mock_answers', 'exam_results']:
                            if key in st.session_state: del st.session_state[key]

                        _perf_log.info(f"[STEP1] Gerando {qt_mock_questions} questões via Gemini...")
                        _t1 = time.time()
                        try:
                            questions = run_async(mock_agent.generate_exam_questions(sim_topic, discipline, "médio", count=qt_mock_questions))
                            _perf_log.info(f"[STEP1] {qt_mock_questions} questões geradas em {time.time()-_t1:.1f}s")
                            st.session_state['exam_questions'] = questions
                            # Create experiment and save questions
                            _rag_on = st.session_state.get("rag_enabled", True)
                            exp_id = exp_store.create_experiment({
                                'llm_provider': settings.LLM_PROVIDER,
                                'llm_model': settings.LLM_MODEL_NAME,
                                'llm_temperature': settings.LLM_TEMPERATURE,
                                'num_questions': qt_mock_questions,
                                'num_students': qt_mock_students,
                                'divergence_threshold': st.session_state.get('divergence_threshold', 2.0),
                                'rag_enabled': _rag_on,
                                'rag_top_k': getattr(settings, 'RAG_TOP_K', 4) if _rag_on else 0,
                                'condition': 'A (com RAG)' if _rag_on else 'B (sem RAG)',
                                'discipline': discipline,
                                'topic': sim_topic,
                            })
                            st.session_state['current_experiment_id'] = exp_id
                            exp_store.save_questions(exp_id, questions)
                            _perf_log.info(f"[EXP-{exp_id}] Experiment created, {qt_mock_questions} questions saved")
                            save_persistence_data()
                            st.success(f"{qt_mock_questions} questões geradas! (Experimento #{exp_id})")
                        except Exception as e:
                            _perf_log.error(f"[STEP1] ERRO: {e}")
                            st.error(f"Erro ao gerar questões: {e}")
                        finally:
                            del st.session_state['_generating']

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
                        _perf_log.info(f"[STEP2] Simulando respostas para {qt_mock_students} alunos...")
                        _t2 = time.time()
                        status_container = st.status("✍️ Alunos realizando a prova...", expanded=True)
                        try:
                            questions = st.session_state['exam_questions']
                            # 4 níveis de qualidade conforme TCC: excelente, adequada, fraca, fora do tema
                            profiles = ["excellent", "average", "poor", "off_topic"]
                            profile_labels = {"excellent": "Excelente", "average": "Adequado", "poor": "Fraco", "off_topic": "Fora do Tema"}
                            students_list = []
                            for i in range(qt_mock_students):
                                qual = profiles[i % len(profiles)]
                                students_list.append({"id": 200 + i, "name": f"Aluno {i+1} ({profile_labels[qual]})", "quality": qual})
                            st.session_state['batch_students_list'] = students_list

                            # Save students to experiment
                            exp_id = st.session_state.get('current_experiment_id')
                            if exp_id:
                                exp_store.save_students(exp_id, students_list)

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

                                    # Para TCC: cada aluno responde com seu nível fixo
                                    # (sem randomização, pra garantir reprodutibilidade)
                                    actual_quality = base_quality

                                    tasks.append(mock_agent.generate_student_answer(q, actual_quality, s['name']))

                                # Executa o lote da questão
                                async def run_question_batch():
                                    return await safe_gather(*tasks)

                                batch_answers = run_async(run_question_batch())

                                # Salva resultados
                                for s_idx, ans in enumerate(batch_answers):
                                    s_id = students_list[s_idx]['id']
                                    all_mock_answers[q.id][s_id] = ans
                                    # Save answer to experiment
                                    if exp_id:
                                        exp_store.save_answer(
                                            exp_id, str(q.id), str(s_id),
                                            students_list[s_idx]['name'],
                                            ans.text,
                                            students_list[s_idx].get('quality')
                                        )

                                gen_bar.progress((q_idx + 1) / len(questions))

                            st.session_state['batch_all_mock_answers'] = all_mock_answers
                            save_persistence_data()
                            _perf_log.info(f"[STEP2] Respostas simuladas em {time.time()-_t2:.1f}s")
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
                     _perf_log.info("[STEP3] Iniciando correção automática...")
                     _t3 = time.time()
                     status_container = st.status("🧑‍🏫 Corrigindo...", expanded=True)
                     try:
                        questions = st.session_state['exam_questions']
                        all_mock_answers = st.session_state['batch_all_mock_answers']

                        # Create experiment if not exists (e.g. loaded from previous)
                        exp_id = st.session_state.get('current_experiment_id')
                        if not exp_id:
                            _rag_on = st.session_state.get("rag_enabled", True)
                            exp_id = exp_store.create_experiment({
                                'llm_provider': settings.LLM_PROVIDER,
                                'llm_model': settings.LLM_MODEL_NAME,
                                'llm_temperature': settings.LLM_TEMPERATURE,
                                'num_questions': len(questions),
                                'num_students': len(st.session_state.get('batch_students_list', [])),
                                'divergence_threshold': st.session_state.get('divergence_threshold', 2.0),
                                'rag_enabled': _rag_on,
                                'rag_top_k': getattr(settings, 'RAG_TOP_K', 4) if _rag_on else 0,
                                'condition': 'A (com RAG)' if _rag_on else 'B (sem RAG)',
                                'discipline': discipline,
                                'topic': st.session_state.get('global_discipline', ''),
                                'reused_from_experiment': st.session_state.get('_reused_from_exp'),
                            })
                            st.session_state['current_experiment_id'] = exp_id
                            exp_store.save_questions(exp_id, questions)
                            if st.session_state.get('batch_students_list'):
                                exp_store.save_students(exp_id, st.session_state['batch_students_list'])
                            _perf_log.info(f"[EXP-{exp_id}] Created for correction (reuse mode)")
                        students_list = st.session_state.get('batch_students_list', [])

                        students_results_map = {s['id']: {"id": s['id'], "name": s['name'], "total_grade": 0, "results": []} for s in students_list}
                        corr_bar = status_container.progress(0)

                        for q_idx, q in enumerate(questions):
                            _tq = time.time()
                            _perf_log.info(f"[STEP3] Corrigindo Q{q_idx+1}/{len(questions)}...")
                            status_container.write(f"Corrigindo Q{q_idx+1}...")
                            rag_context = []  # RAG context fetched by pipeline nodes

                            # Prepare inputs
                            inputs_by_student = {}
                            _rag_on = st.session_state.get("rag_enabled", True)
                            for s in students_list:
                                if s['id'] in all_mock_answers[q.id]:
                                    ans = all_mock_answers[q.id][s['id']]
                                    inputs_by_student[s['id']] = {
                                        "question": q, "student_answer": ans,
                                        "rag_contexts": None if _rag_on else [],  # None=fetch, []=skip
                                        "correction_1": None, "correction_2": None, "correction_arbiter": None,
                                        "divergence_detected": False, "divergence_value": 0.0, "all_corrections": [], "final_score": None
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
                                        "question_id": str(q.id), "question_text": q.statement,
                                        "answer_text": inp['student_answer'].text,
                                        "grade": final_state.get('final_score', 0),
                                        "divergence": final_state.get('divergence_detected', False),
                                        "state": final_state
                                    })
                                    students_results_map[s_id]["total_grade"] += final_state.get('final_score', 0)

                                    # Save to experiment store
                                    if exp_id:
                                        student_name_for_exp = next(
                                            (s['name'] for s in students_list if s['id'] == s_id),
                                            f"Student_{s_id}"
                                        )
                                        exp_store.save_pipeline_state(
                                            exp_id, str(q.id), str(s_id),
                                            student_name_for_exp, final_state
                                        )

                                    # Track this submission in analytics
                                    from datetime import datetime

                                    # Extract criterion scores from corrections
                                    criterion_scores = {}
                                    all_corr = final_state.get('all_corrections', [])
                                    if all_corr:
                                        last_correction = all_corr[-1]
                                        if hasattr(last_correction, 'criterion_scores'):
                                            for crit in last_correction.criterion_scores:
                                                criterion_scores[crit.criterion] = crit.score

                                    submission_record = SubmissionRecord(
                                        submission_id=f"SUB_{s_id}_{q.id}_{datetime.now().timestamp()}",
                                        question_id=str(q.id),
                                        question_text=q.statement,
                                        student_answer=inp['student_answer'].text,
                                        grade=final_state.get('final_score', 0),
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

                            _perf_log.info(f"[STEP3] Q{q_idx+1} corrigida em {time.time()-_tq:.1f}s")
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
                        _perf_log.info(f"[STEP3] Correção completa em {time.time()-_t3:.1f}s")
                        # Finalize experiment
                        if exp_id:
                            exp_store.finish_experiment(exp_id, "completed")
                            _perf_log.info(f"[EXP-{exp_id}] Experiment completed and saved")
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
        tab_overview, tab_student, tab_class, tab_plagiarism = st.tabs([
            "📋 Visão Geral",
            "👤 Perfil do Aluno",
            "🏫 Análise da Turma",
            "🔍 Similaridade"
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

        with tab_plagiarism:
            render_plagiarism_dashboard(all_profiles)

elif operation_mode == "🔗 End-to-End (Backend API)":
    st.title("🔗 End-to-End via Backend API (QA1)")
    st.markdown("""
    Executa o fluxo completo via API REST do backend FastAPI, cobrindo **todas as etapas do QA1**:
    cadastrar → publicar → indexar → corrigir → persistir → revisar → aprovar → finalizar.
    """)

    # Backend connection
    api_url = st.text_input("URL do Backend", value="http://localhost:8000")
    client = get_api_client(api_url)

    # Health check
    col_health, col_login = st.columns(2)
    with col_health:
        if st.button("🏥 Health Check"):
            if client.health():
                st.success("Backend online!")
            else:
                st.error(f"Backend offline em {api_url}")

    # Login
    if 'api_logged_in' not in st.session_state:
        st.session_state['api_logged_in'] = False

    if not st.session_state['api_logged_in']:
        st.subheader("🔐 Login")
        with st.form("login_form"):
            email = st.text_input("Email", value="teacher@example.com")
            password = st.text_input("Senha", type="password")
            if st.form_submit_button("Entrar"):
                try:
                    result = client.login(email, password)
                    st.session_state['api_logged_in'] = True
                    st.session_state['api_user'] = result.get('user', {})
                    st.success(f"Logado como {result['user'].get('email', '?')}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro no login: {e}")
    else:
        user = st.session_state.get('api_user', {})
        st.success(f"Logado como **{user.get('first_name', '')} {user.get('last_name', '')}** ({user.get('email', '')})")
        if st.button("Logout"):
            st.session_state['api_logged_in'] = False
            st.session_state.pop('api_user', None)
            st.rerun()

        st.divider()

        # ─── Tabs: Criar Prova | Provas Existentes | Revisão ───
        tab_create, tab_list, tab_review = st.tabs(["📝 Criar Prova & Corrigir", "📋 Provas Existentes", "✅ Revisão Docente"])

        with tab_create:
            st.subheader("Criar Prova via API")

            exam_title = st.text_input("Título da Prova", value="Experimento TCC — Algoritmos")
            exam_desc = st.text_area("Descrição", value="Prova gerada via Streamlit para validação end-to-end", height=80)

            st.markdown("---")
            st.subheader("Questões")

            # Use questions from batch mode if available
            if 'exam_questions' in st.session_state:
                st.info(f"{len(st.session_state['exam_questions'])} questões disponíveis do modo Batch")
                use_batch = st.checkbox("Usar questões do modo Batch", value=True)
            else:
                use_batch = False
                st.warning("Gere questões no modo 'Batch Processing' primeiro, ou digite abaixo:")

            if not use_batch:
                num_qs = st.number_input("Número de questões", 1, 10, 3, key="api_num_qs")
                api_questions = []
                for i in range(num_qs):
                    q_text = st.text_area(f"Questão {i+1}", key=f"api_q_{i}", height=80)
                    api_questions.append({"statement": q_text, "points": 10.0})

            st.markdown("---")
            st.subheader("Respostas dos Alunos")

            if 'batch_all_mock_answers' in st.session_state and 'batch_students_list' in st.session_state:
                st.info(f"{len(st.session_state['batch_students_list'])} alunos com respostas disponíveis do modo Batch")
                use_batch_answers = st.checkbox("Usar respostas do modo Batch", value=True)
            else:
                use_batch_answers = False
                st.warning("Simule respostas no modo 'Batch Processing' primeiro")

            st.markdown("---")

            # Execute full flow
            if st.button("🚀 Executar Fluxo End-to-End", type="primary"):
                if use_batch and 'exam_questions' not in st.session_state:
                    st.error("Gere questões primeiro no modo Batch")
                else:
                    status = st.status("🔄 Executando fluxo end-to-end...", expanded=True)

                    try:
                        # Step 1: Create exam
                        status.write("**1/7** Criando prova...")
                        exam = client.create_exam(exam_title, exam_desc)
                        exam_uuid = exam['uuid']
                        status.write(f"✅ Prova criada: `{exam_uuid}`")

                        # Step 2: Add questions
                        if use_batch:
                            questions = st.session_state['exam_questions']
                            questions_data = [{"statement": q.statement, "points": getattr(q, 'total_points', 10.0)} for q in questions]
                        else:
                            questions_data = api_questions

                        status.write(f"**2/7** Adicionando {len(questions_data)} questões...")
                        created_qs = []
                        for i, qd in enumerate(questions_data):
                            q = client.add_question(exam_uuid, qd['statement'], qd.get('points', 10.0), i + 1)
                            created_qs.append(q)
                        status.write(f"✅ {len(created_qs)} questões adicionadas")

                        # Step 3: Add answers
                        status.write("**3/7** Inserindo respostas dos alunos...")
                        answer_count = 0
                        created_answers = []

                        if use_batch_answers:
                            students = st.session_state['batch_students_list']
                            all_answers = st.session_state['batch_all_mock_answers']

                            for q_idx, cq in enumerate(created_qs):
                                q_uuid = cq['uuid']
                                # Match by position (batch questions may have different UUIDs)
                                if use_batch:
                                    orig_q = questions[q_idx]
                                    orig_q_id = orig_q.id
                                    answers_for_q = all_answers.get(orig_q_id, all_answers.get(str(orig_q_id), {}))
                                else:
                                    answers_for_q = {}

                                for s_id, ans in answers_for_q.items():
                                    import uuid as _uuid
                                    student_uuid = str(_uuid.uuid5(_uuid.NAMESPACE_DNS, f"student_{s_id}"))
                                    try:
                                        a = client.add_answer(exam_uuid, q_uuid, student_uuid, ans.text)
                                        created_answers.append(a)
                                        answer_count += 1
                                    except Exception as e:
                                        status.write(f"⚠️ Erro ao inserir resposta: {e}")

                        status.write(f"✅ {answer_count} respostas inseridas")

                        # Step 4: Publish (triggers grading)
                        status.write("**4/7** Publicando prova (dispara correção automática)...")
                        pub = client.publish_exam(exam_uuid)
                        status.write(f"✅ Prova publicada! Correção em background...")

                        # Step 5: Wait for grading
                        status.write("**5/7** Aguardando correção automática...")
                        progress = st.progress(0)
                        max_wait = 300
                        start = time.time()
                        final_status = "TIMEOUT"

                        while time.time() - start < max_wait:
                            elapsed = time.time() - start
                            progress.progress(min(elapsed / max_wait, 0.99))
                            exam_data = client.get_exam(exam_uuid)
                            current_status = exam_data.get('status', '')
                            if current_status in ('GRADED', 'WARNING'):
                                final_status = current_status
                                progress.progress(1.0)
                                break
                            time.sleep(5)

                        if final_status == "TIMEOUT":
                            status.write("⚠️ Timeout aguardando correção (5 min)")
                        else:
                            status.write(f"✅ Correção concluída! Status: **{final_status}**")

                        # Step 6: Get review
                        status.write("**6/7** Obtendo resultados da revisão...")
                        try:
                            review = client.get_review(exam_uuid)
                            st.session_state['api_review'] = review
                            st.session_state['api_exam_uuid'] = exam_uuid

                            total_answers = sum(len(q.get('student_answers', [])) for q in review.get('questions', []))
                            status.write(f"✅ Revisão obtida: {total_answers} respostas corrigidas")
                        except Exception as e:
                            status.write(f"⚠️ Erro ao obter revisão: {e}")

                        # Step 7: Persistência
                        status.write("**7/7** Dados persistidos no banco de dados do backend ✅")

                        status.update(label="✅ Fluxo end-to-end completo!", state="complete")

                        # Save to experiment store
                        exp_id = exp_store.create_experiment({
                            'llm_provider': settings.LLM_PROVIDER,
                            'llm_model': settings.LLM_MODEL_NAME,
                            'mode': 'end-to-end (backend API)',
                            'exam_uuid': exam_uuid,
                            'final_status': final_status,
                            'num_questions': len(created_qs),
                            'num_answers': answer_count,
                        })
                        exp_store.finish_experiment(exp_id, "completed")
                        _perf_log.info(f"[QA1] End-to-end complete: exam={exam_uuid}, status={final_status}")

                    except Exception as e:
                        status.update(label="❌ Erro no fluxo", state="error")
                        st.error(f"Erro: {e}")
                        import traceback
                        st.code(traceback.format_exc())

        with tab_list:
            st.subheader("Provas no Backend")
            if st.button("🔄 Atualizar Lista"):
                try:
                    exams = client.list_exams()
                    st.session_state['api_exams'] = exams
                except Exception as e:
                    st.error(f"Erro: {e}")

            if 'api_exams' in st.session_state:
                for exam in st.session_state['api_exams']:
                    with st.expander(f"{exam.get('title', '?')} — {exam.get('status', '?')}"):
                        st.json(exam)
                        if st.button(f"Ver Revisão", key=f"rev_{exam['uuid']}"):
                            try:
                                review = client.get_review(exam['uuid'])
                                st.session_state['api_review'] = review
                                st.session_state['api_exam_uuid'] = exam['uuid']
                                st.success("Revisão carregada! Vá para aba 'Revisão Docente'")
                            except Exception as e:
                                st.error(f"Erro: {e}")

        with tab_review:
            st.subheader("Revisão Docente (QA1 — Etapa Final)")

            if 'api_review' not in st.session_state:
                st.info("Execute o fluxo end-to-end ou selecione uma prova existente primeiro")
            else:
                review = st.session_state['api_review']
                exam_uuid = st.session_state.get('api_exam_uuid', '?')

                st.markdown(f"**Prova:** {review.get('exam_title', '?')} | **Status:** {review.get('status', '?')}")
                st.markdown(f"**Turma:** {review.get('class_name', 'N/A')} | **Alunos:** {review.get('total_students', 0)} | **Questões:** {review.get('total_questions', 0)}")

                for q in review.get('questions', []):
                    with st.expander(f"Q{q.get('question_number', '?')}: {q.get('statement', '?')[:80]}..."):
                        for ans in q.get('student_answers', []):
                            col_info, col_actions = st.columns([3, 1])
                            with col_info:
                                st.markdown(f"**{ans.get('student_name', '?')}** — Nota: **{ans.get('score', 'N/A')}** | Status: `{ans.get('status', '?')}`")
                                st.caption(f"Resposta: {ans.get('answer_text', '')[:200]}...")

                                if ans.get('criteria_scores'):
                                    for cs in ans['criteria_scores']:
                                        st.caption(f"  • {cs.get('criterion_name', '?')}: {cs.get('raw_score', '?')}/{cs.get('max_score', '?')} — {cs.get('feedback', '')[:100]}")

                            with col_actions:
                                ans_uuid = ans.get('answer_uuid', '')
                                if ans.get('status') != 'APPROVED':
                                    if st.button("✅ Aprovar", key=f"approve_{ans_uuid}"):
                                        try:
                                            client.approve_answer(ans_uuid)
                                            st.success("Aprovada!")
                                            # Refresh
                                            st.session_state['api_review'] = client.get_review(exam_uuid)
                                            st.rerun()
                                        except Exception as e:
                                            st.error(str(e))
                                else:
                                    st.caption("✅ Aprovada")

                st.markdown("---")
                col_final, col_report = st.columns(2)
                with col_final:
                    if st.button("📋 Finalizar Revisão", type="primary"):
                        try:
                            result = client.finalize_review(exam_uuid)
                            st.success(f"Revisão finalizada! {result}")
                        except Exception as e:
                            st.error(f"Erro: {e}")

                with col_report:
                    if st.button("📥 Download Relatório"):
                        try:
                            path = f"tcc/results/report_{exam_uuid}.xlsx"
                            client.download_report(exam_uuid, path)
                            st.success(f"Relatório salvo em {path}")
                        except Exception as e:
                            st.error(f"Erro: {e}")

