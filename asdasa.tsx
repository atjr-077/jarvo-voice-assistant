import React, { useState, useEffect } from 'react';

const PersonalizedFlow = () => {
  const [source, setSource] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  useEffect(() => {
    // Simulate detecting the user's source (e.g., from URL parameters)
    const detectedSource = new URLSearchParams(window.location.search).get('source');
    setSource(detectedSource || 'default');
    setIsLoading(false);
  }, []);

  const getFlowContent = () => {
    switch (source) {
      case 'instagram':
        return (
          <div className="p-6 rounded-lg shadow-md bg-white">
            <h2 className="text-2xl font-bold text-[#F60] mb-4">Welcome from Instagram!</h2>
            <p className="text-gray-700">Check out our exclusive offers tailored just for you.</p>
            <button className="mt-4 px-4 py-2 bg-[#F60] text-white rounded-md hover:bg-opacity-90">
              View Offers
            </button>
          </div>
        );
      case 'referral':
        return (
          <div className="p-6 rounded-lg shadow-md bg-white">
            <h2 className="text-2xl font-bold text-green-600 mb-4">Welcome from a Referral!</h2>
            <p className="text-gray-700">Thank you for joining us through a friend. Here's a special gift for you.</p>
            <button className="mt-4 px-4 py-2 bg-green-600 text-white rounded-md hover:bg-opacity-90">
              Claim Gift
            </button>
          </div>
        );
      case 'blog':
        return (
          <div className="p-6 rounded-lg shadow-md bg-white">
            <h2 className="text-2xl font-bold text-[#F60] mb-4">Welcome from our Blog!</h2>
            <p className="text-gray-700">Dive deeper into our content with these recommended reads.</p>
            <button className="mt-4 px-4 py-2 bg-[#F60] text-white rounded-md hover:bg-opacity-90">
              Explore More
            </button>
          </div>
        );
      default:
        return (
          <div className="p-6 rounded-lg shadow-md bg-white">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">Welcome!</h2>
            <p className="text-gray-700">Discover what we have to offer.</p>
            <button className="mt-4 px-4 py-2 bg-gray-800 text-white rounded-md hover:bg-opacity-90">
              Get Started
            </button>
          </div>
        );
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen p-4">
      {isLoading ? (
        <div className="text-gray-600">Loading...</div>
      ) : (
        getFlowContent()
      )}
    </div>
  );
};

export default PersonalizedFlow;