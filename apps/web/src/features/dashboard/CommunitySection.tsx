"use client";

import { useState } from "react";
import { api } from "@nourishloop/api-client";
import type {
  CommunityPostRead, CommunityReportRead, MealLogRead,
} from "@nourishloop/api-client/schema";

type Props = {
  posts: CommunityPostRead[];
  mealLogs: MealLogRead[];
  sharedMealLogIds: string[];
  reports: CommunityReportRead[];
  isModerator: boolean;
  busy: boolean;
  onAction: (action: () => Promise<unknown>) => Promise<boolean>;
  onLoadMore: () => void;
};

export default function CommunitySection({
  posts, mealLogs, sharedMealLogIds, reports, isModerator, busy, onAction, onLoadMore,
}: Props) {
  const [caption, setCaption] = useState("");
  const [shareMealId, setShareMealId] = useState("");
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [reportReasons, setReportReasons] = useState<Record<string, "spam" | "harassment" | "misinformation" | "other">>({});
  const [reportedPostIds, setReportedPostIds] = useState<string[]>([]);
  const unshared = mealLogs.filter(log => !sharedMealLogIds.includes(log.id));

  return <section className="mt-10 rounded-2xl bg-white p-6 shadow-sm">
    <h2 className="text-2xl font-bold">Community</h2>
    <p className="mt-2 text-sm text-slate-600">Share a confirmed meal with the community. Posting is always your choice.</p>
    {unshared.length > 0 && <form className="mt-5 flex flex-wrap gap-3" onSubmit={event => {
      event.preventDefault();
      if (!shareMealId || !caption.trim()) return;
      void onAction(() => api.shareMeal({ meal_log_id: shareMealId, caption: caption.trim() }))
        .then(ok => { if (ok) { setCaption(""); setShareMealId(""); } });
    }}>
      <select aria-label="Confirmed meal to share" required value={shareMealId}
        onChange={event => setShareMealId(event.target.value)}
        className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
        <option value="">Choose a confirmed meal</option>
        {unshared.map(log => <option key={log.id} value={log.id}>{log.menu_item.name}</option>)}
      </select>
      <input aria-label="Community caption" required maxLength={500} value={caption}
        onChange={event => setCaption(event.target.value)}
        placeholder="What would you say about it?"
        className="min-w-56 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm" />
      <button disabled={busy} className="rounded-full bg-emerald-700 px-5 py-2 text-sm font-semibold text-white disabled:opacity-50">Share meal</button>
    </form>}
    {posts.length === 0 ? <p className="mt-5 text-sm text-slate-500">No meals shared yet.</p> :
      <ul className="mt-5 grid gap-4 sm:grid-cols-2">{posts.map(post => <li key={post.id} className="rounded-xl border border-slate-200 p-4">
        <p className="text-xs font-semibold text-emerald-700">{post.author_display_name} · {new Date(post.created_at).toLocaleString()}</p>
        <h3 className="mt-2 font-bold">{post.meal.menu_item.name}</h3>
        <p className="mt-2 text-sm text-slate-700">{post.caption}</p>
        <p className="mt-2 text-xs text-slate-500">≈ {post.meal.nutrition.calories_kcal} kcal · illustrative estimate</p>
        <div className="mt-3 flex flex-wrap items-center gap-3">
          <button disabled={busy} onClick={() => void onAction(() =>
            post.liked_by_me ? api.unlikePost(post.id) : api.likePost(post.id))}
            className="text-xs font-semibold text-emerald-700">
            {post.liked_by_me ? "Unlike" : "Like"} · {post.like_count}
          </button>
          {post.is_mine && <button disabled={busy} onClick={() => void onAction(() => api.deletePost(post.id))}
            className="text-xs font-semibold text-red-700">Remove my post</button>}
        </div>
        <ul className="mt-4 space-y-2">{post.comments.map(comment => <li key={comment.id} className="rounded-lg bg-slate-50 p-2 text-sm">
          <strong>{comment.author_display_name}</strong> {comment.body}
          {(comment.is_mine || isModerator) && <button disabled={busy}
            onClick={() => void onAction(() => api.deleteComment(comment.id))}
            className="ml-2 text-xs text-red-700">Remove comment</button>}
        </li>)}</ul>
        <form className="mt-3 flex gap-2" onSubmit={event => {
          event.preventDefault();
          const body = drafts[post.id]?.trim();
          if (!body) return;
          void onAction(() => api.comment(post.id, { body })).then(ok => {
            if (ok) setDrafts(current => ({ ...current, [post.id]: "" }));
          });
        }}>
          <input aria-label={"Comment on " + post.meal.menu_item.name} value={drafts[post.id] ?? ""}
            onChange={event => setDrafts(current => ({ ...current, [post.id]: event.target.value }))}
            maxLength={500} required placeholder="Add a comment"
            className="min-w-0 flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm" />
          <button disabled={busy} className="text-xs font-semibold text-emerald-700">Comment</button>
        </form>
        {!post.is_mine && <div className="mt-3 flex gap-2">
          <select aria-label={"Report reason for " + post.meal.menu_item.name}
            value={reportReasons[post.id] ?? "spam"}
            onChange={event => setReportReasons(current => ({
              ...current, [post.id]: event.target.value as "spam" | "harassment" | "misinformation" | "other",
            }))} className="rounded-lg border border-slate-300 px-2 py-1 text-xs">
            <option value="spam">Spam</option><option value="harassment">Harassment</option>
            <option value="misinformation">Misinformation</option><option value="other">Other</option>
          </select>
          <button disabled={busy || reportedPostIds.includes(post.id)} onClick={() => void onAction(() => api.reportPost(post.id, {
            reason: reportReasons[post.id] ?? "spam",
          })).then(ok => { if (ok) setReportedPostIds(ids => [...ids, post.id]); })}
            className="text-xs font-semibold text-red-700">{reportedPostIds.includes(post.id) ? "Reported" : "Report post"}</button>
        </div>}
      </li>)}</ul>}
    {posts.length >= 20 && <button disabled={busy} onClick={onLoadMore}
      className="mt-5 text-sm font-semibold text-emerald-700">Load more posts</button>}
    {isModerator && <div className="mt-8 border-t border-slate-200 pt-5">
      <h3 className="text-lg font-semibold">Moderator queue</h3>
      {reports.length === 0 ? <p className="mt-2 text-sm text-slate-500">No pending reports.</p> :
        <ul className="mt-3 space-y-3">{reports.map(report => <li key={report.id} className="rounded-lg bg-amber-50 p-3 text-sm">
          <p className="font-semibold">{report.post_author}: {report.post_caption}</p>
          <p className="mt-1 text-xs">Reason: {report.reason}{report.detail ? " · " + report.detail : ""}</p>
          <div className="mt-2 flex gap-4">
            <button disabled={busy} onClick={() => void onAction(() => api.resolveReport(report.id, { action: "dismiss" }))}
              className="font-semibold text-emerald-700">Dismiss</button>
            <button disabled={busy} onClick={() => void onAction(() => api.resolveReport(report.id, { action: "remove" }))}
              className="font-semibold text-red-700">Remove post</button>
          </div>
        </li>)}</ul>}
    </div>}
  </section>;
}
