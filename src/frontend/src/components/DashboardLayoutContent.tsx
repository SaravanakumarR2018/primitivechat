'use client';

import ChatHistory from '@/components/ChatHistory';
import { DashboardHeader } from '@/features/dashboard/DashboardHeader';
import { DashboardSidebarProvider, useDashboardSidebar } from '@/features/dashboard/DashboardSidebarContext';

type DashboardLayoutContentProps = {
  children: React.ReactNode;
  sidebarNavLinks: Array<{ href: string; label: string }>;
};

export default function DashboardLayoutContent({ children, sidebarNavLinks }: DashboardLayoutContentProps) {
  return (
    <DashboardSidebarProvider>
      <DashboardLayoutContentInner sidebarNavLinks={sidebarNavLinks}>
        {children}
      </DashboardLayoutContentInner>
    </DashboardSidebarProvider>
  );
}

function DashboardLayoutContentInner({ children, sidebarNavLinks }: DashboardLayoutContentProps) {
  const { isSidebarOpen } = useDashboardSidebar();

  return (
    <div className="flex min-h-screen flex-col overflow-hidden">
      {/* Global Sidebar */}
      <div className="fixed left-0 top-0 z-50">
        <ChatHistory navLinks={sidebarNavLinks} />
      </div>
      {/* Header */}
      <div className="sticky top-0 z-50 w-full bg-white shadow-md">
        <div className="mx-auto flex max-w-screen-xl items-center justify-between px-3 py-4">
          <DashboardHeader
            menu={[
              { href: '/dashboard', label: 'Home' },
              { href: '/dashboard/organization-profile/organization-members', label: 'Members' },
              { href: '/dashboard/organization-profile', label: 'Settings' },
            ]}
          />
        </div>
      </div>
      <div
        id="dashboard-scroll-container"
        className={`flex-1 overflow-y-auto bg-muted pt-3 transition-all duration-300${isSidebarOpen ? ' md:ml-72' : ' ml-16'}`}
      >
        <div className="mx-auto max-w-screen-xl p-8 px-3 pb-16 pt-6">
          {children}
        </div>
      </div>
    </div>
  );
}
