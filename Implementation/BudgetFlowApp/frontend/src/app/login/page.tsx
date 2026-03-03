"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch, ApiError } from "@/lib/api";
import { setAccessToken, setRefreshToken, normalizeEmail, validateEmail } from "@/lib/auth";
import Card from "@/components/ui/Card";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import Alert from "@/components/ui/Alert";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [apiError, setApiError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setApiError("");
    const errs: Record<string, string> = {};
    const em = normalizeEmail(email);
    const emailErr = validateEmail(em);
    if (emailErr) errs.email = emailErr;
    if (!password) errs.password = "Password is required";
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setErrors({});
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.set("username", em);
      params.set("password", password);
      const data = await apiFetch<{ access_token: string; refresh_token?: string }>("/api/v1/auth/login", {
        method: "POST",
        formUrlEncoded: params,
        auth: false,
      });
      setAccessToken(data.access_token);
      if (data.refresh_token) setRefreshToken(data.refresh_token);
      router.push("/dashboard");
    } catch (err) {
      setApiError((err as ApiError).detail || "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <Card className="w-full max-w-sm">
        <h1 className="mb-6 text-xl font-semibold text-neutral-900">Login</h1>
        {apiError && <div className="mb-4"><Alert>{apiError}</Alert></div>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} error={errors.email} autoComplete="email" />
          <Input label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} error={errors.password} autoComplete="current-password" />
          <Button type="submit" loading={loading} className="w-full">Login</Button>
        </form>
        <p className="mt-4 text-center text-sm text-neutral-500">
          No account?{" "}
          <Link href="/signup" className="font-medium text-neutral-900 hover:underline">Sign up</Link>
        </p>
      </Card>
    </div>
  );
}
