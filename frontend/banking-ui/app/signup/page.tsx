
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

import { signup } from "@/lib/api";


export default function SignupPage() {

  const router = useRouter();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);


  async function handleSignup(
    event: React.FormEvent
  ) {

    event.preventDefault();

    setError("");
    setLoading(true);

    try {

      await signup(
        email,
        password,
        name
      );

      router.push("/login");

    } catch (error) {

      setError(
        error instanceof Error
          ? error.message
          : "Signup failed"
      );

    } finally {

      setLoading(false);

    }
  }


  return (
    <main className="flex min-h-screen items-center justify-center">

      <div className="w-full max-w-md">

        <h1 className="mb-6 text-3xl font-bold">
          Create Account
        </h1>


        <form
          onSubmit={handleSignup}
          className="space-y-4"
        >

          <input
            type="text"
            placeholder="Name"
            value={name}
            onChange={(e) =>
              setName(e.target.value)
            }
            className="w-full rounded border p-3"
            required
          />


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
            <p className="rounded bg-red-50 p-3 text-sm text-red-600">
              {error}
            </p>
          )}


          <button
            type="submit"
            disabled={loading}
            className="w-full rounded bg-black p-3 text-white disabled:opacity-50"
          >
            {loading
              ? "Creating account..."
              : "Sign Up"}
          </button>

        </form>


        <p className="mt-6 text-center text-sm text-gray-500">

          Already have an account?{" "}

          <button
            type="button"
            onClick={() => router.push("/login")}
            className="font-medium text-black underline"
          >
            Login
          </button>

        </p>

      </div>

    </main>
  );
}
