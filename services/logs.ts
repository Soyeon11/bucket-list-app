// Activity log API functions mapping to API_SPEC.md /items/{item_id}/logs endpoints
import apiClient from './api';

// ─── Types ────────────────────────────────────────────────────────────────────

export interface MediaFile {
  id: string;
  type: 'image' | 'video';
  storage_path: string;
  mime_type?: string;
  size_bytes?: number;
  order: number;
  upload_status: 'pending' | 'uploaded' | 'failed';
  signed_url?: string;
}

export interface ActivityLog {
  id: string;
  item_id: string;
  user_id: string;
  note?: string | null;
  logged_at: string;
  created_at: string;
  media: MediaFile[];
}

export interface ActivityLogCreate {
  note?: string | null;
  logged_at?: string;
}

export interface UploadFileSpec {
  filename: string;
  mime_type: string;
  size_bytes: number;
  order: number;
}

export interface SignedUploadUrl {
  storage_path: string;
  signed_url: string;
  order: number;
  filename: string;
}

export interface PaginatedLogsResponse {
  data: ActivityLog[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    has_next: boolean;
  };
}

// ─── API functions ────────────────────────────────────────────────────────────

/**
 * GET /items/{item_id}/logs — fetch paginated activity logs for an item
 */
export async function getLogs(
  itemId: string,
  page = 1,
  limit = 20
): Promise<PaginatedLogsResponse> {
  const { data } = await apiClient.get(`/items/${itemId}/logs`, {
    params: { page, limit },
  });
  return data;
}

/**
 * POST /items/{item_id}/logs — create a new activity log entry
 */
export async function createLog(
  itemId: string,
  payload: ActivityLogCreate
): Promise<ActivityLog> {
  const { data } = await apiClient.post(`/items/${itemId}/logs`, payload);
  return data;
}

/**
 * GET /items/{item_id}/logs/{log_id} — fetch a single activity log by ID
 */
export async function getLog(itemId: string, logId: string): Promise<ActivityLog> {
  const { data } = await apiClient.get(`/items/${itemId}/logs/${logId}`);
  return data;
}

/**
 * DELETE /items/{item_id}/logs/{log_id} — permanently delete an activity log
 */
export async function deleteLog(itemId: string, logId: string): Promise<void> {
  await apiClient.delete(`/items/${itemId}/logs/${logId}`);
}

/**
 * POST /items/{item_id}/logs/{log_id}/upload-urls — request signed upload URLs for media files
 */
export async function getUploadUrls(
  itemId: string,
  logId: string,
  files: UploadFileSpec[]
): Promise<SignedUploadUrl[]> {
  const { data } = await apiClient.post(
    `/items/${itemId}/logs/${logId}/upload-urls`,
    { files }
  );
  return data.urls;
}

/**
 * Upload a local file directly to Supabase Storage using a pre-signed PUT URL.
 * Uses native fetch so this works in both React Native and web environments.
 */
export async function uploadFileToStorage(
  signedUrl: string,
  fileUri: string,
  mimeType: string
): Promise<void> {
  // Fetch the file as a blob and PUT directly to Supabase Storage signed URL
  const response = await fetch(fileUri);
  const blob = await response.blob();
  const uploadRes = await fetch(signedUrl, {
    method: 'PUT',
    headers: { 'Content-Type': mimeType },
    body: blob,
  });
  if (!uploadRes.ok) {
    throw new Error(`Storage upload failed: ${uploadRes.status}`);
  }
}
