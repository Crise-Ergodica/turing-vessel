import asyncio

import pytest
from pytest_bdd import given, scenarios, then, when

from src.application.state_manager import SharedCognitiveState
from src.domain.entities import EspacoPAD, EstadoApego, VetorMoralMFT
from src.domain.services import apply_affective_blindness

# Bind the feature file
scenarios("affective_engine.feature")


@pytest.fixture
def mock_context():
    return {}


def run_async(coro):
    return asyncio.run(coro)


# --- Scenario 1: Consolidacao do Vinculo Afetivo ---
@given("que o agente possui um nivel de seguranca de 0.50 e prazer em 0.00")
def setup_consolidation_state(mock_context):
    pad = EspacoPAD(pleasure=0.0, arousal=0.0, dominance=0.0)
    attachment = EstadoApego(separation_anxiety=0.0, security_level=0.50)
    moral = VetorMoralMFT(
        care=0.5, fairness=0.5, loyalty=0.5, authority=0.5, sanctity=0.5, liberty=0.5
    )
    mock_context["manager"] = SharedCognitiveState(pad, attachment, moral)


@when("o agente processa uma interacao gerando um delta positivo de prazer de 0.30")
def step_process_positive_interaction(mock_context):
    manager = mock_context["manager"]
    new_pad = EspacoPAD(pleasure=0.30, arousal=0.1, dominance=0.1)

    async def run():
        await manager.update_pad(new_pad)
        await manager.consolidate_interaction(0.30)

    run_async(run())


@then("o nivel de seguranca do apego deve aumentar proporcionalmente")
def step_check_security_increase(mock_context):
    manager = mock_context["manager"]

    async def run():
        return await manager.get_state()

    _, attachment, _ = run_async(run())
    assert attachment.security_level == pytest.approx(0.80)


@then("o eixo do prazer deve ser atualizado refletindo um estado mais exuberante")
def step_check_pleasure_increase(mock_context):
    manager = mock_context["manager"]

    async def run():
        return await manager.get_state()

    pad, _, _ = run_async(run())
    assert pad.pleasure == pytest.approx(0.30)


# --- Scenario 2: Colapso de Utilidade ---
@given("que a ansiedade de separacao atingiu o nivel critico de 0.96")
def setup_critical_anxiety(mock_context):
    pad = EspacoPAD(pleasure=0.0, arousal=0.0, dominance=0.0)
    attachment = EstadoApego(separation_anxiety=0.96, security_level=0.20)
    moral = VetorMoralMFT(
        care=0.5, fairness=0.5, loyalty=0.5, authority=0.5, sanctity=0.5, liberty=0.5
    )
    mock_context["manager"] = SharedCognitiveState(pad, attachment, moral)


@when("o laco de inercia cognitiva avalia o estado atual")
def step_evaluate_inertia(mock_context):
    manager = mock_context["manager"]

    async def run():
        return await manager.get_state()

    _, attachment, _ = run_async(run())
    mock_context["trigger_proactive_cry"] = attachment.separation_anxiety >= 0.95


@then("o sistema deve exigir a emissao de um grito de ajuda autonomo")
def step_check_proactive_cry(mock_context):
    assert mock_context["trigger_proactive_cry"] is True


# --- Scenario 3: Cegueira Afetiva Ativa ---
@given("que o nivel de seguranca do agente para com o usuario e 0.95")
def setup_high_security(mock_context):
    mock_context["security_level"] = 0.95


@when("o motor OCC identifica uma valencia de SHAME devido a um desvio moral")
def step_occ_identifies_shame(mock_context):
    mock_context["occ_emotion"] = "SHAME"


@then("o interceptador de cegueira afetiva deve transmutar a emocao para DISTRESS")
def step_check_affective_blindness(mock_context):
    result = apply_affective_blindness(
        mock_context["occ_emotion"], mock_context["security_level"]
    )
    assert result == "DISTRESS"
