/**
 * 对话框相关的通用Hooks
 * 提供ESC关闭、点击外部关闭等通用逻辑
 */

import { useEffect, useRef, useCallback, useState } from 'react';

/**
 * ESC键关闭Hook
 * 当对话框打开时，按ESC键触发关闭回调
 */
export function useEscapeClose(
  isOpen: boolean,
  onClose: () => void,
  enabled: boolean = true
) {
  useEffect(() => {
    if (!isOpen || !enabled) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose, enabled]);
}

/**
 * 点击外部关闭Hook
 * 当点击对话框外部区域时触发关闭回调
 */
export function useClickOutsideClose<T extends HTMLElement>(
  isOpen: boolean,
  onClose: () => void,
  enabled: boolean = true
) {
  const ref = useRef<T>(null);

  useEffect(() => {
    if (!isOpen || !enabled) return;

    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen, onClose, enabled]);

  return ref;
}

/**
 * 组合Hook：ESC和点击外部关闭
 * 同时支持两种关闭方式的对话框
 */
export function useDialogClose<T extends HTMLElement>(
  isOpen: boolean,
  onClose: () => void,
  options?: {
    escapeEnabled?: boolean;
    clickOutsideEnabled?: boolean;
  }
) {
  const { escapeEnabled = true, clickOutsideEnabled = true } = options || {};

  useEscapeClose(isOpen, onClose, escapeEnabled);
  const ref = useClickOutsideClose<T>(isOpen, onClose, clickOutsideEnabled);

  return ref;
}

/**
 * 防抖关闭Hook
 * 防止用户快速重复触发关闭
 */
export function useDebouncedClose(
  onClose: () => void,
  delay: number = 300
) {
  const closingRef = useRef(false);

  const debouncedClose = useCallback(() => {
    if (closingRef.current) return;

    closingRef.current = true;
    onClose();

    setTimeout(() => {
      closingRef.current = false;
    }, delay);
  }, [onClose, delay]);

  return debouncedClose;
}

/**
 * 抽屉动画状态Hook
 * 管理抽屉的打开/关闭动画状态
 */
export function useDrawerAnimation(
  isOpen: boolean,
  animationDuration: number = 300
) {
  const [isVisible, setIsVisible] = useState(isOpen);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setIsVisible(true);
      setIsAnimating(true);
      setTimeout(() => setIsAnimating(false), animationDuration);
    } else {
      setIsAnimating(true);
      setTimeout(() => {
        setIsVisible(false);
        setIsAnimating(false);
      }, animationDuration);
    }
  }, [isOpen, animationDuration]);

  return { isVisible, isAnimating };
}