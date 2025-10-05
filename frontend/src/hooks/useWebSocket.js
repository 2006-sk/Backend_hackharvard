import { useState, useEffect, useRef } from "react";

const useWebSocket = (url, onMessage) => {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [error, setError] = useState(null);
  const wsRef = useRef(null);
  const onMessageRef = useRef(onMessage);

  // Update the ref when onMessage changes
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  // Connect once when component mounts
  useEffect(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    console.log("🔌 Connecting to WebSocket:", url);
    setIsConnecting(true);
    setError(null);

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log("✅ WebSocket connected successfully");
        setIsConnected(true);
        setIsConnecting(false);
        setError(null); // Clear any previous errors
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log("📨 WebSocket message received:", data);
          if (onMessageRef.current) {
            onMessageRef.current(data);
          }
        } catch (parseError) {
          console.error("❌ Error parsing WebSocket message:", parseError);
          console.log("Raw message:", event.data);
        }
      };

      ws.onclose = (event) => {
        console.log(
          "🔌 WebSocket connection closed:",
          event.code,
          event.reason
        );
        setIsConnected(false);
        setIsConnecting(false);

        // Log error if not a clean close
        if (event.code !== 1000) {
          console.error(
            "❌ WebSocket closed with error code:",
            event.code,
            "Reason:",
            event.reason
          );
        }
      };

      ws.onerror = (error) => {
        console.error("❌ WebSocket error:", error);
        setError("WebSocket connection error");
        setIsConnecting(false);
      };
    } catch (error) {
      console.error("❌ Failed to create WebSocket:", error);
      setError("Failed to create WebSocket connection");
      setIsConnecting(false);
    }

    // Cleanup on unmount
    return () => {
      if (wsRef.current) {
        console.log("🔌 Disconnecting WebSocket...");
        wsRef.current.close(1000, "Manual disconnect");
        wsRef.current = null;
      }
      setIsConnected(false);
      setIsConnecting(false);
      setError(null);
    };
  }, [url]); // Remove onMessage from dependencies to prevent reconnection loops

  const disconnect = () => {
    if (wsRef.current) {
      console.log("🔌 Disconnecting WebSocket...");
      wsRef.current.close(1000, "Manual disconnect");
      wsRef.current = null;
    }
    setIsConnected(false);
    setIsConnecting(false);
    setError(null);
  };

  const sendMessage = (message) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    } else {
      console.warn("WebSocket is not connected");
    }
  };

  return {
    isConnected,
    isConnecting,
    error,
    disconnect,
    sendMessage,
    ws: wsRef.current,
  };
};

export default useWebSocket;
