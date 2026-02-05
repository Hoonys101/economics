"use client";

import { useWatchtowerStore } from "@/store/useWatchtowerStore";
import { Vote } from "lucide-react";

export default function PoliticsPage() {
  const { snapshot } = useWatchtowerStore();

  if (!snapshot) {
     return (
      <div className="flex items-center justify-center h-full text-gray-500">
        Awaiting political data...
      </div>
    );
  }

  const { politics } = snapshot;

  const getPartyColor = (party: string) => {
    switch (party) {
        case 'RED': return 'text-red-500';
        case 'BLUE': return 'text-blue-500';
        default: return 'text-gray-500';
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold flex items-center">
        <Vote className="mr-3" /> Political Landscape
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
            <h3 className="text-sm text-gray-500 mb-1">Ruling Party</h3>
            <div className={`text-3xl font-bold ${getPartyColor(politics.party)}`}>{politics.party}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
            <h3 className="text-sm text-gray-500 mb-1">Approval Rating</h3>
            <div className="text-3xl font-bold">{(politics.approval_rating * 100).toFixed(1)}%</div>
             <div className="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700 mt-2">
                <div className="bg-blue-600 h-2.5 rounded-full" style={{ width: `${politics.approval_rating * 100}%` }}></div>
            </div>
        </div>
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
            <h3 className="text-sm text-gray-500 mb-1">Social Cohesion</h3>
            <div className="text-3xl font-bold">{(politics.social_cohesion * 100).toFixed(1)}%</div>
             <div className="w-full bg-gray-200 rounded-full h-2.5 dark:bg-gray-700 mt-2">
                <div className="bg-green-600 h-2.5 rounded-full" style={{ width: `${politics.social_cohesion * 100}%` }}></div>
            </div>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
        <h3 className="text-lg font-bold mb-4">Current Events</h3>
        {politics.current_events.length === 0 ? (
            <div className="text-gray-500 italic">No significant events detected.</div>
        ) : (
            <ul className="space-y-2">
                {politics.current_events.map((event, index) => (
                    <li key={index} className="flex items-start">
                        <span className="inline-block w-2 h-2 mt-2 mr-2 bg-blue-500 rounded-full"></span>
                        <span>{event}</span>
                    </li>
                ))}
            </ul>
        )}
      </div>
    </div>
  );
}
