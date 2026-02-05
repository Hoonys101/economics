import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";
import { ConnectionManager } from "@/components/ConnectionManager";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "The Watchtower",
  description: "Simulation Command Center",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <div className="flex h-screen overflow-hidden bg-gray-100 dark:bg-gray-950">
            <Sidebar />
            <main className="flex-1 overflow-auto p-8 text-gray-900 dark:text-gray-100">
                <ConnectionManager />
                {children}
            </main>
        </div>
      </body>
    </html>
  );
}
