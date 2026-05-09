// Single media thumbnail component for activity log entries
import React from 'react';
import { Image, TouchableOpacity, View, Text } from 'react-native';
import { MediaFile } from '@/services/logs';

interface Props {
  media: MediaFile;
  onDelete?: () => void;
}

export default function MediaPreviewItem({ media, onDelete }: Props) {
  const isVideo = media.type === 'video';

  return (
    <View className="relative w-full aspect-square bg-gray-200 rounded-lg overflow-hidden">
      {media.signed_url ? (
        <Image
          source={{ uri: media.signed_url }}
          className="w-full h-full"
          resizeMode="cover"
        />
      ) : (
        <View className="w-full h-full items-center justify-center">
          <Text className="text-gray-400 text-xs">
            {media.upload_status === 'pending' ? '업로드 중...' : '미디어'}
          </Text>
        </View>
      )}
      {isVideo && (
        <View className="absolute bottom-1 left-1 bg-black/50 rounded px-1">
          <Text className="text-white text-xs">▶</Text>
        </View>
      )}
      {onDelete && (
        <TouchableOpacity
          onPress={onDelete}
          className="absolute top-1 right-1 bg-black/60 rounded-full w-5 h-5 items-center justify-center"
        >
          <Text className="text-white text-xs">✕</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}
