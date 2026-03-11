import { useState, useEffect } from "react";

type NetworkStatus = "online" | "offline" | "slow" | "unknown";

export function useNetworkStatus(): NetworkStatus {
    const [status, setStatus] = useState<NetworkStatus>("unknown");

    useEffect(() => {
        // Check initial status
        if (typeof window !== "undefined") {
            setStatus(navigator.onLine ? "online" : "offline");
        }

        const handleOnline = () => setStatus("online");
        const handleOffline = () => setStatus("offline");

        window.addEventListener("online", handleOnline);
        window.addEventListener("offline", handleOffline);

        return () => {
            window.removeEventListener("online", handleOnline);
            window.removeEventListener("offline", handleOffline);
        };
    }, []);

    return status;
}
