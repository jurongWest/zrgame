"use client";

import { useMemo, useState } from "react";
import Image from "next/image";

type Props = {
  title: string;
  items: string[];
  imageBasePath: string;
};

function shuffle<T>(arr: T[]) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function toFileKey(name: string) {
  return name.replace(/\s+/g, "").toLowerCase();
}

function ChoiceButton({
  label,
  src,
  onClick,
}: {
  label: string;
  src: string;
  onClick: () => void;
}) {
  const [loaded, setLoaded] = useState(false);

  return (
    <button
      onClick={onClick}
      style={{
        padding: 18,
        borderRadius: 14,
        fontSize: 18,
        cursor: "pointer",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 8,
      }}
    >
      <Image
        src={src}
        alt={label}
        width={120}
        height={120}
        loading="eager"
        unoptimized
        onLoad={() => setLoaded(true)}
      />

      {/* 👇 name appears ONLY after image loads */}
      {loaded && <span>{label}</span>}
    </button>
  );
}

export default function Tournament({ title, items, imageBasePath }: Props) {
  const initial = useMemo(() => shuffle(items), [items]);

  const [currentRound, setCurrentRound] = useState<string[]>(initial);
  const [nextRound, setNextRound] = useState<string[]>([]);
  const [pair, setPair] = useState<[string, string]>(() => [
    initial[0],
    initial[1],
  ]);
  const [index, setIndex] = useState(2);
  const [roundSize, setRoundSize] = useState(initial.length);
  const [winner, setWinner] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  function restart() {
    const s = shuffle(items);
    setCurrentRound(s);
    setNextRound([]);
    setPair([s[0], s[1]]);
    setIndex(2);
    setRoundSize(s.length);
    setWinner(null);
  }

  function choose(chosen: string) {
    if (winner) return;

    const updatedNext = [...nextRound, chosen];

    if (index < currentRound.length) {
      setNextRound(updatedNext);
      setPair([currentRound[index], currentRound[index + 1]]);
      setIndex(index + 2);
      return;
    }

    const shuffledWinners = shuffle(updatedNext);

    if (shuffledWinners.length === 1) {
      setWinner(shuffledWinners[0]);
      return;
    }

    setCurrentRound(shuffledWinners);
    setNextRound([]);
    setPair([shuffledWinners[0], shuffledWinners[1]]);
    setIndex(2);
    setRoundSize(shuffledWinners.length);
  }

  const totalMatches = roundSize / 2;
  const matchNumber = Math.min(Math.floor(index / 2), totalMatches);

  return (
    <main
      style={{
        maxWidth: 720,
        margin: "40px auto",
        padding: "0 16px",
        fontFamily: "system-ui",
      }}
    >
      <h1 style={{ fontSize: 32, marginBottom: 8 }}>{title}</h1>

      <div style={{ display: "flex", gap: 12, marginBottom: 16 }}>
        <button
          onClick={restart}
          style={{
            padding: "10px 14px",
            borderRadius: 10,
            border: "1px solid #333",
          }}
        >
          Restart
        </button>
      </div>

      {winner ? (
        <section
          style={{ padding: 18, border: "1px solid #eee", borderRadius: 14 }}
        >
          <h2 style={{ marginTop: 0 }}>🏆 Champion</h2>
          <div style={{ fontSize: 24, fontWeight: 700 }}>{winner}</div>
        </section>
      ) : (
        <section
          style={{ padding: 18, border: "1px solid #eee", borderRadius: 14 }}
        >
          <div style={{ marginBottom: 10, color: "#666" }}>
            Round of {roundSize} — Match {matchNumber}/{totalMatches}
          </div>

          <div
            style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}
          >
            {[pair[0], pair[1]].map((item) => {
              const src = `${imageBasePath}/${toFileKey(item)}.png`;

              return (
                <ChoiceButton
                  key={item}
                  label={item}
                  src={src}
                  onClick={() => choose(item)}
                />
              );
            })}
          </div>
        </section>
      )}
    </main>
  );
}
