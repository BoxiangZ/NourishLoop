"use client";

import type { ReactNode } from "react";
import type { MeRead } from "@nourishloop/api-client/schema";

export type Screen = "discover" | "workouts" | "for-you" | "history" | "community" | "rewards" | "profile";

const planItems = [
  { id: "for-you", label: "My plan", icon: "spark" },
  { id: "history", label: "Progress & history", icon: "history" },
] as const;
const exploreItems = [
  { id: "discover", label: "Discover", icon: "search" },
  { id: "workouts", label: "Workouts", icon: "workouts" },
  { id: "community", label: "Community", icon: "community" },
  { id: "rewards", label: "Rewards", icon: "rewards" },
  { id: "profile", label: "Profile", icon: "profile" },
] as const;
const items = [...planItems, ...exploreItems];

function Icon({ name }: { name: string }) {
  const path: Record<string, ReactNode> = {
    search: <><circle cx="10.8" cy="10.8" r="6.5" /><path d="m16 16 4.2 4.2" /></>,
    workouts: <><path d="M3 9v6m3-8v10m12-10v10m3-8v6M6 12h12" /></>,
    spark: <><path d="m12 2 1.8 6.2L20 10l-6.2 1.8L12 18l-1.8-6.2L4 10l6.2-1.8L12 2Z" /><path d="m19 17 .5 1.5L21 19l-1.5.5L19 21l-.5-1.5L17 19l1.5-.5L19 17Z" /></>,
    history: <><rect x="4" y="4" width="16" height="16" rx="3" /><path d="M8 9h8M8 13h8M8 17h5" /></>,
    community: <><path d="M20 11.5a7.5 7.5 0 0 1-7.5 7.5H5l1.7-3.1A7.5 7.5 0 1 1 20 11.5Z" /><path d="M8 11h8M8 14h5" /></>,
    rewards: <><rect x="4" y="10" width="16" height="10" rx="2" /><path d="M12 10v10M4 13h16M12 10c-5 0-6-2.5-4.5-4.2C9 4 11 6 12 10Zm0 0c5 0 6-2.5 4.5-4.2C15 4 13 6 12 10Z" /></>,
    profile: <><circle cx="12" cy="8" r="3.5" /><path d="M5 20a7 7 0 0 1 14 0" /></>,
  };
  return <svg viewBox="0 0 24 24" width="21" height="21" fill="none" stroke="currentColor"
    strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{path[name]}</svg>;
}

type Props = {
  screen: Screen;
  me: MeRead | null;
  onNavigate: (screen: Screen) => void;
  children: ReactNode;
};

export default function AppShell({ screen, me, onNavigate, children }: Props) {
  const initials = me?.profile.display_name.trim().slice(0, 1).toUpperCase() || "N";
  const navButton = (item: typeof items[number], compact = false) =>
    <button key={item.id} type="button" onClick={() => onNavigate(item.id)}
      className={compact ? "nl-bottom-item" : "nl-nav-item"}
      data-active={screen === item.id} aria-current={screen === item.id ? "page" : undefined}
      aria-label={item.label}>
      <Icon name={item.icon} /><span>{compact && item.id === "history" ? "Progress" : item.label}</span>
    </button>;

  return <div className="nl-app">
    <aside className="nl-sidebar">
      <button className="nl-brand" onClick={() => onNavigate("for-you")}>Nourish<span>Loop</span><i /></button>
      <nav aria-label="Main navigation" className="nl-side-nav">
        <p className="nl-side-label">PLAN</p>
        {planItems.map(item => navButton(item))}
        <p className="nl-side-label nl-side-label-secondary">EXPLORE &amp; SETTINGS</p>
        {exploreItems.map(item => navButton(item))}
      </nav>
    </aside>
    <div className="nl-workspace">
      <header className="nl-topbar">
        <button className="nl-mobile-brand" onClick={() => onNavigate("for-you")}>Nourish<span>Loop</span></button>
        <div className="nl-topbar-spacer" />
        <button className="nl-avatar" onClick={() => onNavigate("profile")} aria-label="Open profile">{initials}</button>
      </header>
      <main className="nl-main" id="main-content">{children}</main>
    </div>
    <nav className="nl-bottom-nav" aria-label="Mobile navigation">
      {items.filter(item => item.id !== "profile" && item.id !== "workouts").map(item => navButton(item, true))}
    </nav>
  </div>;
}
