import { FileType } from '../../types/file';
import { getFileIconConfig } from '../../utils/fileIcons';

interface FileIconProps {
  type: FileType;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

const sizeClasses = {
  sm: 'w-4 h-4 text-sm',
  md: 'w-6 h-6 text-2xl',
  lg: 'w-12 h-12 text-4xl',
};

/**
 * 文件图标组件
 * 根据文件类型渲染对应的图标
 */
export function FileIcon({ type, size = 'md', className = '' }: FileIconProps) {
  const config = getFileIconConfig(type);
  const sizeClass = sizeClasses[size];

  return (
    <span
      className={`${sizeClass} flex items-center justify-center ${className}`}
      style={{ color: config.color }}
      role="img"
      aria-label={`${type} file`}
    >
      {config.icon}
    </span>
  );
}