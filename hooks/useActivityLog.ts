// TanStack Query hooks for activity log data fetching and mutations
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  getLogs,
  getLog,
  createLog,
  deleteLog,
  getUploadUrls,
  uploadFileToStorage,
  ActivityLogCreate,
  UploadFileSpec,
} from '@/services/logs';

// ─── Query keys ───────────────────────────────────────────────────────────────

export const logKeys = {
  all: ['logs'] as const,
  list: (itemId: string) => [...logKeys.all, 'list', itemId] as const,
  detail: (logId: string) => [...logKeys.all, 'detail', logId] as const,
};

// ─── Read hooks ───────────────────────────────────────────────────────────────

/**
 * Fetch paginated activity logs for a given bucket list item.
 */
export function useActivityLogs(itemId: string, page = 1) {
  return useQuery({
    queryKey: logKeys.list(itemId),
    queryFn: () => getLogs(itemId, page),
    enabled: !!itemId,
  });
}

/**
 * Fetch a single activity log by item ID and log ID.
 */
export function useActivityLog(itemId: string, logId: string) {
  return useQuery({
    queryKey: logKeys.detail(logId),
    queryFn: () => getLog(itemId, logId),
    enabled: !!itemId && !!logId,
  });
}

// ─── Mutation hooks ───────────────────────────────────────────────────────────

interface CreateLogInput {
  itemId: string;
  payload: ActivityLogCreate;
  mediaFiles?: Array<{
    uri: string;
    filename: string;
    mimeType: string;
    fileSize: number;
  }>;
}

/**
 * Create an activity log entry, then optionally upload media files via signed URLs.
 * Invalidates the log list and the parent bucket item detail on success.
 */
export function useCreateLog() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ itemId, payload, mediaFiles }: CreateLogInput) => {
      const log = await createLog(itemId, payload);

      if (mediaFiles && mediaFiles.length > 0) {
        const fileSpecs: UploadFileSpec[] = mediaFiles.map((f, idx) => ({
          filename: f.filename,
          mime_type: f.mimeType,
          size_bytes: f.fileSize,
          order: idx + 1,
        }));

        const signedUrls = await getUploadUrls(itemId, log.id, fileSpecs);

        await Promise.all(
          signedUrls.map((urlInfo, idx) =>
            uploadFileToStorage(urlInfo.signed_url, mediaFiles[idx].uri, mediaFiles[idx].mimeType)
          )
        );
      }

      return log;
    },
    onSuccess: (_data, { itemId }) => {
      queryClient.invalidateQueries({ queryKey: logKeys.list(itemId) });
      queryClient.invalidateQueries({ queryKey: ['bucket-items', 'detail', itemId] });
    },
  });
}

/**
 * Delete an activity log entry.
 * Invalidates the log list and the parent bucket item detail on success.
 */
export function useDeleteLog() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ itemId, logId }: { itemId: string; logId: string }) =>
      deleteLog(itemId, logId),
    onSuccess: (_data, { itemId }) => {
      queryClient.invalidateQueries({ queryKey: logKeys.list(itemId) });
      queryClient.invalidateQueries({ queryKey: ['bucket-items', 'detail', itemId] });
    },
  });
}
