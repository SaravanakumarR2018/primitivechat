/* eslint-disable react/no-array-index-key */
export const TicketListSkeleton = () => {
  return (
    <div className="relative w-full rounded-md border shadow-md">
      <ul className="custom-scrollbar max-h-[80vh] overflow-y-auto rounded-md bg-white shadow">
        {/* Sticky Header Row */}
        <li className="sticky top-0 z-10 flex items-center justify-between gap-4 border-b bg-white px-4 py-3 text-sm font-semibold md:text-base">
          <div className="w-[10%]">ID</div>
          <div className="w-1/2 md:w-1/5">Title</div>
          <div className="hidden w-[15%] md:block">Reported By</div>
          <div className="hidden w-[15%] md:block">Assignee</div>
          <div className="hidden w-[10%] md:flex">Status</div>
          <div className="hidden w-[10%] md:flex">Priority</div>
          <div className="hidden w-1/5 justify-center text-center md:flex md:w-[10%]">Created</div>
          <div className="w-[10%] text-center md:w-[5%]">Action</div>
        </li>

        {[...Array(10)].map((_, index) => (
          <li
            key={index}
            className="flex items-center justify-between gap-4 bg-white px-4 py-3"
          >
            <div className="h-4 w-[10%] animate-pulse rounded bg-gray-200" />
            <div className="h-4 w-1/2 animate-pulse rounded bg-gray-200 md:w-1/5" />
            <div className="hidden h-4 w-[15%] animate-pulse rounded bg-gray-200 md:block" />
            <div className="hidden h-4 w-[15%] animate-pulse rounded bg-gray-200 md:block" />
            <div className="hidden h-6 w-[10%] animate-pulse rounded bg-gray-200 md:flex" />
            <div className="hidden h-6 w-[10%] animate-pulse rounded bg-gray-200 md:flex" />
            <div className="hidden h-4 w-1/5 animate-pulse justify-center rounded bg-gray-200 text-center md:flex md:w-[10%]" />
            <div className="flex w-[10%] items-center justify-center gap-2 md:w-[5%]">
              <div className="size-5 animate-pulse rounded-full bg-gray-300" />
              <div className="size-5 animate-pulse rounded-full bg-gray-300" />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};

export const TicketDetailSkeleton = () => {
  return (
    <div className="mx-auto max-w-5xl animate-pulse rounded-lg bg-white p-6 shadow-md">
      <div className="mb-6 h-8 w-32 rounded bg-gray-300"></div>

      <div className="flex flex-col gap-8 md:flex-row">
        {/* Left Pane */}
        <div className="space-y-4 md:w-1/2">
          <div className="h-5 w-20 rounded bg-gray-300"></div>
          <div className="h-10 w-full rounded bg-gray-300"></div>

          <div className="h-5 w-24 rounded bg-gray-300"></div>
          <div className="h-20 w-full rounded bg-gray-300"></div>

          <div className="h-5 w-24 rounded bg-gray-300"></div>
          <div className="h-10 w-full rounded bg-gray-300"></div>
        </div>

        {/* Vertical Divider */}
        <div className="hidden w-px bg-gray-300 md:block" />

        {/* Right Pane */}
        <div className="space-y-4 md:w-1/2">
          <div className="h-5 w-24 rounded bg-gray-300"></div>
          <div className="h-10 w-full rounded bg-gray-300"></div>

          <div className="h-5 w-28 rounded bg-gray-300"></div>
          <div className="h-10 w-full rounded bg-gray-300"></div>

          <div className="h-5 w-20 rounded bg-gray-300"></div>
          <div className="h-10 w-full rounded bg-gray-300"></div>

          <div className="h-5 w-24 rounded bg-gray-300"></div>
          <div className="h-10 w-full rounded bg-gray-200"></div>

          {/* Custom Fields */}
          <div>
            <div className="mb-2 h-6 w-32 rounded bg-gray-300"></div>
            {[...Array(2)].map((_, i) => (
              <div key={i} className="mb-4">
                <div className="mb-1 h-4 w-24 rounded bg-gray-300"></div>
                <div className="h-10 w-full rounded bg-gray-200"></div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Comments */}
      <div className="mt-10">
        <div className="mb-4 h-6 w-32 rounded bg-gray-300"></div>
        <div className="mb-4 h-20 w-full rounded bg-gray-300"></div>
        <div className="mb-6 h-10 w-32 rounded bg-gray-400"></div>

        {/* Simulated Comments */}
        {[...Array(2)].map((_, i) => (
          <div key={i} className="mb-4 rounded border bg-gray-100 p-3">
            <div className="mb-2 h-4 w-3/4 rounded bg-gray-300"></div>
            <div className="h-3 w-1/2 rounded bg-gray-200"></div>
          </div>
        ))}
      </div>

      {/* Footer Actions */}
      <div className="mt-8 flex justify-between">
        <div className="h-4 w-32 rounded bg-gray-300"></div>
        <div className="flex gap-4">
          <div className="h-10 w-24 rounded bg-gray-400"></div>
          <div className="h-10 w-24 rounded bg-gray-400"></div>
        </div>
      </div>
    </div>
  );
};

export const ChatHistorySkeleton = () => {
  return (
    <div className="relative h-[calc(100vh-8rem)] overflow-y-hidden bg-white p-4">
      <ul className="space-y-2">
        {[...Array(20)].map((_, index) => (
          <li
            key={index}
            className="mb-2 flex items-center justify-between rounded-lg bg-gray-100 p-2 hover:bg-gray-200"
          >
            {/* Chat preview skeleton */}
            <div className="h-4 w-3/4 animate-pulse rounded bg-gray-200" />
            {/* Action icons skeleton */}
            <div className="flex items-center gap-2">
              <div className="size-5 animate-pulse rounded-full bg-gray-300" />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
};
