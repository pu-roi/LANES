import type { Metadata } from "next";
import { FeedPage } from "@/features/feed/FeedPage";

export const metadata: Metadata = {
  title: "Community Feed",
};

export default function Page() {
  return <FeedPage />;
}
