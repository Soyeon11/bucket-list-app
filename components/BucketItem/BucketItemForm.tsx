// Form component for creating or editing a bucket list item
import React, { useState } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, Text, TouchableOpacity, View } from 'react-native';
import { CATEGORIES, PRIORITIES, CategoryId, Priority } from '@/constants/categories';
import { CreateItemPayload, UpdateItemPayload } from '@/services/bucketlist';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';

interface FormValues {
  title: string;
  category: CategoryId | '';
  priority: Priority;
  description: string;
  tags: string[];
}

interface FormErrors {
  title?: string;
  category?: string;
}

interface BucketItemFormProps {
  initialValues?: Partial<FormValues>;
  onSubmit: (payload: CreateItemPayload | UpdateItemPayload) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
  submitLabel?: string;
}

export function BucketItemForm({
  initialValues,
  onSubmit,
  onCancel,
  isLoading = false,
  submitLabel = '저장',
}: BucketItemFormProps) {
  const [values, setValues] = useState<FormValues>({
    title: initialValues?.title ?? '',
    category: initialValues?.category ?? '',
    priority: initialValues?.priority ?? 'medium',
    description: initialValues?.description ?? '',
    tags: initialValues?.tags ?? [],
  });
  const [errors, setErrors] = useState<FormErrors>({});
  const [tagInput, setTagInput] = useState('');

  // ─── Validation ─────────────────────────────────────────────────────────────
  function validate(): boolean {
    const newErrors: FormErrors = {};
    if (!values.title.trim()) {
      newErrors.title = '제목을 입력해주세요.';
    } else if (values.title.length > 100) {
      newErrors.title = '제목은 100자 이내로 입력해주세요.';
    }
    if (!values.category) {
      newErrors.category = '카테고리를 선택해주세요.';
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  // ─── Handlers ───────────────────────────────────────────────────────────────
  function handleAddTag() {
    const trimmed = tagInput.trim().toLowerCase();
    if (trimmed && !values.tags.includes(trimmed) && values.tags.length < 10) {
      setValues(v => ({ ...v, tags: [...v.tags, trimmed] }));
      setTagInput('');
    }
  }

  function handleRemoveTag(tag: string) {
    setValues(v => ({ ...v, tags: v.tags.filter(t => t !== tag) }));
  }

  async function handleSubmit() {
    if (!validate()) return;

    const payload: CreateItemPayload | UpdateItemPayload = {
      title: values.title.trim(),
      category: values.category as CategoryId,
      priority: values.priority,
      description: values.description.trim() || undefined,
      tags: values.tags.length > 0 ? values.tags : undefined,
    };

    await onSubmit(payload);
  }

  // ─── Render ─────────────────────────────────────────────────────────────────
  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      style={{ flex: 1 }}
    >
    <ScrollView
      className="flex-1 bg-surface"
      keyboardShouldPersistTaps="handled"
      contentContainerStyle={{ padding: 16, gap: 20 }}
    >
      {/* Title */}
      <Input
        label="제목 *"
        placeholder="버킷리스트 아이템 제목을 입력하세요"
        value={values.title}
        onChangeText={text => setValues(v => ({ ...v, title: text }))}
        error={errors.title}
        maxLength={100}
        returnKeyType="next"
      />

      {/* Category selector */}
      <View>
        <Text className="mb-2 text-sm font-medium text-gray-700">카테고리 *</Text>
        {errors.category && (
          <Text className="mb-1 text-xs text-red-500">{errors.category}</Text>
        )}
        <View className="flex-row flex-wrap gap-2">
          {CATEGORIES.map(cat => {
            const selected = values.category === cat.id;
            return (
              <TouchableOpacity
                key={cat.id}
                accessibilityLabel={`카테고리: ${cat.label}`}
                accessibilityRole="radio"
                accessibilityState={{ selected }}
                onPress={() => setValues(v => ({ ...v, category: cat.id }))}
                className={[
                  'flex-row items-center rounded-full px-3 py-2 border',
                  selected ? 'border-primary bg-primary-50' : 'border-gray-200 bg-white',
                ].join(' ')}
              >
                <Text className="mr-1 text-sm">{cat.emoji}</Text>
                <Text
                  className={`text-sm font-medium ${
                    selected ? 'text-primary' : 'text-gray-600'
                  }`}
                >
                  {cat.label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      {/* Priority selector */}
      <View>
        <Text className="mb-2 text-sm font-medium text-gray-700">우선순위</Text>
        <View className="flex-row gap-2">
          {PRIORITIES.map(p => {
            const selected = values.priority === p.id;
            return (
              <TouchableOpacity
                key={p.id}
                accessibilityLabel={`우선순위: ${p.label}`}
                accessibilityRole="radio"
                accessibilityState={{ selected }}
                onPress={() => setValues(v => ({ ...v, priority: p.id }))}
                className={[
                  'flex-1 items-center rounded-xl border py-3',
                  selected ? 'border-transparent' : 'border-gray-200 bg-white',
                ].join(' ')}
                style={selected ? { backgroundColor: `${p.color}20`, borderColor: p.color } : {}}
              >
                <Text
                  className={`text-sm font-semibold ${selected ? '' : 'text-gray-500'}`}
                  style={selected ? { color: p.color } : {}}
                >
                  {p.label}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>
      </View>

      {/* Description */}
      <Input
        label="설명"
        placeholder="버킷리스트 아이템에 대한 설명을 입력하세요 (선택)"
        value={values.description}
        onChangeText={text => setValues(v => ({ ...v, description: text }))}
        multiline
        numberOfLines={4}
        maxLength={500}
        textAlignVertical="top"
        className="min-h-[96px]"
        hint={`${values.description.length}/500자`}
      />

      {/* Tags */}
      <View>
        <Text className="mb-2 text-sm font-medium text-gray-700">태그</Text>
        {/* Tag chips */}
        {values.tags.length > 0 && (
          <View className="mb-2 flex-row flex-wrap gap-2">
            {values.tags.map(tag => (
              <TouchableOpacity
                key={tag}
                accessibilityLabel={`태그 제거: ${tag}`}
                onPress={() => handleRemoveTag(tag)}
                className="flex-row items-center rounded-full bg-gray-100 px-3 py-1"
              >
                <Text className="text-sm text-gray-700">#{tag}</Text>
                <Text className="ml-1 text-xs text-gray-400">✕</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}
        <View className="flex-row items-center gap-2">
          <View className="flex-1">
            <Input
              placeholder="태그 입력 후 추가 (최대 10개)"
              value={tagInput}
              onChangeText={setTagInput}
              onSubmitEditing={handleAddTag}
              returnKeyType="done"
              maxLength={20}
            />
          </View>
          <TouchableOpacity
            accessibilityLabel="태그 추가"
            onPress={handleAddTag}
            className="rounded-xl bg-gray-100 px-4 py-3"
          >
            <Text className="text-sm font-medium text-gray-600">추가</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Action buttons */}
      <View style={{ flexDirection: 'row', gap: 12, paddingTop: 8, paddingBottom: 32 }}>
        <View style={{ flex: 1 }}>
          <Button
            label="취소"
            variant="secondary"
            onPress={onCancel}
            fullWidth
            disabled={isLoading}
          />
        </View>
        <View style={{ flex: 1 }}>
          <Button
            label={submitLabel}
            variant="primary"
            onPress={handleSubmit}
            isLoading={isLoading}
            fullWidth
          />
        </View>
      </View>
    </ScrollView>
    </KeyboardAvoidingView>
  );
}
