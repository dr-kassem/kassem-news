import AdminShell from "@/components/admin/AdminShell";

export const metadata = {
  title: "لوحة التحكم",
  robots: { index: false, follow: false, nocache: true },
};

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return <AdminShell>{children}</AdminShell>;
}
