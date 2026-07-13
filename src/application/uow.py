import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.infrastructure.database.repositories import (
    AttachmentEngineRepositoryImpl,
    EpisodicMemoryRepositoryImpl,
)


class AsyncUnitOfWork:
    """Implements the Unit of Work pattern using SQLAlchemy 2.0 AsyncSession.

    Coordinates transaction boundaries and repository access for application cases.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        user_id: uuid.UUID,
    ):
        self.session_factory = session_factory
        self.user_id = user_id
        self.session: AsyncSession | None = None
        self._episodic_repo: EpisodicMemoryRepositoryImpl | None = None
        self._attachment_repo: AttachmentEngineRepositoryImpl | None = None

    @property
    def episodic_repo(self) -> EpisodicMemoryRepositoryImpl:
        """Returns the episodic memory repository wrapper."""
        if not self._episodic_repo:
            raise RuntimeError(
                "Unit of Work session not started. Access repository inside async with."
            )
        return self._episodic_repo

    @property
    def attachment_repo(self) -> AttachmentEngineRepositoryImpl:
        """Returns the attachment engine repository wrapper."""
        if not self._attachment_repo:
            raise RuntimeError(
                "Unit of Work session not started. Access repository inside async with."
            )
        return self._attachment_repo

    async def __aenter__(self) -> "AsyncUnitOfWork":
        # Create transaction session
        self.session = self.session_factory()

        # Shared session factory proxy to allow the repositories to reuse
        # the UoW session
        class SharedSessionFactoryProxy:
            def __init__(self, session_instance: AsyncSession):
                self.session_instance = session_instance

            def __call__(self) -> "SharedSessionFactoryProxy":
                return self

            async def __aenter__(self) -> AsyncSession:
                return self.session_instance

            async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
                # Session lifecycle is managed exclusively by the UoW parent
                pass

        shared_proxy = SharedSessionFactoryProxy(self.session)

        # Instantiate repositories bound to the shared session
        self._episodic_repo = EpisodicMemoryRepositoryImpl(shared_proxy)
        self._attachment_repo = AttachmentEngineRepositoryImpl(
            shared_proxy, self.user_id
        )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        if self.session:
            try:
                if exc_type:
                    await self.session.rollback()
                else:
                    await self.session.commit()
            finally:
                await self.session.close()

            # Clean up instances
            self.session = None
            self._episodic_repo = None
            self._attachment_repo = None
