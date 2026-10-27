import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "NourishLoop",
  description: "Demo meal decisions for a healthier routine",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
