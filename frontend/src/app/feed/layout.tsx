import React from 'react';
import { LeftSidebar } from '@/features/feed/LeftSidebar';
import { RightSidebar } from '@/features/feed/RightSidebar';

export default function FeedLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-transparent text-gray-900 flex flex-col items-center w-full mt-0 sm:mt-2 relative">
      {/* 3-Column Layout Wrapper */}
      <div className="flex w-full px-0 sm:px-4 xl:px-6 pt-0 sm:pt-2">
        
        {/* Left Navigation */}
        <LeftSidebar />

        {/* Center & Right Wrapper */}
        <div className="flex-1 flex justify-center items-start min-w-0 px-0 sm:px-4 lg:px-8 gap-5 xl:gap-6">
          
          {/* Main Content Area (Feed List or Post Detail) */}
          <main className="w-full max-w-[720px] min-w-0 bg-transparent relative">
            {children}
          </main>

          {/* Right Auxiliary Panel */}
          <RightSidebar />
        </div>
        
      </div>
    </div>
  );
}
