import asyncio
import json

import boto3

from opentelemetry import propagate

from shared.config import settings


class AgentQueueClient:

    def __init__(self):
        self.sqs = boto3.client(
            "sqs",
            region_name=settings.BEDROCK_REGION,
        )

    def _send_message(
        self,
        payload: dict,
        trace_attributes: dict,
    ):

        return self.sqs.send_message(
            QueueUrl=settings.AGENT_QUEUE_URL,
            MessageBody=json.dumps(payload),
            MessageAttributes=trace_attributes,
        )

    async def submit_message(
        self,
        job_id: str,
        request: str,
        user_id: int,
        role: str,
        conversation_id: int,
    ):

        payload = {
            "job_id": job_id,
            "job_type": "MESSAGE",
            "request": request,
            "user_id": user_id,
            "role": role,
            "conversation_id": conversation_id,
        }

        # ----------------------------------------------
        # Inject current OpenTelemetry trace context
        # ----------------------------------------------

        carrier = {}

        propagate.inject(carrier)

        trace_attributes = {}

        if "traceparent" in carrier:
            trace_attributes["traceparent"] = {
                "StringValue": carrier["traceparent"],
                "DataType": "String",
            }

        await asyncio.to_thread(
            self._send_message,
            payload,
            trace_attributes,
        )

        return {
            "job_id": job_id,
            "status": "QUEUED",
        }

    async def submit_card_approval(
        self,
        job_id: str,
        user_id: int,
        role: str,
        conversation_id: int,
        approved: bool,
    ):

        payload = {
            "job_id": job_id,
            "job_type": "CARD_APPROVAL",
            "user_id": user_id,
            "role": role,
            "conversation_id": conversation_id,
            "approved": approved,
        }

        # ----------------------------------------------
        # Inject current OpenTelemetry trace context
        # ----------------------------------------------

        carrier = {}

        propagate.inject(carrier)

        trace_attributes = {}

        if "traceparent" in carrier:
            trace_attributes["traceparent"] = {
                "StringValue": carrier["traceparent"],
                "DataType": "String",
            }

        await asyncio.to_thread(
            self._send_message,
            payload,
            trace_attributes,
        )

        return {
            "job_id": job_id,
            "status": "QUEUED",
        }