import { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';

export function Tooltip({ children, content, position = 'top', className = '' }) {
  const [isVisible, setIsVisible] = useState(false);
  const [coords, setCoords] = useState({});
  const triggerRef = useRef(null);
  const tooltipRef = useRef(null);

  const updateTooltipPosition = () => {
    if (triggerRef.current && tooltipRef.current) {
      const triggerRect = triggerRef.current.getBoundingClientRect();
      const tooltipRect = tooltipRef.current.getBoundingClientRect();
      
      let top, left;
      
      switch (position) {
        case 'top':
          top = triggerRect.top - tooltipRect.height - 8;
          left = triggerRect.left + (triggerRect.width - tooltipRect.width) / 2;
          break;
        case 'bottom':
          top = triggerRect.bottom + 8;
          left = triggerRect.left + (triggerRect.width - tooltipRect.width) / 2;
          break;
        case 'left':
          top = triggerRect.top + (triggerRect.height - tooltipRect.height) / 2;
          left = triggerRect.left - tooltipRect.width - 8;
          break;
        case 'right':
          top = triggerRect.top + (triggerRect.height - tooltipRect.height) / 2;
          left = triggerRect.right + 8;
          break;
        default:
          top = triggerRect.top - tooltipRect.height - 8;
          left = triggerRect.left + (triggerRect.width - tooltipRect.width) / 2;
      }
      
      // Adjust for viewport edges
      if (left < 8) left = 8;
      if (left + tooltipRect.width > window.innerWidth - 8) {
        left = window.innerWidth - tooltipRect.width - 8;
      }
      if (top < 8) top = 8;
      if (top + tooltipRect.height > window.innerHeight - 8) {
        top = window.innerHeight - tooltipRect.height - 8;
      }
      
      setCoords({ top, left });
    }
  };

  useEffect(() => {
    if (isVisible) {
      updateTooltipPosition();
      window.addEventListener('resize', updateTooltipPosition);
      window.addEventListener('scroll', updateTooltipPosition, true);
    }
    return () => {
      window.removeEventListener('resize', updateTooltipPosition);
      window.removeEventListener('scroll', updateTooltipPosition, true);
    };
  }, [isVisible, content]);

  const showTooltip = () => {
    setIsVisible(true);
  };

  const hideTooltip = () => {
    setIsVisible(false);
  };

  return (
    <>
      <div
        ref={triggerRef}
        onMouseEnter={showTooltip}
        onMouseLeave={hideTooltip}
        onFocus={showTooltip}
        onBlur={hideTooltip}
        className="inline-block"
      >
        {children}
      </div>
      
      {isVisible && createPortal(
        <div
          ref={tooltipRef}
          className={`fixed z-50 px-3 py-1.5 text-xs font-medium rounded-md shadow-lg bg-gray-900 text-white dark:bg-nord-3 dark:text-nord-6 transition-opacity duration-200 ${className}`}
          style={{
            top: `${coords.top}px`,
            left: `${coords.left}px`,
          }}
        >
          {content}
          <div 
            className={`absolute w-2 h-2 bg-gray-900 dark:bg-nord-3 transform rotate-45 -z-10`}
            style={{
              ...(position === 'top' && { 
                bottom: '-4px',
                left: '50%',
                transform: 'translateX(-50%) rotate(45deg)',
              }),
              ...(position === 'bottom' && { 
                top: '-4px',
                left: '50%',
                transform: 'translateX(-50%) rotate(45deg)',
              }),
              ...(position === 'left' && { 
                top: '50%',
                right: '-4px',
                transform: 'translateY(-50%) rotate(45deg)',
              }),
              ...(position === 'right' && { 
                top: '50%',
                left: '-4px',
                transform: 'translateY(-50%) rotate(45deg)',
              }),
            }}
          />
        </div>,
        document.body
      )}
    </>
  );
}
