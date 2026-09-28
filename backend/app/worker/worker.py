import asyncio
import json

import boto3

from app.db.database import SessionLocal
from app.worker.job_processor import JobProcessor

from shared.config import settings
from opentelemetry import propagate, trace
from shared.tracing import init_tracing

AWS_REGION = settings.BEDROCK_REGION

MAX_MESSAGES = 1
WAIT_TIME_SECONDS = 20
VISIBILITY_TIMEOUT = 900


sqs = boto3.client(
    "sqs",
    region_name=AWS_REGION,
)

processor = JobProcessor()
tracer = trace.get_tracer(
    "banking-agent-worker"
)

def receive_messages():

    return sqs.receive_message(
        QueueUrl=settings.AGENT_QUEUE_URL,
        MaxNumberOfMessages=MAX_MESSAGES,
        WaitTimeSeconds=WAIT_TIME_SECONDS,
        VisibilityTimeout=VISIBILITY_TIMEOUT,
        AttributeNames=[
            "ApproximateReceiveCount",
        ],
        MessageAttributeNames=[
            "All",
        ],
    )


def delete_message(
    receipt_handle: str,
):

    sqs.delete_message(
        QueueUrl=settings.AGENT_QUEUE_URL,
        ReceiptHandle=receipt_handle,
    )


async def process_message(
    message: dict,
):

    body = json.loads(
        message["Body"]
    )

    job_id = body["job_id"]

    receive_count = int(
        message.get(
            "Attributes",
            {},
        ).get(
            "ApproximateReceiveCount",
            "1",
        )
    )

    # --------------------------------------------------
    # Extract OpenTelemetry trace context from SQS
    # --------------------------------------------------

    message_attributes = message.get(
        "MessageAttributes",
        {}
    )

    traceparent_attribute = (
        message_attributes.get(
            "traceparent"
        )
    )

    carrier = {}

    if traceparent_attribute:

        carrier["traceparent"] = (
            traceparent_attribute["StringValue"]
        )

    context = propagate.extract(
        carrier
    )

    # --------------------------------------------------
    # Continue the distributed trace
    # --------------------------------------------------

    with tracer.start_as_current_span(
        "agent_worker.process_job",
        context=context,
    ) as span:

        span.set_attribute(
            "banking.job_id",
            str(job_id),
        )

        span.set_attribute(
            "banking.operation",
            "process_job",
        )

        span.set_attribute(
            "banking.agent",
            "worker",
        )

        db = SessionLocal()

        try:

            await processor.process(
                db=db,
                payload=body,
            )

            span.set_attribute(
                "banking.status",
                "completed",
            )

            delete_message(
                message["ReceiptHandle"]
            )

            print(
                f"[WORKER] Completed "
                f"job={job_id}"
            )

        except Exception as exc:

            span.set_attribute(
                "banking.status",
                "failed",
            )

            span.record_exception(
                exc
            )

            import traceback

            print(
                f"[WORKER] Failed "
                f"job={job_id} "
                f"attempt={receive_count} "
                f"error={exc}"
            )

            traceback.print_exc()

            # Message intentionally NOT deleted.
            #
            # SQS will make it visible again after
            # the visibility timeout.
            #
            # After maxReceiveCount, SQS moves it
            # to the DLQ.

        finally:

            db.close()

async def worker_loop():

    print(
        "[WORKER] Agent worker started"
    )

    while True:

        try:

            response = await asyncio.to_thread(
                receive_messages
            )

            messages = response.get(
                "Messages",
                [],
            )

            if not messages:

                continue

            for message in messages:

                await process_message(
                    message
                )

        except Exception as exc:

            print(
                f"[WORKER LOOP ERROR] {exc}"
            )

            await asyncio.sleep(5)


if __name__ == "__main__":
    
    init_tracing(
    "banking-agent-worker"
)
    asyncio.run(
        worker_loop()
    )