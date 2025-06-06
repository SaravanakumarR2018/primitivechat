'use client';
import React, { useState } from 'react';
import { toast} from 'react-toastify';

interface DeleteFileButtonProps {
  filename: string;
  showTable: boolean;
  fetchFiles: () => void;
  fetchDeletedFiles: () => void;
  onSwitchToDeletedFiles: () => void;
}

export default function DeleteFileButton({
  filename,
  showTable,
  fetchFiles,
  fetchDeletedFiles,
  onSwitchToDeletedFiles,
}: DeleteFileButtonProps) {
  const [showConfirm, setShowConfirm] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      const res = await fetch(`/api/backend/documents?filename=${encodeURIComponent(filename)}`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json' },
      });
      const data = await res.json();

      if (res.ok) {
      toast.success('File Deleted successfully by the user');
      onSwitchToDeletedFiles();
      } else {
        toast.warning(data.message || 'Unexpected response');
      }

      setShowConfirm(false);

      setTimeout(() => {
        showTable ? fetchFiles() : fetchDeletedFiles();
      }, 2000);
    } catch (error) {
      console.error(error);
      toast.error('Error deleting file');
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <>

      {/* Delete Button */}
      <button
        onClick={() => setShowConfirm(true)}
        className="px-3 py-1 text-red-500 rounded hover:bg-red-500 hover:text-white transition"
        aria-label="Delete file"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-5 w-5"
          viewBox="0 0 20 20"
          fill="currentColor"
        >
          <path
            fillRule="evenodd"
            d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2h1v10a2 2 0 002 2h6a2 2 0 002-2V6h1a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zm1 4a1 1 0 011 1v7a1 1 0 11-2 0V7a1 1 0 011-1z"
            clipRule="evenodd"
          />
        </svg>
      </button>

      {/* Confirmation Modal */}
      {showConfirm && (
        <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
          <div className="bg-white p-6 rounded shadow-lg max-w-sm w-full text-center">
            <p className="mb-4 text-lg font-semibold">
              Are you sure you want to delete this file?
            </p>
            <div className="flex justify-center space-x-4">
              <button
                onClick={() => setShowConfirm(false)}
                disabled={isDeleting}
                className="px-4 py-2 bg-gray-300 rounded hover:bg-gray-400"
              >
                Cancel
              </button>
              <button
                onClick={handleDelete}
                disabled={isDeleting}
                className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
              >
                {isDeleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
