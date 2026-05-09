// 3-column grid of media thumbnails for activity log entries
import React from 'react';
import { View } from 'react-native';
import { MediaFile } from '@/services/logs';
import MediaPreviewItem from './MediaPreviewItem';

interface Props {
  media: MediaFile[];
  onDelete?: (mediaId: string) => void;
}

export default function MediaGrid({ media, onDelete }: Props) {
  if (!media.length) return null;

  return (
    <View className="flex-row flex-wrap gap-1 mt-2">
      {media.map((item) => (
        <View key={item.id} className="w-[31%]">
          <MediaPreviewItem
            media={item}
            onDelete={onDelete ? () => onDelete(item.id) : undefined}
          />
        </View>
      ))}
    </View>
  );
}
