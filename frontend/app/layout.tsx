import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";
import "@mantine/core/styles.css";
import "@mantine/notifications/styles.css";

import { ColorSchemeScript, MantineProvider } from "@mantine/core";
import { Notifications } from "@mantine/notifications";
import MainContainer from "@/components/MainContainer";

export const metadata: Metadata = {
  title: "Feedback-Copilot",
  description: "RAG-basierte Analyse von In-Car Kundenfeedback für VW",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="de">
      <head>
        <ColorSchemeScript />
      </head>
      <body>
        <MantineProvider>
          <MainContainer>{children}</MainContainer>
          <Notifications />
        </MantineProvider>
      </body>
    </html>
  );
}
