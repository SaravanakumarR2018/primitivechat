import React from 'react';

type DeleteConfirmationModalProps = {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
};

const DeleteConfirmationModal: React.FC<DeleteConfirmationModalProps> = ({ isOpen, onClose, onConfirm }) => {
  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="rounded-lg bg-white p-6 shadow-lg">
        <h2 className="mb-4 text-lg font-semibold">Are you sure?</h2>
        <p className="mb-6 text-gray-600">Your ticket will be permanently deleted.</p>
        <div className="flex justify-end gap-4">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-gray-300 px-4 py-2 text-gray-600 hover:bg-gray-100"
          >
            No
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="rounded-lg bg-red-600 px-4 py-2 text-white hover:bg-red-700"
          >
            Yes, Delete
          </button>
        </div>
      </div>
    </div>
  );
};

export default DeleteConfirmationModal;
