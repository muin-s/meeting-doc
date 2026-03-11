import { Meeting, Transcript, ActionItem, Participant } from "@/types";

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
}> {
  return fetcher<{
    transcript_text: string;
    video_id: string;
    word_count: number;
  }>("/api/v1/meetings/fetch-transcript/", {
    method: "POST",
    body: JSON.stringify({ youtube_url: url }),
  });
}
