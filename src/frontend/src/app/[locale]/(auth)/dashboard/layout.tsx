import { getTranslations } from 'next-intl/server';

import { getCustomerGuid } from '@/api/backend-sdk/sendToken';
import DashboardLayoutContent from '@/components/DashboardLayoutContent';
import ErrorPage from '@/components/ui/error_page';

export async function generateMetadata(props: { params: { locale: string } }) {
  const t = await getTranslations({
    locale: props.params.locale,
    namespace: 'Dashboard',
  });

  return {
    title: t('meta_title'),
    description: t('meta_description'),
  };
}

export default async function DashboardLayout(props: { children: React.ReactNode }) {
  try {
    const customerGuid = await getCustomerGuid();
    if (!customerGuid) {
      return <ErrorPage />;
    }
    // You can pass customerGuid to DashboardLayoutContent if needed
  } catch (error) {
    console.error('Error fetching customer GUID:', error);
    return <ErrorPage />;
  }

  const sidebarNavLinks = [
    { href: '/dashboard/tickets', label: 'Tickets' },
    { href: '/dashboard/checkclerk', label: 'Checkclerk' },
    { href: '/dashboard/app-settings', label: 'App Settings' },
    { href: '/dashboard/chat', label: 'Chat' },
  ];

  return (
    <DashboardLayoutContent sidebarNavLinks={sidebarNavLinks}>
      {props.children}
    </DashboardLayoutContent>
  );
}

export const dynamic = 'force-dynamic';
