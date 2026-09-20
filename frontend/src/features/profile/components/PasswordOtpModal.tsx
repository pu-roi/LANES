"use client";

import React, { useState, useEffect, useRef } from "react";
import { Modal } from "@/shared/ui";
import { ChevronLeft, Loader2, Mail } from "lucide-react";

interface PasswordOtpModalProps {
  isOpen: boolean;
  onClose: () => void;
  email: string;
  onVerify: (code: string) => Promise<void>;
  onResendOtp: () => Promise<number | void>;
  initialCooldown?: number;
}

export default function PasswordOtpModal({
  isOpen,
  onClose,
  email,
  onVerify,
  onResendOtp,
  initialCooldown = 60,
}: PasswordOtpModalProps) {
  const [otpCode, setOtpCode] = useState("");
  const [isVerifying, setIsVerifying] = useState(false);
  const [isResending, setIsResending] = useState(false);
  const [errorMsg, setErrorMsg] = useState("");
  const [cooldownSeconds, setCooldownSeconds] = useState(initialCooldown);

  const isSubmittingRef = useRef(false);

  // Initialize and tick cooldown timer
  useEffect(() => {
    if (!isOpen) {
      setOtpCode("");
      setErrorMsg("");
      setIsVerifying(false);
      isSubmittingRef.current = false;
      return;
    }
    setCooldownSeconds(initialCooldown || 60);
    // Auto-focus first input on open
    const timer = setTimeout(() => {
      document.getElementById("pwd-otp-digit-0")?.focus();
    }, 100);
    return () => clearTimeout(timer);
  }, [isOpen, initialCooldown]);

  useEffect(() => {
    if (cooldownSeconds <= 0) return;
    const timer = setInterval(() => {
      setCooldownSeconds((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [cooldownSeconds]);

  const formatCooldown = (sec: number) => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}m ${s.toString().padStart(2, "0")}s`;
  };

  const handleTriggerVerify = async (codeToVerify: string) => {
    if (codeToVerify.length !== 6 || isSubmittingRef.current) return;

    isSubmittingRef.current = true;
    setIsVerifying(true);
    setErrorMsg("");

    try {
      await onVerify(codeToVerify);
    } catch (err: any) {
      const detail =
        err?.response?.data?.detail ||
        err?.message ||
        "Invalid verification code. Please try again.";
      setErrorMsg(detail);
      setOtpCode("");
      isSubmittingRef.current = false;
      setTimeout(() => {
        document.getElementById("pwd-otp-digit-0")?.focus();
      }, 50);
    } finally {
      setIsVerifying(false);
    }
  };

  const handleResend = async () => {
    if (isResending || cooldownSeconds > 0) return;
    setIsResending(true);
    setErrorMsg("");
    try {
      const nextCd = await onResendOtp();
      setCooldownSeconds(typeof nextCd === "number" ? nextCd : 60);
      setOtpCode("");
      setTimeout(() => {
        document.getElementById("pwd-otp-digit-0")?.focus();
      }, 50);
    } catch (err: any) {
      const detail =
        err?.response?.data?.detail ||
        err?.message ||
        "Failed to resend code. Please wait.";
      setErrorMsg(detail);
    } finally {
      setIsResending(false);
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} bare title="Verify Password Change">
      <div className="bg-white rounded-2xl shadow-2xl p-6 sm:p-8 space-y-6 border border-slate-100 text-center">
        {/* Email Icon Header */}
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-blue-50 text-blue-600 ring-8 ring-blue-50/50 mx-auto">
          <Mail className="w-7 h-7" />
        </div>

        <div className="space-y-1">
          <h3 className="text-xl font-bold text-slate-900 tracking-tight">
            Check your inbox
          </h3>
          <p className="text-sm text-slate-500 max-w-xs mx-auto">
            We sent a 6-digit confirmation code to
            <br />
            <span className="font-semibold text-slate-900 break-all">{email}</span>
          </p>
        </div>

        {/* 6-box Numeric Digit Inputs with Zero-Click Auto-Submit */}
        <div className="flex justify-center items-center gap-2 sm:gap-3 py-1">
          {[0, 1, 2, 3, 4, 5].map((index) => {
            const digit = otpCode[index] || "";
            return (
              <input
                key={index}
                id={`pwd-otp-digit-${index}`}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                disabled={isVerifying}
                autoFocus={index === 0}
                onChange={(e) => {
                  const val = e.target.value.replace(/\D/g, "");
                  const newOtp = otpCode.split("");
                  newOtp[index] = val;
                  const joined = newOtp.join("").slice(0, 6);
                  setOtpCode(joined);
                  if (val && index < 5) {
                    const nextInput = document.getElementById(`pwd-otp-digit-${index + 1}`);
                    nextInput?.focus();
                  }
                  if (joined.length === 6) {
                    handleTriggerVerify(joined);
                  }
                }}
                onKeyDown={(e) => {
                  if (e.key === "Backspace" && !digit && index > 0) {
                    const prevInput = document.getElementById(`pwd-otp-digit-${index - 1}`);
                    prevInput?.focus();
                  }
                }}
                onPaste={(e) => {
                  e.preventDefault();
                  const pasted = e.clipboardData
                    .getData("text")
                    .replace(/\D/g, "")
                    .slice(0, 6);
                  setOtpCode(pasted);
                  if (pasted.length === 6) {
                    handleTriggerVerify(pasted);
                  } else if (pasted.length > 0) {
                    const targetIdx = Math.min(pasted.length, 5);
                    document.getElementById(`pwd-otp-digit-${targetIdx}`)?.focus();
                  }
                }}
                className={`w-11 h-13 sm:w-12 sm:h-14 text-center text-xl sm:text-2xl font-bold rounded-xl border transition-all duration-200 outline-none select-none ${
                  digit
                    ? "border-blue-600 bg-white text-blue-600 shadow-sm ring-2 ring-blue-100"
                    : "border-slate-200 bg-slate-50/80 text-slate-900 focus:border-blue-500 focus:bg-white focus:ring-4 focus:ring-blue-100"
                } ${isVerifying ? "opacity-60 cursor-wait" : ""}`}
              />
            );
          })}
        </div>

        {/* Error Notification */}
        {errorMsg && (
          <div className="p-3 text-xs text-rose-600 bg-rose-50 border border-rose-200 rounded-lg text-center font-medium animate-shake">
            {errorMsg}
          </div>
        )}

        {/* Bottom Actions */}
        <div className="mt-4 flex items-center justify-between pt-4 border-t border-slate-100">
          <button
            type="button"
            onClick={onClose}
            disabled={isVerifying}
            className="flex items-center text-sm font-semibold text-slate-500 hover:text-slate-800 transition-colors cursor-pointer disabled:opacity-50"
          >
            <ChevronLeft className="w-4 h-4 mr-1" />
            Cancel
          </button>

          <div className="flex items-center gap-3">
            {isVerifying ? (
              <span className="flex items-center gap-2 text-xs sm:text-sm text-blue-600 font-semibold">
                <Loader2 className="animate-spin h-4 w-4 text-blue-500" />
                Verifying...
              </span>
            ) : (
              <button
                type="button"
                onClick={handleResend}
                disabled={isResending || cooldownSeconds > 0}
                className={`text-xs sm:text-sm font-semibold transition-colors px-3 py-1.5 rounded-lg border cursor-pointer ${
                  cooldownSeconds > 0
                    ? "border-slate-200 bg-slate-100 text-slate-400 cursor-not-allowed"
                    : "border-slate-300 bg-white hover:bg-slate-50 text-slate-700 shadow-sm"
                }`}
              >
                {isResending
                  ? "Sending..."
                  : cooldownSeconds > 0
                  ? `Resend (${formatCooldown(cooldownSeconds)})`
                  : "Resend Code"}
              </button>
            )}
          </div>
        </div>
      </div>
    </Modal>
  );
}
