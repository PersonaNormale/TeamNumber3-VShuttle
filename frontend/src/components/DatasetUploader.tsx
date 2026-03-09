import { useRef, type ChangeEvent } from "react";
import type { DatasetLoadRequest } from "../types";

type DatasetUploaderProps = {
  onDatasetParsed: (dataset: DatasetLoadRequest) => Promise<void>;
  loading: boolean;
};

export function DatasetUploader({ onDatasetParsed, loading }: DatasetUploaderProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const normalizeDataset = (raw: unknown): DatasetLoadRequest => {
    if (Array.isArray(raw)) {
      return { scenarios: raw as DatasetLoadRequest["scenarios"] };
    }

    if (
      typeof raw === "object" &&
      raw !== null &&
      "scenarios" in raw &&
      Array.isArray((raw as { scenarios: unknown }).scenarios)
    ) {
      return raw as DatasetLoadRequest;
    }

    throw new Error(
      "Formato dataset non valido: usa un array di scenari o un oggetto con chiave 'scenarios'."
    );
  };

  const handleFileChange = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    const text = await file.text();
    const parsed = normalizeDataset(JSON.parse(text));
    await onDatasetParsed(parsed);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <section className="panel">
      <h2>Upload Dataset</h2>
      <p>Carica un file JSON con array scenari oppure con shape {'{ "scenarios": [...] }'}.</p>
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
