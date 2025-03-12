export default function ErrorPage() {
  return (
    <div className="flex h-screen w-full items-center justify-center bg-white">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-red-600">Something went wrong</h1>
        <p className="text-lg text-gray-700">An error occurred while loading the page.</p>
      </div>
    </div>
  );
}
