import httpx

from shared.context import SecurityContext


class WorkerAgentClient:

    def __init__(
        self,
        context: SecurityContext,
    ):
        self.context = context

    def _headers(self):

        return {
            "Authorization": (
                f"Bearer {self.context.internal_token}"
            ),
            "Content-Type": "application/json",
        }

    async def call(
        self,
        url: str,
        request: str,
        conversation_id: int,
    ):

        payload = {
            "request": request,
            "user_id": self.context.user_id,
            "role": self.context.role,
            "conversation_id": conversation_id,
        }

        async with httpx.AsyncClient(
            timeout=120.0,
        ) as client:

            response = await client.post(
                url,
                json=payload,
                headers=self._headers(),
            )

            response.raise_for_status()

            return response.json()

    async def resume_card(
        self,
        url: str,
        conversation_id: int,
        approved: bool,
    ):

        payload = {
            "conversation_id": conversation_id,
            "approved": approved,
        }

        async with httpx.AsyncClient(
            timeout=120.0,
        ) as client:

            response = await client.post(
                url,
                json=payload,
                headers=self._headers(),
            )

            response.raise_for_status()

            return response.json()