"use client";

import { motion } from "framer-motion";
import { Logo } from "@/shared/ui/Logo";
import LoginForm from "@/features/auth/LoginForm";
import { useAuth } from "@/hooks/useAuth";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";
import { Loader2 } from "lucide-react";

function LoginPageContent() {
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


  return (
    <div className="relative flex-1 w-full h-[100dvh] overflow-hidden bg-slate-50 flex flex-col lg:flex-row">
      
      {/* Mobile Background Image (Hidden on Desktop) */}
      <div 
        className="fixed inset-0 z-0 bg-cover bg-center bg-no-repeat lg:hidden"
        style={{ backgroundImage: "url('/bg-image/agnes.png')" }}
      />
      <div className="fixed inset-0 z-0 bg-blue-900/55 mix-blend-multiply lg:hidden" />
      <div className="fixed inset-0 z-0 bg-gradient-to-t from-slate-950/80 via-blue-950/45 to-blue-900/40 lg:hidden" />
      
      <motion.div
        initial={{ x: "-100%" }}
        animate={{ x: 0 }}
        transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        className="fixed top-0 left-0 bottom-0 z-10 hidden lg:flex flex-col w-[46%] xl:w-[44%] text-white p-8 xl:p-12 shadow-2xl"
        style={{ clipPath: "polygon(0 0, 100% 0, 80% 100%, 0 100%)" }}
      >
        {/* Background Image */}
        <div 
          className="absolute inset-0 bg-cover bg-center bg-no-repeat"
          style={{ backgroundImage: "url('/bg-image/agnes.png')" }}
        />
        {/* Overlay with balanced blue tint */}
        <div className="absolute inset-0 bg-blue-900/65 mix-blend-multiply" />
        <div className="absolute inset-0 bg-gradient-to-br from-blue-900/70 via-blue-950/60 to-slate-900/75" />

        {/* Content */}
        <div className="relative z-10 flex flex-col h-full">
          {/* Logo & Brand */}
          <Logo size="xl" theme="dark" className="mb-6 xl:mb-8" />

          {/* Desktop Hero Content */}
          <div className="mt-auto mb-12 xl:mb-16 max-w-[280px] sm:max-w-[320px] xl:max-w-sm 2xl:max-w-md">
            <h1 className="text-3xl xl:text-4xl 2xl:text-5xl font-extrabold mb-4 xl:mb-6 leading-[1.15] tracking-tight text-white drop-shadow-md">
              Your safe route <br/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-300 to-cyan-300 drop-shadow-sm">
                through the storm.
              </span>
            </h1>
            
            <p className="text-blue-100/90 text-sm xl:text-base font-medium leading-relaxed mb-8 xl:mb-12">
              Join the community network. Report hazards, discover safe alternatives, and help everyone get home securely.
            </p>

            <div className="grid grid-cols-2 gap-4 xl:gap-8 pt-6 xl:pt-8 border-t border-white/15">
              <div>
                <div className="text-xl xl:text-2xl font-extrabold text-white mb-1 tracking-tight">100%</div>
                <div className="text-blue-200/80 text-[10px] xl:text-xs font-semibold uppercase tracking-wider">Community Driven</div>
              </div>
              <div>
                <div className="text-xl xl:text-2xl font-extrabold text-white mb-1 tracking-tight">Real-time</div>
                <div className="text-blue-200/80 text-[10px] xl:text-xs font-semibold uppercase tracking-wider">Hazard Alerts</div>
              </div>
            </div>
          </div>

          {/* Tribute Note pinned at bottom flush left */}
          <p className="absolute bottom-2 left-0 text-[10px] xl:text-[11px] font-medium tracking-wide text-blue-200/60 italic text-left">
            In heartfelt tribute to Agnes Avellana & Sarah Montemayor
          </p>
        </div>
      </motion.div>

      {/* RIGHT SECTION (Form) */}
      <motion.div
        initial={{ x: "100%" }}
        animate={{ x: 0 }}
        transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        className="relative z-20 flex-1 flex flex-col items-center p-6 lg:p-12 overflow-y-auto lg:ml-[44%] xl:ml-[42%]"
      >
        <div className="w-full flex flex-col items-center my-auto">
          {/* Mobile Header (Hidden on Desktop) */}
          <Logo size="lg" theme="dark" className="lg:hidden w-full justify-center max-w-xl mb-8" />

          {/* Form Container */}
          <div className="w-full max-w-xl lg:ml-[-6%] xl:ml-[-8%] z-10 relative">
            {/* Form Header */}
            <div className="text-center lg:text-left space-y-2 mb-8 pl-2">
              <h2 className="text-3xl font-extrabold text-white lg:text-slate-900 tracking-tight drop-shadow-md lg:drop-shadow-none">Welcome back</h2>
              <p className="text-sm text-blue-100 lg:text-slate-500 font-medium">Log in to view your profile and saved routes.</p>
            </div>

            {/* Form Container Card matching RegisterForm */}
            <div className="w-full max-w-xl mx-auto bg-white/10 backdrop-blur-sm lg:bg-white rounded-2xl shadow-2xl lg:shadow-[0_8px_40px_rgba(59,130,246,0.15)] border border-white/20 lg:border-slate-200/80 border-t-4 border-t-blue-600 lg:ring-1 lg:ring-blue-100/50">
              <div className="p-8 pt-10">
                <LoginForm />
              </div>
            </div>

            {/* Mobile Tribute Note */}
            <p className="lg:hidden text-center text-[11px] text-blue-100/70 mt-6 italic">
              In heartfelt tribute to Agnes Avellana & Sarah Montemayor
            </p>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="flex-1 bg-gray-50 flex items-center justify-center p-4 min-h-screen">
          <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
        </div>
      }
    >
      <LoginPageContent />
    </Suspense>
  );
}
