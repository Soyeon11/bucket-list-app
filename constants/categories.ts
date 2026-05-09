// Bucket list category definitions matching PRD and API specification

export type CategoryId = 'travel' | 'food' | 'hobby' | 'fitness' | 'culture' | 'outdoor';

export interface Category {
  id: CategoryId;
  label: string;
  emoji: string;
  color: string;
}

export const CATEGORIES: Category[] = [
  {
    id: 'travel',
    label: '여행',
    emoji: '✈️',
    color: '#3B82F6', // Blue
  },
  {
    id: 'food',
    label: '음식',
    emoji: '🍽️',
    color: '#EF4444', // Red
  },
  {
    id: 'hobby',
    label: '취미',
    emoji: '🎨',
    color: '#8B5CF6', // Violet
  },
  {
    id: 'fitness',
    label: '피트니스',
    emoji: '💪',
    color: '#10B981', // Emerald
  },
  {
    id: 'culture',
    label: '문화',
    emoji: '🎭',
    color: '#F59E0B', // Amber
  },
  {
    id: 'outdoor',
    label: '아웃도어',
    emoji: '🏔️',
    color: '#6366F1', // Indigo
  },
];

export const CATEGORY_MAP: Record<CategoryId, Category> = CATEGORIES.reduce(
  (acc, cat) => ({ ...acc, [cat.id]: cat }),
  {} as Record<CategoryId, Category>
);

export type Priority = 'high' | 'medium' | 'low';

export interface PriorityOption {
  id: Priority;
  label: string;
  score: number;
  color: string;
}

export const PRIORITIES: PriorityOption[] = [
  { id: 'high', label: '높음', score: 40, color: '#EF4444' },
  { id: 'medium', label: '보통', score: 25, color: '#F59E0B' },
  { id: 'low', label: '낮음', score: 10, color: '#10B981' },
];

export const PRIORITY_MAP: Record<Priority, PriorityOption> = PRIORITIES.reduce(
  (acc, p) => ({ ...acc, [p.id]: p }),
  {} as Record<Priority, PriorityOption>
);
