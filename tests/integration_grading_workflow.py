"""Real LangGraph + SQLite integration with deterministic external-provider doubles.

Run with pytest after installing requirements-dev.txt. No provider credential,
network call, model metric, latency benchmark or human annotation is involved.
The stdlib-only regression workflow intentionally discovers test_*.py separately.
"""

import asyncio
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch
from uuid import UUID

# Configuration required by the production settings schema; values are test-only.
# No .env file or credential is needed or written by these tests.
with patch.dict(
    os.environ,
    {
        "DATABASE_URL": "postgresql://offline:offline@localhost/offline",
        "SECRET_KEY": "offline-integration-fixture-key",
        "BREVO_API_KEY": "offline-fixture",
        "BREVO_VERIFICATION_TEMPLATE_ID": "1",
        "BREVO_RECOVERY_CODE_TEMPLATE_ID": "2",
        "LANGSMITH_TRACING_ENABLED": "false",
    },
):
    from src.core.settings import settings
    from src.domain.ai.agent_schemas import AgentCorrection, AgentID, CriterionScore
    from src.domain.ai.rag_schemas import RetrievedContext
    from src.domain.ai.schemas import (
        EvaluationCriterion,
        ExamQuestion,
        QuestionMetadata,
        StudentAnswer,
    )
    from src.domain.ai.workflow.graph import create_grading_graph

from app.experiment_store import ExperimentStore


def correction(agent_id, score):
    return AgentCorrection(
        agent_id=agent_id,
        total_score=score,
        reasoning_chain="Synthetic integration fixture: the response is scored against one criterion.",
        criteria_scores=[CriterionScore(criterion="Correctness", score=score, max_score=10)],
        feedback_text="Synthetic deterministic provider response.",
    )


def initial_state(contexts):
    question_id = UUID(int=1)
    return {
        "exam_uuid": UUID(int=2),
        "question": ExamQuestion(
            id=question_id,
            statement="Explain the binary search tree ordering invariant.",
            rubric=[
                EvaluationCriterion(name="Correctness", description="States ordering invariant")
            ],
            metadata=QuestionMetadata(discipline="Computer Science", topic="Search trees"),
        ),
        "student_answer": StudentAnswer(
            student_id=UUID(int=3),
            question_id=question_id,
            text="Left keys are smaller and right keys are larger at every node.",
        ),
        "rag_contexts": contexts,
        "correction_1": None,
        "correction_2": None,
        "correction_arbiter": None,
        "divergence_detected": False,
        "divergence_value": None,
        "all_corrections": [],
        "final_score": None,
        "error": None,
        "processing_metadata": None,
    }


class GradingWorkflowIntegration(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.enterContext(
            patch.dict(
                os.environ,
                {
                    "LANGSMITH_TRACING": "false",
                    "LANGSMITH_TRACING_V2": "false",
                    "LANGCHAIN_TRACING_V2": "false",
                },
            )
        )

    async def run_workflow(self, c1_score, c2_score, arbiter_score=8, contexts=None):
        calls = []

        async def examine(**kwargs):
            calls.append(kwargs)
            # Yield to exercise both real parallel LangGraph branches.
            await asyncio.sleep(0)
            agent_id = kwargs["agent_id"]
            score = c1_score if agent_id == AgentID.CORRETOR_1 else c2_score
            return correction(agent_id, score)

        examiner = Mock(evaluate=AsyncMock(side_effect=examine))
        arbiter = Mock(evaluate=AsyncMock(return_value=correction(AgentID.ARBITER, arbiter_score)))
        retrieved = [
            RetrievedContext(
                content="At every node, all left keys precede the node and all right keys follow it.",
                source_document="synthetic_reference.txt",
                page_number=1,
                chunk_index=0,
                relevance_score=0.9,
                discipline="Computer Science",
                topic="Search trees",
            )
        ]
        retriever = Mock(search_context=AsyncMock(return_value=retrieved))
        prefix = "src.domain.ai.workflow.nodes"
        with (
            patch.object(settings, "DIVERGENCE_THRESHOLD", 2.0),
            patch(f"{prefix}._create_examiner_agent", return_value=examiner),
            patch(f"{prefix}._create_arbiter_agent", return_value=arbiter),
            patch(f"{prefix}._create_retrieval_service", return_value=retriever),
        ):
            state = initial_state(contexts)
            result = await create_grading_graph().ainvoke(state)
        self.assertEqual(examiner.evaluate.await_count, 2)
        self.assertCountEqual([call["agent_id"] for call in calls], list(AgentID)[:2])
        return state, result, calls, retriever, arbiter

    async def test_retrieval_parallel_agents_consensus_and_sqlite_export(self):
        state, result, calls, retriever, arbiter = await self.run_workflow(7, 9)
        # Equality at the configured threshold must not call the arbiter.
        self.assertFalse(result["divergence_detected"])
        self.assertEqual(result["divergence_value"], 2)
        self.assertEqual(result["final_score"], 8)
        self.assertEqual(len(result["all_corrections"]), 2)
        arbiter.evaluate.assert_not_awaited()
        retriever.search_context.assert_awaited_once_with(
            query=state["question"].statement,
            exam_uuid=state["exam_uuid"],
            discipline="Computer Science",
            topic="Search trees",
        )
        for call in calls:
            self.assertEqual(call["rag_contexts"], result["rag_contexts"])
        metadata = result["processing_metadata"]
        self.assertEqual(metadata["retrieval_status"], "completed")
        self.assertEqual(metadata["retrieval_context_count"], 1)
        self.assertGreaterEqual(metadata["retrieval_elapsed_ms"], 0)

        with tempfile.TemporaryDirectory() as tmp:
            store = ExperimentStore(str(Path(tmp) / "integration.sqlite"))
            experiment_id = store.create_experiment({"evidence_type": "synthetic_integration"})
            question_id = state["question"].id
            student_id = state["student_answer"].student_id
            store.save_question(experiment_id, state["question"])
            store.save_answer(
                experiment_id,
                question_id,
                student_id,
                "anonymous-fixture",
                state["student_answer"].text,
            )
            for item in result["all_corrections"]:
                role = item.agent_id.value if isinstance(item.agent_id, AgentID) else item.agent_id
                store.save_correction(experiment_id, question_id, student_id, item, role)
            store.save_rag_contexts(experiment_id, question_id, student_id, result["rag_contexts"])
            store.save_result(experiment_id, question_id, student_id, result)
            store.finish_experiment(experiment_id)
            exported = store.export_experiment(experiment_id)
            store.conn.close()
        self.assertEqual(exported["results"][0]["final_score"], 8)
        self.assertEqual(exported["results"][0]["processing_metadata"], metadata)
        self.assertEqual(
            exported["rag_contexts"][0]["chunk_content"], result["rag_contexts"][0].content
        )
        self.assertEqual(len(exported["corrections"][0]["criterion_scores"]), 1)
        self.assertEqual(exported["answers"][0]["answer_text"], state["student_answer"].text)

    async def test_divergent_pair_routes_to_arbiter_then_closest_pair(self):
        _, result, _, retriever, arbiter = await self.run_workflow(
            2, 8, arbiter_score=9, contexts=[]
        )
        self.assertTrue(result["divergence_detected"])
        self.assertEqual(result["divergence_value"], 6)
        self.assertEqual(result["final_score"], 8.5)
        self.assertEqual(len(result["all_corrections"]), 3)
        arbiter.evaluate.assert_awaited_once()
        self.assertEqual(arbiter.evaluate.await_args.kwargs["correction_1"].total_score, 2)
        self.assertEqual(arbiter.evaluate.await_args.kwargs["correction_2"].total_score, 8)
        retriever.search_context.assert_not_awaited()
        self.assertEqual(result["processing_metadata"]["retrieval_status"], "preprovided")
        self.assertEqual(result["processing_metadata"]["retrieval_context_count"], 0)

    async def test_preprovided_nonempty_context_bypasses_external_retrieval(self):
        context = RetrievedContext(
            content="Synthetic explicit context.",
            source_document="fixture.txt",
            relevance_score=1,
            discipline="Computer Science",
            topic="Search trees",
        )
        _, result, calls, retriever, _ = await self.run_workflow(8, 8, contexts=[context])
        retriever.search_context.assert_not_awaited()
        self.assertEqual(result["rag_contexts"], [context])
        self.assertTrue(all(call["rag_contexts"] == [context] for call in calls))
        self.assertEqual(result["processing_metadata"]["retrieval_context_count"], 1)

    async def test_provider_error_propagates_instead_of_fabricating_grade(self):
        prefix = "src.domain.ai.workflow.nodes"
        examiner = Mock(evaluate=AsyncMock(side_effect=RuntimeError("synthetic provider failure")))
        with patch(f"{prefix}._create_examiner_agent", return_value=examiner):
            with self.assertRaisesRegex(RuntimeError, "synthetic provider failure"):
                await create_grading_graph().ainvoke(initial_state([]))

    async def test_real_agents_render_prompts_and_use_structured_model_output(self):
        from langchain_core.runnables import RunnableLambda

        from src.services.agents.arbiter_agent import ArbiterAgent
        from src.services.agents.examiner_agent import ExaminerAgent

        examiner_prompts = []
        arbiter_prompts = []

        def examiner_response(prompt):
            rendered = prompt.to_string()
            examiner_prompts.append(rendered)
            if "AgentID.CORRETOR_1" in rendered:
                return correction(None, 2)
            self.assertIn("AgentID.CORRETOR_2", rendered)
            return correction(None, 8)

        def arbiter_response(prompt):
            rendered = prompt.to_string()
            arbiter_prompts.append(rendered)
            self.assertIn("Corretor 1 deu a nota: 2.0", rendered)
            self.assertIn("Corretor 2 deu a nota: 8.0", rendered)
            self.assertIn("Synthetic integration fixture", rendered)
            return correction(None, 9)

        examiner_model = Mock()
        examiner_model.with_structured_output.return_value = RunnableLambda(examiner_response)
        arbiter_model = Mock()
        arbiter_model.with_structured_output.return_value = RunnableLambda(arbiter_response)
        context = RetrievedContext(
            content="Synthetic context proving that prompt formatting passes retrieval evidence.",
            source_document="fixture-context.txt",
            relevance_score=1,
            discipline="Computer Science",
            topic="Search trees",
        )
        prefix = "src.domain.ai.workflow.nodes"
        with (
            patch("src.services.agents.examiner_agent.get_chat_model", return_value=examiner_model),
            patch("src.services.agents.arbiter_agent.get_chat_model", return_value=arbiter_model),
            patch(f"{prefix}._create_examiner_agent", side_effect=ExaminerAgent),
            patch(f"{prefix}._create_arbiter_agent", side_effect=ArbiterAgent),
            patch.object(settings, "DIVERGENCE_THRESHOLD", 2.0),
        ):
            result = await create_grading_graph().ainvoke(initial_state([context]))
        self.assertEqual(result["final_score"], 8.5)
        self.assertEqual(len(examiner_prompts), 2)
        self.assertEqual(len(arbiter_prompts), 1)
        for prompt in examiner_prompts + arbiter_prompts:
            self.assertIn("Explain the binary search tree ordering invariant.", prompt)
            self.assertIn("Left keys are smaller", prompt)
            self.assertIn("Correctness", prompt)
            self.assertIn(context.content, prompt)
        self.assertEqual(examiner_model.with_structured_output.call_count, 2)
        examiner_model.with_structured_output.assert_called_with(AgentCorrection)
        arbiter_model.with_structured_output.assert_called_once_with(AgentCorrection)
        self.assertEqual(result["correction_1"].agent_id, AgentID.CORRETOR_1)
        self.assertEqual(result["correction_2"].agent_id, AgentID.CORRETOR_2)
        self.assertEqual(result["correction_arbiter"].agent_id, AgentID.ARBITER)
