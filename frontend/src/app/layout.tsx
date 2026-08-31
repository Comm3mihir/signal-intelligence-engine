import React from "react";
import "./globals.css";
import Navigation from "@/components/Navigation";

export const metadata = {
  title: "SIGNAL — Strategic Geopolitical Intelligence Engine",
  description: "Command-center briefing platform mapping external OSINT events to business dependencies, transparent risk scoring, evidence traceability, and AI transformation priorities.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet" />
      </head>
      <body className="bg-ink text-paper min-h-screen flex flex-col antialiased">
        <Navigation />
        <main className="flex-1 max-w-[1320px] w-full mx-auto px-4 sm:px-8 py-7 relative z-10">
          {children}
        </main>
        <footer className="border-t border-line bg-panel py-6 text-center font-mono text-[10.5px] text-paper-faint tracking-wider">
          <p>© 2026 SIGNAL STRATEGIC INTELLIGENCE ENGINE — ALL RIGHTS RESERVED</p>
        </footer>
      </body>
    </html>
  );
}
