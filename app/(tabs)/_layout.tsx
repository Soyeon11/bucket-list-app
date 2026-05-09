// Bottom tab navigation layout: 홈, 버킷리스트, 기록, 갤러리
import { Redirect, Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useUserStore } from '@/store/userStore';

type IoniconsName = React.ComponentProps<typeof Ionicons>['name'];

interface TabIconProps {
  name: IoniconsName;
  color: string;
  size: number;
  focused: boolean;
}

function TabIcon({ name, color, size }: TabIconProps) {
  return <Ionicons name={name} size={size} color={color} />;
}

export default function TabsLayout() {
  const { session, isLoading } = useUserStore();

  if (isLoading) return null;

  // Not authenticated → redirect to login
  if (!session) return <Redirect href="/(auth)/login" />;

  return (
    <Tabs
      screenOptions={{
        tabBarActiveTintColor: '#6366F1',
        tabBarInactiveTintColor: '#9CA3AF',
        tabBarStyle: {
          backgroundColor: '#FFFFFF',
          borderTopColor: '#F3F4F6',
          paddingBottom: 4,
        },
        headerShown: false,
      }}
    >
      <Tabs.Screen
        name="index"
        options={{
          title: '홈',
          tabBarIcon: props => <TabIcon name={props.focused ? 'home' : 'home-outline'} {...props} />,
        }}
      />
      <Tabs.Screen
        name="bucketlist"
        options={{
          title: '버킷리스트',
          tabBarIcon: props => (
            <TabIcon name={props.focused ? 'list' : 'list-outline'} {...props} />
          ),
        }}
      />
      <Tabs.Screen
        name="record"
        options={{
          title: '기록',
          tabBarIcon: props => (
            <TabIcon name={props.focused ? 'camera' : 'camera-outline'} {...props} />
          ),
        }}
      />
      <Tabs.Screen
        name="gallery"
        options={{
          title: '갤러리',
          tabBarIcon: props => (
            <TabIcon name={props.focused ? 'images' : 'images-outline'} {...props} />
          ),
        }}
      />
    </Tabs>
  );
}
