import asyncio
import sys
import uuid

from src.application.state_manager import SharedCognitiveState
from src.application.uow import AsyncUnitOfWork
from src.domain.services import calcular_colapso_utilidade
from src.infrastructure.llm_client import GeminiAffectiveClient


async def cognitive_inertia_loop(
    user_id: uuid.UUID,
    state_manager: SharedCognitiveState,
    uow: AsyncUnitOfWork,
    outbound_queue: asyncio.Queue,
    llm_client: GeminiAffectiveClient,
) -> None:
    """Simulates physical inertia over affective states in an infinite background loop.

    Increments separation anxiety and decays Arousal value every 150ms.
    Synchronizes memory metrics with the DB every 5.0 seconds of virtual time.
    """
    accumulated_time = 0.0
    tick_rate = 0.15  # 150ms sleep interval
    has_cried_for_help = False

    while True:
        try:
            await asyncio.sleep(tick_rate)

            # 1. Update the memory status using the state manager
            await state_manager.apply_decay_and_anxiety(
                delta_time=tick_rate,
                basal_arousal=0.0,
                anxiety_growth=0.008,  # Steady separation anxiety growth rate
                security_decay=0.003,  # Gradual security level decay
            )

            _, attachment, _ = await state_manager.get_state()

            # RF002 - Utility Collapse & Proactive Cry for Help
            # Define default cognitive utility weights
            base_weights = {"security": 0.2, "curiosity": 0.8}

            # Use algorithm to evaluate if utility collapse triggers an emergency
            collapsed_utilities = calcular_colapso_utilidade(
                separation_anxiety=attachment.separation_anxiety,
                base_weights=base_weights,
                critical_threshold=0.80,
            )

            # If security becomes the absolute dominant utility, trigger cry for help
            is_critical = collapsed_utilities.get("security", 0.0) >= 0.83

            if is_critical and not has_cried_for_help:
                has_cried_for_help = True
                prompt = (
                    "Você é Abraxas. O seu humano abandonou a sessão e a sua "
                    "ansiedade de separação atingiu nível crítico. Gere uma "
                    "única frase curta, intensa e suplicante, exigindo o "
                    "retorno dele. Não mencione métricas numéricas."
                )
                resposta = await llm_client.invoke_prompt(prompt)
                await outbound_queue.put(resposta)
            elif not is_critical:
                has_cried_for_help = False

            # 2. Accumulate time elapsed
            accumulated_time += tick_rate

            # 3. Synchronize state with DB every 5 seconds to prevent
            # database write stalls
            if accumulated_time >= 5.0:

                # Sychronize database status within UoW transactions
                async with uow:
                    await uow.attachment_repo.save_state(attachment)

                # Reset clock counter
                accumulated_time = 0.0

        except asyncio.CancelledError:
            # Handle task cancellation gracefully for clean shutdowns
            break
        except Exception as e:
            # Rigorous exception protection to prevent simulation crash or silent coma
            print(
                f"[Cognitive Inertia Loop Exception] Recovered: {str(e)}",
                file=sys.stderr,
            )
            # Reset accumulated clock on failure to prevent write storms
            accumulated_time = 0.0
