/* eslint-disable no-console */
'use client';

import 'react-toastify/dist/ReactToastify.css';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { toast, ToastContainer } from 'react-toastify';
import { TicketDetailSkeleton } from '@/components/ui/Skeletons';

const TicketDetailPage = () => {
  const params = useParams();
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [ticket, setTicket] = useState<any>(null);
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'High',
    status: 'OPEN',
    reported_by: '',
    assigned: '',
  });

  useEffect(() => {
    const fetchTicket = async () => {
      try {
        const response = await fetch(`http://localhost:8000/tickets/${params.id}?customer_guid=9a376cd0-396e-4a5a-9313-f8dfcfcba174`);
        if (!response.ok) {
          throw new Error('Failed to fetch ticket');
        }
        const data = await response.json();
        setTicket(data);
        setFormData({
          title: data.title || '',
          description: data.description || '',
          priority: data.priority || 'High',
          status: data.status || 'OPEN',
          reported_by: data.reported_by || '',
          assigned: data.assigned || '',
        });
      } catch (error) {
        toast.error('Error fetching ticket');
        console.log(error);
      } finally {
        setLoading(false);
      }
    };

    fetchTicket();
  }, [params.id]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleUpdate = async () => {
    try {
      const response = await fetch(`http://localhost:8000/tickets/${params.id}?customer_guid=9a376cd0-396e-4a5a-9313-f8dfcfcba174`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        toast.success('Ticket updated successfully!');
        setTimeout(() => router.push('/dashboard/tickets'), 2000);
      } else {
        toast.error('Failed to update ticket.');
      }
    } catch (error) {
      toast.error('Error updating ticket.');
      console.log(error);
    }
  };

  if (loading) {
    return <TicketDetailSkeleton/>;
  }
  if (!ticket) {
    return <p className="text-center text-red-500">Ticket not found</p>;
  }

  return (
    <div className="mx-auto max-w-2xl rounded-lg bg-white p-6 shadow-md">
      <ToastContainer position="top-right" autoClose={3000} />
      <h1 className="text-2xl font-bold">Edit Ticket</h1>

      <div className="mt-4 space-y-4">
        <div>
          <label htmlFor="title" className="block text-sm font-medium">Title</label>
          <input type="text" id="title" name="title" value={formData.title} onChange={handleChange} className="mt-1 w-full rounded border p-2" />
        </div>

        <div>
          <label htmlFor="description" className="block text-sm font-medium">Description</label>
          <textarea id="description" name="description" value={formData.description} onChange={handleChange} className="mt-1 w-full rounded border p-2" rows={3} />
        </div>

        <div>
          <label htmlFor="priority" className="block text-sm font-medium">Priority</label>
          <select id="priority" name="priority" value={formData.priority} onChange={handleChange} className="mt-1 w-full rounded border p-2">
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
        </div>

        <div>
          <label htmlFor="status" className="block text-sm font-medium">Status</label>
          <select id="status" name="status" value={formData.status} onChange={handleChange} className="mt-1 w-full rounded border p-2">
            <option value="OPEN">Open</option>
            <option value="IN PROGRESS">In Progress</option>
            <option value="RESOLVED">Resolved</option>
          </select>
        </div>

        <div>
          <label htmlFor="reported_by" className="block text-sm font-medium">Reported By</label>
          <input type="text" id="reported_by" name="reported_by" value={formData.reported_by} onChange={handleChange} className="mt-1 w-full rounded border p-2" />
        </div>

        <div>
          <label htmlFor="assigned" className="block text-sm font-medium">Assigned</label>
          <input type="text" id="assigned" name="assigned" value={formData.assigned} onChange={handleChange} className="mt-1 w-full rounded border p-2" />
        </div>

        {ticket.custom_fields && Object.keys(ticket.custom_fields).length > 0 && (
          <div className="mt-4">
            <h2 className="text-lg font-semibold">Custom Fields</h2>
            {Object.entries(ticket.custom_fields).map(([key, value]) => (
              <div key={key} className="mt-2">
                <label htmlFor={key} className="block text-sm font-medium">{key}</label>
                <input type="text" id={key} name={key} value={String(value)} readOnly className="mt-1 w-full rounded border bg-gray-100 p-2" />
              </div>
            ))}
          </div>
        )}

        <button onClick={handleUpdate} type="button" className="mt-4 w-full rounded bg-blue-500 p-2 text-white hover:bg-blue-600">
          Update Ticket
        </button>
      </div>

      <Link href="/dashboard/tickets" className="mt-4 inline-block text-blue-500 underline">
        ← Back to Tickets
      </Link>
    </div>
  );
};

export default TicketDetailPage;
