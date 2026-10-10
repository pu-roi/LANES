"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ChevronDown, ExternalLink, Newspaper, RefreshCw } from "lucide-react";
import { Button } from "@/shared/ui";
import { getLocalNewsUpdates } from "./localNewsApi";
import { newsDate, publisherLink } from "./newsPresentation";

export function LocalUpdates({ collapsible = false }: { collapsible?: boolean }) {
  const [offline, setOffline] = useState(false);
  useEffect(() => {
    const update = () => setOffline(!navigator.onLine);
    update();
    window.addEventListener("online", update);
    window.addEventListener("offline", update);
    return () => {
      window.removeEventListener("online", update);
      window.removeEventListener("offline", update);
    };
  }, []);
  const query = useQuery({
    queryKey: ["news", "local-updates"],
    queryFn: ({ signal }) => getLocalNewsUpdates(signal),
    staleTime: 60_000,
    refetchInterval: 60_000,
    refetchIntervalInBackground: false,
    refetchOnWindowFocus: true,
    refetchOnReconnect: "always",
    retry: false,
  });
  const content = <div className="space-y-3">
    <p className="text-xs leading-relaxed text-gray-500">Recent Metro Manila flood news. Article reports may not reflect current conditions.</p>
    {offline && <p role="status" className="text-xs text-amber-800">Offline. Showing last downloaded news when available.</p>}
    {query.isError && <div className="space-y-2">
      <p role="alert" className="text-sm text-red-700">Couldn’t load local news. {query.data && "Previously downloaded articles are shown below."}</p>
      <Button variant="outline" size="sm" className="min-h-11" disabled={offline || query.isFetching} onClick={() => void query.refetch()}>Retry local news</Button>
    </div>}
    {query.isPending && !query.isError && !offline && <div role="status" aria-label="Loading local news" className="space-y-2">
      <div aria-hidden="true" className="h-4 w-full rounded bg-gray-100 motion-safe:animate-pulse" />
      <div aria-hidden="true" className="h-4 w-2/3 rounded bg-gray-100 motion-safe:animate-pulse" />
    </div>}
    {query.data?.items.length === 0 && <p className="text-sm text-gray-500">No recent local flood news is available.</p>}
    {query.data && <>
      <ul className="divide-y divide-gray-100">
        {query.data.items.map((article) => {
          const link = publisherLink(article.source_url);
          return <li key={article.id} className="py-3 first:pt-0 last:pb-0">
            {link ? <a href={link} target="_blank" rel="noopener noreferrer" className="flex min-h-11 items-start gap-2 rounded text-sm font-medium leading-relaxed text-gray-900 hover:text-blue-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500">
              <span className="min-w-0 break-words">{article.title}<span className="sr-only"> (opens in a new tab)</span></span>
              <ExternalLink className="mt-1 size-3.5 shrink-0 text-gray-400" aria-hidden="true" />
            </a> : <p className="break-words text-sm font-medium text-gray-900">{article.title}</p>}
            <p className="mt-1 break-words text-xs text-gray-500">{article.publisher}</p>
            <p className="mt-1 text-xs text-gray-500">Published <time dateTime={article.published_at}>{newsDate(article.published_at, "Date not stated")}</time></p>
          </li>;
        })}
      </ul>
      <div className="flex items-center justify-between gap-2 border-t border-gray-100 pt-2">
        <p className="min-w-0 flex-1 text-[11px] text-gray-500">Last checked {newsDate(query.data.as_of)}</p>
        <Button variant="ghost" size="sm" className="min-h-11 min-w-11 shrink-0 px-2" aria-label="Refresh local news" disabled={offline || query.isFetching} onClick={() => void query.refetch()}>
          <RefreshCw className={`size-4 ${query.isFetching ? "motion-safe:animate-spin" : ""}`} aria-hidden="true" />
        </Button>
      </div>
    </>}
  </div>;
  return <section aria-label="Local Updates" className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
    {collapsible ? <details className="group">
      <summary className="flex min-h-11 cursor-pointer list-none items-center gap-2 rounded font-semibold text-gray-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 [&::-webkit-details-marker]:hidden">
        <Newspaper className="size-5 text-purple-500" aria-hidden="true" />
        <span className="flex-1">Local Updates</span>
        <ChevronDown className="size-4 text-gray-500 group-open:rotate-180" aria-hidden="true" />
      </summary>
      <div className="pt-3">{content}</div>
    </details> : <>
      <h3 className="mb-4 flex items-center gap-2 font-semibold text-gray-900"><Newspaper className="size-5 text-purple-500" aria-hidden="true" />Local Updates</h3>
      {content}
    </>}
  </section>;
}
