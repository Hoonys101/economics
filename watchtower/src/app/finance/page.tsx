"use client";

import { useWatchtowerStore } from "@/store/useWatchtowerStore";
import { BadgeDollarSign } from "lucide-react";

export default function FinancePage() {
  const { snapshot } = useWatchtowerStore();

  if (!snapshot) {
    return (
      <div className="flex items-center justify-center h-full text-gray-500">
        Awaiting financial data...
      </div>
    );
  }

  const { monetary } = snapshot;

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold flex items-center">
        <BadgeDollarSign className="mr-3" /> Finance Dashboard
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
            <h3 className="text-sm text-gray-500 mb-1">Base Rate</h3>
            <div className="text-3xl font-bold">{monetary.base_rate.toFixed(2)}%</div>
        </div>
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
            <h3 className="text-sm text-gray-500 mb-1">Interbank Rate</h3>
            <div className="text-3xl font-bold">{monetary.interbank_rate.toFixed(2)}%</div>
        </div>
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
            <h3 className="text-sm text-gray-500 mb-1">M2 Supply</h3>
            <div className="text-3xl font-bold">{monetary.m2_supply.toLocaleString()}</div>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
        <h3 className="text-lg font-bold mb-4">Exchange Rates</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Object.entries(monetary.exchange_rates).map(([currency, rate]) => (
                <div key={currency} className="p-4 bg-gray-50 dark:bg-gray-700 rounded">
                    <div className="text-sm text-gray-500 dark:text-gray-300">{currency}</div>
                    <div className="text-xl font-mono">{rate.toFixed(2)}</div>
                </div>
            ))}
        </div>
      </div>
    </div>
  );
}
