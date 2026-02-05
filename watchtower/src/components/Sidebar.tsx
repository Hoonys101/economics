"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { LayoutDashboard, BadgeDollarSign, Vote, Server, Activity } from "lucide-react";
import { clsx } from "clsx";

const navItems = [
  { name: "Overview", href: "/", icon: LayoutDashboard },
  { name: "Finance", href: "/finance", icon: BadgeDollarSign },
  { name: "Politics", href: "/politics", icon: Vote },
  { name: "System", href: "/system", icon: Server },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <div className="flex h-screen w-64 flex-col bg-gray-900 text-white flex-shrink-0">
      <div className="flex items-center justify-center h-16 border-b border-gray-800">
        <Activity className="h-6 w-6 mr-2 text-blue-500" />
        <span className="text-xl font-bold">The Watchtower</span>
      </div>
      <nav className="flex-1 px-2 py-4 space-y-2">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={clsx(
                "flex items-center px-4 py-3 text-sm font-medium rounded-md transition-colors",
                isActive
                  ? "bg-gray-800 text-white"
                  : "text-gray-400 hover:bg-gray-800 hover:text-white"
              )}
            >
              <item.icon className="mr-3 h-5 w-5" />
              {item.name}
            </Link>
          );
        })}
      </nav>
      <div className="p-4 border-t border-gray-800">
        <div className="text-xs text-gray-500 text-center">
            PH6-WT-001
        </div>
      </div>
    </div>
  );
}
