"use client";

import { useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { authClient } from "@/features/auth/api/authClient";
import { ChevronLeft } from "lucide-react";
import Link from "next/link";
import { useToast } from "@/shared/ui/Toast";
import { Button } from "@/shared/ui/Button";
import { useQueryClient } from "@tanstack/react-query";

function VerifyContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const email = searchParams.get("email") || "";
  const queryClient = useQueryClient();

  const [otp, setOtp] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const { success } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const result = await authClient.verifyOtp(email, otp) as any;
      // Store token with correct key for useAuth
      localStorage.setItem("lanes_token", result.access_token);
      await queryClient.invalidateQueries({ queryKey: ['auth-user'] });
      success("Verification Successful", "Your email has been verified. You are now logged in!");
      router.push("/");
    } catch (err: any) {
      console.error(err);
      setError(err.response?.data?.detail || "Invalid verification code.");
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setLoading(true);
    setError("");
    try {
      await authClient.resendOtp(email);
      success("OTP Sent", "A new code has been sent to your email.");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to resend code.");
    } finally {
      setLoading(false);
    }
  };

  if (!email) {
    return (
      <div className="text-center mt-10">
        <p className="text-muted-foreground">Invalid verification request.</p>
        <Link href="/register" className="text-primary hover:underline mt-4 block">
          Return to registration
        </Link>
      </div>
    );
  }

  return (
    <div className="w-full max-w-md mx-auto mt-12 px-6">
      <Link href="/register" className="inline-flex items-center text-muted-foreground hover:text-foreground mb-8">
        <ChevronLeft className="w-5 h-5 mr-1" />
        Back
      </Link>

      <div className="mb-8">
        <h1 className="text-3xl font-extrabold text-foreground tracking-tight">Verify Email</h1>
        <p className="text-muted-foreground mt-2">
          We sent a 6-digit code to <strong className="text-foreground">{email}</strong>.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        <input 
          type="text" 
          placeholder="000000" 
          required
          maxLength={6}
          value={otp} 
          onChange={e => setOtp(e.target.value.replace(/\D/g, ''))}
          className="w-full text-center text-3xl tracking-[1em] font-mono p-4 rounded-xl bg-muted/50 border-none outline-none focus:ring-2 focus:ring-primary/50 text-foreground"
        />

        {error && (
          <div className="p-3 bg-red-500/20 border border-red-500/50 rounded-xl text-red-500 text-sm">
            {error}
          </div>
        )}

        <Button
          type="submit"
          size="lg"
          disabled={loading || otp.length !== 6}
          className="w-full text-lg rounded-xl shadow-lg shadow-blue-500/25"
        >
          {loading ? "Verifying..." : "Verify & Continue"}
        </Button>
      </form>

      <div className="mt-8 text-center">
        <p className="text-sm text-muted-foreground">
          Didn't receive the code?{" "}
          <button 
            type="button" 
            onClick={handleResend}
            disabled={loading}
            className="text-primary hover:underline font-semibold disabled:opacity-50"
          >
            Resend it
          </button>
        </p>
      </div>
    </div>
  );
}

export default function VerifyPage() {
  return (
    <div className="w-full">
      <Suspense fallback={<div className="p-10 text-center">Loading...</div>}>
        <VerifyContent />
      </Suspense>
    </div>
  );
}
