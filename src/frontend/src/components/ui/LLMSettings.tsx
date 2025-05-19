'use client';

import 'react-toastify/dist/ReactToastify.css';

import { PencilSquareIcon } from '@heroicons/react/24/solid';
import { useEffect, useState } from 'react';
import { toast, ToastContainer } from 'react-toastify';

export default function LLMSettings() {
  const [llmprovider, setLlmProvider] = useState('');
  const [model, setModel] = useState('');
  const [useLLM, setUseLLM] = useState(false);
  const [isEditing, setIsEditing] = useState(false);

  async function fetchSettings() {
    try {
      const res = await fetch('/api/backend/llmSettings', { method: 'GET' });
      const data = await res.json();
      setUseLLM(data.llm_response_mode === 'LLM');
      setLlmProvider(data.llmprovider);
      setModel(data.model);
    } catch (error) {
      console.error('Error fetching settings:', error);
      toast.error('Failed to fetch current settings');
    }
  }

  useEffect(() => {
    fetchSettings();
  }, []);

  async function handleEditClick() {
    if (isEditing) {
      try {
        const res = await fetch('/api/backend/llmSettings', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            use_llm: useLLM,
            llmprovider,
            model,
          }),
        });

        if (res.ok) {
          const result = await res.json();
          toast.success(result.message || 'Settings updated successfully');
        } else {
          toast.error('Failed to update settings');
          await fetchSettings(); // Revert
        }
      } catch (error) {
        console.error('Error submitting settings:', error);
        toast.error('Error updating settings');
        await fetchSettings(); // Revert
      }
    }

    setIsEditing(!isEditing);
  }

  return (
    <div className="flex min-h-screen flex-col items-center bg-gray-100 px-4 py-8">
      <ToastContainer position="top-right" autoClose={3000} hideProgressBar />

      <div className="flex max-w-md flex-col space-y-4 rounded-lg bg-white p-6 shadow-md sm:max-w-3xl sm:flex-row sm:items-center sm:space-x-4 sm:space-y-0">
        <span className="text-sm font-semibold text-gray-700 sm:text-base">LLM</span>

        <input
          type="text"
          value={llmprovider}
          onChange={e => setLlmProvider(e.target.value)}
          disabled={!isEditing}
          placeholder="Provider"
          className="w-full rounded border px-3 py-2 text-sm disabled:bg-gray-100 disabled:text-gray-500 sm:w-32"
        />

        <input
          type="text"
          value={model}
          onChange={e => setModel(e.target.value)}
          disabled={!isEditing}
          placeholder="Model"
          className="w-full rounded border px-3 py-2 text-sm disabled:bg-gray-100 disabled:text-gray-500 sm:w-48"
        />

        <label className="flex items-center justify-between sm:justify-start">
          <span className="sr-only">Enable LLM</span>
          <div className="relative">
            <input
              type="checkbox"
              checked={useLLM}
              onChange={() => isEditing && setUseLLM(!useLLM)}
              className="sr-only"
              disabled={!isEditing}
            />
            <div className={`h-5 w-10 rounded-full shadow-inner transition ${useLLM ? 'bg-blue-500' : 'bg-gray-300'}`} />
            <div className={`absolute left-0 top-0 size-5 rounded-full bg-white shadow transition ${useLLM ? 'translate-x-5' : ''}`} />
          </div>
        </label>

        <button
          type="button"
          onClick={handleEditClick}
          className="p-2"
          title={isEditing ? 'Save' : 'Edit'}
        >
          {isEditing
            ? <span className="rounded bg-green-500 p-2 text-white">Save</span>
            : <PencilSquareIcon className="size-5 text-gray-600" />}
        </button>
      </div>
    </div>
  );
}
