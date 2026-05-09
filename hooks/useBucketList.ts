// TanStack Query hooks for bucket list CRUD with optimistic updates
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  getItems,
  getItem,
  createItem,
  updateItem,
  deleteItem,
  completeItem,
  BucketItem,
  CreateItemPayload,
  UpdateItemPayload,
  GetItemsParams,
} from '@/services/bucketlist';

// ─── Query keys ───────────────────────────────────────────────────────────────

export const bucketListKeys = {
  all: ['bucketList'] as const,
  lists: () => [...bucketListKeys.all, 'list'] as const,
  list: (params: GetItemsParams) => [...bucketListKeys.lists(), params] as const,
  details: () => [...bucketListKeys.all, 'detail'] as const,
  detail: (id: string) => [...bucketListKeys.details(), id] as const,
};

// ─── Read hooks ───────────────────────────────────────────────────────────────

/**
 * Fetch paginated bucket list items.
 * Cached for 5 minutes; stale after 1 minute.
 */
export function useBucketList(params: GetItemsParams = {}) {
  return useQuery({
    queryKey: bucketListKeys.list(params),
    queryFn: () => getItems(params),
    staleTime: 1000 * 60, // 1 minute
    gcTime: 1000 * 60 * 5, // 5 minutes
  });
}

/**
 * Fetch a single bucket list item by ID.
 */
export function useBucketItem(itemId: string) {
  return useQuery({
    queryKey: bucketListKeys.detail(itemId),
    queryFn: () => getItem(itemId),
    enabled: !!itemId,
    staleTime: 1000 * 60,
  });
}

// ─── Mutation hooks ───────────────────────────────────────────────────────────

/**
 * Create a new bucket list item.
 * Invalidates the list cache on success.
 */
export function useCreateBucketItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CreateItemPayload) => createItem(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: bucketListKeys.lists() });
    },
  });
}

/**
 * Update a bucket list item with optimistic UI update.
 */
export function useUpdateBucketItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ itemId, payload }: { itemId: string; payload: UpdateItemPayload }) =>
      updateItem(itemId, payload),

    // Optimistic update: immediately reflect changes in the detail cache
    onMutate: async ({ itemId, payload }) => {
      await queryClient.cancelQueries({ queryKey: bucketListKeys.detail(itemId) });
      const previousItem = queryClient.getQueryData<BucketItem>(bucketListKeys.detail(itemId));

      if (previousItem) {
        queryClient.setQueryData<BucketItem>(bucketListKeys.detail(itemId), {
          ...previousItem,
          ...payload,
          updated_at: new Date().toISOString(),
        });
      }

      return { previousItem };
    },

    onError: (_err, { itemId }, context) => {
      // Roll back on error
      if (context?.previousItem) {
        queryClient.setQueryData(bucketListKeys.detail(itemId), context.previousItem);
      }
    },

    onSettled: (_data, _err, { itemId }) => {
      queryClient.invalidateQueries({ queryKey: bucketListKeys.detail(itemId) });
      queryClient.invalidateQueries({ queryKey: bucketListKeys.lists() });
    },
  });
}

/**
 * Delete a bucket list item with optimistic removal from list cache.
 */
export function useDeleteBucketItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (itemId: string) => deleteItem(itemId),

    // Optimistic update: remove from all list caches immediately
    onMutate: async (itemId: string) => {
      await queryClient.cancelQueries({ queryKey: bucketListKeys.lists() });

      const previousLists = queryClient.getQueriesData<{ data: BucketItem[] }>({
        queryKey: bucketListKeys.lists(),
      });

      queryClient.setQueriesData<{ data: BucketItem[]; pagination: unknown }>(
        { queryKey: bucketListKeys.lists() },
        old => {
          if (!old) return old;
          return {
            ...old,
            data: old.data.filter(item => item.id !== itemId),
          };
        }
      );

      return { previousLists };
    },

    onError: (_err, _itemId, context) => {
      // Roll back on error
      if (context?.previousLists) {
        context.previousLists.forEach(([queryKey, data]) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
    },

    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: bucketListKeys.lists() });
    },
  });
}

/**
 * Mark a bucket list item as completed with optimistic update.
 */
export function useCompleteBucketItem() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (itemId: string) => completeItem(itemId),

    onMutate: async (itemId: string) => {
      await queryClient.cancelQueries({ queryKey: bucketListKeys.detail(itemId) });
      const previousItem = queryClient.getQueryData<BucketItem>(bucketListKeys.detail(itemId));

      if (previousItem) {
        queryClient.setQueryData<BucketItem>(bucketListKeys.detail(itemId), {
          ...previousItem,
          status: 'completed',
          completed_at: new Date().toISOString(),
        });
      }

      return { previousItem };
    },

    onError: (_err, itemId, context) => {
      if (context?.previousItem) {
        queryClient.setQueryData(bucketListKeys.detail(itemId), context.previousItem);
      }
    },

    onSettled: (_data, _err, itemId) => {
      queryClient.invalidateQueries({ queryKey: bucketListKeys.detail(itemId) });
      queryClient.invalidateQueries({ queryKey: bucketListKeys.lists() });
    },
  });
}
