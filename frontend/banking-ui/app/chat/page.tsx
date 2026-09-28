"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import {
  createConversation,
  getConversations,
  getMessages,
  sendMessage,
  approveCardAction,
  getJobStatus,
} from "@/lib/api";

import {
  Conversation,
  Message,
  CardApproval,
} from "@/types/chat";

import ConversationList from "@/components/ConversationList";
import ChatWindow from "@/components/ChatWindow";
import MessageInput from "@/components/MessageInput";

export default function ChatPage() {
  const router = useRouter();

  const [processing, setProcessing] =
    useState(false);

  const [conversations, setConversations] =
    useState<Conversation[]>([]);

  const [selectedConversationId, setSelectedConversationId] =
    useState<number | null>(null);

  const [messages, setMessages] =
    useState<Message[]>([]);

  const [approval, setApproval] =
    useState<CardApproval | null>(null);

  const [approving, setApproving] =
    useState(false);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  const sleep = (ms: number) =>
    new Promise((resolve) =>
      setTimeout(resolve, ms)
    );

  // ==========================================================
  // POLL JOB
  // ==========================================================

  const pollJob = async (
    jobId: string,
    conversationId: number
  ) => {
    setProcessing(true);
    setError(null);

    try {
      while (true) {
        const job = await getJobStatus(jobId);

        // ----------------------------------------------------
        // Still waiting
        // ----------------------------------------------------

        if (
          job.status === "QUEUED" ||
          job.status === "PROCESSING"
        ) {
          await sleep(1000);
          continue;
        }

        // ----------------------------------------------------
        // Completed
        // ----------------------------------------------------

        if (job.status === "COMPLETED") {
          if (
            job.message &&
            conversationId === selectedConversationId
          ) {
            setMessages((previous) => [
              ...previous,
              job.message!,
            ]);
          }

          break;
        }

        // ----------------------------------------------------
        // Card approval required
        // ----------------------------------------------------

        if (
          job.status === "APPROVAL_REQUIRED"
        ) {
          if (
            conversationId === selectedConversationId
          ) {
            setApproval(
              job.approval
            );
          }

          break;
        }

        // ----------------------------------------------------
        // Failed
        // ----------------------------------------------------

        if (job.status === "FAILED") {
          setError(
            job.error ||
              "We could not process your request."
          );

          break;
        }

        break;
      }
    } catch (error) {
      console.error(
        "Job polling error:",
        error
      );

      setError(
        error instanceof Error
          ? error.message
          : "Unable to check request status."
      );
    } finally {
      setProcessing(false);
    }
  };

  // ==========================================================
  // LOAD CONVERSATIONS
  // ==========================================================

  useEffect(() => {
    const token =
      localStorage.getItem(
        "access_token"
      );

    if (!token) {
      router.push("/login");
      return;
    }

    async function loadConversations() {
      try {
        const data =
          await getConversations();

        setConversations(data);

        if (data.length > 0) {
          setSelectedConversationId(
            data[0].id
          );
        }
      } catch (error) {
        console.error(error);
        router.push("/login");
      } finally {
        setLoading(false);
      }
    }

    loadConversations();
  }, [router]);

  // ==========================================================
  // LOAD MESSAGES
  // ==========================================================

  useEffect(() => {
    if (
      selectedConversationId === null
    ) {
      setMessages([]);
      setApproval(null);
      setError(null);
      return;
    }

    const conversationId =
      selectedConversationId;

    async function loadMessages() {
      try {
        setError(null);

        const data =
          await getMessages(
            conversationId
          );

        setMessages(data);
        setApproval(null);
      } catch (error) {
        console.error(error);

        setError(
          error instanceof Error
            ? error.message
            : "Unable to load messages."
        );
      }
    }

    loadMessages();
  }, [selectedConversationId]);

  // ==========================================================
  // CREATE CONVERSATION
  // ==========================================================

  async function handleCreateConversation() {
    try {
      setError(null);

      const conversation =
        await createConversation();

      setConversations(
        (previous) => [
          conversation,
          ...previous,
        ]
      );

      setSelectedConversationId(
        conversation.id
      );

      setMessages([]);
      setApproval(null);
    } catch (error) {
      console.error(error);

      setError(
        error instanceof Error
          ? error.message
          : "Unable to create conversation."
      );
    }
  }

  // ==========================================================
  // SEND MESSAGE
  // ==========================================================

  async function handleSendMessage(
    content: string
  ) {
    if (
      selectedConversationId === null ||
      processing ||
      approval !== null
    ) {
      return;
    }

    try {
      setError(null);

      const conversationId =
        selectedConversationId;

      const data =
        await sendMessage(
          conversationId,
          content
        );

      // The backend immediately returns the
      // saved USER message.
      setMessages((previous) => [
        ...previous,
        ...data.messages,
      ]);

      // Backend has now queued the expensive
      // LangGraph/agent work in SQS.
      if (data.job_id) {
  console.log("POLLING JOB:", data.job_id);

  await pollJob(
    data.job_id,
    conversationId
  );
}
    } catch (error) {
      console.error(
        "Send message error:",
        error
      );

      setError(
        error instanceof Error
          ? error.message
          : "Unable to send message."
      );
    }
  }

  // ==========================================================
  // CARD APPROVAL
  // ==========================================================

  async function handleApproval(
    approved: boolean
  ) {
    if (
      selectedConversationId === null ||
      !approval ||
      processing ||
      approving
    ) {
      return;
    }

    try {
      setApproving(true);
      setError(null);

      const conversationId =
        selectedConversationId;

      // Remove the current approval UI.
      setApproval(null);

      // This does NOT call the Card Agent directly.
      // Main Backend creates another SQS job.
      const data =
        await approveCardAction(
          conversationId,
          approved
        );

      // Wait for the worker to resume
      // the Card Agent checkpoint.
      if (data.job_id) {
  console.log("POLLING JOB:", data.job_id);

  await pollJob(
    data.job_id,
    conversationId
  );
}
    } catch (error) {
      console.error(
        "Approval error:",
        error
      );

      setError(
        error instanceof Error
          ? error.message
          : "Unable to process approval."
      );
    } finally {
      setApproving(false);
    }
  }

  // ==========================================================
  // LOGOUT
  // ==========================================================

  function handleLogout() {
    localStorage.removeItem(
      "access_token"
    );

    router.push("/login");
  }

  // ==========================================================
  // LOADING
  // ==========================================================

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        Loading...
      </div>
    );
  }

  // ==========================================================
  // UI
  // ==========================================================

  return (
    <main className="flex h-screen">

      <ConversationList
        conversations={conversations}
        selectedConversationId={
          selectedConversationId
        }
        onSelect={
          setSelectedConversationId
        }
        onCreate={
          handleCreateConversation
        }
      />

      <section className="flex min-w-0 flex-1 flex-col">

        <header className="flex items-center justify-between border-b p-4">

          <h1 className="font-semibold">
            Banking Support AI
          </h1>

          <button
            onClick={handleLogout}
            className="rounded border px-3 py-2 text-sm"
          >
            Logout
          </button>

        </header>

        {error && (
          <div className="border-b px-4 py-2 text-sm text-red-600">
            {error}
          </div>
        )}

        {processing && (
          <div className="border-b px-4 py-2 text-sm text-gray-500">
            Processing your request...
          </div>
        )}

        <ChatWindow
          messages={messages}
          approval={approval}
          approving={approving}
          onApproval={handleApproval}
        />

        <MessageInput
          disabled={
            selectedConversationId === null ||
            processing ||
            approval !== null
          }
          onSend={handleSendMessage}
        />

      </section>

    </main>
  );
}