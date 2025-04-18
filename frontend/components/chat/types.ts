export interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  file?: {
    name: string;
    type: string;
    size: number;
  } | null;
}

export interface TableRow {
  [key: string]: any;
}

export interface DatasetInfo {
  id: string;
  filename: string;
  upload_time: string;
  columns: string[];
  row_count: number;
}

export interface AnalysisResult {
  type: string;
  data: any;
  visualization?: {
    type: string;
    data: any[];
    x: string;
    y: string;
    title: string;
    xLabel: string;
    yLabel: string;
  };
  metrics?: {
    mse?: number;
    r2?: number;
  };
  [key: string]: any;
}

export interface ChatHistory {
  role: string;
  content: string;
}
