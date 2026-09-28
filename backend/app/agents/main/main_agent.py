from app.agents.main.queue_client import AgentQueueClient


class MainAgent:

    def __init__(self):
        self.queue_client = AgentQueueClient()

    async def submit(
        self,
        job_id: str,
        request: str,
        user_id: int,
        role: str,
        conversation_id: int,
    ):

        return await self.queue_client.submit_message(
            job_id=job_id,
            request=request,
            user_id=user_id,
            role=role,
            conversation_id=conversation_id,
        )

    async def submit_card_approval(
        self,
        job_id: str,
        user_id: int,
        role: str,
        conversation_id: int,
        approved: bool,
    ):

        return await self.queue_client.submit_card_approval(
            job_id=job_id,
            user_id=user_id,
            role=role,
            conversation_id=conversation_id,
            approved=approved,
        )