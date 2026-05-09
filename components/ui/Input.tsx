// Reusable text input component with NativeWind styling
import React, { forwardRef } from 'react';
import { Text, TextInput, TextInputProps, View } from 'react-native';

interface InputProps extends TextInputProps {
  label?: string;
  error?: string;
  hint?: string;
}

export const Input = forwardRef<TextInput, InputProps>(
  ({ label, error, hint, ...rest }, ref) => {
    return (
      <View className="w-full">
        {label && (
          <Text className="mb-1 text-sm font-medium text-gray-700">{label}</Text>
        )}
        <TextInput
          ref={ref}
          accessibilityLabel={label}
          className={[
            'w-full rounded-xl border px-4 py-3 text-base text-gray-900 bg-white',
            error ? 'border-red-400' : 'border-gray-300',
            'focus:border-primary',
          ].join(' ')}
          placeholderTextColor="#9CA3AF"
          {...rest}
        />
        {error ? (
          <Text className="mt-1 text-xs text-red-500">{error}</Text>
        ) : hint ? (
          <Text className="mt-1 text-xs text-gray-400">{hint}</Text>
        ) : null}
      </View>
    );
  }
);

Input.displayName = 'Input';
