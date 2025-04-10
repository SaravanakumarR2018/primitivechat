/* eslint-disable react/no-array-index-key */
'use client';

import 'react-toastify/dist/ReactToastify.css';

import { PencilIcon, TrashIcon } from '@heroicons/react/24/solid';
import { useParams, useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { toast, ToastContainer } from 'react-toastify';

import {
  createComment,
  deleteComment,
  deleteTicketByID,
  fetchCommentsByTicketId,
  fetchTicketByID,
  getReportedByName,
  updateComment,
  updateTicketDetails,
} from '@/api/backend-sdk/ticketServiceApiCalls';
import DeleteConfirmationModal from '@/components/ui/DeleteConfirmationModal';
import BrokenTicket from '@/components/ui/NoTicketFoundView';
import { TicketDetailSkeleton } from '@/components/ui/Skeletons';

const PAGE_SIZE = 20;

const TicketDetailPage = () => {
  const params = useParams();
  const router = useRouter();
  const commentBoxRef = useRef<HTMLDivElement>(null);

  const [loading, setLoading] = useState(true);
  const [ticket, setTicket] = useState<any>(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'High',
    status: 'OPEN',
    reported_by: '',
    assigned: '',
    custom_fields: {},
  });

  const [comments, setComments] = useState<any[]>([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [isLoadingComments, setIsLoadingComments] = useState(false);
  const [newComment, setNewComment] = useState('');
  const [posting, setPosting] = useState(false);
  const [deleteTicketId, setDeleteTicketId] = useState<string | null>(null);
  const [editingCommentId, setEditingCommentId] = useState<string | null>(null);
  const [editingText, setEditingText] = useState('');

  // Add this state at the top inside your component
  const [currentUserName, setCurrentUserName] = useState('');

  // Fetch current user's name once on component mount
  useEffect(() => {
    const fetchCurrentUserName = async () => {
      try {
        const name = await getReportedByName();
        setCurrentUserName(name);
      } catch (err) {
        console.error('Failed to fetch current user name:', err);
      }
    };

    fetchCurrentUserName();
  }, []);

  // Load Ticket Info
  useEffect(() => {
    const loadTicket = async () => {
      try {
        const ticketData = await fetchTicketByID(params.id as string);
        setTicket(ticketData);
        setFormData({
          title: ticketData.title || '',
          description: ticketData.description || '',
          priority: ticketData.priority || 'High',
          status: ticketData.status || 'OPEN',
          reported_by: ticketData.reported_by || '',
          assigned: ticketData.assigned || '',
          custom_fields: ticketData.custom_fields || {},
        });
      } catch (error) {
        console.error(error);
        toast.error('Error loading ticket data.');
      } finally {
        setLoading(false);
      }
    };

    loadTicket();
  }, [params.id]);

  // Load first page of comments once on mount
  useEffect(() => {
    const loadInitialComments = async () => {
      setIsLoadingComments(true);
      try {
        const initialComments = await fetchCommentsByTicketId(params.id as string, 1, PAGE_SIZE);
        setComments(initialComments);
        setPage(1);
        setHasMore(initialComments.length === PAGE_SIZE);
      } catch (err: any) {
        if (err?.response?.status === 404) {
          setHasMore(false);
          setComments([]);
        } else {
          console.error(err);
          toast.error('Failed to load comments.');
        }
      } finally {
        setIsLoadingComments(false);
      }
    };

    loadInitialComments();
  }, [params.id]);

  // Scroll-based pagination (triggered only if page > 1)
  useEffect(() => {
    if (page === 1) {
      return;
    }

    const loadMoreComments = async () => {
      if (!hasMore || isLoadingComments) {
        return;
      }

      setIsLoadingComments(true);
      try {
        const newComments = await fetchCommentsByTicketId(params.id as string, page, PAGE_SIZE);
        if (!newComments || newComments.length === 0) {
          setHasMore(false);
        } else {
          setComments(prev => [...prev, ...newComments]);
          if (newComments.length < PAGE_SIZE) {
            setHasMore(false);
          }
        }
      } catch (err: any) {
        if (err?.response?.status === 404) {
          setHasMore(false);
        } else {
          console.error(err);
          toast.error('Failed to load more comments.');
        }
      } finally {
        setIsLoadingComments(false);
      }
    };

    loadMoreComments();
  }, [page, hasMore, isLoadingComments, params.id]);

  // Scroll listener
  useEffect(() => {
    const el = commentBoxRef.current;
    if (!el) {
      return;
    }

    const handleScroll = () => {
      if (el.scrollTop + el.clientHeight >= el.scrollHeight - 50 && hasMore && !isLoadingComments) {
        setPage(prev => prev + 1);
      }
    };

    el.addEventListener('scroll', handleScroll);
    return () => el.removeEventListener('scroll', handleScroll);
  }, [hasMore, isLoadingComments]);

  // Add Comment
  const addComment = async () => {
    if (!newComment.trim()) {
      toast.warning('Comment cannot be empty');
      return;
    }

    try {
      setPosting(true);
      const posted_by = await getReportedByName();
      const commentPayload = {
        ticket_id: ticket.ticket_id,
        posted_by,
        comment: newComment,
      };

      await createComment(commentPayload);

      // Reload just the first page
      const latestComments = await fetchCommentsByTicketId(params.id as string, 1, PAGE_SIZE);
      setComments(latestComments);
      setPage(1);
      setHasMore(latestComments.length === PAGE_SIZE);
      setNewComment('');
      toast.success('Comment added!');
    } catch (error) {
      console.error(error);
      toast.error('Failed to add comment.');
    } finally {
      setPosting(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>,
  ) => {
    const { name, value } = e.target;
    if (name.startsWith('custom_field_')) {
      const fieldKey = name.replace('custom_field_', '');
      setFormData(prev => ({
        ...prev,
        custom_fields: {
          ...prev.custom_fields,
          [fieldKey]: value,
        },
      }));
    } else {
      setFormData(prev => ({ ...prev, [name]: value }));
    }
  };

  const handleDeleteTicket = async () => {
    if (!deleteTicketId) {
      return;
    }
    try {
      await deleteTicketByID(deleteTicketId);
      toast.success('Ticket deleted successfully!');
      setTimeout(() => router.push('/dashboard/tickets'), 2000);
    } catch (error: any) {
      console.error(error);
      toast.error('Error deleting ticket!');
    } finally {
      setDeleteTicketId(null);
    }
  };

  const handleUpdate = async () => {
    try {
      await updateTicketDetails(params.id as string, formData);
      toast.success('Ticket updated successfully!');
      setTimeout(() => router.push('/dashboard/tickets'), 2000);
    } catch (error) {
      console.error(error);
      toast.error('Failed to update ticket.');
    }
  };

  const handleCancelComment = () => {
    setNewComment('');
  };

  const handleEditComment = (comment: any) => {
    setEditingCommentId(comment.comment_id); // or whatever unique identifier you have
    setEditingText(comment.comment);
  };

  const handleSaveEditedComment = async (comment: any) => {
    try {
      await updateComment(params.id as string, comment.comment_id, {
        comment: editingText,
        posted_by: comment.posted_by,
      });

      // Update UI after save
      const updatedComments = await fetchCommentsByTicketId(params.id as string, 1, PAGE_SIZE);
      setComments(updatedComments);
      setEditingCommentId(null);
      toast.success('Comment updated!');
    } catch (err) {
      console.error(err);
      toast.error('Failed to update comment.');
    }
  };

  const handleDeleteComment = async (comment: any) => {
    try {
      await deleteComment(params.id as string, comment.comment_id);
      const updatedComments = await fetchCommentsByTicketId(params.id as string, 1, PAGE_SIZE);
      setComments(updatedComments);
      setPage(1);
      setHasMore(updatedComments.length === PAGE_SIZE);
      toast.success('Comment deleted!');
    } catch (err) {
      console.error(err);
      toast.error('Failed to delete comment.');
    }
  };

  if (loading) {
    return <TicketDetailSkeleton />;
  }
  if (!ticket) {
    return <BrokenTicket />;
  }

  return (
    <div className="mx-auto max-w-5xl rounded-lg bg-white p-6 shadow-md">
      <ToastContainer position="top-right" autoClose={3000} />
      <h1 className="mb-6 text-2xl font-bold">Ticket</h1>

      <div className="flex flex-col gap-8 md:flex-row">
        {/* Left Pane */}
        <div className="space-y-4 md:w-1/2">
          <div className="flex gap-4">
            <div>
              <label htmlFor="status" className="block text-sm font-medium">Status</label>
              <select id="status" name="status" value={formData.status} onChange={handleChange} className="mt-1 rounded border p-2">
                <option value="OPEN">Open</option>
                <option value="IN_PROGRESS">In Progress</option>
                <option value="CLOSED">Closed</option>
              </select>
            </div>
          </div>
          <div>
            <label htmlFor="title" className="block text-sm font-medium">Title</label>
            <input type="text" id="title" name="title" value={formData.title} onChange={handleChange} className="mt-1 w-full rounded border p-2" />
          </div>
          <div>
            <label htmlFor="description" className="block text-sm font-medium">Description</label>
            <textarea id="description" name="description" value={formData.description} onChange={handleChange} className="mt-1 w-full rounded border p-2" rows={5} />
          </div>
        </div>

        <div className="hidden w-px bg-gray-300 md:block" />

        {/* Right Pane */}
        <div className="space-y-4 md:w-1/2">
          <div className="flex gap-4">
            <div>
              <label htmlFor="priority" className="block text-sm font-medium">Priority</label>
              <select id="priority" name="priority" value={formData.priority} onChange={handleChange} className="mt-1 w-full rounded border p-2">
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
              </select>
            </div>
          </div>

          <div>
            <label htmlFor="reported_by" className="block text-sm font-medium">Reported By</label>
            <input type="text" id="reported_by" name="reported_by" value={formData.reported_by} onChange={handleChange} disabled className="mt-1 w-full rounded border p-2" />
          </div>

          <div>
            <label htmlFor="assigned" className="block text-sm font-medium">Assigned</label>
            <input type="text" id="assigned" name="assigned" value={formData.assigned} onChange={handleChange} className="mt-1 w-full rounded border p-2" />
          </div>

          {ticket.created_at && (
            <div>
              <label htmlFor="created_at" className="block text-sm font-medium">Created At</label>
              <p className="mt-1 rounded border bg-gray-100 p-2 text-sm text-gray-600">{new Date(ticket.created_at).toLocaleString()}</p>
            </div>
          )}

          {ticket.custom_fields && Object.keys(ticket.custom_fields).length > 0 && (
            <div>
              <h2 className="text-lg font-semibold">Custom Fields</h2>
              {Object.entries(formData.custom_fields).map(([key, value]) => (
                <div key={key} className="mt-2">
                  <label htmlFor={`custom_field_${key}`} className="block text-sm font-medium">{key}</label>
                  <input
                    type="text"
                    id={`custom_field_${key}`}
                    name={`custom_field_${key}`}
                    value={value as string}
                    onChange={handleChange}
                    className="mt-1 w-full rounded border p-2"
                  />
                </div>
              ))}
            </div>
          )}

        </div>
      </div>

      <div className="mt-8 flex justify-end">
        <button onClick={handleUpdate} type="button" className="rounded bg-blue-500 px-4 py-2 text-white hover:bg-blue-600">
          Save
        </button>
      </div>

      <DeleteConfirmationModal isOpen={!!deleteTicketId} onClose={() => setDeleteTicketId(null)} onConfirm={handleDeleteTicket} />

      {/* Comments Section */}
      <div className="mt-10">
        <h2 className="mb-2 text-lg font-semibold">Comments</h2>

        <div className="mb-6">
          <textarea
            rows={2}
            value={newComment}
            onChange={e => setNewComment(e.target.value)}
            placeholder="Write your comment here..."
            className="w-full rounded border p-2"
          />
          <button
            type="button"
            onClick={addComment}
            disabled={posting}
            className={`mt-2 rounded px-4 py-2 text-white ${posting ? 'bg-gray-400' : 'bg-blue-600 hover:bg-blue-700'}`}
          >
            {posting ? 'Saving...' : 'Save'}
          </button>
          <button
            type="button"
            onClick={handleCancelComment}
            className="ml-2 rounded bg-gray-200 px-4 py-2 text-gray-700 hover:bg-gray-300"
          >
            Cancel
          </button>
        </div>

        <div ref={commentBoxRef} className="max-h-[300px] space-y-4 overflow-y-auto pr-2">
          {comments.length > 0
            ? (
                comments.map((comment, idx) => {
                  const isOwnComment = comment.posted_by === currentUserName;

                  return (
                    <div key={idx} className="relative rounded border bg-gray-50 p-3">
                      {editingCommentId === comment.comment_id
                        ? (
                            <>
                              <textarea
                                rows={2}
                                value={editingText}
                                onChange={e => setEditingText(e.target.value)}
                                className="w-full rounded border p-2"
                              />
                              <div className="mt-2 flex gap-2">
                                <button
                                  type="button"
                                  onClick={() => handleSaveEditedComment(comment)}
                                  className="rounded bg-green-500 px-3 py-1 text-white hover:bg-green-600"
                                >
                                  Save
                                </button>
                                <button
                                  type="button"
                                  onClick={() => setEditingCommentId(null)}
                                  className="rounded bg-gray-300 px-3 py-1 text-gray-700 hover:bg-gray-400"
                                >
                                  Cancel
                                </button>
                              </div>
                            </>
                          )
                        : (
                            <>
                              <p className="text-sm text-gray-800">{comment.comment}</p>
                              <p className="mt-1 text-xs text-gray-500">
                                By
                                {' '}
                                {comment.posted_by}
                                {' '}
                                on
                                {' '}
                                {new Date(comment.created_at).toLocaleString()}
                              </p>

                              {isOwnComment && (
                                <div className="absolute right-2 top-2 flex gap-2">
                                  <button
                                    type="button"
                                    onClick={() => handleEditComment(comment)}
                                    className="hover:text-blue-600"
                                    title="Edit"
                                  >
                                    <PencilIcon className="size-3" />
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => handleDeleteComment(comment)}
                                    className="hover:text-red-600"
                                    title="Delete"
                                  >
                                    <TrashIcon className="size-3" />
                                  </button>
                                </div>
                              )}
                            </>
                          )}
                    </div>
                  );
                })
              )
            : (
                <p className="italic text-gray-500">No comments available.</p>
              )}

          {isLoadingComments && <p className="text-center text-sm text-gray-400">Loading more comments...</p>}
        </div>
      </div>

      <div className="mt-8 flex justify-between">
        <button type="button" className="rounded bg-red-500 px-4 py-2 text-white hover:bg-red-600" onClick={() => setDeleteTicketId(ticket.ticket_id)}>
          Delete
        </button>
        <button onClick={handleUpdate} type="button" className="rounded bg-blue-500 px-4 py-2 text-white hover:bg-blue-600">
          Save
        </button>
      </div>
    </div>
  );
};

export default TicketDetailPage;
