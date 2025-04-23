export interface Dataset {
  id: string;
  filename: string;
  upload_time: string; // ISO 8601 date string
  columns: string[];
  row_count: number;
}

export interface DatasetsResponse {
  datasets: Dataset[];
}
