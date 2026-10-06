"use client";

import { AlertTriangle, RefreshCw } from "lucide-react";
import { Button, Card, CardContent, CardTitle } from "@/shared/ui";

export default function NewsIntelligenceError({ unstable_retry }: { unstable_retry: () => void }) {
  return (
    <Card role="alert" className="mx-auto w-full max-w-[1600px] border-red-200 bg-red-50 shadow-sm">
      <CardContent className="space-y-4 p-5 sm:p-6">
        <AlertTriangle className="h-6 w-6 text-red-600" aria-hidden="true" />
        <CardTitle>Could not open News Intelligence</CardTitle>
        <p className="text-sm text-red-800">The page could not be loaded. Try again to reopen the workspace.</p>
        <Button type="button" variant="outline" onClick={unstable_retry} className="gap-2">
          <RefreshCw className="h-4 w-4" aria-hidden="true" />Try again
        </Button>
      </CardContent>
    </Card>
  );
}
