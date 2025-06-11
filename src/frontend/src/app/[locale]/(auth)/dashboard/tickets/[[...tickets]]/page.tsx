'use client';

import { useOrganization } from '@clerk/nextjs';
import dynamic from 'next/dynamic';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useState } from 'react';

import Pagination from '@/components/ui/Pagination';
import Sidebar from '@/components/ui/SideBar';
import { TicketListSkeleton } from '@/components/ui/Skeletons';

const TicketList = dynamic(() => import('@/components/ui/TicketList'));

const TicketManagementPage = () => {
  const { organization } = useOrganization();
  const router = useRouter();
  const searchParams = useSearchParams();

  const [currentPage, setCurrentPage] = useState(Number(searchParams.get('page')) || 1);
  const [totalPages, setTotalPages] = useState(1);
  const [disableNext, setDisableNext] = useState(false);

  // 👇 Watch for URL param changes and update `currentPage`
  useEffect(() => {
    const pageFromParams = Number(searchParams.get('page')) || 1;
    setCurrentPage(pageFromParams);
  }, [searchParams]);

  const handlePageChange = (newPage: number) => {
    setCurrentPage(newPage);
    router.push(`/dashboard/tickets?page=${newPage}`);
  };

  return (
    <div className="flex flex-col md:flex-row flex-1">
      <Sidebar organizationName={organization?.name || null} />
      <main className="flex-1 p-4 text-sm">
        <div className="flex justify-end">
          <button
            type="button"
            onClick={() => router.push('/dashboard/tickets/create')}
            className="mb-2 flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-white shadow-md hover:bg-blue-700"
          >
            <span className="text-xl">
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="size-6">
                <path fillRule="evenodd" d="M12 3.75a.75.75 0 0 1 .75.75v6.75h6.75a.75.75 0 0 1 0 1.5h-6.75v6.75a.75.75 0 0 1-1.5 0v-6.75H4.5a.75.75 0 0 1 0-1.5h6.75V4.5a.75.75 0 0 1 .75-.75Z" clipRule="evenodd" />
              </svg>
            </span>
            <span>Create Ticket</span>
          </button>
        </div>

        <Suspense fallback={<TicketListSkeleton />}>
          <TicketList page={currentPage} setTotalPages={setTotalPages} setDisableNext={setDisableNext} />
        </Suspense>

        <Pagination currentPage={currentPage} totalPages={totalPages} onPageChange={handlePageChange} disableNext={disableNext} />
      </main>
    </div>
  );
};

export default TicketManagementPage;
