"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Input } from "@/shared/ui/Input";
import { Button } from "@/shared/ui/Button";
import { Loader2, Eye, EyeOff } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useToast } from "@/shared/ui/Toast";
import { FcGoogle } from "react-icons/fc";

export default function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get('redirect');
  const { info } = useToast();
  const { login, isLoggingIn } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    
    const formData = new URLSearchParams();
    formData.append("username", username);
    formData.append("password", password);

    try {
      const data = await login(formData);
      
      // Determine role by fetching profile
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
      const profileResponse = await fetch(`${baseUrl}/auth/test-token`, {
        method: "POST",
        headers: { "Authorization": `Bearer ${data.access_token}` }
      });
      
      if (profileResponse.ok) {
        const profile = await profileResponse.json();
        if (profile.role?.name === "Super Admin") {
          router.push("/admin/dashboard");
          return;
        } else if (profile.role?.name !== "Commuter") {
          router.push("/");
          return;
        }
      }
      
      // If Commuter, auth state is updated globally. No reload needed.
    } catch (err: any) {
      try {
        const parsed = JSON.parse(err.message);
        if (parsed.code === "UNVERIFIED_ACCOUNT") {
          const resendUrl = process.env.NEXT_PUBLIC_API_URL || "/api/v1";
          await fetch(`${resendUrl}/auth/resend-otp`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: parsed.email })
          });
          router.push(`/verify?email=${encodeURIComponent(parsed.email)}`);
          return;
        }
      } catch (e) {
        // Not a JSON string
      }
      setErrorMsg(err.message || "Login failed. Please check your credentials.");
    }
  };

  return (
    <form onSubmit={handleLogin} className="space-y-4">
      {errorMsg && (
        <div className="p-3 bg-red-50 text-red-700 text-sm rounded-lg font-medium">
          {errorMsg}
        </div>
      )}
      <Input
        label="Email or Username"
        labelClassName="text-white lg:text-slate-700 font-semibold drop-shadow-sm"
        type="text"
        placeholder="Enter your email or username"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
        required
      />
      <Input
        label="Password"
        labelClassName="text-white lg:text-slate-700 font-semibold drop-shadow-sm"
        type={showPassword ? "text" : "password"}
        placeholder="••••••••"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
        className="text-gray-900 bg-white"
        rightIcon={
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="p-1 text-gray-400 hover:text-gray-600 focus:outline-none"
            tabIndex={-1}
          >
            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        }
      />
      <div className="flex justify-end mt-1">
        <a href="#" className="text-sm text-blue-200 lg:text-blue-600 font-medium hover:text-white lg:hover:text-blue-500 hover:underline transition-colors">Forgot password?</a>
      </div>
      <div className="pt-2">
        <Button type="submit" className="w-full" disabled={isLoggingIn}>
          {isLoggingIn ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Signing in...
            </>
          ) : (
            "Sign In"
          )}
        </Button>
      </div>
      
      <div className="relative flex items-center py-2">
        <div className="flex-grow border-t border-white/20 lg:border-slate-200"></div>
        <span className="flex-shrink-0 mx-4 text-white/80 lg:text-slate-400 text-sm font-medium">or</span>
        <div className="flex-grow border-t border-white/20 lg:border-slate-200"></div>
      </div>

      <div>
        <button
          type="button"
          onClick={() => info("Under Development", "Google Sign-In is currently under development.")}
          className="w-full flex items-center justify-center gap-2 bg-white text-slate-700 border border-slate-300 font-medium py-2.5 rounded-lg hover:bg-slate-50 transition-colors shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500/50"
        >
          <FcGoogle className="w-5 h-5" />
          Sign in with Google
        </button>
      </div>

      <div className="text-center pt-2">
        <p className="text-sm text-blue-100 lg:text-slate-600">
          Don't have an account?{" "}
          <Link
            href={redirectTo ? `/register?redirect=${encodeURIComponent(redirectTo)}` : "/register"}
            className="text-white lg:text-blue-600 font-bold lg:font-semibold hover:text-blue-200 lg:hover:text-blue-700 hover:underline transition-colors"
          >
            Sign up
          </Link>
        </p>
      </div>
    </form>
  );
}
