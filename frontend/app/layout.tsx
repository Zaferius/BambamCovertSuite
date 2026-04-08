import "./globals.css";

import type { Metadata } from "next";
import { Bitter } from "next/font/google";
import { AuthProvider } from "./lib/auth-context";
import { ActionProvider } from "./lib/action-context";

const bitter = Bitter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Bambam Converter Suite",
  description: "A powerful, self-hosted media conversion tool.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={bitter.className}>
        <AuthProvider>
          <ActionProvider>
            {children}
          </ActionProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
