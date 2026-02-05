import os
import json
import streamlit as st
from src.domain.schemas import (
    ExamQuestion, EvaluationCriterion, QuestionMetadata, 
    StudentAnswer, RetrievedContext, AgentCorrection
)

PERSISTENCE_FILE = "data/storage/exam_state.json"

def save_persistence_data():
    """Salva o estado atual (questões, respostas e resultados) em arquivo JSON."""
    data = {}
    
    # 1. Save Questions
    if 'exam_questions' in st.session_state:
        data['exam_questions'] = [q.model_dump() for q in st.session_state['exam_questions']]
    
    # 2. Save Batch Answers
    if 'batch_all_mock_answers' in st.session_state:
        # structure: {question_id: {student_id: answer_obj}}
        serialized_answers = {}
        for q_id, s_map in st.session_state['batch_all_mock_answers'].items():
            serialized_answers[q_id] = {s_id: ans.model_dump() for s_id, ans in s_map.items()}
        data['batch_all_mock_answers'] = serialized_answers
        
        if 'batch_students_list' in st.session_state:
            data['batch_students_list'] = st.session_state['batch_students_list']

    # 3. Save Results
    if 'exam_results' in st.session_state:
        # exam_results is a list of student summaries
        results_serialized = []
        for student_res in st.session_state['exam_results']:
            student_copy = student_res.copy()
            details_serialized = []
            
            for detail in student_res['details']:
                det_copy = detail.copy()
                state = detail['state'] # This is the GraphState dict
                
                # Manual serialization of the complex GraphState
                state_ser = {
                    "question": state['question'].model_dump(),
                    "student_answer": state['student_answer'].model_dump(),
                    "rag_context": [r.model_dump() for r in state['rag_context']],
                    "individual_corrections": [c.model_dump() for c in state.get('individual_corrections', [])],
                    "divergence_detected": state.get('divergence_detected'),
                    "divergence_value": state.get('divergence_value'),
                    "final_grade": state.get('final_grade'),
                    "processing_metadata": state.get('processing_metadata', {})
                }
                det_copy['state'] = state_ser
                details_serialized.append(det_copy)
            
            student_copy['details'] = details_serialized
            results_serialized.append(student_copy)
        
        data['exam_results'] = results_serialized
        
    try:
        if not os.path.exists("data/storage"):
            os.makedirs("data/storage")
            
        with open(PERSISTENCE_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        st.error(f"Erro ao salvar persistência: {e}")

def load_persistence_data():
    """Carrega dados do disco para o session_state se existirem."""
    if not os.path.exists(PERSISTENCE_FILE):
        return

    try:
        with open(PERSISTENCE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 1. Load Questions
        if 'exam_questions' in data and 'exam_questions' not in st.session_state:
            st.session_state['exam_questions'] = [ExamQuestion(**q) for q in data['exam_questions']]
            
        # 2. Load Batch Answers
        if 'batch_all_mock_answers' in data and 'batch_all_mock_answers' not in st.session_state:
            deserialized_answers = {}
            for q_id, s_map in data['batch_all_mock_answers'].items():
                deserialized_answers[q_id] = {int(s_id): StudentAnswer(**ans_dict) for s_id, ans_dict in s_map.items()}
            st.session_state['batch_all_mock_answers'] = deserialized_answers
        
        if 'batch_students_list' in data and 'batch_students_list' not in st.session_state:
            st.session_state['batch_students_list'] = data['batch_students_list']

        # 3. Load Results
        if 'exam_results' in data and 'exam_results' not in st.session_state:
            results_loaded = []
            for s_res in data['exam_results']:
                s_copy = s_res.copy()
                details_loaded = []
                for det in s_res['details']:
                    d_copy = det.copy()
                    state_raw = det['state']
                    
                    # Reconstruct objects
                    state_loaded = {
                        "question": ExamQuestion(**state_raw['question']),
                        "student_answer": StudentAnswer(**state_raw['student_answer']),
                        "rag_context": [RetrievedContext(**r) for r in state_raw['rag_context']],
                        "individual_corrections": [AgentCorrection(**c) for c in state_raw['individual_corrections']],
                        "divergence_detected": state_raw.get('divergence_detected'),
                        "divergence_value": state_raw.get('divergence_value'),
                        "final_grade": state_raw.get('final_grade'),
                        "processing_metadata": state_raw.get('processing_metadata', {})
                    }
                    d_copy['state'] = state_loaded
                    details_loaded.append(d_copy)
                
                s_copy['details'] = details_loaded
                results_loaded.append(s_copy)
            
            st.session_state['exam_results'] = results_loaded
            st.toast("Dados anteriores carregados com sucesso!", icon="💾")

    except Exception as e:
        st.error(f"Erro ao carregar dados salvos: {e}")
