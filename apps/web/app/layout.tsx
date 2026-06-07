import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AlphaMomentum Daily 5",
  description: "Daily swing-trading recommendation dashboard",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
