export interface Message {
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export interface TableRow {
  [key: string]: string | number | boolean | null;
}
