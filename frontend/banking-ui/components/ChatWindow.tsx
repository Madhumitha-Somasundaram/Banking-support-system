"use client";

import { Message, CardApproval } from "@/types/chat";

interface Props {
  messages: Message[];
  approval: CardApproval | null;
  approving: boolean;
  onApproval: (approved: boolean) => Promise<void>;
}

export default function ChatWindow({
  messages,
  approval,
  approving,
  onApproval,
}: Props) {
  return (
    <div className="flex-1 overflow-y-auto p-6">

      {messages.length === 0 && (
        <div className="flex h-full items-center justify-center">
          <p className="text-gray-500">
            Start a conversation with your banking assistant.
          </p>
        </div>
      )}

      <div className="mx-auto max-w-3xl space-y-4">

        {messages.map((message) => {
          const isUser = message.role === "USER";

          return (
            <div
              key={message.id}
              className={`flex ${
                isUser
                  ? "justify-end"
                  : "justify-start"
              }`}
            >
              <div
                className={`max-w-[75%] rounded-lg px-4 py-3 ${
                  isUser
                    ? "bg-black text-white"
                    : "bg-gray-100 text-black"
                }`}
              >
                <p className="whitespace-pre-wrap">
                  {message.content}
                </p>
              </div>
            </div>
          );
        })}

        {approval && (
          <div className="rounded-lg border bg-white p-4 shadow-sm">

            <p className="font-medium">
              {approval.message}
            </p>

            {approval.description && (
              <p className="mt-1 text-sm text-gray-500">
                {approval.description}
              </p>
            )}

            <div className="mt-4 flex gap-3">

              <button
                onClick={() => onApproval(true)}
                disabled={approving}
                className="rounded-lg bg-black px-4 py-2 text-sm text-white disabled:opacity-40"
              >
                {approving ? "Processing..." : "Approve"}
              </button>

              <button
                onClick={() => onApproval(false)}
                disabled={approving}
                className="rounded-lg border px-4 py-2 text-sm disabled:opacity-40"
              >
                Reject
              </button>

            </div>

          </div>
        )}

      </div>

    </div>
  );
}