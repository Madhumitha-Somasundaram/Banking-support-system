export interface Conversation {
  id: number;
  user_id: number;
  created_at: string;
  updated_at: string | null;
}

export interface Message {
  id: number;
  conversation_id: number;
  role: string;
  content: string;
  created_at: string;
}

export interface CardApproval {
  type: string;
  action: "freeze_card" | "unfreeze_card";
  card_id: number;
  last4: string;
  message: string;
  description?: string | null;
}

export interface ChatResponse {
  messages: Message[];
  approval: CardApproval | null;
  job_id: string | null;
  status: string | null;
}

export interface JobStatus {
  job_id: string;
  conversation_id: number;
  status:
    | "QUEUED"
    | "PROCESSING"
    | "COMPLETED"
    | "APPROVAL_REQUIRED"
    | "FAILED";

  message: Message | null;

  approval: CardApproval | null;

  error: string | null;
}