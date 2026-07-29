import { PostDetailPage } from '@/features/feed/PostDetailPage';

export default async function PostPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = await params;
  return <PostDetailPage postId={parseInt(resolvedParams.id)} />;
}
