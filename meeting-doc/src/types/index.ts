export interface Meeting {
  id: string;
  title: string;
  description: string;
  date: string;
  duration_minutes: number;
  thumbnail_url: string;
  is_active: boolean;
  participant_count: number;
  action_item_count: number;
  created_at: string;
  updated_at: string;
}

export interface Transcript {
  id: string;
  meeting: string;
  text: string;
  speaker: string | null;
  timestamp: number;
  order: number;
}

export interface ActionItem {
  id: string;
  meeting: string;
  description: string;
  assignee: string | null;
  priority: string;
  status: string;
  due_date: string | null;
  created_at: string;
}

export interface Participant {
  id: string;
  meeting: string;
  name: string;
  email: string;
  role: string;
}

export interface AIResult {
  summary: string;
  action_items: Array<{
    description: string;
    assignee: string | null;
    priority: "high" | "medium" | "low";
    due_date: string | null;
  }>;
  key_decisions: string[];
  participants_detected: string[];
}

export interface KeyMoment {
  timestamp_seconds: number;
  label: string;
  description: string;
  confidence: "high" | "medium" | "low";
  frame_url: string | null;
  youtube_url: string;
}