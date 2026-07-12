import type { ReactNode } from "react";
import Link from "next/link";

export const metadata = {
  title: "Teodora Pălii | Dietetician",
  description:
    "Consultații de nutriție, planuri alimentare și calculator gratuit de nutrienți bazat pe surse europene.",
};

const navLinkStyle = {
  color: "#26352f",
  fontSize: 14,
  fontWeight: 600,
  textDecoration: "none",
} as const;

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="ro">
      <body
        style={{
          margin: 0,
          backgroundColor: "#f7f5ef",
          color: "#17211d",
          fontFamily:
            'Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        }}
      >
        <header
          style={{
            position: "sticky",
            top: 0,
            zIndex: 20,
            borderBottom: "1px solid rgba(38, 53, 47, 0.12)",
            backgroundColor: "rgba(247, 245, 239, 0.94)",
            backdropFilter: "blur(14px)",
          }}
        >
          <nav
            style={{
              alignItems: "center",
              display: "flex",
              gap: 24,
              justifyContent: "space-between",
              margin: "0 auto",
              maxWidth: 1180,
              padding: "16px 24px",
            }}
          >
            <Link
              href="/"
              style={{
                color: "#17211d",
                fontSize: 18,
                fontWeight: 800,
                textDecoration: "none",
              }}
            >
              Teodora Pălii
            </Link>

            <div
              style={{
                alignItems: "center",
                display: "flex",
                flexWrap: "wrap",
                gap: 18,
                justifyContent: "flex-end",
              }}
            >
              <Link href="/calculator" style={navLinkStyle}>
                Calculator
              </Link>
              <Link href="/foods" style={navLinkStyle}>
                Bază de date
              </Link>
              <Link href="/#servicii" style={navLinkStyle}>
                Servicii
              </Link>
              <Link href="/#blog" style={navLinkStyle}>
                Blog
              </Link>
              <Link
                href="/#contact"
                style={{
                  ...navLinkStyle,
                  border: "1px solid #2d5f4c",
                  borderRadius: 8,
                  padding: "9px 14px",
                }}
              >
                Programează-te
              </Link>
            </div>
          </nav>
        </header>
        {children}
      </body>
    </html>
  );
}
