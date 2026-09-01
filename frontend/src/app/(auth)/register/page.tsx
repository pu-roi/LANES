"use client";

import { RegisterForm } from "@/features/auth/components/RegisterForm";
import Link from "next/link";
import { motion } from "framer-motion";
import { Logo } from "@/shared/ui/Logo";
import { useSearchParams } from "next/navigation";

import { Suspense } from "react";
import { Loader2 } from "lucide-react";

function RegisterPageContent() {
  const searchParams = useSearchParams();
  const redirectTo = searchParams.get('redirect') || undefined;
  return (
    <div className="relative flex-1 w-full overflow-hidden bg-slate-50 flex flex-col lg:flex-row">
      
      {/* Mobile Background Image (Hidden on Desktop) */}
      <div 
        className="fixed inset-0 z-0 bg-cover bg-center bg-no-repeat brightness-110 lg:hidden"
        style={{ backgroundImage: "url('/bg-image/sarah.png')" }}
      />
      <div className="fixed inset-0 z-0 bg-blue-800/35 mix-blend-multiply lg:hidden" />
      <div className="fixed inset-0 z-0 bg-gradient-to-t from-slate-950/60 via-blue-950/25 to-transparent lg:hidden" />
      
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
          style={{ backgroundImage: "url('/bg-image/sarah.png')" }}
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
        className="relative z-20 flex-1 flex flex-col items-center justify-center p-4 sm:p-6 lg:p-12 min-h-screen overflow-y-auto lg:ml-[44%] xl:ml-[42%] pb-[calc(var(--bottom-nav-height,1rem)+env(safe-area-inset-bottom,1rem))]"
      >
        <div className="w-full flex flex-col items-center my-auto py-6 sm:py-8">
          {/* Mobile Header (Hidden on Desktop) */}
          <Logo size="lg" theme="dark" className="lg:hidden w-full justify-center max-w-xl mb-6" />

          {/* Form Container */}
          {/* We use a negative left margin on desktop to pull the form slightly left to balance the slanted space */}
          <div className="w-full max-w-xl lg:ml-[-6%] xl:ml-[-8%] z-10 relative">
            {/* Form Header */}
            <div className="text-center lg:text-left space-y-1 sm:space-y-2 mb-6 sm:mb-8 pl-2">
              <h2 className="text-2xl sm:text-3xl font-extrabold text-white lg:text-slate-900 tracking-tight drop-shadow-md lg:drop-shadow-none">Create an account</h2>
              <p className="text-sm sm:text-base text-blue-100 lg:text-slate-500 font-medium">Join LANES as a citizen to get started.</p>
            </div>

            <RegisterForm redirectTo={redirectTo} />

            <div className="text-center pt-6 sm:pt-8 pb-4">
              <p className="text-sm text-blue-100 lg:text-slate-600">
                Already have an account?{" "}
                <Link href={redirectTo ? `/login?redirect=${encodeURIComponent(redirectTo)}` : "/login"} className="text-white lg:text-blue-600 font-bold lg:font-medium hover:text-blue-200 lg:hover:text-blue-700 hover:underline transition-colors">
                  Log in
                </Link>
              </p>
            </div>

            {/* Mobile Tribute Note */}
            <p className="lg:hidden text-center text-[11px] text-blue-100/70 pt-2 italic">
              In heartfelt tribute to Agnes Avellana & Sarah Montemayor
            </p>
          </div>
        </div>
      </motion.div>

    </div>
  );
}

export default function RegisterPage() {
  return (
    <Suspense
      fallback={
        <div className="flex-1 bg-gray-50 flex items-center justify-center p-4 min-h-screen">
          <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
        </div>
      }
    >
      <RegisterPageContent />
    </Suspense>
  );
}
