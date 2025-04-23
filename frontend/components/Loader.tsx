import { useState, useEffect, useRef } from "react";

export const Loader = ({ loading }: { loading: boolean }) => {
  const [thinkingTime, setThinkingTime] = useState(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Start/stop timer based on loading
  useEffect(() => {
    if (loading) {
      setThinkingTime(0); // Reset
      timerRef.current = setInterval(() => {
        setThinkingTime((prev) => prev + 1);
      }, 1000);
    } else {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [loading]);

  const formatTime = (seconds: number) => {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s < 10 ? "0" : ""}${s}`;
  };

  return (
    <div className="flex justify-center items-center py-8">
      <div className="w-6 h-6 border-4 border-blue-400 border-dashed rounded-full animate-spin"></div>
      <span className="ml-3 text-sm text-gray-400">
        Thinking... {formatTime(thinkingTime)}
      </span>
    </div>
  );
};
