import { AnalyticsPanel } from "@/features/analytics/AnalyticsPanel";

export const metadata = {
  title: "Analytics",
};

export default function AnalyticsPage() {
  return (
    <main className="relative w-full h-screen overflow-hidden pointer-events-none">
      <div className="pointer-events-auto h-full">
        <AnalyticsPanel />
      </div>
    </main>
  );
}
