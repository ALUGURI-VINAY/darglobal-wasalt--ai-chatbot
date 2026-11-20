# DarGlobal × Wasalt Real Estate AI Chatbot — Frontend

An intelligent real estate conversational assistant and property discovery workspace designed for **DarGlobal** and **Wasalt**.

## Tech Stack & Architecture

- **Framework**: TanStack Start (Full-stack SSR / SPA framework built on Nitro & Vite)
- **UI Library**: React 19 + TypeScript
- **Styling**: Tailwind CSS v4 + Custom Luxury Theme Variables (Manrope typography)
- **Component Primitives**: Radix UI (Dialog, Dropdown Menu, Popover, Tooltip, Accordion, ScrollArea)
- **AI Elements**: Streamdown (progressive markdown & math streaming), Lucide React icons
- **State & Routing**: TanStack React Router with type-safe file-based routing (`/chat/$threadId`, `/sources`, `/history`, `/about`)
- **Data Persistence**: Client-side session and thread persistence via LocalStorage
- **Streaming Client**: SSE (Server-Sent Events) reader via `ReadableStream` with automatic fallback to synchronous REST endpoints

## Getting Started

### Prerequisites
- Node.js >= 20
- npm >= 10

### Installation
```bash
npm install
```

### Local Development
```bash
# Starts the Vite development server with Hot Module Replacement
npm run dev
```

### Building for Production
```bash
# Build for deployment (Vercel, Cloudflare, Node)
npm run build
```

## Environment Configuration

Configure the backend API URL using the environment variable:
- `VITE_API_BASE_URL`: Base URL of the FastAPI backend (e.g., `http://localhost:8000` for local or `https://api.yourdomain.com` for production).
