import { Meeting, Transcript, ActionItem, Participant, KeyMoment } from "@/types";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

async function fetcher<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${url}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || error.error || `Request failed with status ${response.status}`);
  }

  return response.json();
}

export async function getMeetings(): Promise<Meeting[]> {
  return fetcher<Meeting[]>("/api/v1/meetings/");
}

export async function getMeeting(id: string): Promise<Meeting> {
  return fetcher<Meeting>(`/api/v1/meetings/${id}/`);
}

export async function createMeeting(data: Partial<Meeting>): Promise<Meeting> {
  return fetcher<Meeting>("/api/v1/meetings/", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getActionItems(meetingId: string): Promise<ActionItem[]> {
  return fetcher<ActionItem[]>(`/api/v1/action-items/?meeting=${meetingId}`);
}

export async function getTranscripts(meetingId: string): Promise<Transcript[]> {
  return fetcher<Transcript[]>(`/api/v1/transcripts/?meeting=${meetingId}`);
}

export async function getParticipants(meetingId: string): Promise<Participant[]> {
  return fetcher<Participant[]>(`/api/v1/participants/?meeting=${meetingId}`);
}

export async function fetchYoutubeTranscript(url: string): Promise<{
  transcript_text: string;
  video_id: string;
  word_count: number;
  transcript_timestamps: Array<{ text: string; start: number; duration: number }>;
}> {
  return fetcher("/api/v1/meetings/fetch-transcript/", {
    method: "POST",
    body: JSON.stringify({ youtube_url: url }),
  });
}

export async function processTranscript(transcriptText: string): Promise<{
  summary: string;
  action_items: Array<{
    description: string;
    assignee: string | null;
    priority: "high" | "medium" | "low";
    due_date: string | null;
  }>;
  key_decisions: string[];
  participants_detected: string[];
}> {
  return fetcher("/api/v1/meetings/process-transcript/", {
    method: "POST",
    body: JSON.stringify({ transcript_text: transcriptText }),
  });
}

export async function analyzeContext(
  videoId: string,
  transcriptTimestamps: Array<{ text: string; start: number; duration: number }>
): Promise<{ key_moments: KeyMoment[] }> {
  return fetcher("/api/v1/meetings/analyze-context/", {
    method: "POST",
    body: JSON.stringify({
      video_id: videoId,
      transcript_timestamps: transcriptTimestamps,
    }),
  });
}