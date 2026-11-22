"use client";

import { useEffect, useState } from "react";

const KEY = (id: number) => `kassem_reactions_${id}`;

type State = { likes: number; dislikes: number; mine: "like" | "dislike" | null };

export default function Reactions({ articleId }: { articleId: number }) {
  const [state, setState] = useState<State>({ likes: 0, dislikes: 0, mine: null });
  const [ready, setReady] = useState(false);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(KEY(articleId));
      if (raw) setState(JSON.parse(raw));
    } catch {
      /* ignore */
    }
    setReady(true);
  }, [articleId]);

  function persist(next: State) {
    setState(next);
    try {
      localStorage.setItem(KEY(articleId), JSON.stringify(next));
    } catch {
      /* ignore */
    }
  }

  function vote(kind: "like" | "dislike") {
    const next = { ...state };
    if (state.mine === kind) {
      // undo
      if (kind === "like") next.likes = Math.max(0, next.likes - 1);
      else next.dislikes = Math.max(0, next.dislikes - 1);
      next.mine = null;
    } else {
      if (state.mine === "like") next.likes = Math.max(0, next.likes - 1);
      if (state.mine === "dislike") next.dislikes = Math.max(0, next.dislikes - 1);
      if (kind === "like") next.likes += 1;
      else next.dislikes += 1;
      next.mine = kind;
    }
    persist(next);
  }

  if (!ready) return null;

  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        onClick={() => vote("like")}
        aria-pressed={state.mine === "like"}
        className={`btn-ghost px-3 py-1.5 text-xs ${state.mine === "like" ? "border-brand text-brand-bright" : ""}`}
      >
        👍 {state.likes}
      </button>
      <button
        type="button"
        onClick={() => vote("dislike")}
        aria-pressed={state.mine === "dislike"}
        className={`btn-ghost px-3 py-1.5 text-xs ${state.mine === "dislike" ? "border-brand text-brand-bright" : ""}`}
      >
        👎 {state.dislikes}
      </button>
    </div>
  );
}
