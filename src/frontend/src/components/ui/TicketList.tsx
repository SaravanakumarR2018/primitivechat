/* eslint-disable no-console */
import { ArrowRightIcon } from '@heroicons/react/24/solid';
import { format } from 'date-fns';
import Link from 'next/link';
import React, { useEffect, useState } from 'react';
import { ClipLoader } from 'react-spinners';
import { toast, ToastContainer } from 'react-toastify';

import { TicketListSkeleton } from '@/components/ui/Skeletons';

import BrokenTicket from './NoTicketFoundView';

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
  const [data, setData] = useState<Ticket[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [isFinalBatch, setIsFinalBatch] = useState<boolean>(false);
  const [loadingState, setLoadingState] = useState<{ [key: string]: boolean }>({}); // Track updates

  const batchNumber = Math.floor((page - 1) / 15) + 1;
  const customerGuid = '9a376cd0-396e-4a5a-9313-f8dfcfcba174'; // Replace with actual GUID

  useEffect(() => {
    const fetchTickets = async () => {
      setLoading(true);
      try {
        const response = await fetch(
          `http://localhost:8000/tickets/customer/${customerGuid}?page=${batchNumber}&page_size=${FETCH_SIZE}`,
        );

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to fetch tickets');
        }

        const result: Ticket[] = await response.json();

        if (batchNumber > 1 && result.length === 0) {
          setIsFinalBatch(true);
          setData([]);
        } else {
          setData(result);
          setIsFinalBatch(result.length < FETCH_SIZE);
        }
      } catch (error: any) {
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchTickets();
  }, [batchNumber, customerGuid]);

  useEffect(() => {
    const pagesInBatch = data.length > 0 ? Math.ceil(data.length / PAGE_SIZE) : (isFinalBatch ? 0 : 15);
    const computedTotalPages = isFinalBatch
      ? (batchNumber - 1) * 15 + pagesInBatch
      : (batchNumber - 1) * 15 + 15;

    setTotalPages(computedTotalPages);
    setDisableNext(isFinalBatch && page >= computedTotalPages);
  }, [data, isFinalBatch, page, batchNumber, setTotalPages, setDisableNext]);

  // Do not modify updateTicket
  const updateTicket = async (ticketId: string, field: 'status' | 'priority', value: string) => {
    setLoadingState(prev => ({ ...prev, [`${ticketId}-${field}`]: true })); // Show small spinner

    try {
      const response = await fetch(`http://localhost:8000/tickets/${ticketId}?customer_guid=${customerGuid}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ [field]: value }),
      });

      if (!response.ok) {
        throw new Error('Failed to update ticket');
      }

      console.log(ticketId, field, value);

      setData(prevData =>
        prevData.map(ticket =>
          ticket.ticket_id === ticketId ? { ...ticket, [field]: value } : ticket,
        ),
      );

      toast.success(`Ticket ${field} updated successfully!`);
    } catch (error: any) {
      toast.error(`Error updating ticket: ${error.message}`);
    } finally {
      setLoadingState(prev => ({ ...prev, [`${ticketId}-${field}`]: false })); // Hide spinner
    }
  };

  if (error) {
    if (error.includes('No tickets found')) {
      setDisableNext(true);
      return <BrokenTicket />;
    }
    return <p className="text-red-500">Failed to load tickets.</p>;
  }

  if (loading) {
    return <TicketListSkeleton />;
  }

  // When no tickets are found, render BrokenTicket without rendering the header/pagination
  if (data.length === 0) {
    return <BrokenTicket />;
  }

  const localPage = ((page - 1) % 15) + 1;
  const startIndex = (localPage - 1) * PAGE_SIZE;
  const tickets = data.slice(startIndex, startIndex + PAGE_SIZE);

  return (
    <div className="custom-scrollbar relative max-h-[500px] w-full overflow-y-auto rounded-md border shadow-md">
      <ToastContainer position="top-right" autoClose={3000} />
      <ul className="sticky top-0 z-10 bg-white shadow">
        <li className="grid grid-cols-[0.5fr_2fr_1.5fr_1.5fr_1fr_1fr_1fr_auto] gap-4 border-b p-3 font-semibold">
          <div>ID</div>
          <div>Title</div>
          <div>Reported By</div>
          <div>Assignee</div>
          <div>Status</div>
          <div>Priority</div>
          <div className="text-right">Created</div>
          <div className="text-center">Action</div>
        </li>
      </ul>

      <ul>
        {tickets.map(ticket => (
          <li
            key={ticket.ticket_id}
            className="grid grid-cols-[0.5fr_2fr_1.5fr_1.5fr_1fr_1fr_1fr_auto] items-center gap-4 rounded-lg border-transparent bg-white p-4 hover:bg-gray-100"
          >
            <div className="font-semibold">{ticket.ticket_id}</div>
            <div
              className="cursor-pointer truncate font-semibold text-blue-600"
              style={{ maxWidth: '200px' }}
              role="button"
              tabIndex={0}
              onClick={e => e.currentTarget.classList.toggle('whitespace-normal')}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.currentTarget.classList.toggle('whitespace-normal');
                }
              }}
            >
              {ticket.title}
            </div>

            <div
              className="cursor-pointer truncate font-semibold text-gray-700"
              style={{ maxWidth: '200px' }}
              role="button"
              tabIndex={0}
              onClick={e => e.currentTarget.classList.toggle('whitespace-normal')}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.currentTarget.classList.toggle('whitespace-normal');
                }
              }}
            >
              {ticket.reported_by}
            </div>
            <div
              className="cursor-pointer truncate font-semibold text-gray-700"
              style={{ maxWidth: '200px' }}
              role="button"
              tabIndex={0}
              onClick={e => e.currentTarget.classList.toggle('whitespace-normal')}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.currentTarget.classList.toggle('whitespace-normal');
                }
              }}
            >
              {ticket.assigned}
            </div>

            <div className="relative">
              <select
                className="min-w-[100px] cursor-pointer rounded p-1 text-xs font-semibold focus:outline-none"
                value={ticket.status}
                onChange={e => updateTicket(ticket.ticket_id, 'status', e.target.value)}
              >
                <option value="OPEN">Open</option>
                <option value="IN_PROGRESS">In Progress</option>
                <option value="CLOSED">Closed</option>
              </select>
              {loadingState[`${ticket.ticket_id}-priority`] && (
                <ClipLoader size={15} color="#000" className="absolute right-2 top-1.5" />
              )}
            </div>

            <div className="relative">
              <select
                className="min-w-[100px] cursor-pointer rounded p-1 text-xs font-semibold focus:outline-none"
                value={ticket.priority}
                onChange={e => updateTicket(ticket.ticket_id, 'priority', e.target.value)}
              >
                <option value="High">High</option>
                <option value="Medium">Medium</option>
                <option value="Low">Low</option>
              </select>
              {loadingState[`${ticket.ticket_id}-priority`] && (
                <ClipLoader size={15} color="#000" className="absolute right-2 top-1.5" />
              )}
            </div>

            <div className="text-right text-gray-700">
              {ticket.created_at ? format(new Date(ticket.created_at), 'dd MMM yyyy') : 'N/A'}
            </div>

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
