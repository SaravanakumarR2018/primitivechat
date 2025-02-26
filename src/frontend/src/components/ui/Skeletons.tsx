/* eslint-disable react/no-array-index-key */
export const TicketListSkeleton = () => {
  return (
    <div className="custom-scrollbar relative max-h-[500px] w-full overflow-y-auto rounded-md border shadow-md">
      {/* Fixed Table Header */}
      <ul className="sticky top-0 z-10 bg-white shadow">
        <li className="grid grid-cols-[0.5fr_2fr_1.5fr_1.5fr_1fr_1fr_1fr_auto] gap-4 border-b p-3 font-semibold">
          <div>ID</div>
          <div>Title</div>
          <div>Reported By</div>
          <div>Assignee</div>
          <div>Status</div>
          <div>Priority</div>
          <div className="text-center">Created</div>
          <div className="text-center">Action</div>
        </li>
      </ul>

      {/* Skeleton Loader */}
      <ul>
        {[...Array(10)].map((_, index) => (
          <li
            key={index}
            className="grid animate-pulse grid-cols-[0.5fr_2fr_1.5fr_1.5fr_1fr_1fr_1fr_auto] items-center gap-4 rounded-lg border-transparent bg-white p-4"
          >
            <div className="h-4 w-12 rounded bg-gray-300"></div>
            <div className="h-4 w-40 rounded bg-gray-300"></div>
            <div className="h-4 w-28 rounded bg-gray-300"></div>
            <div className="h-4 w-28 rounded bg-gray-300"></div>
            <div className="h-4 w-20 rounded bg-gray-300"></div>
            <div className="h-4 w-24 rounded bg-gray-300"></div>
            <div className="h-4 w-24 rounded bg-gray-300"></div>
            <div className="flex size-8 items-center justify-center rounded-full bg-gray-300"></div>
          </li>
        ))}
      </ul>
    </div>
  );
};
