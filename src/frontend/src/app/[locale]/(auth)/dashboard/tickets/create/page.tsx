'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';
import { toast } from 'react-toastify';

import { createTicket, fetchCustomFields } from '@/api/backend-sdk/ticketServiceApiCalls';

const CreateTicketPage = () => {
  const router = useRouter();
  const [customFields, setCustomFields] = useState([]);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    chat_id: null,
    title: '',
    description: '',
    priority: 'Medium', // Default value
    reported_by: '',
    assigned: '',
    custom_fields: {},
  });

  useEffect(() => {
    loadCustomFields();
  }, []);

  const loadCustomFields = async () => {
    try {
      const data = await fetchCustomFields();
      setCustomFields(data.custom_fields || []);
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
        router.push('/dashboard/tickets'); // Redirect to ticket list page
      } else {
        throw new Error('Invalid response from server');
      }
    } catch (error) {
      toast.error(`Error creating ticket`);
      console.error('Error creating ticket:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto max-w-2xl p-6">
      <h2 className="mb-4 text-lg font-semibold">Create Ticket</h2>

      <form onSubmit={handleSubmit} className="space-y-4">
        {[
          { label: 'Title', name: 'title' },
          { label: 'Description', name: 'description', type: 'textarea' },
          { label: 'Reported By', name: 'reported_by' },
          { label: 'Assigned To', name: 'assigned' },
        ].map(({ label, name, type }) => (
          <div key={name}>
            <label htmlFor={name} className="text-sm font-medium">{label}</label>
            {type === 'textarea'
              ? <textarea id={name} name={name} value={formData[name]} onChange={handleChange} className="w-full rounded border p-2" />
              : <input id={name} name={name} type="text" value={formData[name]} onChange={handleChange} className="w-full rounded border p-2" />}
          </div>
        ))}

        {/* Priority Dropdown */}
        <div>
          <label htmlFor="priority" className="text-sm font-medium">Priority</label>
          <select id="priority" name="priority" value={formData.priority} onChange={handleChange} className="w-full rounded border p-2">
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
                  type={field_type === 'number' ? 'number' : field_type === 'date' ? 'date' : 'text'}
                  value={formData.custom_fields[field_name] || ''}
                  onChange={e => handleCustomFieldChange(e, field_name)}
                  className="w-full rounded border p-2"
                  required={required}
                />
              </div>
            ))}
          </div>
        )}

        <button type="submit" disabled={loading} className="rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700">
          {loading ? 'Creating...' : 'Create Ticket'}
        </button>
      </form>
    </div>
  );
};

export default CreateTicketPage;
