import React from 'react';
import { LeftSidebar } from '@/features/feed/LeftSidebar';
import { RightSidebar } from '@/features/feed/RightSidebar';

export default function FeedLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-transparent text-gray-900 flex flex-col items-center w-full mt-2 relative">
      {/* 3-Column Layout Wrapper */}
      <div className="flex w-full px-2 lg:px-4 xl:px-8 pt-2 max-w-[1600px]">
        
        {/* Left Navigation */}
        <LeftSidebar />

        {/* Center & Right Wrapper */}
        <div className="flex-1 flex justify-center min-w-0 px-4 lg:px-8 gap-6">
          
          {/* Main Content Area (Feed List or Post Detail) */}
          <main className="w-full max-w-[720px] bg-transparent relative">
            {children}
          </main>

          {/* Right Auxiliary Panel */}
          <RightSidebar />
        </div>
        
      </div>
    </div>
  );
}
