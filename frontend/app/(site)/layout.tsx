import AssistantWidget from "@/components/AssistantWidget";
import AutoRefresh from "@/components/AutoRefresh";
import BreakingTicker from "@/components/BreakingTicker";
import SiteFooter from "@/components/SiteFooter";
import SiteHeader from "@/components/SiteHeader";
import UtilityBar from "@/components/UtilityBar";
import { api } from "@/lib/api";

export default async function SiteLayout({ children }: { children: React.ReactNode }) {
  const breaking = (await api.breaking()) || [];
  return (
    <>
      <AutoRefresh />
      <UtilityBar />
      <SiteHeader />
      <BreakingTicker items={breaking} />
      <main className="container-page py-6">{children}</main>
      <SiteFooter />
      <AssistantWidget />
    </>
  );
}
