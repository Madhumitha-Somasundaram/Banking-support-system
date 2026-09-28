"use client";

import { Conversation } from "@/types/chat";


interface Props {
  conversations: Conversation[];
  selectedConversationId: number | null;
  onSelect: (id: number) => void;
  onCreate: () => void;
}


export default function ConversationList({
  conversations,
  selectedConversationId,
  onSelect,
  onCreate,
}: Props) {

  return (
    <div className="flex h-full w-72 flex-col border-r">

      <div className="flex items-center justify-between border-b p-4">

        <h2 className="font-semibold">
          Conversations
        </h2>

        <button
          onClick={onCreate}
          className="rounded bg-black px-3 py-1 text-sm text-white"
        >
          +
        </button>

      </div>


      <div className="flex-1 overflow-y-auto">

        {conversations.length === 0 && (
          <p className="p-4 text-sm text-gray-500">
            No conversations yet.
          </p>
        )}


        {conversations.map((conversation) => (

          <button
            key={conversation.id}
            onClick={() =>
              onSelect(conversation.id)
            }
            className={`w-full border-b p-4 text-left ${
              selectedConversationId === conversation.id
                ? "bg-gray-100"
                : "hover:bg-gray-50"
            }`}
          >

            <p className="font-medium">
              Conversation #{conversation.id}
            </p>

            <p className="text-xs text-gray-500">
              {new Date(
                conversation.updated_at ||
                conversation.created_at
              ).toLocaleString()}
            </p>

          </button>

        ))}

      </div>

    </div>
  );
}