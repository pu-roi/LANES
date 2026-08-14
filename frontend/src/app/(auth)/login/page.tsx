"use client";

import { motion } from "framer-motion";
import { Logo } from "@/shared/ui/Logo";
import LoginForm from "@/features/auth/LoginForm";
import { useAuth } from "@/hooks/useAuth";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect } from "react";
import { Loader2 } from "lucide-react";

export default function LoginPage() {
  const { isAuthenticated, isLoading, user } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    if (isAuthenticated && !isLoading) {
      const redirectUrl = searchParams.get('redirect');
      
      if (redirectUrl && redirectUrl.startsWith('/')) {
        router.push(redirectUrl);
      } else if (typeof window !== 'undefined' && sessionStorage.getItem('lanes_post_intent')) {
        sessionStorage.removeItem('lanes_post_intent');
        router.push('/feed?openPostModal=true');
      } else {
        const u = user as any;
        if (u?.role?.name === 'Super Admin' || u?.role?.name === 'Moderator' || u?.role?.name === 'DRRM Officer') {
          router.push('/admin/dashboard');
        } else {
          router.push('/map');
        }
      }
    }
  }, [isAuthenticated, isLoading, router, user, searchParams]);

  if (isLoading || isAuthenticated) {
    return (
      <div className="flex-1 bg-gray-50 flex items-center justify-center p-4">
        <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="relative flex-1 w-full h-[100dvh] overflow-hidden bg-slate-50 flex flex-col lg:flex-row">
      
      {/* Mobile Background Image (Hidden on Desktop) */}
      <div 
        className="fixed inset-0 z-0 bg-cover bg-center bg-no-repeat lg:hidden"
        style={{ backgroundImage: "url('https://images.unsplash.com/photo-1527018601619-a508a2be00cd?q=80&w=2070&auto=format&fit=crop')" }}
      />
      <div className="fixed inset-0 z-0 bg-blue-900/40 mix-blend-multiply lg:hidden" />
      <div className="fixed inset-0 z-0 bg-gradient-to-br from-slate-900/50 to-blue-900/60 lg:hidden" />
      
      <motion.div
        initial={{ x: "-100%" }}
        animate={{ x: 0 }}
        transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        className="fixed top-0 left-0 bottom-0 z-10 hidden lg:flex flex-col w-[45%] text-white p-12 shadow-2xl"
        style={{ clipPath: "polygon(0 0, 100% 0, 75% 100%, 0 100%)" }}
      >
        {/* Background Image */}
        <div 
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{ backgroundImage: "url('https://images.unsplash.com/photo-1527018601619-a508a2be00cd?q=80&w=2070&auto=format&fit=crop')" }}
        />
        {/* Overlay */}
        <div className="absolute inset-0 bg-blue-900/85 mix-blend-multiply" />
        <div className="absolute inset-0 bg-gradient-to-br from-blue-900/90 to-slate-900/80" />

        {/* Content */}
        <div className="relative z-10 flex flex-col h-full">
          {/* Logo & Brand */}
          <Logo size="xl" theme="dark" className="mb-8" />

          {/* Desktop Hero Content */}
          <div className="mt-auto mb-16 pr-8">
            <div className="inline-flex items-center px-3 py-1.5 rounded-full bg-blue-500/20 border border-blue-400/30 backdrop-blur-md text-blue-100 text-sm font-semibold tracking-wide mb-8 shadow-sm">
              <span className="w-2 h-2 rounded-full bg-cyan-400 mr-2 animate-pulse shadow-[0_0_8px_rgba(34,211,238,0.8)]" />
              Live Flood Navigation
            </div>
            
            <h1 className="text-4xl lg:text-5xl font-extrabold mb-6 leading-[1.1] tracking-tight text-white drop-shadow-md">
              Your safe route <br/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-300 to-cyan-300 drop-shadow-sm">
                through the storm.
              </span>
            </h1>
            
            <p className="text-blue-100/90 text-base font-medium leading-relaxed max-w-md mb-12">
              Join the community network. Report hazards, discover safe alternatives, and help everyone get home securely.
            </p>

            <div className="grid grid-cols-2 gap-8 pt-8 border-t border-white/15">
              <div>
                <div className="text-2xl font-extrabold text-white mb-1 tracking-tight">100%</div>
                <div className="text-blue-200/80 text-xs font-semibold uppercase tracking-wider">Community Driven</div>
              </div>
              <div>
                <div className="text-2xl font-extrabold text-white mb-1 tracking-tight">Real-time</div>
                <div className="text-blue-200/80 text-xs font-semibold uppercase tracking-wider">Hazard Alerts</div>
              </div>
            </div>
          </div>
        </div>
      </motion.div>

      {/* RIGHT SECTION (Form) */}
      <motion.div
        initial={{ x: "100%" }}
        animate={{ x: 0 }}
        transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        className="relative z-20 flex-1 flex flex-col items-center p-6 lg:p-12 overflow-y-auto lg:ml-[45%]"
      >
        <div className="w-full flex flex-col items-center my-auto">
          {/* Mobile Header (Hidden on Desktop) */}
          <Logo size="lg" theme="dark" className="lg:hidden w-full justify-center max-w-xl mb-8" />

          {/* Form Container */}
          <div className="w-full max-w-xl lg:ml-[-10%] z-10 relative">
            {/* Form Header */}
            <div className="text-center lg:text-left space-y-2 mb-8 pl-2">
              <h2 className="text-3xl font-extrabold text-white lg:text-slate-900 tracking-tight drop-shadow-md lg:drop-shadow-none">Welcome back</h2>
              <p className="text-blue-100 lg:text-slate-500 font-medium">Log in to view your profile and saved routes.</p>
            </div>

            {/* Form Container Card matching RegisterForm */}
            <div className="w-full max-w-xl mx-auto bg-white/20 backdrop-blur-2xl lg:bg-white rounded-2xl shadow-2xl lg:shadow-[0_8px_40px_rgba(59,130,246,0.15)] lg:border lg:border-slate-200/80 border border-white/40 border-t-4 border-t-blue-600 lg:ring-1 lg:ring-blue-100/50">
              <div className="p-8 pt-10">
                <LoginForm />
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
