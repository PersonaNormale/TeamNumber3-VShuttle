import { useRef, type ChangeEvent } from "react";
import type { DatasetLoadRequest } from "../types";

type DatasetUploaderProps = {
  onDatasetParsed: (dataset: DatasetLoadRequest) => Promise<void>;
  loading: boolean;
};

export function DatasetUploader({ onDatasetParsed, loading }: DatasetUploaderProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    const text = await file.text();
    const raw = JSON.parse(text) as unknown;
    const parsed: DatasetLoadRequest = Array.isArray(raw)
          ? { scenarios: raw }
          : raw as DatasetLoadRequest;
    await onDatasetParsed(parsed);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <section className="panel">
      <h2>Upload Dataset</h2>
      <p>Carica un file JSON con array scenarios.</p>
      <input
        ref={fileInputRef}
        disabled={loading}
        type="file"
        accept="application/json"
        onChange={(event) => {
          void handleFileChange(event);
        }}
      />
    </section>
  );
}
