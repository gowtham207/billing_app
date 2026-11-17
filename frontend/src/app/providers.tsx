import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useState, type ReactNode } from 'react'
import { BrowserRouter } from 'react-router-dom'
import { ToastProvider } from '@/components/common/ui'
import { SessionProvider } from '@/hooks/session'

export function AppProviders({ children }: { children: ReactNode }) {
  const [client] = useState(() => new QueryClient({ defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } } }))
  return (
    <QueryClientProvider client={client}>
      <SessionProvider>
        <ToastProvider>
          <BrowserRouter>{children}</BrowserRouter>
        </ToastProvider>
      </SessionProvider>
    </QueryClientProvider>
  )
}
