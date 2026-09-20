import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";
import { cn } from "@/lib/utils";

export function useFinePointer() {
  const [fine, setFine] = useState(false);
  useEffect(() => {
    const mq = window.matchMedia("(hover: hover) and (pointer: fine)");
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)");
    const update = () => setFine(mq.matches && !reduced.matches);
    update();
    mq.addEventListener("change", update);
    reduced.addEventListener("change", update);
    return () => {
      mq.removeEventListener("change", update);
      reduced.removeEventListener("change", update);
    };
  }, []);
  return fine;
}

type TiltCardProps = {
  children: ReactNode;
  className?: string;
  intensity?: number;
  lift?: number;
};

export function TiltCard({ children, className, intensity = 8, lift = 6 }: TiltCardProps) {
  const ref = useRef<HTMLDivElement>(null);
  const enabled = useFinePointer();

  const handleMove = useCallback(
    (event: React.MouseEvent<HTMLDivElement>) => {
      const node = ref.current;
      if (!node || !enabled) return;
      const rect = node.getBoundingClientRect();
      const px = (event.clientX - rect.left) / rect.width - 0.5;
      const py = (event.clientY - rect.top) / rect.height - 0.5;
      node.style.transform = `rotateX(${(-py * intensity).toFixed(2)}deg) rotateY(${(px * intensity).toFixed(2)}deg) translateZ(${lift}px)`;
    },
    [enabled, intensity, lift],
  );

  const handleLeave = useCallback(() => {
    const node = ref.current;
    if (!node) return;
    node.style.transform = "rotateX(0deg) rotateY(0deg) translateZ(0px)";
  }, []);

  return (
    <div className="tilt-scene">
      <div
        ref={ref}
        onMouseMove={handleMove}
        onMouseLeave={handleLeave}
        className={cn(
          "tilt-surface rounded-2xl border border-border bg-card p-5 shadow-[0_18px_50px_-30px_rgba(0,0,0,0.9)]",
          className,
        )}
      >
        {children}
      </div>
    </div>
  );
}
