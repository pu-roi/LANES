"use client";

import Link from "next/link";
import { User } from "lucide-react";
import { Button } from "@/shared/ui";

/** The original Report Flood sign-in view, shared by both reporting modes. */
export function FloodReportLoginGate({ redirect = "/map?action=report" }: { redirect?: string }) {
  return (
    <div className="flex flex-col items-center justify-center h-full p-6 text-center space-y-4">
      <div className="w-16 h-16 bg-orange-100 rounded-full flex items-center justify-center text-orange-500 mb-2 mt-8">
        <User className="w-8 h-8" />
      </div>
      <h3 className="text-lg font-bold text-gray-900">Login Required</h3>
      <p className="text-sm text-gray-500">
        You need to be logged in to report a flood and help the community.
      </p>
      <Link href={`/login?redirect=${encodeURIComponent(redirect)}`} className="w-full mt-4">
        <Button className="w-full">Go to Login</Button>
      </Link>
    </div>
  );
}
