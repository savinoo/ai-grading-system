"""
Experimento TCC — Correção Automatizada com IA
Executa setup completo: turma, alunos, prova, questões, critérios, respostas.
Depois publica para acionar correção automática.
"""
import httpx, json, sys, uuid, time
from pathlib import Path
from datetime import datetime, timezone
import bcrypt
from sqlalchemy import create_engine, text

BASE = "http://localhost:8000"
DB_URL = "postgresql://gradinguser:gradingpass@localhost:5432/gradingdb"
client = httpx.Client(base_url=BASE, timeout=120)
engine = create_engine(DB_URL)
RESULTS_FILE = Path("tcc/experiment-results.json")

results = {"config": {}, "condition_a": [], "condition_b": [], "stability": []}


def log(msg):
    print(f"[EXP] {msg}")


def api(method, path, **kwargs):
    r = getattr(client, method)(path, **kwargs)
    return r


# ============================================================
# AUTH
# ============================================================
log("=== Login ===")
r = api("post", "/auth/login", json={"email": "prof.tcc@teste.com", "password": "Teste123!"})
assert r.status_code == 200, f"Login failed: {r.text}"
tokens = r.json()
access_token = tokens["access_token"]
teacher_uuid = tokens["user_uuid"]
headers = {"Authorization": f"Bearer {access_token}"}
log(f"  teacher: {teacher_uuid}")

# ============================================================
# TURMA
# ============================================================
log("\n=== Criando turma ===")
r = api("post", "/classes", json={
    "name": "TCC-2026-Experimento",
    "description": "Turma para experimentos do TCC"
}, headers=headers)
assert r.status_code in (200, 201), f"Turma failed: {r.text}"
class_uuid = r.json().get("uuid") or r.json().get("class_uuid")
log(f"  class_uuid: {class_uuid}")

# ============================================================
# ALUNOS (criar 4 direto no banco + associar à turma)
# ============================================================
log("\n=== Criando alunos ===")
LEVELS = ["excelente", "adequada", "fraca", "fora_tema"]
LEVEL_NAMES = {"excelente": "Excelente", "adequada": "Adequada", "fraca": "Fraca", "fora_tema": "Fora do Tema"}
student_uuids = {}

with engine.connect() as conn:
    for level in LEVELS:
        s_uuid = str(uuid.uuid4())
        s_name = f"Aluno {LEVEL_NAMES[level]}"
        s_email = f"aluno.{level}@teste.com"

        # Check if exists
        ex = conn.execute(text("SELECT uuid FROM students WHERE email = :e"), {"e": s_email}).fetchone()
        if ex:
            s_uuid = str(ex[0])
            log(f"  {s_name}: exists ({s_uuid})")
        else:
            conn.execute(text("""
                INSERT INTO students (uuid, full_name, email, active, created_at, updated_at)
                VALUES (:uuid, :name, :email, true, :now, :now)
            """), {"uuid": s_uuid, "name": s_name, "email": s_email, "now": datetime.now(timezone.utc)})
            log(f"  {s_name}: created ({s_uuid})")

        student_uuids[level] = s_uuid
    conn.commit()

# Associar alunos à turma via API
for level, s_uuid in student_uuids.items():
    r = api("post", f"/classes/{class_uuid}/students", json={"student_uuid": s_uuid}, headers=headers)
    log(f"  Associar {level} à turma: {r.status_code}")

# ============================================================
# PROVA
# ============================================================
log("\n=== Criando prova ===")
r = api("post", "/exams", json={
    "title": "Avaliação - Inteligência Artificial na Educação",
    "description": "Prova discursiva sobre IA aplicada ao contexto educacional",
    "class_uuid": class_uuid,
}, headers=headers)
assert r.status_code in (200, 201), f"Prova failed: {r.text}"
exam_data = r.json()
exam_uuid = exam_data.get("uuid") or exam_data.get("exam_uuid")
log(f"  exam_uuid: {exam_uuid}")

# ============================================================
# CRITÉRIOS
# ============================================================
log("\n=== Associando critérios ===")
r = api("get", "/grading-criteria", headers=headers)
catalog = {c["code"]: c for c in r.json()} if r.status_code == 200 else {}

CRITERIA_MAP = [
    {"catalog_code": "CORRECAO_TECNICA", "weight": 0.30, "max_points": 10.0},
    {"catalog_code": "COMPLETUDE", "weight": 0.25, "max_points": 10.0},
    {"catalog_code": "CLAREZA", "weight": 0.25, "max_points": 10.0},
    {"catalog_code": "ADEQUACAO_ENUNCIADO", "weight": 0.20, "max_points": 10.0},
]

exam_criteria_uuids = []
for cm in CRITERIA_MAP:
    cat = catalog.get(cm["catalog_code"])
    if not cat:
        log(f"  WARN: {cm['catalog_code']} not in catalog, skipping")
        continue
    crit_uuid = cat.get("uuid") or cat.get("criteria_uuid")
    r = api("post", "/exam-criteria", json={
        "exam_uuid": exam_uuid,
        "criteria_uuid": crit_uuid,
        "weight": cm["weight"],
        "max_points": cm["max_points"],
    }, headers=headers)
    if r.status_code in (200, 201):
        ec = r.json()
        exam_criteria_uuids.append(ec.get("uuid") or ec.get("exam_criteria_uuid"))
        log(f"  {cm['catalog_code']}: OK (peso={cm['weight']})")
    else:
        log(f"  {cm['catalog_code']}: FAIL {r.status_code} - {r.text[:200]}")

# ============================================================
# QUESTÕES
# ============================================================
log("\n=== Criando questões ===")
QUESTIONS = [
    "Explique o conceito de Retrieval-Augmented Generation (RAG) e como essa técnica pode ser aplicada em sistemas educacionais para melhorar a qualidade de respostas geradas por modelos de linguagem.",
    "Descreva o funcionamento de um sistema multiagente para correção automatizada de provas discursivas. Quais são as vantagens de utilizar múltiplos agentes em comparação com um único modelo avaliador?",
    "Discuta as limitações e os desafios éticos do uso de inteligência artificial para avaliação de respostas discursivas em contextos acadêmicos. Como o papel do professor pode ser preservado nesse cenário?",
]

question_uuids = []
for i, stmt in enumerate(QUESTIONS, 1):
    r = api("post", "/exam-questions", json={
        "exam_uuid": exam_uuid,
        "statement": stmt,
        "question_order": i,
        "points": 10.0,
    }, headers=headers)
    if r.status_code in (200, 201):
        q = r.json()
        quuid = q.get("uuid") or q.get("question_uuid")
        question_uuids.append(quuid)
        log(f"  Q{i}: {quuid}")
    else:
        log(f"  Q{i} FAIL: {r.text[:200]}")

# ============================================================
# RESPOSTAS SINTÉTICAS
# ============================================================
log("\n=== Inserindo respostas ===")

ANSWERS = {
    1: {
        "excelente": "O Retrieval-Augmented Generation (RAG) é uma técnica que combina a capacidade generativa de modelos de linguagem (LLMs) com a recuperação de informações relevantes de bases de dados externas. O processo funciona em três etapas: primeiro, a consulta do usuário é convertida em um vetor de embeddings; segundo, esse vetor é utilizado para buscar documentos similares em uma base vetorial (como ChromaDB ou FAISS); terceiro, os trechos recuperados são incluídos no prompt enviado ao LLM, fornecendo contexto factual para a geração da resposta. Em sistemas educacionais, o RAG pode ser aplicado para personalizar o feedback ao aluno, ancorando as avaliações no material didático específico da disciplina. Por exemplo, ao corrigir uma prova discursiva, o sistema pode recuperar trechos do livro-texto ou das notas de aula para verificar se a resposta do aluno está alinhada com o conteúdo ensinado. Isso reduz alucinações do modelo e aumenta a rastreabilidade da avaliação.",
        "adequada": "RAG é uma técnica que usa recuperação de documentos para complementar as respostas de um modelo de linguagem. O sistema busca textos relevantes em uma base de dados e passa para o LLM junto com a pergunta. Na educação, isso pode ser usado para fazer o modelo dar respostas mais baseadas no conteúdo do curso, em vez de inventar informações.",
        "fraca": "RAG é quando a inteligência artificial busca coisas na internet para responder melhor. Isso pode ser usado na educação para ajudar os alunos.",
        "fora_tema": "A inteligência artificial tem avançado muito nos últimos anos, especialmente com o surgimento do ChatGPT. Empresas como Google e OpenAI investem bilhões nessa tecnologia. O mercado de trabalho está sendo transformado e muitas profissões podem ser substituídas.",
    },
    2: {
        "excelente": "Um sistema multiagente para correção automatizada utiliza múltiplos agentes de IA que avaliam a mesma resposta de forma independente. Na arquitetura típica, dois corretores primários (C1 e C2) analisam a resposta contra uma rubrica predefinida, produzindo notas por critério e justificativas textuais. Após a avaliação independente, um mecanismo de verificação de divergência calcula a diferença absoluta entre as notas. Se a divergência ultrapassa um limiar configurado, um terceiro agente árbitro é acionado. A nota final é calculada por consenso: com duas avaliações, média simples; com três, média das duas mais próximas. As vantagens incluem: robustez, detecção de inconsistências, auditabilidade via Chain-of-Thought e reprodutibilidade do pipeline.",
        "adequada": "Um sistema multiagente usa vários agentes de IA que corrigem a mesma resposta separadamente. Cada um dá sua nota e justificativa, e depois o sistema compara. Se houver muita diferença, um terceiro corretor desempata. É mais confiável que usar apenas um.",
        "fraca": "Sistema multiagente é quando tem vários robôs corrigindo a prova. É melhor que um só porque dois é melhor que um.",
        "fora_tema": "Os sistemas operacionais modernos utilizam arquiteturas multiprocessadas. O Linux implementa escalonamento com algoritmos como Round Robin e CFS. A comunicação entre processos pode ser feita via pipes, sockets ou memória compartilhada.",
    },
    3: {
        "excelente": "O uso de IA para avaliação de respostas discursivas apresenta limitações técnicas e desafios éticos. Tecnicamente, LLMs podem apresentar viés em relação a estilos de escrita e vocabulário, potencialmente desfavorecendo alunos com diferentes backgrounds. Além disso, operam por correlações estatísticas, podendo falhar em avaliar raciocínios originais. A reprodutibilidade também é um desafio. Eticamente, há questões sobre transparência, privacidade dos dados acadêmicos e o risco de automatizar decisões com impacto educacional. O papel do professor pode ser preservado posicionando a IA como ferramenta de apoio: o sistema gera avaliação inicial estruturada que o docente revisa, ajusta e aprova antes da consolidação. Isso mantém a autoridade pedagógica enquanto reduz o esforço operacional.",
        "adequada": "As limitações incluem o viés dos modelos de IA e a dificuldade de avaliar respostas criativas. Eticamente, é questionável usar IA para decidir notas. O professor deve continuar como decisor final, usando a IA apenas como ferramenta auxiliar.",
        "fraca": "IA tem problemas porque pode errar e não é justo usar robô para dar nota. O professor deveria corrigir tudo sozinho.",
        "fora_tema": "A ética na ciência da computação abrange privacidade de dados até impacto ambiental dos data centers. A LGPD no Brasil estabelece regras para tratamento de dados pessoais. O GDPR na Europa é semelhante.",
    },
}

answer_map = {}
for q_idx, q_uuid in enumerate(question_uuids, 1):
    for level in LEVELS:
        s_uuid = student_uuids[level]
        text_answer = ANSWERS[q_idx][level]
        r = api("post", "/student-answers", json={
            "exam_uuid": exam_uuid,
            "question_uuid": q_uuid,
            "student_uuid": s_uuid,
            "answer_text": text_answer,
        }, headers=headers)
        if r.status_code in (200, 201):
            a = r.json()
            a_uuid = a.get("uuid") or a.get("answer_uuid")
            answer_map[(q_idx, level)] = a_uuid
            log(f"  Q{q_idx}/{LEVEL_NAMES[level]}: {a_uuid}")
        else:
            log(f"  Q{q_idx}/{LEVEL_NAMES[level]} FAIL: {r.text[:200]}")

log(f"\nTotal: {len(answer_map)}/12 respostas inseridas")

# ============================================================
# SAVE CONFIG
# ============================================================
results["config"] = {
    "exam_uuid": exam_uuid,
    "class_uuid": class_uuid,
    "teacher_uuid": teacher_uuid,
    "question_uuids": question_uuids,
    "answer_map": {f"Q{k[0]}_{k[1]}": v for k, v in answer_map.items()},
    "student_uuids": student_uuids,
    "exam_criteria_uuids": exam_criteria_uuids,
    "llm_provider": "groq",
    "llm_model": "llama-3.3-70b-versatile",
    "llm_temperature": 0.0,
    "embedding_provider": "ollama/nomic-embed-text",
    "divergence_threshold": 2.0,
    "rag_top_k": 4,
    "timestamp": datetime.now(timezone.utc).isoformat(),
}

RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
RESULTS_FILE.write_text(json.dumps(results, indent=2, ensure_ascii=False))

log("\n" + "=" * 60)
log("SETUP COMPLETO")
log("=" * 60)
log(f"  Prova: {exam_uuid}")
log(f"  Questões: {len(question_uuids)}")
log(f"  Respostas: {len(answer_map)}")
log(f"  Critérios: {len(exam_criteria_uuids)}")

if len(answer_map) == 12 and len(question_uuids) == 3 and len(exam_criteria_uuids) >= 3:
    log("\n=== Publicando prova (aciona correção automática) ===")
    r = api("post", f"/exams/{exam_uuid}/publish", headers=headers)
    log(f"  Publish: {r.status_code}")
    if r.status_code in (200, 201):
        log(f"  {r.json()}")
        log("\n  Correção em background iniciada!")
        log("  Aguardando processamento...")

        # Poll status
        for attempt in range(30):
            time.sleep(10)
            r = api("get", f"/exams/{exam_uuid}", headers=headers)
            if r.status_code == 200:
                exam_status = r.json().get("status", "?")
                log(f"  [{attempt+1}/30] Status: {exam_status}")
                if exam_status in ("GRADED", "WARNING", "FINALIZED"):
                    log(f"\n  Correção concluída! Status: {exam_status}")
                    break
            else:
                log(f"  [{attempt+1}/30] Check failed: {r.status_code}")

        # Collect results
        log("\n=== Coletando resultados ===")
        r = api("get", f"/reviews/exams/{exam_uuid}", headers=headers)
        if r.status_code == 200:
            review_data = r.json()
            RESULTS_FILE.write_text(json.dumps({
                **results,
                "review": review_data,
            }, indent=2, ensure_ascii=False, default=str))
            log(f"  Resultados salvos em {RESULTS_FILE}")
        else:
            log(f"  Review failed: {r.status_code} - {r.text[:200]}")
    else:
        log(f"  FAIL: {r.text[:300]}")
else:
    log("\n  Setup incompleto, não publicando.")
