import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.application.game_loop import cognitive_inertia_loop
from src.application.perception import process_user_input
from src.application.state_manager import SharedCognitiveState
from src.application.uow import AsyncUnitOfWork
from src.domain.entities import EspacoPAD, EstadoApego, VetorMoralMFT
from src.infrastructure.llm_client import GeminiAffectiveClient


@pytest.mark.asyncio
async def test_shared_cognitive_state_thread_safety():
    """Verify that SharedCognitiveState updates values correctly and applies
    clamping.
    """
    pad = EspacoPAD(pleasure=0.5, arousal=0.8, dominance=0.2)
    attachment = EstadoApego(separation_anxiety=0.1, security_level=0.9)
    moral = VetorMoralMFT(
        care=0.9, fairness=0.8, loyalty=0.7, authority=0.6, sanctity=0.5, liberty=0.4
    )
    state = SharedCognitiveState(pad, attachment, moral)

    # Test update_pad
    new_pad = EspacoPAD(pleasure=0.9, arousal=0.9, dominance=0.9)
    await state.update_pad(new_pad)
    current_pad, _, _ = await state.get_state()
    # Magnitude should be capped to 1.0 since norm of (0.9, 0.9, 0.9) > 1.0
    magnitude = (
        current_pad.pleasure**2 + current_pad.arousal**2 + current_pad.dominance**2
    ) ** 0.5
    assert magnitude == pytest.approx(1.0)

    # Test apply_decay_and_anxiety
    await state.apply_decay_and_anxiety(delta_time=1.0, basal_arousal=0.0)
    current_pad, current_attach, _ = await state.get_state()
    # Arousal must decay towards 0.0
    assert current_pad.arousal < 0.9
    # Separation anxiety must increase
    assert current_attach.separation_anxiety > 0.1
    # Security must decrease
    assert current_attach.security_level < 0.9


@pytest.mark.asyncio
async def test_process_user_input_use_case():
    """Verify that process_user_input coordinates LLM inference and applies
    OCC mappings.
    """
    # 1. Setup mock UoW
    uow = MagicMock(spec=AsyncUnitOfWork)
    uow.episodic_repo = AsyncMock()
    uow.episodic_repo.get_recent_episodes = AsyncMock(
        return_value=[{"trigger_context": "User: hi | Agent response: hello"}]
    )
    uow.attachment_repo = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)

    user_id = uuid.uuid4()

    # 2. Mock state manager
    pad = EspacoPAD(pleasure=0.0, arousal=0.0, dominance=0.0)
    attachment = EstadoApego(separation_anxiety=0.5, security_level=0.5)
    moral = VetorMoralMFT(
        care=0.9, fairness=0.8, loyalty=0.7, authority=0.6, sanctity=0.5, liberty=0.4
    )
    state_manager = SharedCognitiveState(pad, attachment, moral)

    # 3. Mock LLM client returning explicit OCC tags
    llm_client = GeminiAffectiveClient(api_key="dummy")
    llm_client.invoke_prompt = AsyncMock(
        return_value="[OCC_EMOTIONS: JOY, PRIDE] I am happy to see you!"
    )

    # 4. Execute perception use case
    result = await process_user_input(
        user_id=user_id,
        text="Hello agent!",
        state_manager=state_manager,
        uow=uow,
        llm_client=llm_client,
    )

    assert result["clean_message"] == "I am happy to see you!"
    # Verify PAD changed based on JOY & PRIDE deltas
    assert result["pad_state"].pleasure > 0.0
    assert result["pad_state"].arousal > 0.0
    assert result["pad_state"].dominance > 0.0

    # Ensure repositories were written to
    assert uow.episodic_repo.save_episode.called
    assert uow.attachment_repo.save_state.called


@pytest.mark.asyncio
async def test_cognitive_inertia_loop_cancellation():
    """Verify that cognitive_inertia_loop runs, updates state periodically
    and cancels cleanly.
    """
    # 1. Setup mock UoW
    uow = MagicMock(spec=AsyncUnitOfWork)
    uow.attachment_repo = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)

    user_id = uuid.uuid4()

    pad = EspacoPAD(pleasure=0.5, arousal=0.5, dominance=0.5)
    attachment = EstadoApego(separation_anxiety=0.2, security_level=0.8)
    moral = VetorMoralMFT(
        care=0.9, fairness=0.8, loyalty=0.7, authority=0.6, sanctity=0.5, liberty=0.4
    )
    state_manager = SharedCognitiveState(pad, attachment, moral)

    # 2. Spawn the loop in a background task
    outbound_queue = asyncio.Queue()
    llm_client = MagicMock(spec=GeminiAffectiveClient)
    task = asyncio.create_task(
        cognitive_inertia_loop(user_id, state_manager, uow, outbound_queue, llm_client)
    )

    # Let the loop execute for a few cycles (200ms)
    await asyncio.sleep(0.2)

    # 3. Cancel the background task
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    # Verify that the state was updated (anxiety increased and arousal decayed)
    final_pad, final_attach, _ = await state_manager.get_state()
    assert final_pad.arousal < 0.5
    assert final_attach.separation_anxiety > 0.2


@pytest.mark.asyncio
async def test_consolidate_interaction():
    """Verify that consolidate_interaction updates security level with proper

    clamping.
    """
    pad = EspacoPAD(pleasure=0.5, arousal=0.5, dominance=0.5)
    attachment = EstadoApego(separation_anxiety=0.2, security_level=0.5)
    moral = VetorMoralMFT(
        care=0.9,
        fairness=0.8,
        loyalty=0.7,
        authority=0.6,
        sanctity=0.5,
        liberty=0.4,
    )
    state_manager = SharedCognitiveState(pad, attachment, moral)

    # Positive delta
    await state_manager.consolidate_interaction(0.2)
    _, final_attach, _ = await state_manager.get_state()
    assert final_attach.security_level == pytest.approx(0.7)

    # Overflows clamping
    await state_manager.consolidate_interaction(0.5)
    _, final_attach, _ = await state_manager.get_state()
    assert final_attach.security_level == pytest.approx(1.0)

    # Negative delta
    await state_manager.consolidate_interaction(-1.2)
    _, final_attach, _ = await state_manager.get_state()
    assert final_attach.security_level == pytest.approx(0.0)


@pytest.mark.asyncio
async def test_cognitive_inertia_loop_proactive_cry():
    """Verify that cognitive_inertia_loop triggers proactive cry for help

    when separation_anxiety >= 0.95.
    """
    uow = MagicMock(spec=AsyncUnitOfWork)
    uow.attachment_repo = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)

    user_id = uuid.uuid4()

    pad = EspacoPAD(pleasure=0.5, arousal=0.5, dominance=0.5)
    attachment = EstadoApego(separation_anxiety=0.96, security_level=0.8)
    moral = VetorMoralMFT(
        care=0.9,
        fairness=0.8,
        loyalty=0.7,
        authority=0.6,
        sanctity=0.5,
        liberty=0.4,
    )
    state_manager = SharedCognitiveState(pad, attachment, moral)

    outbound_queue = asyncio.Queue()
    llm_client = MagicMock(spec=GeminiAffectiveClient)
    llm_client.invoke_prompt = AsyncMock(return_value="Volte logo, por favor!")

    # Start loop
    task = asyncio.create_task(
        cognitive_inertia_loop(user_id, state_manager, uow, outbound_queue, llm_client)
    )

    # Let it execute for a few cycles
    await asyncio.sleep(0.25)

    # Cancel task
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    # Verify that the message was sent to the queue
    assert outbound_queue.qsize() == 1
    msg = await outbound_queue.get()
    assert msg == "Volte logo, por favor!"


@pytest.mark.asyncio
async def test_cognitive_inertia_loop_exception_handling(capsys):
    """Verify cognitive_inertia_loop handles exceptions properly without crashing."""

    uow = MagicMock(spec=AsyncUnitOfWork)
    uow.attachment_repo = AsyncMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)

    user_id = uuid.uuid4()

    state_manager = MagicMock(spec=SharedCognitiveState)
    # The loop triggers apply_decay_and_anxiety, so we'll mock it to raise an exception
    state_manager.apply_decay_and_anxiety = AsyncMock(
        side_effect=[
            Exception("Simulated crash"),
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ]
    )
    pad = EspacoPAD(pleasure=0.5, arousal=0.5, dominance=0.5)
    attachment = EstadoApego(separation_anxiety=0.2, security_level=0.8)
    moral = VetorMoralMFT(
        care=0.9, fairness=0.8, loyalty=0.7, authority=0.6, sanctity=0.5, liberty=0.4
    )
    state_manager.get_state = AsyncMock(return_value=(pad, attachment, moral))

    outbound_queue = asyncio.Queue()
    llm_client = MagicMock(spec=GeminiAffectiveClient)

    task = asyncio.create_task(
        cognitive_inertia_loop(user_id, state_manager, uow, outbound_queue, llm_client)
    )

    # Let the loop execute for a few cycles
    await asyncio.sleep(0.4)

    # Cancel the background task
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    captured = capsys.readouterr()
    assert (
        "[Cognitive Inertia Loop Exception] Recovered: Simulated crash" in captured.err
    )
    # The loop should have continued despite the exception, calling
    # apply_decay_and_anxiety again
    assert state_manager.apply_decay_and_anxiety.call_count >= 2
