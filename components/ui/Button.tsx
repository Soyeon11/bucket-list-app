// Reusable button component with NativeWind styling
import React from 'react';
import { ActivityIndicator, Pressable, Text, PressableProps } from 'react-native';

type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost';
type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends Omit<PressableProps, 'style'> {
  label: string;
  variant?: ButtonVariant;
  size?: ButtonSize;
  isLoading?: boolean;
  fullWidth?: boolean;
}

const variantClasses: Record<ButtonVariant, { container: string; text: string }> = {
  primary: {
    container: 'bg-primary active:bg-primary-600',
    text: 'text-white font-semibold',
  },
  secondary: {
    container: 'bg-primary-100 active:bg-primary-200',
    text: 'text-primary-700 font-semibold',
  },
  danger: {
    container: 'bg-red-500 active:bg-red-600',
    text: 'text-white font-semibold',
  },
  ghost: {
    container: 'bg-transparent active:bg-gray-100',
    text: 'text-primary font-semibold',
  },
};

const sizeClasses: Record<ButtonSize, { container: string; text: string }> = {
  sm: { container: 'px-3 py-2 rounded-lg', text: 'text-sm' },
  md: { container: 'px-5 py-3 rounded-xl', text: 'text-base' },
  lg: { container: 'px-6 py-4 rounded-2xl', text: 'text-lg' },
};

export function Button({
  label,
  variant = 'primary',
  size = 'md',
  isLoading = false,
  fullWidth = false,
  disabled,
  ...rest
}: ButtonProps) {
  const isDisabled = disabled || isLoading;
  const { container, text } = variantClasses[variant];
  const { container: sizeContainer, text: sizeText } = sizeClasses[size];

  return (
    <Pressable
      accessibilityLabel={label}
      accessibilityRole="button"
      disabled={isDisabled}
      className={[
        'flex-row items-center justify-center',
        container,
        sizeContainer,
        fullWidth ? 'w-full' : '',
        isDisabled ? 'opacity-50' : '',
      ]
        .filter(Boolean)
        .join(' ')}
      {...rest}
    >
      {isLoading && <ActivityIndicator size="small" color="white" className="mr-2" />}
      <Text className={`${text} ${sizeText}`}>{label}</Text>
    </Pressable>
  );
}
