"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { login } from "@/lib/api";


export default function LoginPage() {
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");


  async function handleLogin(
    event: React.FormEvent
  ) {
    event.preventDefault();

    setError("");

    try {
      const data = await login(
        email,
        password
      );

      localStorage.setItem(
        "access_token",
        data.access_token
      );

      router.push("/chat");

    } catch (error) {
      setError(
        error instanceof Error
          ? error.message
          : "Login failed"
      );
    }
  }


  return (
    <main className="flex min-h-screen items-center justify-center">

      <div className="w-full max-w-md">

        <h1 className="mb-6 text-3xl font-bold">
          Banking Support
        </h1>


        <form
          onSubmit={handleLogin}
          className="space-y-4"
        >

          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) =>
              setEmail(e.target.value)
            }
            className="w-full rounded border p-3"
            required
          />


          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) =>
              setPassword(e.target.value)
            }
            className="w-full rounded border p-3"
            required
          />


          {error && (
            <p className="text-red-500">
              {error}
            </p>
          )}


          <button
            type="submit"
            className="w-full rounded bg-black p-3 text-white"
          >
            Login
          </button>

        </form>

      </div>

    </main>
  );
}