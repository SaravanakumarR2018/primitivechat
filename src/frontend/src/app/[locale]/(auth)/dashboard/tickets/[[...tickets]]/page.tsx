/* eslint-disable no-console */
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

  const handlePageChange = (newPage: number) => {
    console.log('📢 handlePageChange Triggered in TicketManagementPage - New Page:', newPage);
    setCurrentPage(newPage);
  };

  useEffect(() => {
    console.log('🔄 Current Page Updated:', currentPage);
  }, [currentPage]);

  useEffect(() => {
    const newPage = Number(searchParams.get('page')) || 1;
    console.log('🔄 URL Page Param Updated:', newPage);
    setCurrentPage(newPage);
  }, [searchParams]);

  console.log('🎬 TicketManagementPage Rendered');

  return (
    <div className="flex h-screen flex-col rounded-md bg-white md:flex-row">
      <Sidebar organizationName={organization?.name || null} />
      <main className="flex-1 overflow-x-auto p-4 text-sm">
        <Pagination
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={(newPage: number) => {
            console.log('🖱 Pagination Clicked: New Page =', newPage);
            handlePageChange(newPage);
            if (newPage > 1) {
              router.push(`/dashboard/tickets?page=${newPage}`, { scroll: true });
            } else {
              router.push('/dashboard/tickets', { scroll: false });
            }
          }}
          disableNext={disableNext}
        />
        <div className="w-full overflow-x-auto">
          <Suspense fallback={<TicketListSkeleton />}>
            <TicketList page={currentPage} setTotalPages={setTotalPages} setDisableNext={setDisableNext} />
          </Suspense>
        </div>
      </main>
    </div>
  );
};

export default TicketManagementPage;
