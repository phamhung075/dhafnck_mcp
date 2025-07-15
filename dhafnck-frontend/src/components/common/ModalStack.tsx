import React, { useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../../store/store';
import { uiActions } from '../../store/store';
import type { Modal } from '../../types/application';

export function ModalStack() {
  const dispatch = useAppDispatch();
  const { modalStack } = useAppSelector(state => state.ui);

  // Handle escape key to close top modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && modalStack.length > 0) {
        const topModal = modalStack[modalStack.length - 1];
        if (topModal.onClose) {
          topModal.onClose();
        } else {
          dispatch(uiActions.popModal());
        }
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [modalStack, dispatch]);

  // Prevent body scroll when modals are open
  useEffect(() => {
    if (modalStack.length > 0) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [modalStack.length]);

  if (modalStack.length === 0) return null;

  return (
    <>
      {modalStack.map((modal, index) => (
        <ModalRenderer
          key={modal.id}
          modal={modal}
          isTop={index === modalStack.length - 1}
          zIndex={50 + index}
          onClose={() => {
            if (modal.onClose) {
              modal.onClose();
            } else {
              dispatch(uiActions.popModal());
            }
          }}
        />
      ))}
    </>
  );
}

interface ModalRendererProps {
  modal: Modal;
  isTop: boolean;
  zIndex: number;
  onClose: () => void;
}

function ModalRenderer({ modal, isTop, zIndex, onClose }: ModalRendererProps) {
  const opacity = isTop ? 'bg-opacity-50' : 'bg-opacity-25';

  switch (modal.type) {
    case 'dialog':
      return (
        <DialogModal
          modal={modal}
          onClose={onClose}
          zIndex={zIndex}
          opacity={opacity}
        />
      );
    
    case 'drawer':
      return (
        <DrawerModal
          modal={modal}
          onClose={onClose}
          zIndex={zIndex}
          opacity={opacity}
        />
      );
    
    case 'fullscreen':
      return (
        <FullscreenModal
          modal={modal}
          onClose={onClose}
          zIndex={zIndex}
        />
      );
    
    default:
      return (
        <DialogModal
          modal={modal}
          onClose={onClose}
          zIndex={zIndex}
          opacity={opacity}
        />
      );
  }
}

// Dialog Modal (center overlay)
function DialogModal({ modal, onClose, zIndex, opacity }: {
  modal: Modal;
  onClose: () => void;
  zIndex: number;
  opacity: string;
}) {
  return (
    <div 
      className={`fixed inset-0 bg-black ${opacity} flex items-center justify-center p-4`}
      style={{ zIndex }}
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {modal.title}
          </h2>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <span className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">✕</span>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto max-h-[calc(90vh-8rem)]">
          {modal.content}
        </div>

        {/* Actions */}
        {modal.actions && modal.actions.length > 0 && (
          <div className="px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex justify-end gap-3">
            {modal.actions.map((action, index) => (
              <button
                key={index}
                onClick={() => {
                  action.action();
                  if (action.variant !== 'secondary') {
                    onClose();
                  }
                }}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  action.variant === 'primary'
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : action.variant === 'danger'
                    ? 'bg-red-600 text-white hover:bg-red-700'
                    : 'bg-gray-200 dark:bg-gray-600 text-gray-900 dark:text-white hover:bg-gray-300 dark:hover:bg-gray-500'
                }`}
              >
                {action.label}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// Drawer Modal (slide from right)
function DrawerModal({ modal, onClose, zIndex, opacity }: {
  modal: Modal;
  onClose: () => void;
  zIndex: number;
  opacity: string;
}) {
  return (
    <div 
      className={`fixed inset-0 bg-black ${opacity}`}
      style={{ zIndex }}
      onClick={(e) => {
        if (e.target === e.currentTarget) {
          onClose();
        }
      }}
    >
      <div className="fixed right-0 top-0 h-full w-full max-w-md bg-white dark:bg-gray-800 shadow-xl transform transition-transform duration-300 ease-in-out animate-slide-in-right">
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            {modal.title}
          </h2>
          <button
            onClick={onClose}
            className="p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
          >
            <span className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">✕</span>
          </button>
        </div>

        {/* Content */}
        <div className="p-6 overflow-y-auto h-[calc(100vh-8rem)]">
          {modal.content}
        </div>

        {/* Actions */}
        {modal.actions && modal.actions.length > 0 && (
          <div className="absolute bottom-0 left-0 right-0 px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
            <div className="flex justify-end gap-3">
              {modal.actions.map((action, index) => (
                <button
                  key={index}
                  onClick={() => {
                    action.action();
                    if (action.variant !== 'secondary') {
                      onClose();
                    }
                  }}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    action.variant === 'primary'
                      ? 'bg-blue-600 text-white hover:bg-blue-700'
                      : action.variant === 'danger'
                      ? 'bg-red-600 text-white hover:bg-red-700'
                      : 'bg-gray-200 dark:bg-gray-600 text-gray-900 dark:text-white hover:bg-gray-300 dark:hover:bg-gray-500'
                  }`}
                >
                  {action.label}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Fullscreen Modal
function FullscreenModal({ modal, onClose, zIndex }: {
  modal: Modal;
  onClose: () => void;
  zIndex: number;
}) {
  return (
    <div 
      className="fixed inset-0 bg-white dark:bg-gray-900"
      style={{ zIndex }}
    >
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
          {modal.title}
        </h2>
        <button
          onClick={onClose}
          className="p-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
        >
          <span className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200">✕</span>
        </button>
      </div>

      {/* Content */}
      <div className="p-6 overflow-y-auto h-[calc(100vh-5rem)]">
        {modal.content}
      </div>

      {/* Actions */}
      {modal.actions && modal.actions.length > 0 && (
        <div className="absolute bottom-0 left-0 right-0 px-6 py-4 border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900">
          <div className="flex justify-end gap-3">
            {modal.actions.map((action, index) => (
              <button
                key={index}
                onClick={() => {
                  action.action();
                  if (action.variant !== 'secondary') {
                    onClose();
                  }
                }}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  action.variant === 'primary'
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : action.variant === 'danger'
                    ? 'bg-red-600 text-white hover:bg-red-700'
                    : 'bg-gray-200 dark:bg-gray-600 text-gray-900 dark:text-white hover:bg-gray-300 dark:hover:bg-gray-500'
                }`}
              >
                {action.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}