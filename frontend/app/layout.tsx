import "./globals.css";

import type { Metadata } from "next";
import type { ReactNode } from "react";


export const metadata: Metadata = {
  title: "Bambam Converter Suite Web",
  description: "Phase 1 web shell for the self-hosted Bambam Converter Suite.",
};


export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
