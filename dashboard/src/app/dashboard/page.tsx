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
      // First, check authentication status
      const authResponse = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_API_URL}/api/v1/auth-status`, { credentials: 'include' });
      if (!authResponse.ok || !(await authResponse.json()).isAuthenticated) {
        window.location.href = '/';
        return;
      }

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/api/v1/sleep-data?start_datetime=${startDate.toISOString()}&end_datetime=${endDate.toISOString()}`,
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
      <h1 className="text-4xl font-bold bg-gradient-to-r from-orange-400 to-purple-400 bg-clip-text text-transparent mb-8">
        Your Sleep Data
      </h1>
      <a href="/" className="mb-10 text-blue-500 hover:underline">Back to Home</a>

      <div className="flex flex-col sm:flex-row gap-4 items-center justify-center mb-10">
        <div className="flex flex-col flex-shrink-0 w-50">
          <DateTimePicker
            label="Start Date"
            selected={startDate}
            onChange={(date) => date && setStartDate(date)}
          />
        </div>
        <div className="flex flex-col flex-shrink-0 w-50">
          <DateTimePicker
            label="End Date"
            selected={endDate}
            onChange={(date) => date && setEndDate(date)}
          />
        </div>
        <button
          onClick={fetchData}
          className="bg-gradient-to-r from-orange-500 to-orange-600 hover:from-orange-600 hover:to-orange-700 text-white px-6 py-2 rounded-lg font-semibold transition-all mt-6"
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