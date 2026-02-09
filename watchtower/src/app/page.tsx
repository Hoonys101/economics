"use client";

import { useWatchtowerStore } from "@/store/useWatchtowerStore";
import { Activity, AlertTriangle, TrendingUp, Users, Play, Pause, FastForward, Settings } from "lucide-react";
import { useState, useEffect } from "react";

export default function OverviewPage() {
  const { snapshot, isConnected, commandConnected, sendCommand, endpoint } = useWatchtowerStore();

  // Local state for sliders to ensure smooth dragging
  const [baseRate, setBaseRate] = useState(0.05);

  // Sync local state with snapshot when it arrives (optional, but good for initial load)
  useEffect(() => {
    if (snapshot) {
        // If we wanted to sync the slider to the actual simulation state:
        // setBaseRate(snapshot.monetary.base_rate);
        // But for "commanding", we might want it to stay where we put it.
        // Let's just use the default or last set value for now.
    }
  }, [snapshot]);

  if (!isConnected || !snapshot) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
            <h1 className="text-2xl font-bold mb-2">Connecting to The Watchtower...</h1>
            <p className="text-gray-500">Waiting for simulation heartbeat...</p>
            <div className="mt-4 text-xs text-gray-400">{endpoint}</div>
        </div>
      </div>
    );
  }

  const { system_integrity, macro_economy, politics } = snapshot;

  const handleBaseRateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const val = parseFloat(e.target.value);
      setBaseRate(val);
      sendCommand("SET_BASE_RATE", { rate: val });
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Mission Control</h1>
        <div className="flex space-x-2">
            <button onClick={() => sendCommand("PAUSE")} className="p-2 bg-yellow-500 text-white rounded hover:bg-yellow-600" title="Pause"><Pause size={20}/></button>
            <button onClick={() => sendCommand("RESUME")} className="p-2 bg-green-500 text-white rounded hover:bg-green-600" title="Resume"><Play size={20}/></button>
            <button onClick={() => sendCommand("STEP")} className="p-2 bg-blue-500 text-white rounded hover:bg-blue-600" title="Step"><FastForward size={20}/></button>
        </div>
      </div>

      {/* Control Panel */}
      <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-bold flex items-center"><Settings className="mr-2"/> Active Controls</h3>
              <span className={`text-xs px-2 py-1 rounded ${commandConnected ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                  {commandConnected ? 'Connected' : 'Disconnected'}
              </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Central Bank Base Rate: {(baseRate * 100).toFixed(1)}%
                  </label>
                  <input
                      type="range"
                      min="0.0"
                      max="0.2"
                      step="0.005"
                      value={baseRate}
                      onChange={handleBaseRateChange}
                      className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer dark:bg-gray-700"
                  />
                  <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>0%</span>
                      <span>20%</span>
                  </div>
              </div>
          </div>
      </div>

      {/* Alert Banner if Leak */}
      {system_integrity.m2_leak !== 0 && (
          <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 rounded" role="alert">
            <div className="flex">
                <AlertTriangle className="h-6 w-6 mr-4" />
                <div>
                    <p className="font-bold">CRITICAL SYSTEM ALERT</p>
                    <p>M2 Money Leak Detected: {system_integrity.m2_leak}</p>
                </div>
            </div>
          </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* System Integrity */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">System Integrity</h3>
                <Activity className="h-4 w-4 text-blue-500" />
            </div>
            <div className="flex flex-col space-y-2">
                 <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-300">FPS</span>
                    <span className="font-bold">{system_integrity.fps.toFixed(2)}</span>
                 </div>
                 <div className="flex justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-300">M2 Leak</span>
                    <span className={`font-bold ${system_integrity.m2_leak !== 0 ? 'text-red-500' : 'text-green-500'}`}>
                        {system_integrity.m2_leak.toFixed(4)}
                    </span>
                 </div>
            </div>
        </div>

        {/* GDP Growth */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
             <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">GDP Growth</h3>
                <TrendingUp className="h-4 w-4 text-green-500" />
            </div>
            <div className="text-2xl font-bold">{macro_economy.gdp_growth.toFixed(2)}%</div>
        </div>

        {/* Unemployment */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
             <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Unemployment</h3>
                <Users className="h-4 w-4 text-yellow-500" />
            </div>
            <div className="text-2xl font-bold">{macro_economy.unemployment_rate.toFixed(2)}%</div>
        </div>

        {/* Approval Rating */}
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
             <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Gov Approval</h3>
                <Users className="h-4 w-4 text-purple-500" />
            </div>
            <div className="text-2xl font-bold">{(politics.approval_rating * 100).toFixed(1)}%</div>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6">
        <div className="bg-white dark:bg-gray-800 p-6 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-bold mb-4">Tick Status</h3>
            <div className="grid grid-cols-2 gap-4">
                <div>
                    <span className="text-sm text-gray-500">Current Tick</span>
                    <div className="text-xl font-mono">{snapshot.tick}</div>
                </div>
                 <div>
                    <span className="text-sm text-gray-500">Timestamp</span>
                    <div className="text-xl font-mono">{snapshot.timestamp}</div>
                </div>
            </div>
        </div>
      </div>
    </div>
  );
}
