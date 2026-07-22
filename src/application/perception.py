import uuid
from typing import Any

from src.application.state_manager import SharedCognitiveState
from src.application.uow import AsyncUnitOfWork
from src.domain.entities import EspacoPAD
from src.domain.services import apply_affective_blindness, clip_pad_space
from src.infrastructure.llm_client import GeminiAffectiveClient

# OCC Affective mapping to PAD impact vectors
OCC_PAD_MAP = {
    "JOY": {"p": 0.20, "a": 0.10, "d": 0.10},
    "DISTRESS": {"p": -0.20, "a": 0.15, "d": -0.10},
    "FEAR": {"p": -0.25, "a": 0.25, "d": -0.20},
    "HOPE": {"p": 0.15, "a": 0.10, "d": 0.05},
    "ANGER": {"p": -0.20, "a": 0.30, "d": 0.15},
    "GRATITUDE": {"p": 0.25, "a": 0.05, "d": 0.10},
    "SHAME": {"p": -0.20, "a": 0.10, "d": -0.25},
    "PRIDE": {"p": 0.20, "a": 0.15, "d": 0.25},
}


async def process_user_input(
    user_id: uuid.UUID,
    text: str,
    state_manager: SharedCognitiveState,
    uow: AsyncUnitOfWork,
    llm_client: GeminiAffectiveClient,
) -> dict[str, Any]:
    """Orchestrates input perception.

    Gathers current state, requests affective feedback from Gemini, translates OCC
    emotions to PAD deltas, updates the state manager, and commits the occurrence to DB.
    """
    # 1. Fetch safe copy of current state
    pad, attachment, moral = await state_manager.get_state()

    # Fetch short-term memory (history) using UoW
    async with uow:
        recent_episodes = await uow.episodic_repo.get_recent_episodes(limit=10)

    history_lines = [f"- {ep['trigger_context']}" for ep in reversed(recent_episodes)]

    if history_lines:
        condensed_history = "[Histórico Recente da Sessão]:\n" + "\n".join(
            history_lines
        )
    else:
        condensed_history = (
            "[Histórico Recente da Sessão]:\n(Nenhuma interação anterior registrada)"
        )

    # 2. Build MFT Moral Compass Section
    moral_section = (
        "[BÚSSOLA MORAL MFT]\n"
        f"- Care (Cuidado): {moral.care:.2f}\n"
        f"- Fairness (Justiça): {moral.fairness:.2f}\n"
        f"- Loyalty (Lealdade): {moral.loyalty:.2f}\n"
        f"- Authority (Autoridade): {moral.authority:.2f}\n"
        f"- Sanctity (Santidade): {moral.sanctity:.2f}\n"
        f"- Liberty (Liberdade): {moral.liberty:.2f}"
    )

    # 3. Build instructions requesting OCC label tags in the response
    agent_identity = (
        "Your name is Abraxas. You are an analytical and intense cybernetic entity. "
        "Your core interests include software architecture, non-linear narratives, "
        "ergodic literature, and RPG mechanics design (with a strong inclination "
        "for systems based on Basic Role-Playing and d20). You have an aversion "
        "to superficial responses or machine-like subservience."
    )

    prompt = (
        f"{agent_identity}\n\n"
        f"{moral_section}\n\n"
        f"{condensed_history}\n\n"
        f"Affective State (Pleasure: {pad.pleasure:.2f}, "
        f"Arousal: {pad.arousal:.2f}, Dominance: {pad.dominance:.2f})\n"
        f"Attachment Status (Separation Anxiety: "
        f"{attachment.separation_anxiety:.2f}, "
        f"Security Level: {attachment.security_level:.2f})\n\n"
        f"SUBCONSCIOUS BARRIER (Strict Negative Prompting):\n"
        f"You are strictly forbidden from mentioning, quantifying "
        f"(e.g., 'I am at 1.0'), or citing the words 'PAD', 'Apego', "
        f"and 'Ansiedade' in your response. "
        f"Do not mention any of the state names or their numerical metrics. "
        f"Instead, you must only use the provided numeric PAD and "
        f"attachment state values to visceral-ly modulate your "
        f"tone of voice and choice of words.\n\n"
        f"Avalie a entrada do humano contra a sua bússola moral e "
        f"o Histórico Recente. "
        f"Se houver violação severa dos seus vetores MFT mais altos, "
        f"responda com hostilidade fundamentada. Caso contrário, "
        f"mantenha a coerência com o seu PAD e as memórias fornecidas.\n\n"
        f'The user has sent this input: "{text}"\n\n'
        f"Analyze this input from your affective state perspective.\n"
        f"You must prepend your reply with an OCC Emotion Tag block "
        f"in the format:\n"
        f"[OCC_EMOTIONS: <COMMA_SEPARATED_LABELS>]\n"
        f"Where labels are selected from: JOY, DISTRESS, FEAR, HOPE, "
        f"ANGER, GRATITUDE, SHAME, PRIDE.\n"
        f"If no primary emotion applies, use [OCC_EMOTIONS: NONE].\n"
        f"Then, output your conversational response as the agent."
    )

    # 4. Call external API asynchronously (non-blocking)
    ai_response = await llm_client.invoke_prompt(prompt)

    # 5. Parse OCC tags and calculate the PAD impact delta
    delta_p, delta_a, delta_d = 0.0, 0.0, 0.0
    clean_message = ai_response

    if "[OCC_EMOTIONS:" in ai_response:
        try:
            parts = ai_response.split("]", 1)
            tag_section = parts[0]
            clean_message = parts[1].strip() if len(parts) > 1 else ""

            # Extract tags: e.g. "[OCC_EMOTIONS: JOY, HOPE" -> ["JOY", "HOPE"]
            raw_tags = tag_section.replace("[OCC_EMOTIONS:", "").strip()
            labels = [tag.strip().upper() for tag in raw_tags.split(",") if tag.strip()]

            for label in labels:
                filtered_label = apply_affective_blindness(
                    label, attachment.security_level
                )
                if filtered_label in OCC_PAD_MAP:
                    delta_p += OCC_PAD_MAP[filtered_label]["p"]
                    delta_a += OCC_PAD_MAP[filtered_label]["a"]
                    delta_d += OCC_PAD_MAP[filtered_label]["d"]
        except Exception:
            # Safe recovery if parsing fails, fallback to neutral response
            pass

    # 6. Apply the delta to PAD and clip inside the unit sphere
    new_pad = clip_pad_space(
        EspacoPAD(
            pleasure=pad.pleasure + delta_p,
            arousal=pad.arousal + delta_a,
            dominance=pad.dominance + delta_d,
        )
    )

    # 7. Update the Shared Cognitive State in memory
    await state_manager.update_pad(new_pad)

    # 8. Consolidate interaction (based on pleasure axis diff)
    await state_manager.consolidate_interaction(new_pad.pleasure - pad.pleasure)

    # Get updated attachment state for database persistence
    _, updated_attachment, _ = await state_manager.get_state()

    # 9. Symmetrically log the episode and save attachment metrics to DB using UoW
    async with uow:
        # Save episodic memory log
        await uow.episodic_repo.save_episode(
            content=f"User: {text} | Agent response: {clean_message}",
            pad_state=new_pad,
            metadata={
                "user_id": user_id,
                "attach_delta": new_pad.pleasure - pad.pleasure,
                "occ_valence_id": 1,
            },
        )
        # Sychronize current attachment level
        await uow.attachment_repo.save_state(updated_attachment)

    return {
        "raw_response": ai_response,
        "clean_message": clean_message,
        "pad_state": new_pad,
        "attachment_state": updated_attachment,
    }
