# Agent Guidelines & Application Architecture

## Core Guidelines
- Maintain code modularity, strict TypeScript types, and responsive design patterns across mobile and desktop breakpoints.
- Do not add extraneous dependencies; reuse the established Radix UI and Tailwind CSS design system.
- Preserve backward compatibility with both streaming (`/chat/stream`) and synchronous (`/chat`) FastAPI backend contracts.

## Application Architecture
- **API Layer**: All backend interactions route through `src/lib/api.ts` pointing to the FastAPI RAG service. Base URL is configurable via `VITE_API_BASE_URL`.
- **Routing**: TanStack Router with file-based routing (`/`, `/chat/$threadId`, `/sources`, `/history`, `/about`).
- **State Management**: React Context (`AssistantProvider` in `src/components/assistant/context.tsx`) with automatic LocalStorage synchronization for chat threads, company selection, and theme preferences.
- **Rendering & Streaming**: Progressive token-by-token text streaming using Streamdown and AI Elements with auto-scrolling to bottom.
