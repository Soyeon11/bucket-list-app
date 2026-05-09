// Recommendation history screen with paginated FlatList
import React, { useState } from 'react';
import {
  ActivityIndicator,
  FlatList,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { useRecommendationHistory } from '@/hooks/useRecommendation';
import { HistoryItem } from '@/components/Recommendation/HistoryItem';
import { RecommendationHistoryItem } from '@/services/recommendations';

export default function RecommendationHistoryScreen() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useRecommendationHistory(page);

  // Accumulate items across pages
  const [allItems, setAllItems] = React.useState<RecommendationHistoryItem[]>([]);

  React.useEffect(() => {
    if (data?.data) {
      if (page === 1) {
        setAllItems(data.data);
      } else {
        setAllItems(prev => [...prev, ...data.data]);
      }
    }
  }, [data, page]);

  function handleLoadMore() {
    if (data?.pagination.has_next) {
      setPage(prev => prev + 1);
    }
  }

  function handleItemPress(item: RecommendationHistoryItem) {
    // Item detail navigation is a Phase 1 feature
    console.log('History item pressed:', item.id);
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity onPress={() => router.back()} style={styles.backButton} activeOpacity={0.7}>
          <Text style={styles.backText}>← 뒤로</Text>
        </TouchableOpacity>
        <Text style={styles.headerTitle}>추천 기록</Text>
        <View style={styles.headerRight} />
      </View>

      {/* Loading state for initial load */}
      {isLoading && page === 1 ? (
        <View style={styles.centered}>
          <ActivityIndicator size="large" color="#6366F1" />
        </View>
      ) : allItems.length === 0 ? (
        // Empty state
        <View style={styles.centered}>
          <Text style={styles.emptyEmoji}>📭</Text>
          <Text style={styles.emptyTitle}>아직 추천 기록이 없어요</Text>
          <Text style={styles.emptySubtitle}>
            이번 주 추천을 수락하거나 건너뛰면 여기에 기록돼요
          </Text>
        </View>
      ) : (
        <FlatList
          data={allItems}
          keyExtractor={item => item.id}
          contentContainerStyle={styles.listContent}
          ItemSeparatorComponent={() => <View style={styles.separator} />}
          renderItem={({ item }) => (
            <HistoryItem item={item} onPress={() => handleItemPress(item)} />
          )}
          ListFooterComponent={
            data?.pagination.has_next ? (
              <TouchableOpacity
                style={styles.loadMoreButton}
                onPress={handleLoadMore}
                activeOpacity={0.8}
                disabled={isLoading}
              >
                {isLoading ? (
                  <ActivityIndicator size="small" color="#6366F1" />
                ) : (
                  <Text style={styles.loadMoreText}>더 보기</Text>
                )}
              </TouchableOpacity>
            ) : null
          }
        />
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#F3F4F6',
    backgroundColor: '#FFFFFF',
  },
  backButton: {
    paddingVertical: 4,
    paddingRight: 8,
  },
  backText: {
    fontSize: 15,
    color: '#6366F1',
    fontWeight: '600',
  },
  headerTitle: {
    fontSize: 17,
    fontWeight: '700',
    color: '#111827',
  },
  headerRight: {
    width: 48, // balance the back button width
  },
  centered: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingHorizontal: 32,
  },
  emptyEmoji: {
    fontSize: 48,
    marginBottom: 8,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
  },
  emptySubtitle: {
    fontSize: 14,
    color: '#6B7280',
    textAlign: 'center',
    lineHeight: 20,
  },
  listContent: {
    padding: 16,
    gap: 0,
  },
  separator: {
    height: 10,
  },
  loadMoreButton: {
    marginTop: 16,
    backgroundColor: '#FFFFFF',
    borderRadius: 14,
    paddingVertical: 14,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  loadMoreText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#6366F1',
  },
});
