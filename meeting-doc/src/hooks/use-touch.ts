import { useState, useCallback } from "react";

interface TouchState {
    isTouching: boolean;
    startX: number;
    startY: number;
    currentX: number;
    currentY: number;
    deltaX: number;
    deltaY: number;
    direction: "left" | "right" | "up" | "down" | null;
}

export function useTouch() {
    const [touchState, setTouchState] = useState<TouchState>({
        isTouching: false,
        startX: 0,
        startY: 0,
        currentX: 0,
        currentY: 0,
        deltaX: 0,
        deltaY: 0,
        direction: null,
    });

    const onTouchStart = useCallback((e: React.TouchEvent) => {
        const { clientX, clientY } = e.touches[0];
        setTouchState({
            isTouching: true,
            startX: clientX,
            startY: clientY,
            currentX: clientX,
            currentY: clientY,
            deltaX: 0,
            deltaY: 0,
            direction: null,
        });
    }, []);

    const onTouchMove = useCallback(
        (e: React.TouchEvent) => {
            if (!touchState.isTouching) return;

            const { clientX, clientY } = e.touches[0];
            const deltaX = clientX - touchState.startX;
            const deltaY = clientY - touchState.startY;

            let direction: TouchState["direction"] = null;
            if (Math.abs(deltaX) > Math.abs(deltaY)) {
                direction = deltaX > 0 ? "right" : "left";
            } else {
                direction = deltaY > 0 ? "down" : "up";
            }

            setTouchState((prev) => ({
                ...prev,
                currentX: clientX,
                currentY: clientY,
                deltaX,
                deltaY,
                direction,
            }));
        },
        [touchState.isTouching, touchState.startX, touchState.startY],
    );

    const onTouchEnd = useCallback(() => {
        setTouchState((prev) => ({
            ...prev,
            isTouching: false,
        }));
    }, []);

    return {
        ...touchState,
        handlers: {
            onTouchStart,
            onTouchMove,
            onTouchEnd,
        },
    };
}
