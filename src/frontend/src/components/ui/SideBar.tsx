import Link from 'next/link';

type SidebarProps = {
  organizationName: string | null;
};

const Sidebar = ({ organizationName }: SidebarProps) => {
  return (
    <aside className="w-full border-r bg-gray-100 p-4 pr-6 md:w-64">
      <h1 className="mb-4 text-2xl font-bold">Organization</h1>
      <h2 className="text-xl font-semibold">{organizationName || 'Loading...'}</h2>
      <nav className="space-y-2">
        <Link href="/dashboard/tickets" className="block rounded bg-blue-100 p-2 font-semibold text-blue-600">
          Tickets
        </Link>
      </nav>
    </aside>
  );
};

export default Sidebar;
