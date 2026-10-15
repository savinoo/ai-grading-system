"""User-facing Streamlit flows on the actual historical reports."""

from pathlib import Path

from streamlit.testing.v1 import AppTest

DASHBOARD = Path(__file__).resolve().parents[1] / "evaluation" / "dashboard.py"


def metrics(app):
    return {item.label: item.value for item in app.metric}


def test_dashboard_keeps_qa4_cohorts_separate():
    app = AppTest.from_file(str(DASHBOARD), default_timeout=60).run()
    assert not app.exception
    assert metrics(app)["Correções no conjunto"] == "36"
    assert metrics(app)["Casos distintos"] == "12"
    assert metrics(app)["Maior amplitude entre runs"] == "0.625 pts"
    assert metrics(app)["Referência humana"] == "Indisponível"
    app.selectbox(key="cohort").select("QA4 · notebook Q2 (12 correções)").run()
    assert not app.exception
    assert metrics(app)["Correções no conjunto"] == "12"
    assert metrics(app)["Casos distintos"] == "4"
    assert metrics(app)["Maior amplitude entre runs"] == "1.370 pts"
    assert any("Separate implementation" in item.value for item in app.info)


def test_dashboard_exposes_actual_contexts_and_threshold_simulation():
    app = AppTest.from_file(str(DASHBOARD), default_timeout=60).run()
    assert not app.exception
    assert metrics(app)["Encaminhamentos simulados"] == "3 / 36"
    app.select_slider[0].set_value(2.0).run()
    assert metrics(app)["Encaminhamentos simulados"] == "0 / 36"
    app.selectbox(key="rag_comparison").select("notebook_ab").run()
    assert not app.exception
    assert len(app.text) >= 4
    assert any("SHA" in item.value for item in app.caption)
    assert any("Nenhuma comparação histórica" in item.value for item in app.warning)
    assert metrics(app)["Benefício contra humanos"] == "Indisponível"
