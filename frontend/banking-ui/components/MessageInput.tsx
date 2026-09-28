"use client";

import { useState } from "react";


interface Props {
  disabled: boolean;
  onSend: (message: string) => Promise<void>;
}


export default function MessageInput({
  disabled,
  onSend,
}: Props) {

  const [message, setMessage] = useState("");
  const [sending, setSending] = useState(false);


  async function handleSubmit(
    event: React.FormEvent
  ) {

    event.preventDefault();

    const content = message.trim();

    if (!content || disabled || sending) {
      return;
    }


    setSending(true);

    try {

      await onSend(content);

      setMessage("");

    } finally {

      setSending(false);

    }
  }


  return (
    <form
      onSubmit={handleSubmit}
      className="border-t p-4"
    >

      <div className="mx-auto flex max-w-3xl gap-3">

        <input
          value={message}
          onChange={(e) =>
            setMessage(e.target.value)
          }
          disabled={disabled || sending}
          placeholder={
            disabled
              ? "Select a conversation..."
              : "Ask a banking question..."
          }
          className="flex-1 rounded-lg border px-4 py-3 outline-none focus:ring-2"
        />


        <button
          type="submit"
          disabled={
            disabled ||
            sending ||
            !message.trim()
          }
          className="rounded-lg bg-black px-5 py-3 text-white disabled:opacity-40"
        >
          {sending ? "..." : "Send"}
        </button>

      </div>

    </form>
  );
}