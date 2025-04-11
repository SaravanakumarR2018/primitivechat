const UnsavedChangesModal = ({ isOpen, onConfirm, onCancel }: any) => {
  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-lg">
        <h2 className="text-lg font-bold">Unsaved Changes</h2>
        <p className="mt-2">Do you want to save changes to the ticket?</p>
        <div className="mt-4 flex justify-end gap-3">
          <button type="button" onClick={onCancel} className="rounded bg-gray-300 px-4 py-2 text-sm">Discard</button>
          <button type="button" onClick={onConfirm} className="rounded bg-blue-600 px-4 py-2 text-sm text-white">Save</button>
        </div>
      </div>
    </div>
  );
};

export default UnsavedChangesModal;
