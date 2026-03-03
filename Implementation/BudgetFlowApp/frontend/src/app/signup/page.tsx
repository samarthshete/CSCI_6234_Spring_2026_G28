"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiFetch, ApiError } from "@/lib/api";
import { setAccessToken, setRefreshToken, normalizeEmail, validateEmail, validatePassword } from "@/lib/auth";
import Card from "@/components/ui/Card";
import Input from "@/components/ui/Input";
import Button from "@/components/ui/Button";
import Alert from "@/components/ui/Alert";

export default function SignupPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [apiError, setApiError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setApiError("");
    const errs: Record<string, string> = {};
    if (!name.trim()) errs.name = "Name is required";
    const em = normalizeEmail(email);
    const emailErr = validateEmail(em);
    if (emailErr) errs.email = emailErr;
    const passErr = validatePassword(password);
    if (passErr) errs.password = passErr;
    if (password !== confirm) errs.confirm = "Passwords do not match";
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setErrors({});
    setLoading(true);
    try {
      await apiFetch("/api/v1/auth/signup", {
        method: "POST",
        body: { email: em, name: name.trim(), password },
        auth: false,
      });
      const params = new URLSearchParams();
      params.set("username", em);
      params.set("password", password);
      const loginData = await apiFetch<{ access_token: string; refresh_token?: string }>("/api/v1/auth/login", {
        method: "POST",
        formUrlEncoded: params,
        auth: false,
      });
      setAccessToken(loginData.access_token);
      if (loginData.refresh_token) setRefreshToken(loginData.refresh_token);
      router.push("/dashboard");
    } catch (err) {
      setApiError((err as ApiError).detail || "Signup failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <Card className="w-full max-w-sm">
        <h1 className="mb-6 text-xl font-semibold text-neutral-900">Sign Up</h1>
        {apiError && <div className="mb-4"><Alert>{apiError}</Alert></div>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <Input label="Name" value={name} onChange={(e) => setName(e.target.value)} error={errors.name} autoComplete="name" />
          <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} error={errors.email} autoComplete="email" />
          <Input label="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} error={errors.password} autoComplete="new-password" />
          <Input label="Confirm Password" type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} error={errors.confirm} autoComplete="new-password" />
          <Button type="submit" loading={loading} className="w-full">Create Account</Button>
        </form>
        <p className="mt-4 text-center text-sm text-neutral-500">
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-neutral-900 hover:underline">Login</Link>
        </p>
      </Card>
    </div>
  );
}
