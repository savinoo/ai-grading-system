"""
Persistence — Save/load exam state to disk for session recovery.
Adapted for tcc architecture (GradingState with correction_1/correction_2 fields).
"""
import json
import os

import streamlit as st

from src.domain.ai.schemas import ExamQuestion, StudentAnswer
from src.domain.ai.agent_schemas import AgentCorrection
from src.domain.ai.rag_schemas import RetrievedContext

PERSISTENCE_FILE = "data/storage/exam_state.json"


def save_persistence_data():
    """Salva o estado atual (questões, respostas e resultados) em arquivo JSON."""
    data = {}

    if 'exam_questions' in st.session_state:
        data['exam_questions'] = [q.model_dump() for q in st.session_state['exam_questions']]

    if 'exam_results' in st.session_state:
        results_serialized = []
        for student_res in st.session_state['exam_results']:
            student_copy = student_res.copy()
            details_serialized = []

            for detail in student_res.get('details', []):
                det_copy = detail.copy()
                state = detail.get('state', {})

                state_ser = {
                    "question": state['question'].model_dump() if hasattr(state.get('question'), 'model_dump') else state.get('question'),
                    "student_answer": state['student_answer'].model_dump() if hasattr(state.get('student_answer'), 'model_dump') else state.get('student_answer'),
                    "rag_contexts": [r.model_dump() for r in (state.get('rag_contexts') or []) if hasattr(r, 'model_dump')],
                    "correction_1": state['correction_1'].model_dump() if state.get('correction_1') and hasattr(state['correction_1'], 'model_dump') else None,
                    "correction_2": state['correction_2'].model_dump() if state.get('correction_2') and hasattr(state['correction_2'], 'model_dump') else None,
                    "correction_arbiter": state['correction_arbiter'].model_dump() if state.get('correction_arbiter') and hasattr(state['correction_arbiter'], 'model_dump') else None,
                    "divergence_detected": state.get('divergence_detected'),
                    "divergence_value": state.get('divergence_value'),
                    "final_score": state.get('final_score'),
                }
                det_copy['state'] = state_ser
                details_serialized.append(det_copy)

            student_copy['details'] = details_serialized
            results_serialized.append(student_copy)

        data['exam_results'] = results_serialized

    try:
        os.makedirs("data/storage", exist_ok=True)
        with open(PERSISTENCE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    except Exception as e:
        st.error(f"Erro ao salvar persistência: {e}")


def load_persistence_data():
    """Carrega dados do disco para o session_state se existirem."""
    if not os.path.exists(PERSISTENCE_FILE):
        return

    try:
        with open(PERSISTENCE_FILE, encoding='utf-8') as f:
            data = json.load(f)

        if 'exam_questions' in data and 'exam_questions' not in st.session_state:
            st.session_state['exam_questions'] = [ExamQuestion(**q) for q in data['exam_questions']]

        if 'exam_results' in data and 'exam_results' not in st.session_state:
            results_loaded = []
            for s_res in data['exam_results']:
                s_copy = s_res.copy()
                details_loaded = []
                for det in s_res.get('details', []):
                    d_copy = det.copy()
                    state_raw = det.get('state', {})

                    state_loaded = {
                        "question": ExamQuestion(**state_raw['question']) if state_raw.get('question') else None,
                        "student_answer": StudentAnswer(**state_raw['student_answer']) if state_raw.get('student_answer') else None,
                        "rag_contexts": [RetrievedContext(**r) for r in (state_raw.get('rag_contexts') or [])],
                        "correction_1": AgentCorrection(**state_raw['correction_1']) if state_raw.get('correction_1') else None,
                        "correction_2": AgentCorrection(**state_raw['correction_2']) if state_raw.get('correction_2') else None,
                        "correction_arbiter": AgentCorrection(**state_raw['correction_arbiter']) if state_raw.get('correction_arbiter') else None,
                        "divergence_detected": state_raw.get('divergence_detected'),
                        "divergence_value": state_raw.get('divergence_value'),
                        "final_score": state_raw.get('final_score'),
                    }
                    d_copy['state'] = state_loaded
                    details_loaded.append(d_copy)

                s_copy['details'] = details_loaded
                results_loaded.append(s_copy)

            st.session_state['exam_results'] = results_loaded
            st.toast("Dados anteriores carregados com sucesso!", icon="💾")

    except Exception as e:
        st.error(f"Erro ao carregar dados salvos: {e}")
