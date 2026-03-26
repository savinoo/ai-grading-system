"""
API Client — Integração do Streamlit com o backend FastAPI.

Cobre o fluxo end-to-end do TCC (QA1):
  Login → Criar Prova → Questões → Respostas → Publicar → Revisar → Aprovar → Finalizar

Uso:
    client = get_api_client("http://localhost:8000")
    client.login("teacher@example.com", "password123")
    exam = client.create_exam("Prova TCC", "Algoritmos")
    client.add_question(exam['uuid'], "Explique árvores B+", 10.0, 1)
    client.publish_exam(exam['uuid'])
    review = client.get_review(exam['uuid'])
"""
import logging
import time

import requests
import streamlit as st

logger = logging.getLogger("api_client")


class APIClient:
    """HTTP client for the FastAPI backend."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.token = None
        self.user = None
        self._session = requests.Session()

    def _headers(self):
        h = {"Content-Type": "application/json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def _request(self, method, path, **kwargs):
        url = f"{self.base_url}{path}"
        kwargs.setdefault("headers", self._headers())
        kwargs.setdefault("timeout", 60)
        resp = self._session.request(method, url, **kwargs)
        if resp.status_code == 401:
            logger.warning("Token expirado, tentando refresh...")
            if self._refresh_token():
                kwargs["headers"] = self._headers()
                resp = self._session.request(method, url, **kwargs)
        return resp

    def _refresh_token(self):
        try:
            resp = self._session.post(
                f"{self.base_url}/auth/refresh",
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("access_token")
                return True
        except Exception:
            pass
        return False

    # ─── Health ───

    def health(self) -> bool:
        try:
            resp = self._session.get(f"{self.base_url}/health", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    # ─── Auth ───

    def login(self, email: str, password: str) -> dict:
        resp = self._session.post(
            f"{self.base_url}/auth/login",
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        self.token = data.get("access_token")
        # Response has user fields directly (not nested under "user")
        self.user = {
            "uuid": str(data.get("user_uuid", "")),
            "email": data.get("email", ""),
            "user_type": data.get("user_type", ""),
        }
        logger.info(f"Logged in as {self.user.get('email', '?')}")
        data['user'] = self.user  # normalize for consumers
        return data

    def get_me(self) -> dict:
        resp = self._request("GET", "/auth/me")
        resp.raise_for_status()
        return resp.json()

    # ─── Exams ───

    def create_exam(self, title: str, description: str = "", class_uuid: str = None) -> dict:
        body = {"title": title, "description": description}
        if class_uuid:
            body["class_uuid"] = class_uuid
        resp = self._request("POST", "/exams", json=body)
        resp.raise_for_status()
        logger.info(f"Exam created: {resp.json().get('uuid')}")
        return resp.json()

    def get_exam(self, exam_uuid: str) -> dict:
        resp = self._request("GET", f"/exams/{exam_uuid}")
        resp.raise_for_status()
        return resp.json()

    # ─── Classes & Students ───

    def create_class(self, name: str, description: str = "") -> dict:
        resp = self._request("POST", "/classes", json={
            "name": name,
            "description": description,
            "year": 2026,
            "semester": 1,
        })
        resp.raise_for_status()
        return resp.json()

    def add_students_to_class(self, class_uuid: str, students: list) -> dict:
        """Add students to class. Creates students if they don't exist.
        students: list of {"full_name": str, "email": str|None}
        """
        resp = self._request("POST", f"/classes/{class_uuid}/students", json={
            "students": students
        })
        resp.raise_for_status()
        return resp.json()

    def list_exams(self) -> list:
        if not self.user:
            return []
        teacher_uuid = self.user.get("uuid")
        resp = self._request("GET", f"/exams/teacher/{teacher_uuid}")
        resp.raise_for_status()
        return resp.json().get("exams", [])

    def publish_exam(self, exam_uuid: str) -> dict:
        resp = self._request("POST", f"/exams/{exam_uuid}/publish")
        resp.raise_for_status()
        logger.info(f"Exam published: {exam_uuid}")
        return resp.json()

    # ─── Questions ───

    def add_question(self, exam_uuid: str, statement: str, points: float = 10.0, order: int = 1) -> dict:
        resp = self._request("POST", "/exam-questions", json={
            "exam_uuid": exam_uuid,
            "statement": statement,
            "question_order": order,
            "points": points,
        })
        resp.raise_for_status()
        return resp.json()

    def list_questions(self, exam_uuid: str) -> list:
        resp = self._request("GET", f"/exam-questions/exam/{exam_uuid}")
        resp.raise_for_status()
        return resp.json()

    # ─── Student Answers ───

    def add_answer(self, exam_uuid: str, question_uuid: str, student_uuid: str, answer_text: str) -> dict:
        resp = self._request("POST", "/student-answers", json={
            "exam_uuid": exam_uuid,
            "question_uuid": question_uuid,
            "student_uuid": student_uuid,
            "answer_text": answer_text,
        })
        resp.raise_for_status()
        return resp.json()

    # ─── Reviews ───

    def get_review(self, exam_uuid: str) -> dict:
        resp = self._request("GET", f"/reviews/exams/{exam_uuid}")
        resp.raise_for_status()
        return resp.json()

    def approve_answer(self, answer_uuid: str) -> dict:
        resp = self._request("POST", f"/reviews/approve-answer/{answer_uuid}")
        resp.raise_for_status()
        return resp.json()

    def adjust_grade(self, answer_uuid: str, new_score: float, feedback: str = None) -> dict:
        body = {"answer_uuid": answer_uuid, "new_score": new_score}
        if feedback:
            body["feedback"] = feedback
        resp = self._request("PUT", "/reviews/grades/adjust", json=body)
        resp.raise_for_status()
        return resp.json()

    def finalize_review(self, exam_uuid: str) -> dict:
        resp = self._request("POST", "/reviews/finalize", json={
            "exam_uuid": exam_uuid,
            "send_notifications": False,
            "generate_pdf": False,
        })
        resp.raise_for_status()
        return resp.json()

    def download_report(self, exam_uuid: str, output_path: str) -> str:
        resp = self._request("GET", f"/reviews/exams/{exam_uuid}/report")
        resp.raise_for_status()
        with open(output_path, 'wb') as f:
            f.write(resp.content)
        logger.info(f"Report saved: {output_path}")
        return output_path

    # ─── Attachments ───

    def upload_attachment(self, exam_uuid: str, file_path: str) -> dict:
        with open(file_path, 'rb') as f:
            files = {"file": f}
            headers = {}
            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            resp = self._session.post(
                f"{self.base_url}/attachments/upload?exam_uuid={exam_uuid}",
                files=files,
                headers=headers,
                timeout=120
            )
        resp.raise_for_status()
        return resp.json()

    # ─── Full QA1 Flow ───

    def run_qa1_flow(self, title, questions_data, students_answers, status_callback=None):
        """
        Execute the full end-to-end flow (QA1) via backend API.

        Args:
            title: Exam title
            questions_data: List of {"statement": str, "points": float}
            students_answers: Dict of {question_idx: {student_uuid: answer_text}}
            status_callback: Function(step, message) for progress updates

        Returns:
            Dict with exam_uuid, review data, and step statuses
        """
        def log(step, msg):
            logger.info(f"[QA1-{step}] {msg}")
            if status_callback:
                status_callback(step, msg)

        result = {"steps": {}}

        # Step 1: Create exam
        log(1, "Criando prova...")
        exam = self.create_exam(title, f"Experimento TCC — {title}")
        exam_uuid = exam['uuid']
        result['exam_uuid'] = exam_uuid
        result['steps']['criar_prova'] = {"status": "OK", "uuid": exam_uuid}

        # Step 2: Add questions
        log(2, f"Adicionando {len(questions_data)} questões...")
        created_questions = []
        for i, qd in enumerate(questions_data):
            q = self.add_question(exam_uuid, qd['statement'], qd.get('points', 10.0), i + 1)
            created_questions.append(q)
        result['questions'] = created_questions
        result['steps']['questoes'] = {"status": "OK", "count": len(created_questions)}

        # Step 3: Add student answers
        log(3, "Inserindo respostas dos alunos...")
        created_answers = []
        for q_idx, q in enumerate(created_questions):
            q_uuid = q['uuid']
            answers_for_q = students_answers.get(q_idx, {})
            for s_uuid, answer_text in answers_for_q.items():
                ans = self.add_answer(exam_uuid, q_uuid, str(s_uuid), answer_text)
                created_answers.append(ans)
        result['answers'] = created_answers
        result['steps']['respostas'] = {"status": "OK", "count": len(created_answers)}

        # Step 4: Publish (triggers grading)
        log(4, "Publicando prova (dispara correção automática)...")
        pub = self.publish_exam(exam_uuid)
        result['steps']['publicacao'] = {"status": "OK", "response": pub}

        # Step 5: Wait for grading
        log(5, "Aguardando correção automática...")
        max_wait = 300  # 5 minutes
        start = time.time()
        while time.time() - start < max_wait:
            exam_status = self.get_exam(exam_uuid)
            status = exam_status.get('status', '')
            if status in ('GRADED', 'WARNING'):
                log(5, f"Correção concluída! Status: {status}")
                result['steps']['correcao'] = {"status": "OK", "exam_status": status}
                break
            time.sleep(5)
        else:
            result['steps']['correcao'] = {"status": "TIMEOUT", "waited": f"{max_wait}s"}

        # Step 6: Get review
        log(6, "Obtendo resultados da revisão...")
        try:
            review = self.get_review(exam_uuid)
            result['review'] = review
            result['steps']['revisao'] = {"status": "OK"}
        except Exception as e:
            result['steps']['revisao'] = {"status": "ERROR", "error": str(e)}

        return result


# ─── Singleton ───

_client = None


def get_api_client(base_url: str = None) -> APIClient:
    global _client
    if _client is None:
        url = base_url or "http://localhost:8000"
        _client = APIClient(url)
    return _client
