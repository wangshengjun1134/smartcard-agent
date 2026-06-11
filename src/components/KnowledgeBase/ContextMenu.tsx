import { useEffect, useRef, useState } from 'react';

export interface ContextMenuItem {
  id: string;
  label: string;
  icon?: string;
  danger?: boolean;
  disabled?: boolean;
  divider?: boolean;
}

interface ContextMenuProps {
  items: ContextMenuItem[];
  position: { x: number; y: number };
  onSelect: (id: string) => void;
  onClose: () => void;
}

/**
 * 通用右键菜单组件
 */
export function ContextMenu({ items, position, onSelect, onClose }: ContextMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);
  const [adjustedPosition, setAdjustedPosition] = useState(position);

  // 点击外部关闭菜单
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    };

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [onClose]);

  // 调整菜单位置，防止超出屏幕
  useEffect(() => {
    if (menuRef.current) {
      const rect = menuRef.current.getBoundingClientRect();
      const viewportWidth = window.innerWidth;
      const viewportHeight = window.innerHeight;

      let x = position.x;
      let y = position.y;

      if (x + rect.width > viewportWidth) {
        x = viewportWidth - rect.width - 8;
      }
      if (y + rect.height > viewportHeight) {
        y = viewportHeight - rect.height - 8;
      }

      setAdjustedPosition({ x, y });
    }
  }, [position]);

  return (
    <div
      ref={menuRef}
      className="context-menu"
      style={{
        position: 'fixed',
        left: adjustedPosition.x,
        top: adjustedPosition.y,
        zIndex: 1000,
      }}
    >
      {items.map((item, index) => {
        if (item.divider) {
          return <div key={`divider-${index}`} className="context-menu-divider" />;
        }

        return (
          <div
            key={item.id}
            className={`context-menu-item ${item.danger ? 'danger' : ''} ${item.disabled ? 'disabled' : ''}`}
            onClick={() => {
              if (!item.disabled) {
                onSelect(item.id);
                onClose();
              }
            }}
            role="menuitem"
            aria-disabled={item.disabled}
          >
            {item.icon && (
              <span className="context-menu-icon">
                <i className={item.icon} />
              </span>
            )}
            <span className="context-menu-label">{item.label}</span>
          </div>
        );
      })}
    </div>
  );
}