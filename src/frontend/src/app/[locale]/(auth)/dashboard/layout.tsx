import { getTranslations } from 'next-intl/server';
import DashboardClient from '@/components/DashboardClient';
import { getCustomerGuid } from '@/api/backend-sdk/sendToken';
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
    <div>
      <DashboardClient>
        {props.children}
      </DashboardClient>
    </div>
  );
}

export const dynamic = 'force-dynamic';
