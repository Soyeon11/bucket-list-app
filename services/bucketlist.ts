// Bucket list API functions mapping to API_SPEC.md endpoints
import api from './api';
import { CategoryId, Priority } from '@/constants/categories';

// ─── Types ────────────────────────────────────────────────────────────────────

export type ItemStatus = 'active' | 'completed' | 'all';

export interface BucketItem {
  id: string;
  title: string;
  category: CategoryId;
  priority: Priority;
  description: string | null;
  tags: string[];
  status: ItemStatus;
  logs_count?: number;
  last_recommended_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Pagination {
  page: number;
  limit: number;
  total: number;
  has_next: boolean;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: Pagination;
}

export interface GetItemsParams {
  category?: CategoryId;
  status?: ItemStatus;
  priority?: Priority;
  q?: string;
  page?: number;
  limit?: number;
}

export interface CreateItemPayload {
  title: string;
  category: CategoryId;
  priority?: Priority;
  description?: string;
  tags?: string[];
}

export interface UpdateItemPayload {
  title?: string;
  category?: CategoryId;
  priority?: Priority;
  description?: string;
  tags?: string[];
}

export interface CompleteItemResponse {
  id: string;
  status: 'completed';
  completed_at: string;
}

// ─── API functions ────────────────────────────────────────────────────────────

/**
 * GET /items — fetch paginated bucket list items with optional filters
 */
export async function getItems(params: GetItemsParams = {}): Promise<PaginatedResponse<BucketItem>> {
  const { data } = await api.get<PaginatedResponse<BucketItem>>('/items', { params });
  return data;
}

/**
 * POST /items — create a new bucket list item
 */
export async function createItem(payload: CreateItemPayload): Promise<BucketItem> {
  const { data } = await api.post<BucketItem>('/items', payload);
  return data;
}

/**
 * GET /items/{item_id} — fetch a single item by ID
 */
export async function getItem(itemId: string): Promise<BucketItem> {
  const { data } = await api.get<BucketItem>(`/items/${itemId}`);
  return data;
}

/**
 * PATCH /items/{item_id} — update an existing item (partial update)
 */
export async function updateItem(itemId: string, payload: UpdateItemPayload): Promise<BucketItem> {
  const { data } = await api.patch<BucketItem>(`/items/${itemId}`, payload);
  return data;
}

/**
 * DELETE /items/{item_id} — permanently delete an item
 */
export async function deleteItem(itemId: string): Promise<void> {
  await api.delete(`/items/${itemId}`);
}

/**
 * PATCH /items/{item_id}/complete — mark an item as completed
 */
export async function completeItem(itemId: string): Promise<CompleteItemResponse> {
  const { data } = await api.patch<CompleteItemResponse>(`/items/${itemId}/complete`);
  return data;
}
