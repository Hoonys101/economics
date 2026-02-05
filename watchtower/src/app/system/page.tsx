"use client";

import { useWatchtowerStore } from "@/store/useWatchtowerStore";
import { Server, CheckCircle, XCircle } from "lucide-react";

export default function SystemPage() {
  const { snapshot, isConnected, endpoint } = useWatchtowerStore();

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold flex items-center">
        <Server className="mr-3" /> System Diagnostics
      </h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
         {/* Connection Status */}
         <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
            <h3 className="text-lg font-bold mb-4">Uplink Status</h3>
            <div className="flex items-center space-x-2">
                {isConnected ? (
                    <CheckCircle className="text-green-500 h-6 w-6" />
                ) : (
                    <XCircle className="text-red-500 h-6 w-6" />
                )}
                <span className="text-xl">{isConnected ? "Connected" : "Disconnected"}</span>
            </div>
            <div className="mt-2 text-sm text-gray-500">
                Endpoint: {endpoint}
            </div>
         </div>

         {/* Integrity Metrics */}
         {snapshot && (
             <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm">
                <h3 className="text-lg font-bold mb-4">Simulation Health</h3>
                <div className="space-y-3">
                    <div className="flex justify-between border-b pb-2 dark:border-gray-700">
                        <span>FPS (Ticks/Sec)</span>
                        <span className="font-mono">{snapshot.system_integrity.fps.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between border-b pb-2 dark:border-gray-700">
                        <span>M2 Leak</span>
                        <span className={`font-mono ${snapshot.system_integrity.m2_leak !== 0 ? "text-red-500 font-bold" : "text-green-500"}`}>
                            {snapshot.system_integrity.m2_leak.toFixed(6)}
                        </span>
                    </div>
                    <div className="flex justify-between border-b pb-2 dark:border-gray-700">
                        <span>Current Tick</span>
                        <span className="font-mono">{snapshot.tick}</span>
                    </div>
                </div>
             </div>
         )}
      </div>

      {snapshot && (
        <div className="bg-gray-900 text-gray-100 p-6 rounded-lg shadow-sm font-mono text-sm overflow-auto max-h-96">
            <h3 className="text-lg font-bold mb-4 text-white">Raw Payload</h3>
            <pre>{JSON.stringify(snapshot, null, 2)}</pre>
        </div>
      )}
    </div>
  );
}
