import { render } from '@testing-library/react';
import { Button } from './button';

describe('Button', () => {
  it('renders with default variant correctly', () => {
    const { container } = render(<Button>Click me</Button>);
    expect(container.firstChild).toMatchSnapshot();
  });

  it('renders with destructive variant correctly', () => {
    const { container } = render(<Button variant="destructive">Delete</Button>);
    expect(container.firstChild).toMatchSnapshot();
  });
});
