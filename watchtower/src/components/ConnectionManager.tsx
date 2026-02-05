"use client";
import { useEffect } from "react";
import { useWatchtowerStore } from "@/store/useWatchtowerStore";

export function ConnectionManager() {
  const connect = useWatchtowerStore((state) => state.connect);
  const disconnect = useWatchtowerStore((state) => state.disconnect);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return null;
}
