import { useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';

type PaginationProps = {
  currentPage: number;
  totalPages: number;
  onPageChange: (newPage: number) => void;
  disableNext: boolean;
};

const Pagination = ({ currentPage, totalPages, onPageChange, disableNext }: PaginationProps) => {
  const searchParams = useSearchParams();
  const pageParam = Number(searchParams.get('page')) || 1;
  const [page, setPage] = useState(currentPage);

  useEffect(() => {
    setPage(pageParam);
  }, [pageParam]);

  const handlePageClick = (newPage: number) => {
    onPageChange(newPage);
  };

  // Number of visible pages to display on the pagination control.
  const visiblePages = 5;
  // Compute the starting page for the group.
  let startPage = Math.floor((page - 1) / visiblePages) * visiblePages + 1;
  // When we're near the end, adjust startPage so we always show last visiblePages pages.
  if (totalPages - startPage + 1 < visiblePages) {
    startPage = Math.max(totalPages - visiblePages + 1, 1);
  }
  const endPage = Math.min(totalPages, startPage + visiblePages - 1);

  return (
    <div className="mt-4 flex items-center justify-center space-x-2">
      <button
        onClick={() => handlePageClick(page - 1)}
        disabled={page === 1}
        className="rounded-md border bg-gray-200 px-4 py-2 disabled:opacity-50"
        type="button"
      >
        &larr;
      </button>

      {Array.from({ length: endPage - startPage + 1 }, (_, i) => startPage + i).map(pageNum => (
        <button
          key={pageNum}
          onClick={() => handlePageClick(pageNum)}
          className={`rounded-md px-4 py-2 ${page === pageNum ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
          type="button"
        >
          {pageNum}
        </button>
      ))}

      <button
        onClick={() => handlePageClick(page + 1)}
        disabled={disableNext}
        className="rounded-md border bg-gray-200 px-4 py-2 disabled:opacity-50"
        type="button"
      >
        &rarr;
      </button>
    </div>
  );
};

export default Pagination;
