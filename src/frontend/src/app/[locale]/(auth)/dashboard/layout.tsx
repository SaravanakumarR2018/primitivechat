import { getTranslations } from 'next-intl/server';

import { getCustomerGuid } from '@/api/backend-sdk/sendToken';
import ErrorPage from '@/components/ui/error_page';
import { DashboardHeader } from '@/features/dashboard/DashboardHeader';

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
  const t = await getTranslations('DashboardLayout');

  // eslint-disable-next-line no-console
  console.log('🔹 Fetching user in DashboardLayout...');

  try {
    const customerGuid = await getCustomerGuid(); // Now using the cache-based function
    // eslint-disable-next-line no-console
    console.log('Customer GUID:', customerGuid);
  } catch (error) {
    console.error('Error fetching customer GUID:', error);
    return <ErrorPage />;
  }

  return (
    <div className="flex h-screen flex-col overflow-hidden">
      <div className="sticky top-0 z-50 w-full bg-white shadow-md">
        <div className="mx-auto flex max-w-screen-xl items-center justify-between px-3 py-4">
          <DashboardHeader
            menu={[
              {
                href: '/dashboard',
                label: t('home'),
              },
              {
                href: '/dashboard/documents',
                label: 'Documents',
              },
              // PRO: Link to the /dashboard/todos page
              {
                href: '/dashboard/organization-profile/organization-members',
                label: t('members'),
              },
              {
                href: '/dashboard/tickets',
                label: t('tickets'),
              },
              {
                href: '/dashboard/chat',
                label: t('chat'),
              },
              {
                href: '/dashboard/organization-profile',
                label: t('settings'),
              },
              {
                href: '/dashboard/checkclerk',
                label: 'Checkclerk',
              },
              {
                href: '/dashboard/app-settings',
                label: t('app_settings'),
              },
              // PRO: Link to the /dashboard/billing page
            ]}
          />
        </div>
      </div>

      <div className="flex-1 overflow-hidden bg-muted">
        <div className="mx-auto max-w-screen-xl px-3 pb-16 pt-6">
          {props.children}
        </div>
      </div>
    </div>
  );
}

export const dynamic = 'force-dynamic';
