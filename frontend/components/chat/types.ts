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
  [key: string]: string | number;
}
