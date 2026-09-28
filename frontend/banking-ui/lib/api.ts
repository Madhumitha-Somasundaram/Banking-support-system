import type { JobStatus } from "@/types/chat";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000";

export async function getJobStatus(
  jobId: string
): Promise<JobStatus> {
  return request(`/api/chat/jobs/${jobId}`);
}

async function request(
  endpoint: string,
  options: RequestInit = {}
) {
  const token =
    localStorage.getItem("access_token");

  const headers =
    new Headers(options.headers);

  headers.set(
    "Content-Type",
    "application/json"
  );

  if (token) {
    headers.set(
      "Authorization",
      `Bearer ${token}`
    );
  }

  const response = await fetch(
    `${API_URL}${endpoint}`,
    {
      ...options,
      headers,
    }
  );


  if (response.status === 401) {

    localStorage.removeItem(
      "access_token"
    );

    window.location.href = "/login";

    throw new Error(
      "Session expired"
    );
  }


  if (!response.ok) {

    const error =
      await response.json().catch(
        () => ({
          detail: "Request failed",
        })
      );

    throw new Error(
      error.detail ||
      "Request failed"
    );
  }


  return response.json();
}


// ==============================
// AUTH
// ==============================

export async function signup(
  email: string,
  password: string,
  name: string
) {
  return request(
    "/api/auth/signup",
    {
      method: "POST",
      body: JSON.stringify({
        email,
        password,
        name,
      }),
    }
  );
}


export async function login(
  email: string,
  password: string
) {
  return request(
    "/api/auth/login",
    {
      method: "POST",
      body: JSON.stringify({
        email,
        password,
      }),
    }
  );
}


export async function getCurrentUser() {
  return request(
    "/api/auth/me"
  );
}


// ==============================
// CONVERSATIONS
// ==============================

export async function getConversations() {
  return request(
    "/api/chat/conversations"
  );
}


export async function createConversation() {
  return request(
    "/api/chat/conversations",
    {
      method: "POST",
    }
  );
}


// ==============================
// MESSAGES
// ==============================

export async function getMessages(
  conversationId: number
) {
  return request(
    `/api/chat/conversations/${conversationId}/messages`
  );
}


export async function sendMessage(
  conversationId: number,
  content: string
) {
  return request(
    `/api/chat/conversations/${conversationId}/messages`,
    {
      method: "POST",
      body: JSON.stringify({
        content,
      }),
    }
  );
}


// ==============================
// CARD APPROVAL
// ==============================

export async function approveCardAction(
  conversationId: number,
  approved: boolean
) {
  return request(
    `/api/chat/conversations/${conversationId}/card-approval`,
    {
      method: "POST",
      body: JSON.stringify({
        approved,
      }),
    }
  );
}

