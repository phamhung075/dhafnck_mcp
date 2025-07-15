/**
 * Accessibility Utilities and Components
 * Provides WCAG 2.1 AA compliance features, keyboard navigation, and screen reader support
 */

import React, { useState, useEffect, useRef, createContext, useContext, ReactNode, useCallback, useMemo } from 'react';

// ==================
// ACCESSIBILITY TYPES
// ==================

export interface AccessibilityPreferences {
  reducedMotion: boolean;
  highContrast: boolean;
  fontSize: 'small' | 'medium' | 'large' | 'extra-large';
  focusVisible: boolean;
  screenReaderOptimized: boolean;
}

export interface KeyboardNavigation {
  focusedElement: HTMLElement | null;
  focusHistory: HTMLElement[];
  trapFocus: boolean;
  skipLinks: boolean;
}

export interface AriaLiveRegion {
  id: string;
  level: 'polite' | 'assertive' | 'off';
  message: string;
  timestamp: number;
}

// ==================
// ACCESSIBILITY CONTEXT
// ==================

interface AccessibilityContextType {
  preferences: AccessibilityPreferences;
  updatePreferences: (preferences: Partial<AccessibilityPreferences>) => void;
  announceToScreenReader: (message: string, level?: 'polite' | 'assertive') => void;
  keyboardNavigation: KeyboardNavigation;
  focusElement: (element: HTMLElement | null) => void;
  trapFocus: (container: HTMLElement) => () => void;
}

const AccessibilityContext = createContext<AccessibilityContextType | null>(null);

// ==================
// ACCESSIBILITY PROVIDER
// ==================

export function AccessibilityProvider({ children }: { children: ReactNode }) {
  const [preferences, setPreferences] = useState<AccessibilityPreferences>({
    reducedMotion: window.matchMedia('(prefers-reduced-motion: reduce)').matches,
    highContrast: window.matchMedia('(prefers-contrast: high)').matches,
    fontSize: 'medium',
    focusVisible: true,
    screenReaderOptimized: false
  });

  const [keyboardNavigation, setKeyboardNavigation] = useState<KeyboardNavigation>({
    focusedElement: null,
    focusHistory: [],
    trapFocus: false,
    skipLinks: true
  });

  const [liveRegions, setLiveRegions] = useState<AriaLiveRegion[]>([]);
  const liveRegionRef = useRef<HTMLDivElement>(null);

  // Load preferences from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('accessibility-preferences');
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        setPreferences(prev => ({ ...prev, ...parsed }));
      } catch (e) {
        console.warn('Failed to parse accessibility preferences');
      }
    }
  }, []);

  // Save preferences to localStorage
  useEffect(() => {
    localStorage.setItem('accessibility-preferences', JSON.stringify(preferences));
    applyAccessibilityPreferences(preferences);
  }, [preferences]);

  // Update preferences
  const updatePreferences = (newPreferences: Partial<AccessibilityPreferences>) => {
    setPreferences(prev => ({ ...prev, ...newPreferences }));
  };

  // Announce to screen reader
  const announceToScreenReader = useCallback((message: string, level: 'polite' | 'assertive' = 'polite') => {
    const id = `live-region-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const newRegion: AriaLiveRegion = {
      id,
      level,
      message,
      timestamp: Date.now()
    };

    setLiveRegions(prev => [...prev, newRegion]);

    // Clean up old messages
    setTimeout(() => {
      setLiveRegions(prev => prev.filter(region => region.id !== id));
    }, 5000);
  }, []);

  // Focus management
  const focusElement = (element: HTMLElement | null) => {
    if (element) {
      element.focus();
      setKeyboardNavigation(prev => ({
        ...prev,
        focusedElement: element,
        focusHistory: [...prev.focusHistory.slice(-9), element] // Keep last 10
      }));
    }
  };

  // Focus trap
  const trapFocus = (container: HTMLElement) => {
    const focusableElements = getFocusableElements(container);
    if (focusableElements.length === 0) return () => {};

    const firstElement = focusableElements[0];
    const lastElement = focusableElements[focusableElements.length - 1];

    const handleTabKey = (e: KeyboardEvent) => {
      if (e.key !== 'Tab') return;

      if (e.shiftKey) {
        if (document.activeElement === firstElement) {
          e.preventDefault();
          lastElement.focus();
        }
      } else {
        if (document.activeElement === lastElement) {
          e.preventDefault();
          firstElement.focus();
        }
      }
    };

    const handleEscapeKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        const lastFocused = keyboardNavigation.focusHistory[keyboardNavigation.focusHistory.length - 2];
        if (lastFocused) {
          lastFocused.focus();
        }
      }
    };

    container.addEventListener('keydown', handleTabKey);
    container.addEventListener('keydown', handleEscapeKey);
    firstElement.focus();

    return () => {
      container.removeEventListener('keydown', handleTabKey);
      container.removeEventListener('keydown', handleEscapeKey);
    };
  };

  const contextValue: AccessibilityContextType = {
    preferences,
    updatePreferences,
    announceToScreenReader,
    keyboardNavigation,
    focusElement,
    trapFocus
  };

  return (
    <AccessibilityContext.Provider value={contextValue}>
      {children}
      
      {/* Live Regions */}
      <div className="sr-only" ref={liveRegionRef}>
        {liveRegions.map(region => (
          <div
            key={region.id}
            aria-live={region.level}
            aria-atomic="true"
          >
            {region.message}
          </div>
        ))}
      </div>
    </AccessibilityContext.Provider>
  );
}

// ==================
// ACCESSIBILITY HOOKS
// ==================

export function useAccessibility() {
  const context = useContext(AccessibilityContext);
  if (!context) {
    throw new Error('useAccessibility must be used within AccessibilityProvider');
  }
  return context;
}

export function useKeyboardNavigation() {
  const { keyboardNavigation, focusElement, trapFocus } = useAccessibility();
  
  return {
    ...keyboardNavigation,
    focusElement,
    trapFocus,
    handleKeyDown: (e: React.KeyboardEvent, handlers: Record<string, () => void>) => {
      const handler = handlers[e.key];
      if (handler) {
        e.preventDefault();
        handler();
      }
    }
  };
}

export function useAriaLive() {
  const { announceToScreenReader } = useAccessibility();
  
  return useMemo(() => ({
    announce: announceToScreenReader,
    announceError: (message: string) => announceToScreenReader(`Error: ${message}`, 'assertive'),
    announceSuccess: (message: string) => announceToScreenReader(`Success: ${message}`, 'polite'),
    announceStatus: (message: string) => announceToScreenReader(message, 'polite')
  }), [announceToScreenReader]);
}

export function useFocusManagement() {
  const { focusElement, trapFocus, keyboardNavigation } = useAccessibility();
  
  return {
    focusElement,
    trapFocus,
    focusFirst: (container: HTMLElement) => {
      const focusable = getFocusableElements(container);
      if (focusable.length > 0) {
        focusElement(focusable[0]);
      }
    },
    focusLast: (container: HTMLElement) => {
      const focusable = getFocusableElements(container);
      if (focusable.length > 0) {
        focusElement(focusable[focusable.length - 1]);
      }
    },
    restoreFocus: () => {
      const lastFocused = keyboardNavigation.focusHistory[keyboardNavigation.focusHistory.length - 2];
      if (lastFocused && document.contains(lastFocused)) {
        focusElement(lastFocused);
      }
    }
  };
}

// ==================
// UTILITY FUNCTIONS
// ==================

export function getFocusableElements(container: HTMLElement): HTMLElement[] {
  const focusableSelectors = [
    'button:not([disabled])',
    'input:not([disabled])',
    'select:not([disabled])',
    'textarea:not([disabled])',
    'a[href]',
    '[tabindex]:not([tabindex="-1"])',
    '[role="button"]:not([disabled])',
    '[role="link"]:not([disabled])',
    '[role="menuitem"]:not([disabled])',
    '[role="option"]:not([disabled])',
    '[role="tab"]:not([disabled])',
    '[contenteditable="true"]'
  ].join(', ');

  return Array.from(container.querySelectorAll(focusableSelectors))
    .filter(el => isElementVisible(el as HTMLElement)) as HTMLElement[];
}

export function isElementVisible(element: HTMLElement): boolean {
  const style = window.getComputedStyle(element);
  return style.display !== 'none' && 
         style.visibility !== 'hidden' && 
         style.opacity !== '0' &&
         element.offsetWidth > 0 && 
         element.offsetHeight > 0;
}

export function applyAccessibilityPreferences(preferences: AccessibilityPreferences): void {
  const root = document.documentElement;
  
  // Reduced motion
  if (preferences.reducedMotion) {
    root.style.setProperty('--animation-duration', '0.01ms');
    root.style.setProperty('--transition-duration', '0.01ms');
    root.classList.add('reduce-motion');
  } else {
    root.style.removeProperty('--animation-duration');
    root.style.removeProperty('--transition-duration');
    root.classList.remove('reduce-motion');
  }
  
  // High contrast
  if (preferences.highContrast) {
    root.classList.add('high-contrast');
  } else {
    root.classList.remove('high-contrast');
  }
  
  // Font size
  root.setAttribute('data-font-size', preferences.fontSize);
  
  // Focus visible
  if (preferences.focusVisible) {
    root.classList.add('focus-visible');
  } else {
    root.classList.remove('focus-visible');
  }
  
  // Screen reader optimized
  if (preferences.screenReaderOptimized) {
    root.classList.add('screen-reader-optimized');
  } else {
    root.classList.remove('screen-reader-optimized');
  }
}

export function generateAriaLabel(
  baseText: string, 
  context?: Record<string, any>
): string {
  if (!context) return baseText;
  
  let label = baseText;
  
  // Add status information
  if (context.status) {
    label += `, ${context.status}`;
  }
  
  // Add position information
  if (context.position && context.total) {
    label += `, ${context.position} of ${context.total}`;
  }
  
  // Add state information
  if (context.expanded !== undefined) {
    label += `, ${context.expanded ? 'expanded' : 'collapsed'}`;
  }
  
  if (context.selected !== undefined) {
    label += `, ${context.selected ? 'selected' : 'not selected'}`;
  }
  
  if (context.disabled) {
    label += ', disabled';
  }
  
  return label;
}

// ==================
// ACCESSIBILITY COMPONENTS
// ==================

// Skip Links Component
export function SkipLinks({ links }: { links: Array<{ href: string; text: string }> }) {
  return (
    <div className="skip-links">
      {links.map((link, index) => (
        <a
          key={index}
          href={link.href}
          className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-blue-600 focus:text-white focus:rounded focus:shadow-lg"
        >
          {link.text}
        </a>
      ))}
    </div>
  );
}

// Screen Reader Only Component
export function ScreenReaderOnly({ children }: { children: ReactNode }) {
  return <span className="sr-only">{children}</span>;
}

// Focus Trap Component
export function FocusTrap({ 
  children, 
  active = true,
  restoreFocus = true 
}: { 
  children: ReactNode; 
  active?: boolean;
  restoreFocus?: boolean;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const { trapFocus } = useFocusManagement();
  const previousFocusRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    if (!active || !containerRef.current) return;

    previousFocusRef.current = document.activeElement as HTMLElement;
    const cleanup = trapFocus(containerRef.current);

    return () => {
      cleanup();
      if (restoreFocus && previousFocusRef.current) {
        previousFocusRef.current.focus();
      }
    };
  }, [active, trapFocus, restoreFocus]);

  return (
    <div ref={containerRef} tabIndex={-1}>
      {children}
    </div>
  );
}

// ARIA Landmark Component
export function Landmark({ 
  as: Component = 'div',
  role,
  label,
  labelledBy,
  children,
  ...props 
}: {
  as?: React.ElementType;
  role?: string;
  label?: string;
  labelledBy?: string;
  children: ReactNode;
  [key: string]: any;
}) {
  const ariaProps: Record<string, any> = {};
  
  if (role) ariaProps.role = role;
  if (label) ariaProps['aria-label'] = label;
  if (labelledBy) ariaProps['aria-labelledby'] = labelledBy;

  return (
    <Component {...ariaProps} {...props}>
      {children}
    </Component>
  );
}

// Accessible Button Component
export function AccessibleButton({
  children,
  onClick,
  disabled = false,
  ariaLabel,
  ariaDescribedBy,
  ariaExpanded,
  ariaPressed,
  ariaHaspopup,
  className = '',
  ...props
}: {
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  ariaLabel?: string;
  ariaDescribedBy?: string;
  ariaExpanded?: boolean;
  ariaPressed?: boolean;
  ariaHaspopup?: boolean | 'menu' | 'listbox' | 'tree' | 'grid' | 'dialog';
  className?: string;
  [key: string]: any;
}) {
  const { announce } = useAriaLive();

  const handleClick = () => {
    if (onClick && !disabled) {
      onClick();
      if (ariaLabel) {
        announce(`${ariaLabel} activated`);
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if ((e.key === 'Enter' || e.key === ' ') && !disabled) {
      e.preventDefault();
      handleClick();
    }
  };

  return (
    <button
      className={`${className} ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      disabled={disabled}
      aria-label={ariaLabel}
      aria-describedby={ariaDescribedBy}
      aria-expanded={ariaExpanded}
      aria-pressed={ariaPressed}
      aria-haspopup={ariaHaspopup}
      tabIndex={disabled ? -1 : 0}
      {...props}
    >
      {children}
    </button>
  );
}

// Accessible Modal Component
export function AccessibleModal({
  isOpen,
  onClose,
  title,
  children,
  className = ''
}: {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  className?: string;
}) {
  const { announce } = useAriaLive();
  const titleId = `modal-title-${React.useId()}`;

  useEffect(() => {
    if (isOpen) {
      announce(`Modal opened: ${title}`);
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }

    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen, title, announce]);

  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 z-50 overflow-y-auto"
      role="dialog"
      aria-modal="true"
      aria-labelledby={titleId}
    >
      <div className="flex items-center justify-center min-h-screen px-4">
        <div 
          className="fixed inset-0 bg-black bg-opacity-50"
          onClick={onClose}
          aria-hidden="true"
        />
        
        <FocusTrap active={isOpen}>
          <div className={`relative bg-white rounded-lg shadow-xl max-w-lg w-full ${className}`}>
            <div className="p-6">
              <h2 id={titleId} className="text-xl font-semibold mb-4">
                {title}
              </h2>
              
              {children}
              
              <AccessibleButton
                onClick={onClose}
                ariaLabel={`Close ${title} modal`}
                className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
              >
                <span aria-hidden="true">&times;</span>
              </AccessibleButton>
            </div>
          </div>
        </FocusTrap>
      </div>
    </div>
  );
}

// ==================
// ACCESSIBILITY STYLES
// ==================

export const accessibilityStyles = `
  /* Screen reader only */
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }

  .sr-only.focus:not(.sr-only) {
    position: static;
    width: auto;
    height: auto;
    padding: inherit;
    margin: inherit;
    overflow: visible;
    clip: auto;
    white-space: normal;
  }

  /* Skip links */
  .skip-links a {
    position: absolute;
    left: -10000px;
    top: auto;
    width: 1px;
    height: 1px;
    overflow: hidden;
  }

  .skip-links a:focus {
    position: absolute;
    left: 6px;
    top: 6px;
    width: auto;
    height: auto;
    overflow: visible;
    z-index: 1000;
  }

  /* Focus management */
  .focus-visible *:focus {
    outline: 2px solid #2563eb;
    outline-offset: 2px;
  }

  /* Reduced motion */
  .reduce-motion *,
  .reduce-motion *::before,
  .reduce-motion *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }

  /* High contrast */
  .high-contrast {
    filter: contrast(150%);
  }

  .high-contrast button,
  .high-contrast input,
  .high-contrast select,
  .high-contrast textarea {
    border: 2px solid;
  }

  /* Font size scaling */
  [data-font-size="small"] {
    font-size: 0.875rem;
  }

  [data-font-size="medium"] {
    font-size: 1rem;
  }

  [data-font-size="large"] {
    font-size: 1.125rem;
  }

  [data-font-size="extra-large"] {
    font-size: 1.25rem;
  }

  /* Screen reader optimized */
  .screen-reader-optimized {
    /* Simplify layouts for screen readers */
  }

  .screen-reader-optimized .decorative {
    display: none;
  }
`;

export default {
  AccessibilityProvider,
  useAccessibility,
  useKeyboardNavigation,
  useAriaLive,
  useFocusManagement,
  SkipLinks,
  ScreenReaderOnly,
  FocusTrap,
  Landmark,
  AccessibleButton,
  AccessibleModal,
  getFocusableElements,
  generateAriaLabel,
  accessibilityStyles
};