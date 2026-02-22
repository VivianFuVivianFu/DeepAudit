import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Deep-Audit: Black-Box AI Safety & Governance Readiness Scan',
  description: 'A non-invasive behavioral audit for production AI agents. No code access. No data extraction. No deployment required.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
