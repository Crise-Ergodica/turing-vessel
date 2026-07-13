from abc import ABC, abstractmethod
from typing import Any

from src.domain.entities import EspacoPAD, EstadoApego


class EpisodicMemoryRepository(ABC):
    """Abstract Base Class defining the contract for storing and querying
    episodic memories.
    """

    @abstractmethod
    async def save_episode(
        self,
        content: str,
        pad_state: EspacoPAD,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Persists an episodic memory record along with its associated PAD state.

        Returns the unique identifier (ID) of the saved episode.
        """
        pass

    @abstractmethod
    async def get_episode_by_id(self, episode_id: str) -> dict[str, Any] | None:
        """Retrieves a specific episodic memory by its unique identifier."""
        pass

    @abstractmethod
    async def get_recent_episodes(self, limit: int = 10) -> list[dict[str, Any]]:
        """Retrieves the most recent episodic memories up to the specified limit."""
        pass

    @abstractmethod
    async def search_by_affective_state(
        self,
        target_pad: EspacoPAD,
        similarity_threshold: float = 0.5,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Queries episodes based on proximity to a target PAD state.

        Useful for retrieval based on emotional association.
        """
        pass


class AttachmentEngineRepository(ABC):
    """Abstract Base Class defining the contract for managing persistent
    attachment state.
    """

    @abstractmethod
    async def get_current_state(self) -> EstadoApego | None:
        """Retrieves the current persistent attachment state (anxiety, security).

        Returns None if no state has been initialized/saved yet.
        """
        pass

    @abstractmethod
    async def save_state(self, state: EstadoApego) -> None:
        """Persists the updated attachment state."""
        pass

    @abstractmethod
    async def reset_state(self) -> None:
        """Resets the attachment state back to default baseline configurations."""
        pass
