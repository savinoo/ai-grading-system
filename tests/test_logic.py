import unittest
from unittest.mock import MagicMock
from src.domain.schemas import AgentID, CorrectionResult
from src.workflow.nodes import calculate_divergence_node, finalize_grade_node
from src.config.settings import settings

class TestGradingLogic(unittest.TestCase):

    def setUp(self):
        # Configurar threshold padrão para testes
        settings.DIVERGENCE_THRESHOLD = 1.5

    def create_mock_state(self, scores):
        corrections = []
        for i, score in enumerate(scores):
            mock_correction = MagicMock(spec=CorrectionResult)
            mock_correction.total_score = score
            # Atribuir IDs baseados na ordem (0=C1, 1=C2, 2=Arbiter)
            if i == 0:
                mock_correction.agent_id = AgentID.CORRETOR_1
            elif i == 1:
                mock_correction.agent_id = AgentID.CORRETOR_2
            else:
                mock_correction.agent_id = AgentID.ARBITER
            corrections.append(mock_correction)
        
        return {"individual_corrections": corrections}

    def test_divergence_detection_true(self):
        """Teste: Divergência deve ser detectada se diff > threshold"""
        state = self.create_mock_state([5.0, 7.0]) # Diff 2.0 > 1.5
        result = calculate_divergence_node(state)
        self.assertTrue(result["divergence_detected"])
        self.assertAlmostEqual(result["divergence_value"], 2.0)

    def test_divergence_detection_false(self):
        """Teste: Divergência NÃO deve ser detectada se diff <= threshold"""
        state = self.create_mock_state([5.0, 6.0]) # Diff 1.0 < 1.5
        result = calculate_divergence_node(state)
        self.assertFalse(result["divergence_detected"])
        self.assertAlmostEqual(result["divergence_value"], 1.0)

    def test_consensus_simple_mean(self):
        """Teste: Média simples quando há apenas 2 notas"""
        state = self.create_mock_state([6.0, 8.0])
        result = finalize_grade_node(state)
        self.assertAlmostEqual(result["final_grade"], 7.0)

    def test_consensus_advanced_closest_high(self):
        """Teste: Média dos dois maiores quando C3 está mais próximo de C2"""
        # C1=3.0, C2=7.0, C3=8.0
        # Diff(3,7)=4, Diff(7,8)=1 -> Deve escolher 7 e 8
        state = self.create_mock_state([3.0, 7.0, 8.0])
        result = finalize_grade_node(state)
        self.assertAlmostEqual(result["final_grade"], 7.5)

    def test_consensus_advanced_closest_low(self):
        """Teste: Média dos dois menores quando C3 está mais próximo de C1"""
        # C1=4.0, C2=8.0, C3=4.5
        # Ordenado: 4.0, 4.5, 8.0
        # Diff(4, 4.5)=0.5, Diff(4.5, 8)=3.5 -> Deve escolher 4 e 4.5
        state = self.create_mock_state([4.0, 8.0, 4.5])
        result = finalize_grade_node(state)
        self.assertAlmostEqual(result["final_grade"], 4.25)

if __name__ == '__main__':
    unittest.main()
