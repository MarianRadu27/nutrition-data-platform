import type { ReactNode } from "react";
import Link from "next/link";

export const metadata = {
  title: "Nutrition Data Platform",
  description: "Food data browser, meal calculator, and nutrition data tools",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, fontFamily: "sans-serif" }}>
        <header
          style={{
            borderBottom: "1px solid #ddd",
            padding: "12px 16px",
            display: "flex",
            gap: 16,
          }}
        >
          <Link href="/">Home</Link>
          <Link href="/foods">Foods</Link>
          <Link href="/calculator">Calculator</Link>
        </header>
        {children}
      </body>
    </html>
  );
}
