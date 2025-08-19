import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Button, ButtonProps } from '../../../components/ui/button';
import { cn } from '../../../lib/utils';

// Mock the cn utility
jest.mock('../../../lib/utils', () => ({
  cn: jest.fn((...args) => args.filter(Boolean).join(' ')),
}));

describe('Button', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders with default props', () => {
    render(<Button>Click me</Button>);
    
    const button = screen.getByRole('button', { name: /click me/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveClass('theme-btn-primary');
    expect(button).toHaveClass('h-10 px-4 py-2');
  });

  describe('variants', () => {
    it('renders default variant', () => {
      render(<Button variant="default">Default</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveClass('theme-btn-primary');
    });

    it('renders outline variant', () => {
      render(<Button variant="outline">Outline</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveClass('theme-btn-outline');
    });

    it('renders secondary variant', () => {
      render(<Button variant="secondary">Secondary</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveClass('theme-btn-secondary');
    });

    it('renders ghost variant', () => {
      render(<Button variant="ghost">Ghost</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveClass('hover:bg-background-hover text-base-primary');
    });

    it('renders link variant', () => {
      render(<Button variant="link">Link</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveClass('underline-offset-4 hover:underline text-primary');
    });
  });

  describe('sizes', () => {
    it('renders default size', () => {
      render(<Button size="default">Default</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-10 px-4 py-2');
    });

    it('renders small size', () => {
      render(<Button size="sm">Small</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-9 px-3');
    });

    it('renders large size', () => {
      render(<Button size="lg">Large</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-11 px-8');
    });

    it('renders icon size', () => {
      render(<Button size="icon">🔥</Button>);
      
      const button = screen.getByRole('button');
      expect(button).toHaveClass('h-10 w-10 p-0 flex items-center justify-center');
    });
  });

  it('applies custom className', () => {
    render(<Button className="custom-class">Custom</Button>);
    
    const button = screen.getByRole('button');
    expect(button).toHaveClass('custom-class');
  });

  it('forwards ref correctly', () => {
    const ref = React.createRef<HTMLButtonElement>();
    render(<Button ref={ref}>Ref Button</Button>);
    
    expect(ref.current).toBeInstanceOf(HTMLButtonElement);
    expect(ref.current?.textContent).toBe('Ref Button');
  });

  it('handles click events', () => {
    const handleClick = jest.fn();
    render(<Button onClick={handleClick}>Click me</Button>);
    
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('respects disabled state', () => {
    const handleClick = jest.fn();
    render(<Button disabled onClick={handleClick}>Disabled</Button>);
    
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    expect(button).toHaveClass('disabled:opacity-50 disabled:pointer-events-none');
    
    fireEvent.click(button);
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('applies all base classes', () => {
    render(<Button>Base Classes</Button>);
    
    const button = screen.getByRole('button');
    expect(button).toHaveClass('inline-flex');
    expect(button).toHaveClass('items-center');
    expect(button).toHaveClass('justify-center');
    expect(button).toHaveClass('rounded-md');
    expect(button).toHaveClass('text-sm');
    expect(button).toHaveClass('font-medium');
    expect(button).toHaveClass('transition-colors');
    expect(button).toHaveClass('focus-visible:outline-none');
    expect(button).toHaveClass('focus-visible:ring-2');
    expect(button).toHaveClass('focus-visible:ring-ring');
    expect(button).toHaveClass('focus-visible:ring-offset-2');
    expect(button).toHaveClass('ring-offset-background');
  });

  it('passes through HTML button attributes', () => {
    render(
      <Button
        type="submit"
        name="test-button"
        value="test-value"
        aria-label="Test Button"
        data-testid="custom-test-id"
      >
        HTML Attributes
      </Button>
    );
    
    const button = screen.getByRole('button');
    expect(button).toHaveAttribute('type', 'submit');
    expect(button).toHaveAttribute('name', 'test-button');
    expect(button).toHaveAttribute('value', 'test-value');
    expect(button).toHaveAttribute('aria-label', 'Test Button');
    expect(button).toHaveAttribute('data-testid', 'custom-test-id');
  });

  it('combines variant and size classes correctly', () => {
    render(<Button variant="outline" size="lg">Combined</Button>);
    
    const button = screen.getByRole('button');
    expect(button).toHaveClass('theme-btn-outline');
    expect(button).toHaveClass('h-11 px-8');
  });

  it('calls cn utility with correct arguments', () => {
    const customClass = 'my-custom-class';
    render(<Button variant="secondary" size="sm" className={customClass}>CN Test</Button>);
    
    expect(cn).toHaveBeenCalledWith(
      expect.stringContaining('inline-flex'),
      'theme-btn-secondary',
      'h-9 px-3',
      customClass
    );
  });

  it('renders children correctly', () => {
    render(
      <Button>
        <span>Icon</span>
        <span>Text</span>
      </Button>
    );
    
    expect(screen.getByText('Icon')).toBeInTheDocument();
    expect(screen.getByText('Text')).toBeInTheDocument();
  });

  it('has correct display name', () => {
    expect(Button.displayName).toBe('Button');
  });
});