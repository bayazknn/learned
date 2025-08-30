## Brief overview
This rule establishes consistent Python import patterns and terminal command execution for projects with backend module structures, ensuring proper module resolution and avoiding import errors.

## Import patterns
  - Always use absolute imports with the backend prefix when importing from backend modules (e.g., `from backend.tasks.background import process_video_task`)
  - Never use relative imports that assume execution from within the backend directory
  - Maintain consistent import patterns across all backend modules and scripts

## Terminal command execution
  - Execute all Python commands from the project root directory (/home/kenan/Desktop/ai-apps/learned)
  - Never add "cd backend" to terminal commands before running Python scripts or imports
  - Use the full module path in import statements when testing via python -c commands

## Module structure
  - Treat the backend directory as a proper Python package with __init__.py files
  - Ensure all imports reference the backend package explicitly
  - Maintain consistent naming conventions for modules and subpackages

## Development workflow
  - Test imports using the pattern: `python -c "from backend.module.path import function; print('Import successful')"`
  - Verify module resolution works from the project root directory
  - Avoid changing working directories during command execution

## Error prevention
  - ModuleNotFoundError indicates incorrect import patterns or execution directory
  - Always check that imports work from the project root before proceeding
  - Use consistent import patterns to prevent resolution issues
