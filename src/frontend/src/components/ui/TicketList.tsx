/* eslint-disable no-console */
import { useOrganization } from '@clerk/nextjs';
import { ArrowRightIcon } from '@heroicons/react/24/solid';
import { format } from 'date-fns';
import Link from 'next/link';
import React, { useEffect, useState } from 'react';
import { ClipLoader } from 'react-spinners';
import { toast, ToastContainer } from 'react-toastify';

import { fetchTicketsByCustomer, updatePartialTicket } from '@/api/backend-sdk/ticketServiceApiCalls';
import { TicketListSkeleton } from '@/components/ui/Skeletons';

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
  const [data, setData] = useState<Ticket[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isFinalBatch, setIsFinalBatch] = useState<boolean>(false);
  const [loadingState, setLoadingState] = useState<{ [key: string]: boolean }>({});

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
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };
    fetchTickets();
  }, [organization?.id, batchNumber]);

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
      <ul className="custom-scrollbar max-h-[90vh] overflow-auto rounded-md bg-white shadow">
        {/* Sticky Header Row */}
        <li className="sticky top-0 z-10 grid grid-cols-[0.5fr_2fr_1.5fr_1.5fr_1fr_1fr_1fr_auto] gap-4 border-b bg-white p-3 font-semibold">
          <div>ID</div>
          <div>Title</div>
          <div>Reported By</div>
          <div>Assignee</div>
          <div>Status</div>
          <div>Priority</div>
          <div className="text-center">Created</div>
          <div className="text-center">Action</div>
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
            <li key={ticket.ticket_id} className="grid grid-cols-[0.5fr_2fr_1.5fr_1.5fr_1fr_1fr_1fr_auto] items-center gap-4 rounded-lg border-transparent bg-white p-4 hover:bg-gray-100">
              <div className="font-semibold">{ticket.ticket_id}</div>
              <div className="truncate font-semibold text-blue-600">{ticket.title}</div>
              <div className="truncate font-semibold text-gray-700">{ticket.reported_by}</div>
              <div className="truncate font-semibold text-gray-700">{ticket.assigned}</div>
              <div>
                {loadingState[`${ticket.ticket_id}-status`]
                  ? <ClipLoader size={20} color="#36d7b7" />
                  : (
                      <select value={ticket.status} onChange={e => updateTicket(ticket.ticket_id, 'status', e.target.value)}>
                        <option value="OPEN">Open</option>
                        <option value="IN_PROGRESS">In Progress</option>
                        <option value="CLOSED">Closed</option>
                      </select>
                    )}
              </div>
              <div>
                {loadingState[`${ticket.ticket_id}-priority`]
                  ? <ClipLoader size={20} color="#36d7b7" />
                  : (
                      <select value={ticket.priority} onChange={e => updateTicket(ticket.ticket_id, 'priority', e.target.value)}>
                        <option value="High">High</option>
                        <option value="Medium">Medium</option>
                        <option value="Low">Low</option>
                      </select>
                    )}
              </div>
              <div className="text-right text-gray-700">{ticket.created_at ? format(new Date(ticket.created_at), 'dd MMM yyyy') : 'N/A'}</div>
              <Link href={`/dashboard/tickets/${ticket.ticket_id}`} className="text-blue-600">
                <ArrowRightIcon className="size-5" />
              </Link>
            </li>
          ))}
      </ul>
    </div>
  );
};

export default TicketList;
