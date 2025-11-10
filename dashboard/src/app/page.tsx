"use client";

import { useEffect, useState } from 'react';

export default function Home() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // This function will check if the user is authenticated by making a request to a protected endpoint.
    // We'll use a simple profile endpoint for this check. If it returns 200, we are logged in.
    const checkAuthStatus = async () => {
      try {
        // The browser will automatically send the session cookie.
        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_API_URL}/api/v1/auth-status`, { credentials: 'include' });
        if (response.ok) {
          const data = await response.json();
          setIsAuthenticated(data.isAuthenticated);
        } else {
          setIsAuthenticated(false);
        }
      } catch (error) {
        console.error("Error checking authentication status:", error);
        setIsAuthenticated(false);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuthStatus();
  }, []);

  const handleLogin = () => {
    // Redirect the user to the backend's login route.
    window.location.href = `${process.env.NEXT_PUBLIC_BACKEND_API_URL}/login?source=dashboard`;
  };

  if (isLoading) {
    return <main className="flex min-h-screen flex-col items-center justify-center p-24"><p>Loading...</p></main>;
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24">
      <div className="z-10 max-w-5xl w-full items-center justify-between font-mono text-sm lg:flex">
        <h1 className="text-4xl font-bold text-center">Fitbit Sleep Dashboard</h1>
      </div>

      <div className="mt-10">
        {isAuthenticated ? (
          <div>
            <p className="text-lg text-green-500">You are authenticated!</p>
            {/* We will replace this with a link to the actual dashboard view later */}
            <a href="/dashboard" className="mt-4 inline-block bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded">
              Go to Dashboard
            </a>
          </div>
        ) : (
          <div>
            <p className="text-lg text-red-500">Please log in to view your data.</p>
            <button
              onClick={handleLogin}
              className="mt-4 bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
            >
              Login with Fitbit
            </button>
          </div>
        )}
      </div>
    </main>
  );
}
