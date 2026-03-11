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
    if (!file) return;

    const text = await file.text();
    const raw = JSON.parse(text) as unknown;
    const parsed: DatasetLoadRequest = Array.isArray(raw)
      ? { scenarios: raw }
      : (raw as DatasetLoadRequest);

    await onDatasetParsed(parsed);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <section className="uploader-card">
      <p className="eyebrow">Caricamento scenari</p>
      <p className="uploader-text">Seleziona il file JSON: il frontend lo invia e prepara subito la simulazione.</p>
      <label className="upload-button" htmlFor="dataset-file-input">
        Carica file JSON
      </label>
      <input
        id="dataset-file-input"
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
