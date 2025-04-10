/* eslint-disable jsx-a11y/no-autofocus */
import { useOrganization } from '@clerk/nextjs';
import { EllipsisVerticalIcon, PencilSquareIcon, TrashIcon } from '@heroicons/react/24/solid';
import { format } from 'date-fns';
import Link from 'next/link';
import React, { useEffect, useState } from 'react';
import { ClipLoader } from 'react-spinners';
import { toast, ToastContainer } from 'react-toastify';

import { deleteTicketByID, fetchTicketsByCustomer, updatePartialTicket } from '@/api/backend-sdk/ticketServiceApiCalls';
import { TicketListSkeleton } from '@/components/ui/Skeletons';

import DeleteConfirmationModal from './DeleteConfirmationModal';

const FETCH_SIZE = 150;
const PAGE_SIZE = 10;

type Ticket = {
  ticket_id: string;
  title: string;
  reported_by: string;
  assigned: string;
  status: string;
  priority: string;
  created_at: string;
};

type TicketListProps = {
  page: number;
  setTotalPages: (pages: number) => void;
  setDisableNext: (disable: boolean) => void;
};

const TicketList: React.FC<TicketListProps> = ({ page, setTotalPages, setDisableNext }) => {
  const { organization } = useOrganization();
  const [editingAssignee, setEditingAssignee] = useState<{ [key: string]: string }>({});
  const [data, setData] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [isFinalBatch, setIsFinalBatch] = useState<boolean>(false);
  const [loadingState, setLoadingState] = useState<{ [key: string]: boolean }>({});
  const [deleteTicketId, setDeleteTicketId] = useState<string | null>(null);
  const [openMenuTicketId, setOpenMenuTicketId] = useState<string | null>(null);

  const batchNumber = Math.floor((page - 1) / 15) + 1;
  useEffect(() => {
    const fetchTickets = async () => {
      // console.log(organization?.id);
      setLoading(true);
      try {
        const result = await fetchTicketsByCustomer(batchNumber, FETCH_SIZE);
        setData(result);
        setIsFinalBatch(result.length < FETCH_SIZE);
      } catch (error: any) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    };
    fetchTickets();
  }, [organization?.id, batchNumber]);

  const handleDeleteTicket = async () => {
    if (!deleteTicketId) {
      return;
    }

    try {
      await deleteTicketByID(deleteTicketId);
      setData(prevData => prevData.filter(ticket => ticket.ticket_id !== deleteTicketId));
      toast.success('Ticket deleted successfully!');
    } catch (error: any) {
      console.error(error);
      toast.error('Error deleting ticket!');
    } finally {
      setDeleteTicketId(null);
    }
  };

  const handleEditAssignee = (ticketId: string) => {
    setEditingAssignee(prev => ({ ...prev, [ticketId]: data.find(ticket => ticket.ticket_id === ticketId)?.assigned || '' }));
  };

  const handleAssigneeChange = (ticketId: string, value: string) => {
    setEditingAssignee(prev => ({ ...prev, [ticketId]: value }));
  };

  const handleUpdateAssignee = async (ticketId: string) => {
    if (!editingAssignee[ticketId]) {
      return;
    }

    setLoadingState(prev => ({ ...prev, [`${ticketId}-assignee`]: true }));

    try {
      const newAssignee = editingAssignee[ticketId] ?? '';
      await updatePartialTicket(ticketId, 'assigned', newAssignee);

      setData(prevData =>
        prevData.map(ticket =>
          ticket.ticket_id === ticketId ? { ...ticket, assigned: newAssignee } : ticket,
        ),
      );

      toast.success(`Assignee updated successfully!`);

      setEditingAssignee((prev) => {
        const newState = { ...prev };
        delete newState[ticketId];
        return newState;
      });
    } catch (error: any) {
      toast.error(`Error updating assignee: ${error.message}`);
    } finally {
      setLoadingState(prev => ({ ...prev, [`${ticketId}-assignee`]: false }));
    }
  };

  useEffect(() => {
    const pagesInBatch = data.length > 0 ? Math.ceil(data.length / PAGE_SIZE) : 1;
    const computedTotalPages = isFinalBatch ? (batchNumber - 1) * 15 + pagesInBatch : (batchNumber - 1) * 15 + 15;
    setTotalPages(computedTotalPages);
    setDisableNext(isFinalBatch && page >= computedTotalPages);
  }, [data, isFinalBatch, page, batchNumber, setTotalPages, setDisableNext]);

  const updateTicket = async (ticketId: string, field: 'status' | 'priority', value: string) => {
    setLoadingState(prev => ({ ...prev, [`${ticketId}-${field}`]: true }));
    try {
      await updatePartialTicket(ticketId, field, value);
      setData(prevData =>
        prevData.map(ticket =>
          ticket.ticket_id === ticketId ? { ...ticket, [field]: value } : ticket,
        ),
      );
      toast.success(`Ticket ${field} updated successfully!`);
    } catch (error: any) {
      toast.error(`Error updating ticket: ${error.message}`);
    } finally {
      setLoadingState(prev => ({ ...prev, [`${ticketId}-${field}`]: false }));
    }
  };

  if (loading) {
    return <TicketListSkeleton />;
  }

  const localPage = ((page - 1) % 15) + 1;
  const startIndex = (localPage - 1) * PAGE_SIZE;
  const tickets = data.slice(startIndex, startIndex + PAGE_SIZE);

  return (
    <div className="custom-scrollbar relative w-full rounded-md border shadow-md">
      <ToastContainer position="top-right" autoClose={3000} />
      <div className="overflow-x-auto">
        <ul className="custom-scrollbar max-h-[80vh] overflow-auto rounded-md bg-white shadow">
          {/* Sticky Header Row */}
          <li className="sticky top-0 z-10 flex items-center justify-between gap-4 border-b bg-white px-4 py-3 text-sm font-semibold md:text-base">
            <div className="w-[10%]">ID</div>
            <div className="w-1/2 md:w-1/5">Title</div>
            <div className="hidden w-[15%] md:block">Reported By</div>
            <div className="hidden w-[15%] md:block">Assignee</div>
            <div className="hidden w-[10%] md:flex">Status</div>
            <div className="hidden w-[10%] md:flex">Priority</div>
            <div className="hidden w-1/5 justify-center text-center md:flex md:w-[10%]">Created</div>
            <div className="w-[10%] text-center md:w-[5%]">Action</div>
          </li>
          {tickets.length === 0
            ? (
                <div className="flex flex-col items-center justify-center gap-4 p-4">
                  <h1 className="text-lg text-gray-800">No Tickets</h1>
                  <div className="flex gap-4">
                    <Link href="/dashboard">
                      <button className="mb-2 flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-white shadow-md hover:bg-blue-700" type="button">
                        <span>
                          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="size-6">
                            <path fillRule="evenodd" d="M9.53 2.47a.75.75 0 0 1 0 1.06L4.81 8.25H15a6.75 6.75 0 0 1 0 13.5h-3a.75.75 0 0 1 0-1.5h3a5.25 5.25 0 1 0 0-10.5H4.81l4.72 4.72a.75.75 0 1 1-1.06 1.06l-6-6a.75.75 0 0 1 0-1.06l6-6a.75.75 0 0 1 1.06 0Z" clipRule="evenodd" />
                          </svg>
                        </span>
                        Back To Dashboard
                      </button>
                    </Link>
                  </div>
                </div>
              )
            : tickets.map(ticket => (
              <li key={ticket.ticket_id} className="flex items-center justify-between gap-4 bg-white px-4 py-3 hover:bg-gray-100">
                <Link href={`/dashboard/tickets/${ticket.ticket_id}`} className="w-[10%] truncate font-semibold text-blue-600">
                  {ticket.ticket_id}
                </Link>

                {/* Title (Linked) */}
                <Link href={`/dashboard/tickets/${ticket.ticket_id}`} className="w-1/2 truncate font-semibold text-blue-600 md:w-1/5">
                  {ticket.title}
                </Link>
                {' '}
                <div
                  className="hidden w-[15%] truncate text-gray-700 md:block"
                >
                  {
                    ticket.reported_by || 'Unreported'
                  }
                </div>

                <div
                  className="hidden w-[15%] truncate text-gray-700 md:block"
                  role="button"
                  tabIndex={0}
                  onClick={() => handleEditAssignee(ticket.ticket_id)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      handleEditAssignee(ticket.ticket_id);
                    }
                  }}
                >
                  {editingAssignee[ticket.ticket_id] !== undefined
                    ? (
                        <input
                          type="email"
                          className="w-full border p-1"
                          value={editingAssignee[ticket.ticket_id]}
                          onChange={e => handleAssigneeChange(ticket.ticket_id, e.target.value)}
                          onKeyDown={e => e.key === 'Enter' && handleUpdateAssignee(ticket.ticket_id)}
                          autoFocus
                          onBlur={() =>
                            setEditingAssignee((prev) => {
                              const newState = { ...prev };
                              delete newState[ticket.ticket_id]; // Remove the key properly
                              return newState;
                            })}
                        />
                      )
                    : (
                        ticket.assigned || 'Unassigned'
                      )}
                </div>

                <div className="hidden w-[10%] justify-center md:flex">
                  {loadingState[`${ticket.ticket_id}-status`]
                    ? (
                        <ClipLoader size={20} color="#36d7b7" />
                      )
                    : (
                        <select value={ticket.status} onChange={e => updateTicket(ticket.ticket_id, 'status', e.target.value)}>
                          <option value="OPEN">Open</option>
                          <option value="IN_PROGRESS">In Progress</option>
                          <option value="CLOSED">Closed</option>
                        </select>
                      )}
                </div>
                <div className="hidden w-[10%] justify-center md:flex">
                  {loadingState[`${ticket.ticket_id}-priority`]
                    ? (
                        <ClipLoader size={20} color="#36d7b7" />
                      )
                    : (
                        <select value={ticket.priority} onChange={e => updateTicket(ticket.ticket_id, 'priority', e.target.value)}>
                          <option value="High">High</option>
                          <option value="Medium">Medium</option>
                          <option value="Low">Low</option>
                        </select>
                      )}
                </div>
                <div className="hidden w-1/5 justify-center text-center md:flex md:w-[10%]">{ticket.created_at ? format(new Date(ticket.created_at), 'dd MMM yyyy') : 'N/A'}</div>
                <div className="relative flex w-[10%] items-center justify-center gap-2 md:w-[5%]">
                  <Link href={`/dashboard/tickets/${ticket.ticket_id}`} className="text-gray-500 hover:text-blue-600">
                    <PencilSquareIcon className="size-5" />
                  </Link>
                  <button
                    type="button"
                    onClick={() =>
                      setOpenMenuTicketId(prev => (prev === ticket.ticket_id ? null : ticket.ticket_id))}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    <EllipsisVerticalIcon className="size-5" />
                  </button>

                  {openMenuTicketId === ticket.ticket_id && (
                    <div className="absolute right-0 top-6 z-20 w-28 rounded-md border bg-white shadow-md">
                      <button
                        type="button"
                        className="flex w-full items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-gray-100"
                        onClick={() => {
                          setDeleteTicketId(ticket.ticket_id);
                          setOpenMenuTicketId(null);
                        }}
                      >
                        <TrashIcon className="size-4" />
                        Delete
                      </button>
                    </div>
                  )}
                </div>

              </li>
            ))}
        </ul>
      </div>
      <DeleteConfirmationModal
        isOpen={!!deleteTicketId}
        onClose={() => setDeleteTicketId(null)}
        onConfirm={handleDeleteTicket}
      />
    </div>
  );
};

export default TicketList;
