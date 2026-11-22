"use client";

import { useEffect, useState } from "react";

export default function ListenButton({ text }: { text: string }) {
  const [supported, setSupported] = useState(false);
  const [speaking, setSpeaking] = useState(false);

  useEffect(() => {
    setSupported(typeof window !== "undefined" && "speechSynthesis" in window);
    return () => {
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  if (!supported || !text) return null;

  function toggle() {
    const synth = window.speechSynthesis;
    if (speaking) {
      synth.cancel();
      setSpeaking(false);
      return;
    }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "ar-SA";
    utterance.rate = 0.95;
    const voices = synth.getVoices();
    const ar = voices.find((v) => v.lang.toLowerCase().startsWith("ar"));
    if (ar) utterance.voice = ar;
    utterance.onend = () => setSpeaking(false);
    utterance.onerror = () => setSpeaking(false);
    setSpeaking(true);
    synth.speak(utterance);
  }

  return (
    <button
      type="button"
      onClick={toggle}
      aria-pressed={speaking}
      className="btn-ghost px-3 py-1.5 text-xs"
      title={speaking ? "إيقاف الاستماع" : "استمع للمقال"}
    >
      {speaking ? "⏹ إيقاف" : "🔊 استمع"}
    </button>
  );
}
