/* eslint-disable react/no-array-index-key */
export const TicketListSkeleton = () => {
  return (
    <div className="relative w-full rounded-md border shadow-md">
      {/* Skeleton Table with Scrollable Area */}
      <ul className="custom-scrollbar max-h-[90vh] overflow-y-auto rounded-md bg-white shadow">
        {/* Sticky Header Row */}
        <li className="sticky top-0 z-10 grid grid-cols-[0.5fr_2fr_1.5fr_1.5fr_1fr_1fr_1fr_auto] gap-4 border-b bg-white p-3 font-semibold">
          <div>ID</div>
          <div>Title</div>
          <div>Reported By</div>
          <div>Assignee</div>
          <div>Status</div>
          <div>Priority</div>
          <div className="text-center">Created</div>
          <div className="text-center">Action</div>
        </li>
        {/* Skeleton Rows */}
        {[...Array(10)].map((_, index) => (
          <li
            key={index}
            className="grid animate-pulse grid-cols-[0.5fr_2fr_1.5fr_1.5fr_1fr_1fr_1fr_auto] items-center gap-4 rounded-lg border-transparent bg-white p-4 hover:bg-gray-100"
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

export const TicketDetailSkeleton = () => {
  return (
    <div className="mx-auto max-w-2xl animate-pulse rounded-lg bg-white p-6 shadow-md">
      <div className="mb-4 h-6 w-40 rounded bg-gray-300"></div>

      <div className="space-y-4">
        <div>
          <div className="mb-1 h-4 w-20 rounded bg-gray-300"></div>
          <div className="h-10 w-full rounded bg-gray-300"></div>
        </div>

        <div>
          <div className="mb-1 h-4 w-20 rounded bg-gray-300"></div>
          <div className="h-20 w-full rounded bg-gray-300"></div>
        </div>

        <div>
          <div className="mb-1 h-4 w-20 rounded bg-gray-300"></div>
          <div className="h-10 w-full rounded bg-gray-300"></div>
        </div>

        <div>
          <div className="mb-1 h-4 w-20 rounded bg-gray-300"></div>
          <div className="h-10 w-full rounded bg-gray-300"></div>
        </div>

        <div>
          <div className="mb-1 h-4 w-20 rounded bg-gray-300"></div>
          <div className="h-10 w-full rounded bg-gray-300"></div>
        </div>

        <div>
          <div className="mb-1 h-4 w-20 rounded bg-gray-300"></div>
          <div className="h-10 w-full rounded bg-gray-300"></div>
        </div>

        <div>
          <div className="mb-1 h-4 w-20 rounded bg-gray-300"></div>
          <div className="h-10 w-full rounded bg-gray-300"></div>
        </div>

        {/* Custom Fields Placeholder */}
        <div className="mt-4">
          <div className="mb-2 h-5 w-32 rounded bg-gray-300"></div>
          <div className="h-10 w-full rounded bg-gray-300"></div>
        </div>

        <div className="mt-4 h-10 w-full rounded bg-gray-300"></div>
      </div>

      <div className="mt-4 h-5 w-32 rounded bg-gray-300"></div>
    </div>
  );
};
