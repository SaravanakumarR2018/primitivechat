import Image from 'next/image';
import Link from 'next/link';

const BrokenTicket = () => {
  return (
    <div className="flex flex-col items-center justify-center gap-4 p-4">
      <Image
        src="/assets/images/brokenTicket.png"
        alt="Broken Ticket"
        width={300}
        height={300}
      />
      <h1 className="text-lg text-gray-800">Ticket Not Found.</h1>
      <div className="flex gap-4">
        <Link href="/dashboard/tickets">
          <button className="mb-2 flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-white shadow-md hover:bg-blue-700" type="button">
            <span>
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="size-6">
                <path fillRule="evenodd" d="M9.53 2.47a.75.75 0 0 1 0 1.06L4.81 8.25H15a6.75 6.75 0 0 1 0 13.5h-3a.75.75 0 0 1 0-1.5h3a5.25 5.25 0 1 0 0-10.5H4.81l4.72 4.72a.75.75 0 1 1-1.06 1.06l-6-6a.75.75 0 0 1 0-1.06l6-6a.75.75 0 0 1 1.06 0Z" clipRule="evenodd" />
              </svg>
            </span>
            Back To Tickets
          </button>
        </Link>
      </div>
    </div>
  );
};

export default BrokenTicket;
