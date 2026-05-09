// Single log entry card with expandable media grid
import React, { useState } from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import { ActivityLog } from '@/services/logs';
import MediaGrid from './MediaGrid';

interface Props {
  log: ActivityLog;
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr);
  return `${d.getFullYear()}.${String(d.getMonth() + 1).padStart(2, '0')}.${String(d.getDate()).padStart(2, '0')}`;
}

export default function LogCard({ log }: Props) {
  const [expanded, setExpanded] = useState(false);
  const hasMedia = log.media && log.media.length > 0;

  return (
    <View className="bg-white border border-gray-100 rounded-xl p-4 mb-3 shadow-sm">
      <View className="flex-row justify-between items-start">
        <Text className="text-xs text-gray-400">{formatDate(log.logged_at)}</Text>
        {hasMedia && (
          <TouchableOpacity onPress={() => setExpanded(!expanded)}>
            <Text className="text-xs text-blue-500">
              사진 {log.media.length}장 {expanded ? '▲' : '▼'}
            </Text>
          </TouchableOpacity>
        )}
      </View>
      {log.note ? (
        <Text className="mt-2 text-gray-700 text-sm leading-5">{log.note}</Text>
      ) : (
        <Text className="mt-2 text-gray-400 text-sm italic">노트 없음</Text>
      )}
      {expanded && hasMedia && <MediaGrid media={log.media} />}
    </View>
  );
}
