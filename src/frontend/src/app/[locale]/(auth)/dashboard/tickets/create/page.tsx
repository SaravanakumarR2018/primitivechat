'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { toast } from 'react-toastify';

import { createTicket, fetchCustomFields, getReportedByName } from '@/api/backend-sdk/ticketServiceApiCalls';

const CreateTicketPage = () => {
  type FormDataType = {
    chat_id: string | null;
    title: string;
    description: string;
    priority: string;
    reported_by: string;
    assigned: string;
    custom_fields: Record<string, string>;
  };

  const router = useRouter();
  const [customFields, setCustomFields] = useState([]);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState<FormDataType>({
    chat_id: null,
    title: '',
    description: '',
    priority: 'Medium',
    reported_by: '',
    assigned: '',
    custom_fields: {},
  });

  useEffect(() => {
    loadCustomFieldsAndUserName();
  }, []);

  const loadCustomFieldsAndUserName = async () => {
    try {
      const userName = await getReportedByName();
      const fieldsData = await fetchCustomFields();
      // eslint-disable-next-line no-console
      console.log(fieldsData);
      setCustomFields(fieldsData || []);
      if (userName) {
        setFormData(prev => ({ ...prev, reported_by: userName }));
      }
    } catch (error) {
      console.error('Error fetching custom fields:', error);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleCustomFieldChange = (e: React.ChangeEvent<HTMLInputElement>, fieldName: string) => {
    const { value } = e.target;
    setFormData(prev => ({
      ...prev,
      custom_fields: { ...prev.custom_fields, [fieldName]: value },
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await createTicket(formData);

      if (response.ticket_id) {
        toast.success(`Ticket Created Successfully! 🎉 (ID: ${response.ticket_id})`);
        router.push('/dashboard/tickets');
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (error) {
      toast.error('Error creating ticket');
      console.error('Error creating ticket:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto max-w-2xl p-6">
      <h2 className="mb-4 text-lg font-semibold">Create Ticket</h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Title */}
        <div>
          <label htmlFor="title" className="text-sm font-medium">Title</label>
          <input
            id="title"
            name="title"
            type="text"
            value={formData.title}
            onChange={handleChange}
            className="w-full rounded border p-2"
            required
          />
        </div>

        {/* Description */}
        <div>
          <label htmlFor="description" className="text-sm font-medium">Description</label>
          <textarea
            id="description"
            name="description"
            value={formData.description}
            onChange={handleChange}
            className="w-full rounded border p-2"
            required
          />
        </div>

        {/* Reported By - Read-only */}
        <div>
          <label htmlFor="reported_by" className="text-sm font-medium">Reported By</label>
          <input
            id="reported_by"
            name="reported_by"
            type="text"
            value={formData.reported_by}
            disabled
            className="w-full rounded border bg-gray-100 p-2 text-gray-500"
          />
        </div>

        {/* Assigned */}
        <div>
          <label htmlFor="assigned" className="text-sm font-medium">Assigned To</label>
          <input
            id="assigned"
            name="assigned"
            type="text"
            value={formData.assigned}
            onChange={handleChange}
            className="w-full rounded border p-2"
          />
        </div>

        {/* Priority Dropdown */}
        <div>
          <label htmlFor="priority" className="text-sm font-medium">Priority</label>
          <select
            id="priority"
            name="priority"
            value={formData.priority}
            onChange={handleChange}
            className="w-full rounded border p-2"
          >
            <option value="High">High</option>
            <option value="Medium">Medium</option>
            <option value="Low">Low</option>
          </select>
        </div>

        {/* Custom Fields */}
        {customFields.length > 0 && (
          <div>
            <h3 className="mb-2 text-sm font-semibold">Custom Fields</h3>
            {customFields.map(({ field_name, field_type, required }) => (
              <div key={field_name} className="mb-2">
                <label htmlFor={field_name} className="text-sm font-medium">
                  {field_name}
                  {' '}
                  {required && <span className="text-red-500">*</span>}
                </label>
                <input
                  id={field_name}
                  name={field_name}
                  type={
                    field_type === 'number'
                      ? 'number'
                      : field_type === 'date'
                        ? 'date'
                        : 'text'
                  }
                  value={formData.custom_fields[field_name] || ''}
                  onChange={e => handleCustomFieldChange(e, field_name)}
                  className="w-full rounded border p-2"
                  required={required}
                />
              </div>
            ))}
          </div>
        )}

        <button
          type="submit"
          disabled={loading}
          className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
        >
          {loading ? 'Creating...' : 'Create Ticket'}
        </button>
      </form>
    </div>
  );
};

export default CreateTicketPage;
