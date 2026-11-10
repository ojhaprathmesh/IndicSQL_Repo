import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "IndicSQL Studio — Multilingual Database Intelligence",
  description:
    "Ask questions about public datasets in English, Hindi, Hinglish, Bengali, Tamil, Telugu, or Marathi. Powered by the IndicSQL query pipeline.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col font-sans bg-slate-50 text-slate-900 selection:bg-ashoka-200">
        {children}
      </body>
    </html>
  );
}
