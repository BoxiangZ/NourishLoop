type Props = { page: number; hasNext: boolean; onChange: (page: number) => void; label: string };

export default function Pager({ page, hasNext, onChange, label }: Props) {
  return <nav className="nl-pager" aria-label={`${label} pages`}>
    <button disabled={page === 0} onClick={() => onChange(page - 1)} aria-label={`Previous ${label} page`}>← Previous</button>
    <span>Page {page + 1}</span>
    <button disabled={!hasNext} onClick={() => onChange(page + 1)} aria-label={`Next ${label} page`}>Next →</button>
  </nav>;
}
