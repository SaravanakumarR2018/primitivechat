import Image from 'next/image';
import Link from 'next/link';

const BrokenTicket = () => {
  return (
    <div className="flex flex-col items-center justify-center gap-4 p-4">
      <Image
        src="/assets/images/brokenTicketNew.png"
        alt="Broken Ticket"
        width={300}
        height={300}
      />
      <h1 className="text-lg text-gray-800">No Tickets Found.</h1>
      <div className="flex gap-4">

        <Link href="/dashboard">
          <button className="rounded-lg bg-blue-600 px-4 py-2 text-white hover:bg-blue-700" type="button">
            Back To Dashboard
          </button>
        </Link>
      </div>
    </div>
  );
};

export default BrokenTicket;
