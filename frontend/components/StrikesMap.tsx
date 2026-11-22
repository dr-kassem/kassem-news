"use client";

import { useEffect, useRef } from "react";
import "leaflet/dist/leaflet.css";
import type { StrikeReport } from "@/lib/types";

export default function StrikesMap({ items, height = 420 }: { items: StrikeReport[]; height?: number }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<any>(null);
  const located = items.filter((r) => typeof r.lat === "number" && typeof r.lon === "number").length;

  useEffect(() => {
    if (!containerRef.current) return;
    let cancelled = false;

    (async () => {
      const L = (await import("leaflet")).default;
      if (cancelled || !containerRef.current) return;

      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }

      const points = items
        .filter((r) => typeof r.lat === "number" && typeof r.lon === "number")
        .map((r) => [r.lat as number, r.lon as number] as [number, number]);

      const center: [number, number] = points.length
        ? [
            points.reduce((sum, p) => sum + p[0], 0) / points.length,
            points.reduce((sum, p) => sum + p[1], 0) / points.length,
          ]
        : [33.8, 35.8];

      const map = L.map(containerRef.current).setView(center, points.length ? 9 : 8);
      mapRef.current = map;

      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 18,
      }).addTo(map);

      const icon = L.divIcon({
        className: "",
        html: '<span style="display:block;width:12px;height:12px;border-radius:50%;background:#dc2626;border:2px solid #fff;box-shadow:0 0 0 2px #dc262655"></span>',
        iconSize: [12, 12],
        iconAnchor: [6, 6],
      });

      items.forEach((r) => {
        if (typeof r.lat !== "number" || typeof r.lon !== "number") return;
        const marker = L.marker([r.lat, r.lon], { icon }).addTo(map);
        const title = (r.city_name || "موقع").replace(/</g, "&lt;");
        const desc = (r.description || "").replace(/</g, "&lt;");
        marker.bindPopup(
          `<div dir="rtl" style="font-family:inherit;min-width:160px">
             <strong>${title}</strong><br/>
             <span style="font-size:12px;opacity:.8">${r.type_label}</span>
             ${desc ? `<p style="font-size:12px;margin:4px 0 0">${desc}</p>` : ""}
           </div>`,
        );
      });

      if (points.length > 1) map.fitBounds(points as any, { padding: [30, 30] });
    })();

    return () => {
      cancelled = true;
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
      }
    };
  }, [items]);

  return (
    <section className="card overflow-hidden">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-edge px-4 py-3">
        <div>
          <p className="kicker mb-0.5">الرصد الجغرافي</p>
          <h2 className="font-display text-lg font-extrabold text-ink">خريطة المواقع</h2>
        </div>
        <div className="flex flex-wrap items-center gap-3 text-[11px] text-ink-muted">
          <span className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full border-2 border-white bg-red-600 shadow" aria-hidden />
            موقع مرصود
          </span>
          <span>{located} من {items.length} بلاغات محدّدة الإحداثيات</span>
        </div>
      </div>
      <div ref={containerRef} style={{ height, width: "100%" }} />
    </section>
  );
}
