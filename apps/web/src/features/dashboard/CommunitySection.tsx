"use client";

import { useState } from "react";
import { api } from "@nourishloop/api-client";
import type {
  CommunityPostRead, CommunityReportRead, MealLogRead,
} from "@nourishloop/api-client/schema";
import Pager from "./Pager";
import LocalReviews from "./LocalReviews";

type Props = {
  posts: CommunityPostRead[];
  mealLogs: MealLogRead[];
  sharedMealLogIds: string[];
  reports: CommunityReportRead[];
  isModerator: boolean;
  busy: boolean;
  onAction: (action: () => Promise<unknown>) => Promise<boolean>;
  page: number;
  hasNext: boolean;
  onPageChange: (page: number) => void;
};

export default function CommunitySection({
  posts, mealLogs, sharedMealLogIds, reports, isModerator, busy, onAction,
  page, hasNext, onPageChange,
}: Props) {
  const [caption, setCaption] = useState("");
  const [shareMealId, setShareMealId] = useState("");
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [reportReasons, setReportReasons] = useState<Record<string, "spam" | "harassment" | "misinformation" | "other">>({});
  const [reportedPostIds, setReportedPostIds] = useState<string[]>([]);
  const [mode, setMode] = useState<"posts" | "reviews">("posts");
  const unshared = mealLogs.filter(log => !sharedMealLogIds.includes(log.id));

  return <>
    <div className="nl-page-intro"><span className="nl-eyebrow">COMMUNITY / SHARE</span>
      <h1>Good food, better together<span className="nl-orange-dot">.</span></h1>
      <p>Browse local dining experiences or share a meal you tried.</p></div>
    <div className="nl-discover-tabs" role="tablist" aria-label="Community view">
      <button id="community-posts-tab" role="tab" aria-selected={mode === "posts"}
        aria-controls="community-posts" onClick={() => setMode("posts")}>Member posts</button>
      <button id="local-reviews-tab" role="tab" aria-selected={mode === "reviews"}
        aria-controls="local-reviews" onClick={() => setMode("reviews")}>Local reviews</button>
    </div>
    {mode === "reviews" ? <LocalReviews /> :
    <section id="community-posts" role="tabpanel" aria-labelledby="community-posts-tab">
    <form className="nl-composer" onSubmit={event => {
      event.preventDefault();
      if (!shareMealId || !caption.trim()) return;
      void onAction(() => api.shareMeal({ meal_log_id: shareMealId, caption: caption.trim() }))
        .then(ok => { if (ok) { setCaption(""); setShareMealId(""); onPageChange(0); } });
    }}>
      <span className="nl-composer-icon">✦</span>
      <div className="nl-composer-content"><strong>Share a meal you enjoyed</strong>
        <p>Only confirmed meals can be shared. Your post is visible to this local demo community.</p>
        {unshared.length ? <div className="nl-composer-fields">
          <select aria-label="Confirmed meal to share" required value={shareMealId}
            onChange={event => setShareMealId(event.target.value)}>
            <option value="">Choose a confirmed meal</option>
            {unshared.map(log => <option key={log.id} value={log.id}>{log.menu_item.name}</option>)}
          </select>
          <input aria-label="Community caption" required maxLength={500} value={caption}
            onChange={event => setCaption(event.target.value)}
            placeholder="What would you say about it?" />
          <button className="nl-button nl-button-primary" disabled={busy}>Share meal</button>
        </div> : <p className="nl-composer-hint">Confirm a menu meal in My plan to share it here.</p>}
      </div>
    </form>

    {isModerator && <section className="nl-moderator"><div className="nl-section-heading"><div>
      <span className="nl-eyebrow">COMMUNITY CARE</span><h2>Moderator queue</h2></div>
      <span className="nl-count-pill">{reports.length} pending</span></div>
      {reports.length ? <div className="nl-report-list">{reports.map(report => <article key={report.id} className="nl-report-card">
        <strong>{report.post_author}: {report.post_caption}</strong>
        <p>Reported for {report.reason}{report.detail ? ` · ${report.detail}` : ""}</p>
        <div><button disabled={busy} onClick={() => void onAction(() => api.resolveReport(report.id, { action: "dismiss" }))}>Dismiss</button>
          <button disabled={busy} onClick={() => void onAction(() => api.resolveReport(report.id, { action: "remove" }))}>Remove post</button></div>
      </article>)}</div> : <p className="nl-muted">No pending reports.</p>}</section>}

    <div className="nl-section-heading"><div><span className="nl-eyebrow">THE CONVERSATION</span>
      <h2>From the community</h2></div><span className="nl-section-caption">Page {page + 1}</span></div>
    {posts.length ? <div className="nl-post-list">{posts.map(post => <article key={post.id} className="nl-post-card">
      <header><span className="nl-mini-avatar">{post.author_display_name.slice(0, 1)}</span>
        <div><strong>{post.author_display_name}</strong><small>{new Date(post.created_at).toLocaleDateString()}</small></div>
        {post.is_mine && <span className="nl-your-post">Your post</span>}</header>
      <h3>{post.meal.menu_item.name}</h3>
      <p className="nl-post-caption">{post.caption}</p>
      <p className="nl-post-nutrition">≈ {post.meal.nutrition.calories_kcal} kcal · illustrative estimate</p>
      <div className="nl-post-actions">
        <button disabled={busy} onClick={() => void onAction(() =>
          post.liked_by_me ? api.unlikePost(post.id) : api.likePost(post.id))}>
          {post.liked_by_me ? "♥" : "♡"} {post.liked_by_me ? "Unlike" : "Like"} · {post.like_count}
        </button>
        {post.is_mine && <button disabled={busy} onClick={() => void onAction(() => api.deletePost(post.id))}>Remove my post</button>}
      </div>
      {post.comments.length > 0 && <ul className="nl-comment-list">{post.comments.map(comment => <li key={comment.id}>
        <span className="nl-mini-avatar">{comment.author_display_name.slice(0, 1)}</span>
        <div><strong>{comment.author_display_name}</strong><p>{comment.body}</p></div>
        {(comment.is_mine || isModerator) && <button disabled={busy}
          onClick={() => void onAction(() => api.deleteComment(comment.id))}>Remove comment</button>}
      </li>)}</ul>}
      <form className="nl-comment-form" onSubmit={event => {
        event.preventDefault();
        const body = drafts[post.id]?.trim();
        if (!body) return;
        void onAction(() => api.comment(post.id, { body })).then(ok => {
          if (ok) setDrafts(current => ({ ...current, [post.id]: "" }));
        });
      }}>
        <input aria-label={"Comment on " + post.meal.menu_item.name} value={drafts[post.id] ?? ""}
          onChange={event => setDrafts(current => ({ ...current, [post.id]: event.target.value }))}
          maxLength={500} required placeholder="Add a thoughtful comment" />
        <button disabled={busy}>Comment</button>
      </form>
      {!post.is_mine && <div className="nl-report-action">
        <select aria-label={"Report reason for " + post.meal.menu_item.name}
          value={reportReasons[post.id] ?? "spam"}
          onChange={event => setReportReasons(current => ({
            ...current, [post.id]: event.target.value as "spam" | "harassment" | "misinformation" | "other",
          }))}>
          <option value="spam">Spam</option><option value="harassment">Harassment</option>
          <option value="misinformation">Misinformation</option><option value="other">Other</option>
        </select>
        <button disabled={busy || reportedPostIds.includes(post.id)}
          onClick={() => void onAction(() => api.reportPost(post.id, {
            reason: reportReasons[post.id] ?? "spam",
          })).then(ok => { if (ok) setReportedPostIds(ids => [...ids, post.id]); })}>
          {reportedPostIds.includes(post.id) ? "Reported" : "Report post"}
        </button>
      </div>}
    </article>)}</div> : <div className="nl-empty">No meals shared on this page yet. Be the first to start a conversation.</div>}
    <Pager page={page} hasNext={hasNext} onChange={onPageChange} label="community" />
    </section>}
  </>;
}
