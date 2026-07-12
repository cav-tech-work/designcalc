import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "DesignCalc — flat-ground d&b system designer",
  description:
    "Enter a flat, rectangular venue's dimensions and get a house-style d&b sound system design as a top-down plan and a downloadable ArrayCalc .dbpr file.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
