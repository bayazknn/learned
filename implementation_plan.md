# Implementation Plan: Fix AI SDK v5 Compatibility Issues

## Overview
Fix compilation errors in the AI chat components caused by upgrading from AI SDK v4 to v5. The main issues are incompatible useChat hook API, transport configuration changes, and message format updates. The backend uses a custom streaming format that needs to be properly integrated with the new AI SDK UI components.

## Types
Update TypeScript interfaces to match AI SDK v5 API changes:
- Replace `UseChatHelpers` with new hook return types
- Update message format to use `parts` property
- Add proper typing for transport configuration
- Update status enum values ('submitted', 'streaming', 'ready', 'error')

## Files
### yt-learn/components/ai-chat.tsx (MODIFIED)
- Replace old useChat API with new v5 syntax
- Remove `input`, `handleInputChange`, `handleSubmit` properties
- Add manual input state management with `useState`
- Update transport configuration to use `DefaultChatTransport`
- Replace `handleSubmit` calls with `sendMessage({ text: input })`
- Update status mapping for loading states
- Remove deprecated `experimental_attachments` usage
- Update error handling for new API

### yt-learn/components/chat/chat-input.tsx (MODIFIED)
- Update props interface to match new input handling
- Remove `handleInputChange` and `handleSubmit` props
- Add `sendMessage` prop for new API
- Update form submission logic

### yt-learn/components/chat/chat-message.tsx (MODIFIED)
- Update message content extraction to use `parts` property
- Add proper handling for different part types ('text', 'reasoning', etc.)
- Update source handling for new message format
- Maintain backward compatibility with existing message structure

### yt-learn/components/chat/index.ts (NO CHANGE)
- Export statements remain the same

## Functions
### New Functions
- `handleSendMessage`: Replace handleSubmit with sendMessage logic
- `handleInputSubmit`: Handle form submission with manual input state

### Modified Functions
- `handleCustomSubmit`: Update to use sendMessage instead of handleSubmit
- `handleKeyDown`: Update to work with new input handling
- `getMessageContent`: Update to extract content from parts array

### Removed Functions
- None - maintaining backward compatibility

## Classes
No class modifications required - all components are functional.

## Dependencies
### Current Versions (package.json)
- "ai": "^5.0.30"
- "@ai-sdk/react": "^2.0.30"

### Compatibility Notes
- Versions are correct for AI SDK v5
- No dependency updates needed
- Backend API format is custom but compatible

## Testing
### Test Cases Needed
- Verify chat message sending works with new API
- Test file upload functionality with updated transport
- Confirm streaming responses display correctly
- Validate error handling for network issues
- Test thread management with new message format

### Existing Test Files
- No specific chat component tests found
- Backend tests exist but may need updates for new API

## Implementation Order
1. Update ai-chat.tsx with new useChat API
2. Modify chat-input.tsx to work with new input handling
3. Update chat-message.tsx for parts-based message format
4. Test file upload and streaming functionality
5. Verify error handling and status updates
6. Test integration with existing backend API
