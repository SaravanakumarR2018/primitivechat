'use client';

import { useTranslations } from 'next-intl';

import ChatHistory from '@/components/ChatHistory';
import { DashboardHeader } from '@/features/dashboard/DashboardHeader';
import { DashboardSidebarProvider, useDashboardSidebar } from '@/features/dashboard/DashboardSidebarContext';

// Move metadata generation to a separate file if needed for SSR, keep layout as client

function DashboardLayoutContent(props: { children: React.ReactNode; sidebarNavLinks: any[] }) {
  const t = useTranslations('DashboardLayout');
  const { isSidebarOpen } = useDashboardSidebar();

  return (
    <div className="flex h-screen flex-col overflow-auto">
      {/* Global Sidebar */}
      <div className="fixed left-0 top-0 z-50">
        <ChatHistory navLinks={props.sidebarNavLinks} />
      </div>
      {/* Header */}
      <div className="sticky top-0 z-50 w-full bg-white shadow-md">
        <div className="mx-auto flex max-w-screen-xl items-center justify-between px-3 py-4">
          <DashboardHeader
            menu={[
              {
                href: '/dashboard',
                label: t('home'),
              },
              {
                href: '/dashboard/organization-profile/organization-members',
                label: t('members'),
              },
              {
                href: '/dashboard/organization-profile',
                label: t('settings'),
              },
              // ...other menu items if needed
            ]}
          />
        </div>
      </div>
      <div className={`flex-1 overflow-auto bg-muted pt-3 transition-all duration-300${isSidebarOpen ? ' md:ml-72' : ' ml-16'}`}>
        <div className="mx-auto max-w-screen-xl p-8 px-3 pb-16 pt-6">
          {props.children}
        </div>
      </div>
    </div>
  );
}

export default function DashboardLayout(props: { children: React.ReactNode }) {
  // Sidebar navigation links to move from header to sidebar
  const sidebarNavLinks = [
    { href: '/dashboard/tickets', label: 'Tickets' },
    { href: '/dashboard/checkclerk', label: 'Checkclerk' },
    { href: '/dashboard/app-settings', label: 'App Settings' },
    { href: '/dashboard/chat', label: 'Chat' },
  ];

  return (
    <DashboardSidebarProvider>
      <DashboardLayoutContent {...props} sidebarNavLinks={sidebarNavLinks} />
    </DashboardSidebarProvider>
  );
}

export const dynamic = 'force-dynamic';
