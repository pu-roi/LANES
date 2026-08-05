"use client";

import { Construction, Loader2 } from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function ProfileView() {
  const { isAuthenticated, isLoading, logout } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isAuthenticated) {
      if (typeof window !== 'undefined' && sessionStorage.getItem('lanes_post_intent')) {
        sessionStorage.removeItem('lanes_post_intent');
        router.push('/feed?openPostModal=true');
      }
    }
  }, [isAuthenticated, router]);

  if (isLoading) {
    return (
      <div className="flex-1 bg-gray-50 flex items-center justify-center p-4">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  // The NavigationWrapper guarantees we are authenticated if we reach this return
  return (
    <div className="flex-1 bg-gray-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8 text-center max-w-md w-full">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-amber-100 text-amber-600 mb-6">
          <Construction className="w-8 h-8" />
        </div>
        <h1 className="text-2xl font-bold text-slate-900 mb-2">Profile Under Development</h1>
        <p className="text-slate-600 mb-6">
          The user profile and settings page is currently being developed. Stay tuned!
        </p>
        <button
          onClick={() => logout()}
          className="px-4 py-2 bg-red-50 text-red-600 rounded-md font-medium hover:bg-red-100 transition-colors cursor-pointer"
        >
          Log Out
        </button>
      </div>
    </div>
  );
}
