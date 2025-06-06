'use client';
import { useState, useEffect } from 'react';
import { toast, ToastContainer } from 'react-toastify';
import DeleteFileButton from '@/components/ui/DeleteFileButton';
import { format } from 'date-fns';
import { toZonedTime as utcToZonedTime } from 'date-fns-tz';
import 'react-toastify/dist/ReactToastify.css';

interface FileItem {
  fileid: string;
  filename: string;
  embeddingstatus: string;
  uploaded_time?: string;
}

interface DeletedFileItem {
  file_id: string;
  filename: string;
  deletion_status: string;
  uploaded_time?: string;
  delete_request_timestamp?: string;
}

export default function DocumentsPage() {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [deletedFiles, setDeletedFiles] = useState<DeletedFileItem[]>([]);
  const [showTable, setShowTable] = useState(true);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const [loadingFiles, setLoadingFiles] = useState(false);
  const [loadingDeletedFiles, setLoadingDeletedFiles] = useState(false);

  const [currentPage, setCurrentPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);

  const [currentFilePage, setCurrentFilePage] = useState(1);
  const [filesHasMore, setFilesHasMore] = useState(true);

  const fetchFiles = async (page: number) => {
    setLoadingFiles(true);
    console.log(`Fetching list files for page ${page}`);
    try {
      const res = await fetch(`/api/backend/documents?page=${page}&page_size=10`);
      if (!res.ok) throw new Error('Failed to fetch files');
      const data: FileItem[] = await res.json();
      if (data.length < 10) setFilesHasMore(false);
      setFiles(prev => (page === 1 ? data : [...prev, ...data]));
    } catch (error) {
      console.error(error);
      toast.error('Error fetching files');
    } finally {
      setLoadingFiles(false);
    }
  };

  const fetchDeletedFiles = async (page: number) => {
    setLoadingDeletedFiles(true);
    console.log(`Fetching deleted files for page ${page}`);
    try {
      const res = await fetch(`/api/backend/documents/deletedfiles?page=${page}&page_size=10`);
      if (!res.ok) throw new Error('Failed to fetch deleted files');
      const data: DeletedFileItem[] = await res.json();
      if (data.length < 10) setHasMore(false);
      setDeletedFiles(prev => (page === 1 ? data : [...prev, ...data]));
    } catch (error) {
      console.error(error);
      toast.error('Error fetching deleted files');
    } finally {
      setLoadingDeletedFiles(false);
    }
  };

  const handleFilesScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;
    if (scrollHeight - scrollTop <= clientHeight + 50 && filesHasMore && !loadingFiles) {
      const nextPage = currentFilePage + 1;
      setCurrentFilePage(nextPage);
      fetchFiles(nextPage);
    }
  };


  const handleDeletedFilesScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const { scrollTop, scrollHeight, clientHeight } = e.currentTarget;
    if (scrollHeight - scrollTop <= clientHeight + 50 && hasMore && !loadingDeletedFiles) {
      const nextPage = currentPage + 1;
      setCurrentPage(nextPage);
      fetchDeletedFiles(nextPage);
    }
  };

  useEffect(() => {
    if (showTable) {
      setFiles([]);
      setCurrentFilePage(1);
      setFilesHasMore(true);
      fetchFiles(1);
    } else {
      setDeletedFiles([]);
      setCurrentPage(1);
      setHasMore(true);
      fetchDeletedFiles(1);
    }
  }, [showTable]);

  const confirmAndUpload = async () => {
    if (!selectedFile) return;
    setUploading(true);
    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const res = await fetch('/api/backend/documents', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (res.ok) {
        toast.success('File uploaded successfully by the user');
        setSelectedFile(null);
        setShowTable(true);
        setFiles([]);
        setCurrentFilePage(1);
        setFilesHasMore(true);
        fetchFiles(1);
      } else {
        if (res.status === 409) {
          toast.warning('File already uploaded by the user. Please check your files.');
          setSelectedFile(null);
          setShowTable(true);
          setFiles([]);
          setFilesHasMore(true);
          fetchFiles(1);
        } else {
          toast.error(data.detail || 'Upload failed');
        }
      }
    } catch (error) {
      console.error('Error uploading file:', error);
      toast.error('Error uploading file');
    } finally {
      setUploading(false);
      console.log('upload complete');
    }
  };

  return (
    <>
      <ToastContainer position="top-right" autoClose={3000} />
      <div>
        <h3 className="text-xl font-bold mb-4">Documents</h3>
        {/* Drag & Drop & Select File UI */}
        <div className="mb-6 flex justify-center px-4">
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              const file = e.dataTransfer.files?.[0];
              if (file) setSelectedFile(file);
            }}
            className="w-full max-w-6xl border-2 border-dashed border-gray-400 rounded-lg p-6 text-center bg-gray-50 hover:bg-gray-100 transition"
          >
            <p className="font-medium mb-2">Drag and drop a file here</p>
            <p className="text-sm text-gray-500 mb-4">or click below to select a file</p>
            <button
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
              onClick={() => document.getElementById('file-input')?.click()}
            >
              Select a File
            </button>
            <input
              type="file"
              id="file-input"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) setSelectedFile(file);
              }}
            />
          </div>
        </div>

        {/* Tab Buttons */}
        <div className="flex space-x-2 mb-6 justify-start">
          <button
            onClick={() => setShowTable(true)}
            className={`px-4 py-2 rounded-lg ${showTable
                ? 'bg-blue-400 font-semibold text-black'
                : 'font-semibold text-black border-blue-400'
              }`}
          >
            Files
          </button>
          <button
            onClick={() => setShowTable(false)}
            className={`px-4 py-2 rounded-lg ${!showTable
                ? 'bg-blue-400 font-semibold text-black'
                : 'font-semibold text-black border-blue-400'
              }`}
          >
            Deleted Files
          </button>
        </div>

        {/* Confirmation Modal */}
        {selectedFile && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
            <div className="bg-white rounded-lg shadow-lg w-full max-w-sm p-6">
              <h3 className="text-lg font-bold mb-4">Confirm Upload</h3>
              <p className="mb-4">
                Are you sure you want to upload <strong>{selectedFile.name}</strong>?
              </p>
              <div className="flex justify-end space-x-2">
                <button
                  onClick={() => setSelectedFile(null)}
                  className="px-4 py-2 rounded bg-gray-200 hover:bg-gray-300"
                  disabled={uploading}
                >
                  Cancel
                </button>
                <button
                  onClick={confirmAndUpload}
                  className="px-4 py-2 rounded bg-blue-600 text-white hover:bg-blue-700"
                  disabled={uploading}
                >
                  {uploading ? 'Uploading...' : 'Upload'}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Table Display */}

        {showTable ? (
          <div onScroll={handleFilesScroll} className="bg-white shadow rounded-lg overflow-auto max-h-96">
            <table className="w-full text-left table-auto">
              <thead className="sticky top-0 bg-white border-b border-gray-200 text-gray-600 z-10">
                <tr>
                  <th className="p-3">File</th>
                  <th className="p-3">Upload Date and Time</th>
                  <th className="p-3">Upload Status</th>
                  <th className="p-3">Options</th>
                </tr>
              </thead>
              <tbody>
                {files.length === 0 ? (
                  <tr>
                    <td className="p-4 text-center" colSpan={4}>
                      No files found.
                    </td>
                  </tr>
                ) : (
                  <>
                    {files.map((file) => (
                      <tr key={file.fileid} className="hover:bg-gray-100">
                        <td className="p-3">{file.filename}</td>
                        <td className="p-3">
                          {file.uploaded_time
                            ? (() => {
                              const rawDate = new Date(file.uploaded_time + 'Z');
                              const userTimeZone =
                                Intl.DateTimeFormat().resolvedOptions().timeZone;
                              const zonedDate = utcToZonedTime(rawDate, userTimeZone);
                              return format(zonedDate, 'dd MMM yyyy hh:mm a');
                            })()
                            : 'N/A'}
                        </td>
                        <td className="p-3">
                          <div className="flex items-center space-x-2">
                            <span>{file.embeddingstatus}</span>
                            {['EXTRACTING', 'CHUNKING', 'EMBEDDING'].includes(
                              file.embeddingstatus
                            ) && (
                                <svg
                                  className="animate-spin self-center h-4 w-4 text-blue-500"
                                  xmlns="http://www.w3.org/2000/svg"
                                  fill="none"
                                  viewBox="0 0 24 24"
                                >
                                  <circle
                                    className="opacity-25"
                                    cx="12"
                                    cy="12"
                                    r="10"
                                    stroke="currentColor"
                                    strokeWidth="4"
                                  ></circle>
                                  <path
                                    className="opacity-75"
                                    fill="currentColor"
                                    d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                                  ></path>
                                </svg>
                              )}
                          </div>
                        </td>
                        <td className="p-3 flex space-x-2 items-center">
                          <DeleteFileButton
                            filename={file.filename}
                            showTable={showTable}
                            fetchFiles={() => {
                              setFiles([]);
                              setCurrentFilePage(1);
                              setFilesHasMore(true);
                              fetchFiles(1);
                            }}
                            fetchDeletedFiles={() => {
                              setCurrentPage(1);
                              setHasMore(true);
                              fetchDeletedFiles(1);
                            }}
                            onSwitchToDeletedFiles={() => setShowTable(false)}
                          />
                          <button
                            onClick={() => {
                              setFiles([]);
                              setCurrentFilePage(1);
                              setFilesHasMore(true);
                              fetchFiles(1);
                            }}
                            className="px-2 py-1 text-blue-500 rounded hover:bg-blue-500 hover:text-white transition"
                          >
                            &#x21bb;
                          </button>
                        </td>
                      </tr>
                    ))}
                    {files.length > 0 && loadingFiles && (
                      <tr>
                        <td colSpan={4} className="p-4 text-center">
                          <svg
                            className="animate-spin h-6 w-6 text-blue-500 inline-block"
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                          >
                            <circle
                              className="opacity-25"
                              cx="12"
                              cy="12"
                              r="10"
                              stroke="currentColor"
                              strokeWidth="4"
                            ></circle>
                            <path
                              className="opacity-75"
                              fill="currentColor"
                              d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                            ></path>
                          </svg>
                        </td>
                      </tr>
                    )}
                  </>
                )}
              </tbody>
            </table>
          </div>
        ) : (
          <div onScroll={handleDeletedFilesScroll} className="bg-white shadow rounded-lg overflow-auto max-h-96">
            <table className="w-full text-left table-auto">
              <thead className="sticky top-0 bg-white border-b border-gray-200 text-gray-600 z-10">
                <tr>
                  <th className="p-4">File</th>
                  <th className="p-4">Upload Date and Time</th>
                  <th className="p-4">Delete Date and Time</th>
                  <th className="p-4">Deletion Status</th>
                </tr>
              </thead>
              <tbody>
                {deletedFiles.length === 0 ? (
                  <tr>
                    <td className="p-4 text-center" colSpan={4}>
                      No deleted files found.
                    </td>
                  </tr>
                ) : (
                  <>
                    {deletedFiles.map((file) => (
                      <tr key={file.file_id} className="hover:bg-gray-100">
                        <td className="p-4">{file.filename}</td>
                        <td className="p-4">
                          {file.uploaded_time
                            ? (() => {
                              const rawDate = new Date(file.uploaded_time + 'Z');
                              const userTimeZone =
                                Intl.DateTimeFormat().resolvedOptions().timeZone;
                              const zonedDate = utcToZonedTime(rawDate, userTimeZone);
                              return format(zonedDate, 'dd MMM yyyy hh:mm a');
                            })()
                            : 'N/A'}
                        </td>
                        <td className="p-4">
                          {file.delete_request_timestamp
                            ? (() => {
                              const rawDate = new Date(file.delete_request_timestamp + 'Z');
                              const userTimeZone =
                                Intl.DateTimeFormat().resolvedOptions().timeZone;
                              const zonedDate = utcToZonedTime(rawDate, userTimeZone);
                              return format(zonedDate, 'dd MMM yyyy hh:mm a');
                            })()
                            : 'N/A'}
                        </td>
                        <td className="p-4">
                          <div className="flex items-center space-x-2">
                            <span>{file.deletion_status}</span>
                            {['PENDING_DELETION', 'DELETION_IN_PROGRES'].includes(
                              file.deletion_status
                            ) && (
                                <svg
                                  className="animate-spin h-4 w-4 text-blue-500"
                                  xmlns="http://www.w3.org/2000/svg"
                                  fill="none"
                                  viewBox="0 0 24 24"
                                >
                                  <circle
                                    className="opacity-25"
                                    cx="12"
                                    cy="12"
                                    r="10"
                                    stroke="currentColor"
                                    strokeWidth="4"
                                  ></circle>
                                  <path
                                    className="opacity-75"
                                    fill="currentColor"
                                    d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                                  ></path>
                                </svg>
                              )}
                          </div>
                        </td>
                      </tr>
                    ))}
                    {deletedFiles.length > 0 && loadingDeletedFiles && (
                      <tr>
                        <td colSpan={4} className="p-4 text-center">
                          <svg
                            className="animate-spin h-6 w-6 text-blue-500 inline-block"
                            xmlns="http://www.w3.org/2000/svg"
                            fill="none"
                            viewBox="0 0 24 24"
                          >
                            <circle
                              className="opacity-25"
                              cx="12"
                              cy="12"
                              r="10"
                              stroke="currentColor"
                              strokeWidth="4"
                            ></circle>
                            <path
                              className="opacity-75"
                              fill="currentColor"
                              d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                            ></path>
                          </svg>
                        </td>
                      </tr>
                    )}
                  </>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </>
  );
}