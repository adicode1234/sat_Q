import { useId, useRef, useState } from "react";
import { IconCircleCheck, IconCloudUpload, IconX } from "@tabler/icons-react";
import { cn } from "@/lib/utils";

export type UploadedFile = { name: string; url: string; size: number };

type UploadSlotProps = {
  label: string;
  file: UploadedFile | null;
  onFile: (file: UploadedFile | null) => void;
};

export function UploadSlot({ label, file, onFile }: UploadSlotProps) {
  const inputId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  const accept = (list: FileList | null) => {
    const picked = list?.[0];
    if (!picked) return;
    onFile({ name: picked.name, url: URL.createObjectURL(picked), size: picked.size });
  };

  return (
    <div>
      <p className="label-eyebrow mb-2">{label}</p>
      <label
        htmlFor={inputId}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          accept(e.dataTransfer.files);
        }}
        className={cn(
          "group relative flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border border-dashed border-border bg-panel-elevated/40 px-4 py-6 text-center transition-all duration-300 hover:border-mint/60 hover:bg-panel-elevated",
          dragging && "border-mint bg-mint/5",
          file && "border-mint/50",
        )}
      >
        {file ? (
          <div className="flex w-full items-center gap-3 text-left">
            <img
              src={file.url}
              alt={`Preview of ${file.name}`}
              className="h-12 w-12 shrink-0 rounded-lg border border-border object-cover"
            />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-foreground">{file.name}</p>
              <p className="flex items-center gap-1 text-xs text-mint">
                <IconCircleCheck size={14} stroke={1.75} />
                Uploaded · {(file.size / 1024).toFixed(0)} KB
              </p>
            </div>
            <button
              type="button"
              aria-label={`Remove ${file.name}`}
              onClick={(e) => {
                e.preventDefault();
                URL.revokeObjectURL(file.url);
                onFile(null);
                if (inputRef.current) inputRef.current.value = "";
              }}
              className="rounded-md p-1 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
            >
              <IconX size={16} stroke={1.75} />
            </button>
          </div>
        ) : (
          <>
            <IconCloudUpload
              size={26}
              stroke={1.5}
              className="text-muted-foreground transition-colors group-hover:text-mint"
            />
            <span className="text-sm text-foreground">Drop file or browse</span>
            <span className="text-xs text-muted-foreground">GeoTIFF, TIFF, PNG, JPG</span>
          </>
        )}
        <input
          id={inputId}
          ref={inputRef}
          type="file"
          accept="image/*,.tif,.tiff"
          className="sr-only"
          onChange={(e) => accept(e.target.files)}
        />
      </label>
    </div>
  );
}
