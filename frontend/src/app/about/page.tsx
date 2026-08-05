import { Info, Users, Map as MapIcon, Cpu, Construction, ChevronRight } from "lucide-react";
import React from "react";
import Image from "next/image";
import Link from "next/link";

export const metadata = {
  title: "About | LANES",
  description: "About the LANES Project",
};

export default function AboutPage() {
  return (
    <div className="flex-1 bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto space-y-8 sm:space-y-12">
        
        {/* Breadcrumbs */}
        <nav className="flex text-sm text-gray-500 mb-4 sm:mb-8" aria-label="Breadcrumb">
          <ol className="inline-flex items-center space-x-1 md:space-x-3">
            <li className="inline-flex items-center">
              <Link href="/" className="inline-flex items-center hover:text-blue-600 transition-colors">
                Home
              </Link>
            </li>
            <li>
              <div className="flex items-center">
                <ChevronRight className="w-4 h-4 mx-1" />
                <span className="text-gray-400">About</span>
              </div>
            </li>
          </ol>
        </nav>

        {/* Hero Section */}
        <div className="text-center space-y-4 flex flex-col items-center">
          <div className="relative w-32 h-32 mx-auto mb-6">
            <Image
              src="/lanes-logo/lanes-logo.svg" 
              alt="LANES Logo"
              fill
              className="object-contain"
              priority
            />
          </div>
          <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight sm:text-5xl">
            About <span className="text-blue-600">LANES</span>
          </h1>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto">
            Localised Alternative Navigation for Environs under Submersion
          </p>
        </div>

        {/* Project Overview */}
        <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 sm:p-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-blue-50 rounded-lg text-blue-600">
              <Info className="w-6 h-6" />
            </div>
            <h2 className="text-2xl font-bold text-slate-900">Project Overview</h2>
          </div>
          <p className="text-slate-600 leading-relaxed">
            LANES is a real-time, flood-adaptive alternative navigation platform designed for commuters in Pasig City. By mining unstructured, bilingual Taglish text inputs (social media feeds, emergency bulletins, news articles), the system programmatically extracts location tokens, classifies flood depths, and dynamically recalculates driving routes that bypass active inundation zones.
          </p>
        </section>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Academic Context */}
          <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 sm:p-8">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-emerald-50 rounded-lg text-emerald-600">
                <Users className="w-6 h-6" />
              </div>
              <h2 className="text-2xl font-bold text-slate-900">The Team</h2>
            </div>
            <div className="space-y-4 text-slate-600">
              <div>
                <h3 className="font-semibold text-slate-900">Authors</h3>
                <ul className="list-disc pl-5 mt-1 space-y-1">
                  <li>Bellen, Jace H.</li>
                  <li>Cambe, Roi Yvann M.</li>
                  <li>Folloso, Chris Nicolai Z.</li>
                </ul>
              </div>
              <div>
                <h3 className="font-semibold text-slate-900">Adviser</h3>
                <p>Noreen A. Perez, DIT</p>
              </div>
              <div className="pt-4 border-t border-gray-100">
                <p className="text-sm">
                  Developed in partial fulfillment of the requirements for the degree of <strong>Bachelor of Science in Information Technology</strong> at the <strong>College of Computer Studies, Pamantasan ng Lungsod ng Pasig (PLP)</strong>.
                </p>
              </div>
            </div>
          </section>

          {/* Architecture */}
          <section className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6 sm:p-8">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-purple-50 rounded-lg text-purple-600">
                <Cpu className="w-6 h-6" />
              </div>
              <h2 className="text-2xl font-bold text-slate-900">Architecture</h2>
            </div>
            <div className="space-y-4 text-slate-600">
              <p>
                The platform utilizes a strictly decoupled, three-tier architecture to isolate client-side rendering from resource-intensive spatial computations.
              </p>
              <ul className="space-y-3">
                <li>
                  <strong className="text-slate-900 block sm:inline">Client Tier:</strong> Next.js, Tailwind CSS, MapLibre GL JS
                </li>
                <li>
                  <strong className="text-slate-900 block sm:inline">Service Tier:</strong> FastAPI, SQLAlchemy, spaCy NLP, OSRM Engine
                </li>
                <li>
                  <strong className="text-slate-900 block sm:inline">Data Tier:</strong> PostgreSQL + PostGIS
                </li>
              </ul>
            </div>
          </section>
        </div>

        {/* Contact Us (Under Development) */}
        <section className="bg-slate-50 rounded-2xl border border-slate-200 p-6 sm:p-8 text-center relative overflow-hidden">
          <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
            <Construction className="w-32 h-32 text-slate-900" />
          </div>
          <div className="relative z-10 space-y-5 flex flex-col items-center">
            <h2 className="text-2xl font-bold text-slate-900">Contact Us</h2>
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-amber-100 text-amber-800 font-medium text-sm">
              <Construction className="w-4 h-4" />
              Under Development
            </div>
            <p className="text-slate-600 max-w-md mx-auto">
              Our contact form and support channels are currently being set up. Please check back later or reach out through official PLP university channels.
            </p>
          </div>
        </section>

      </div>
    </div>
  );
}
