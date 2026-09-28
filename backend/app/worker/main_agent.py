from app.agents.main.graph import build_graph
from shared.context import SecurityContext
from shared.internal_token import create_internal_token


class WorkerMainAgent:

    async def run(
        self,
        messages,
        user_id: int,
        role: str,
        conversation_id: int,
    ):

        internal_token = create_internal_token(
            user_id=user_id,
            role=role,
            conversation_id=conversation_id,
        )

        context = SecurityContext(
            user_id=user_id,
            role=role,
            conversation_id=conversation_id,
            internal_token=internal_token,
        )

        graph = build_graph(
            context=context,
            conversation_id=conversation_id,
        )

        state = {
            "messages": messages,

            "user_id": user_id,

            "conversation_id": conversation_id,

            "user_role": role,

            "intent": None,

            "selected_worker": None,

            "worker_results": [],

            "retrieved_documents": [],

            "requires_approval": False,

            "approval_status": None,

            "iteration": 0,

            "max_iterations": 10,

            "final_answer": None,
        }

        result = await graph.ainvoke(state)

        last_message = result["messages"][-1]

        content = getattr(
            last_message,
            "content",
            "",
        )

        if isinstance(content, str):

            try:
                import json

                data = json.loads(content)

                if data.get(
                    "status"
                ) == "APPROVAL_REQUIRED":

                    return {
                        "type": "approval_required",
                        "approval": data,
                    }

            except (
                json.JSONDecodeError,
                TypeError,
            ):
                pass

        return {
            "type": "message",
            "content": content,
        }