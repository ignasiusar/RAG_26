export type Job = {
  id: string;
  title: string;
  company: string;
  location: string;
  mode: string; // Hybrid / On-site / Remote
  type?: string; // Full-time, dll
  salary?: string;
  experience?: string;
  match?: string; // alasan kenapa cocok
  requirements?: string[];
  sourceId: number;
  checkedAt: string;
};

export type Source = { id: number; title: string; url?: string };

export type Message = {
  id: string;
  role: "user" | "assistant";
  content: string;
  points?: string[];
  sources?: Source[];
  jobs?: Job[];
};

export type Chat = {
  id: string;
  title: string;
  createdAt: number;
  messages: Message[];
};
