import { getClerkUser } from '@/api/backend-sdk/clerkAuth';

export default async function CheckClerkUserPage() {
  const user = await getClerkUser();

  if (!user) {
    return (
      <div className="mx-auto max-w-lg rounded-lg bg-white p-6 shadow-md">
        <h1 className="mb-4 text-2xl font-semibold">User Details</h1>
        <p className="text-red-500">Failed to fetch user details or unauthorized.</p>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-lg rounded-lg bg-white p-6 shadow-md">
      <h1 className="mb-4 text-2xl font-semibold">User Details</h1>
      <pre className="overflow-x-auto rounded-md bg-gray-100 p-4">
        {JSON.stringify(user, null, 2)}
      </pre>
    </div>
  );
}
