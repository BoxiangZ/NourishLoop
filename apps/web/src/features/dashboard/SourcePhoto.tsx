"use client";

import Image from "next/image";
import { useState } from "react";
import type { SourcePhotoRead } from "@nourishloop/api-client/schema";

export default function SourcePhoto({ photo, variant = "card" }: {
  photo: SourcePhotoRead;
  variant?: "card" | "workout" | "facility";
}) {
  const [failedUrl, setFailedUrl] = useState<string>();
  const unavailable = failedUrl === photo.url;

  return <figure className={`nl-source-photo nl-source-photo-${variant}`}>
    {!unavailable && <Image src={photo.url} alt={photo.alt} width={480} height={320}
      unoptimized loading="lazy" referrerPolicy="no-referrer" onError={() => setFailedUrl(photo.url)} />}
    <figcaption><a href={photo.source_url} target="_blank" rel="noreferrer">
      {unavailable ? "View image at source" : photo.credit} ↗
    </a></figcaption>
  </figure>;
}
