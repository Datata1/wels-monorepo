export interface MatchMeta {
  match_id: string;
  file_name: string;
  video_path: string;
  fps: number;
  total_frames: number;
  date?: string;
  duration?: string;
}

export async function fetchMatches(): Promise<MatchMeta[]> {
  const res = await fetch(`${import.meta.env.VITE_BACKEND_URL || ''}/api/v1/matches`);
  if (!res.ok) throw new Error('Fehler beim Laden der Matches');
  return res.json();
}
