"use client";

import { useEffect, useState } from 'react';
import SleepChart from '@/components/SleepChart';
import DateTimePicker from '@/components/DateTimePicker';

export default function Dashboard() {
  const [sleepData, setSleepData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [startDate, setStartDate] = useState(new Date('2025-10-31T23:45'));
  const [endDate, setEndDate] = useState(new Date('2025-11-01T08:30'));

  const fetchData = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(
        `http://127.0.0.1:5000/api/v1/sleep-data?start_datetime=${startDate.toISOString()}&end_datetime=${endDate.toISOString()}`,
        { credentials: 'include' }
      );

      if (!response.ok) {
        if (response.status === 401) {
          window.location.href = '/';
        }
        throw new Error('Failed to fetch sleep data');
      }

      const data = await response.json();
      setSleepData(data);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("An unknown error occurred");
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (isLoading) {
    return <main className="flex min-h-screen flex-col items-center justify-center p-24"><p>Loading sleep data...</p></main>;
  }

  if (error) {
    return <main className="flex min-h-screen flex-col items-center justify-center p-24"><p>Error: {error}</p></main>;
  }

  return (
    <main className="flex min-h-screen flex-col items-center p-24">
      <h1 className="text-4xl font-bold mb-10">Your Sleep Data</h1>
      <a href="/" className="mb-10 text-blue-500 hover:underline">Back to Home</a>

      <div className="flex items-end space-x-4 mb-10">
        <div className="w-50">
          <DateTimePicker
            label="Start Date"
            selected={startDate}
            onChange={(date) => date && setStartDate(date)}
          />
        </div>
        <div className="w-50">
          <DateTimePicker
            label="End Date"
            selected={endDate}
            onChange={(date) => date && setEndDate(date)}
          />
        </div>
        <button
          onClick={fetchData}
          className="px-4 py-2 text-white bg-blue-500 rounded-md hover:bg-blue-600"
        >
          Go
        </button>
      </div>
      
      <div className="w-full max-w-6xl">
        {sleepData ? <SleepChart data={sleepData} /> : <p>No sleep data to display.</p>}
      </div>
    </main>
  );
}