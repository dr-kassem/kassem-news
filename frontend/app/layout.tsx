import type { Metadata } from "next";
import { Amiri, IBM_Plex_Sans_Arabic } from "next/font/google";
import "./globals.css";

const plexArabic = IBM_Plex_Sans_Arabic({
  subsets: ["arabic", "latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-sans",
  display: "swap",
});

const amiri = Amiri({
  subsets: ["arabic", "latin"],
  weight: ["400", "700"],
  variable: "--font-display",
  display: "swap",
});

export const metadata: Metadata = {
  metadataBase: new URL(process.env.SITE_URL || "https://kassem.news"),
  title: {
    default: "قاسم نيوز | العالم في الصورة الكاملة",
    template: "%s | قاسم نيوز",
  },
  description:
    "قاسم نيوز — منصة إخبارية رقمية عالمية بتغطية موسّعة للبنان والشرق الأوسط، أخبار عاجلة وتحليلات ومتابعة مباشرة للأحداث.",
  keywords: ["أخبار", "لبنان", "الشرق الأوسط", "عالم", "سياسة", "اقتصاد", "عاجل"],
  openGraph: {
    type: "website",
    locale: "ar_SA",
    siteName: "قاسم نيوز",
    title: "قاسم نيوز | العالم في الصورة الكاملة",
    description: "تغطية إخبارية عالمية مع تركيز خاص على لبنان والشرق الأوسط.",
  },
  twitter: { card: "summary_large_image" },
  icons: { icon: "/icon.svg", apple: "/icon.svg" },
  robots: { index: true, follow: true },
};

const themeScript = `(function(){try{if(localStorage.getItem("theme")==="dark"){document.documentElement.classList.add("dark")}}catch(e){}})();`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="ar"
      dir="rtl"
      suppressHydrationWarning
      className={`${plexArabic.variable} ${amiri.variable}`}
    >
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeScript }} />
      </head>
      <body className="min-h-screen bg-base text-ink font-sans">{children}</body>
    </html>
  );
}
