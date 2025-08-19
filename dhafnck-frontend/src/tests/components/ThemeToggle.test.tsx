import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ThemeToggle } from '../../components/ThemeToggle';
import { useTheme } from '../../hooks/useTheme';

// Mock the useTheme hook
jest.mock('../../hooks/useTheme');

describe('ThemeToggle', () => {
  const mockToggleTheme = jest.fn();
  const mockedUseTheme = useTheme as jest.MockedFunction<typeof useTheme>;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders correctly in light mode', () => {
    mockedUseTheme.mockReturnValue({
      theme: 'light',
      toggleTheme: mockToggleTheme,
      setTheme: jest.fn(),
    });

    render(<ThemeToggle />);
    
    const button = screen.getByRole('button', { name: /switch to dark mode/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute('aria-label', 'Switch to dark mode');
    expect(button).toHaveAttribute('title', 'Switch to dark mode');
    
    // Check for Moon icon (indicated by the Moon component from lucide-react)
    const moonIcon = button.querySelector('.lucide-moon');
    expect(moonIcon).toBeInTheDocument();
  });

  it('renders correctly in dark mode', () => {
    mockedUseTheme.mockReturnValue({
      theme: 'dark',
      toggleTheme: mockToggleTheme,
      setTheme: jest.fn(),
    });

    render(<ThemeToggle />);
    
    const button = screen.getByRole('button', { name: /switch to light mode/i });
    expect(button).toBeInTheDocument();
    expect(button).toHaveAttribute('aria-label', 'Switch to light mode');
    expect(button).toHaveAttribute('title', 'Switch to light mode');
    
    // Check for Sun icon
    const sunIcon = button.querySelector('.lucide-sun');
    expect(sunIcon).toBeInTheDocument();
  });

  it('calls toggleTheme when clicked', () => {
    mockedUseTheme.mockReturnValue({
      theme: 'light',
      toggleTheme: mockToggleTheme,
      setTheme: jest.fn(),
    });

    render(<ThemeToggle />);
    
    const button = screen.getByRole('button');
    fireEvent.click(button);
    
    expect(mockToggleTheme).toHaveBeenCalledTimes(1);
  });

  it('applies correct CSS classes', () => {
    mockedUseTheme.mockReturnValue({
      theme: 'light',
      toggleTheme: mockToggleTheme,
      setTheme: jest.fn(),
    });

    render(<ThemeToggle />);
    
    const button = screen.getByRole('button');
    expect(button).toHaveClass('h-9', 'w-9', 'rounded-lg', 'border', 'border-surface-border');
    expect(button).toHaveClass('bg-surface', 'hover:bg-background-hover');
    expect(button).toHaveClass('transition-all', 'hover:scale-105');
    expect(button).toHaveClass('flex', 'items-center', 'justify-center');
  });

  it('toggles between light and dark mode icons', () => {
    const { rerender } = render(<ThemeToggle />);

    // Start with light mode
    mockedUseTheme.mockReturnValue({
      theme: 'light',
      toggleTheme: mockToggleTheme,
      setTheme: jest.fn(),
    });
    rerender(<ThemeToggle />);
    
    let button = screen.getByRole('button');
    expect(button.querySelector('.lucide-moon')).toBeInTheDocument();
    expect(button.querySelector('.lucide-sun')).not.toBeInTheDocument();

    // Switch to dark mode
    mockedUseTheme.mockReturnValue({
      theme: 'dark',
      toggleTheme: mockToggleTheme,
      setTheme: jest.fn(),
    });
    rerender(<ThemeToggle />);
    
    button = screen.getByRole('button');
    expect(button.querySelector('.lucide-sun')).toBeInTheDocument();
    expect(button.querySelector('.lucide-moon')).not.toBeInTheDocument();
  });
});