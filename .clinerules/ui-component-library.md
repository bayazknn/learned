## Brief overview
This rule establishes shadcn/ui as the preferred component library for all React-based projects, ensuring consistency in UI development and component usage patterns.

## Component library preference
  - Always use shadcn/ui components when creating React components
  - Prefer built-in shadcn/ui components over custom implementations for common UI elements
  - Follow shadcn/ui's component patterns and styling conventions

## Development workflow
  - Install shadcn/ui via the official CLI when setting up new React projects
  - Use the components.json configuration file to maintain shadcn/ui settings
  - Keep shadcn/ui components in a dedicated `components/ui/` directory structure

## Coding best practices
  - Import shadcn/ui components using the established path patterns (e.g., `import { Button } from "@/components/ui/button"`)
  - Leverage shadcn/ui's composable component architecture for complex UI needs
  - Follow shadcn/ui's theming and styling approach for consistent visual design

## Project context
  - This preference applies to all React and Next.js projects in the codebase
  - Existing projects should be migrated to use shadcn/ui when components are updated or added
  - New projects must use shadcn/ui from the initial setup

## Integration guidelines
  - Combine shadcn/ui with Tailwind CSS for styling, as shadcn/ui is built on Tailwind
  - Use shadcn/ui's theming system for consistent color schemes and design tokens
  - Follow shadcn/ui's accessibility patterns to ensure WCAG compliance
