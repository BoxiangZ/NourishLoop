import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "@nourishloop/api-client";
import type { MenuLocationRead } from "@nourishloop/api-client/schema";

const NEARBY_KM = 5;
type Coordinates = Pick<MenuLocationRead, "latitude" | "longitude">;
type NearbyLocation = MenuLocationRead & { distanceKm: number };
type LocationResult =
  | { status: "idle" | "locating" | "outside" }
  | { status: "error"; message: string }
  | { status: "ready"; places: NearbyLocation[] };

function distanceKm(from: Coordinates, to: Coordinates): number {
  const radians = Math.PI / 180;
  const latitudeDelta = (to.latitude - from.latitude) * radians;
  const longitudeDelta = (to.longitude - from.longitude) * radians;
  const a = Math.sin(latitudeDelta / 2) ** 2 + Math.cos(from.latitude * radians)
    * Math.cos(to.latitude * radians) * Math.sin(longitudeDelta / 2) ** 2;
  return 6371 * 2 * Math.asin(Math.sqrt(Math.min(1, a)));
}

export default function useNearbyMenuLocations(
  onSelect: (place: MenuLocationRead) => void,
  autoLocate: boolean,
) {
  const [result, setResult] = useState<LocationResult>({ status: "idle" });
  const requestId = useRef(0);
  const invalidateRequest = useCallback(() => { requestId.current++; }, []);

  const locate = useCallback(() => {
    const id = ++requestId.current;
    if (!navigator.geolocation) {
      setResult({ status: "error", message: "Location is unavailable in this browser." });
      return;
    }
    setResult({ status: "locating" });
    navigator.geolocation.getCurrentPosition(({ coords }) => {
      if (id !== requestId.current) return;
      void api.menuLocations().then(locations => {
        if (id !== requestId.current) return;
        const places = locations.map(place => ({ ...place, distanceKm: distanceKm(coords, place) }))
          .filter(place => place.distanceKm <= NEARBY_KM)
          .sort((first, second) => first.distanceKm - second.distanceKm);
        const [closest] = places;
        if (!closest) { setResult({ status: "outside" }); return; }
        setResult({ status: "ready", places });
        onSelect(closest);
      }).catch(() => {
        if (id === requestId.current) {
          setResult({ status: "error", message: "Could not load nearby menu locations." });
        }
      });
    }, ({ code }) => {
      if (id !== requestId.current) return;
      setResult({ status: "error", message: code === 1
        ? "Location access is off. Allow it in your browser settings to use Nearby."
        : "We could not determine your location. Try again or browse by area." });
    }, { maximumAge: 60_000, timeout: 10_000 });
  }, [onSelect]);

  useEffect(() => {
    const id = requestId.current;
    if (autoLocate && navigator.permissions?.query) {
      void navigator.permissions.query({ name: "geolocation" }).then(({ state }) => {
        if (id === requestId.current && state === "granted") locate();
      }).catch(() => {});
    }
    return invalidateRequest;
  }, [autoLocate, invalidateRequest, locate]);

  function stopLocating() {
    invalidateRequest();
    setResult(current => current.status === "locating" ? { status: "idle" } : current);
  }

  return { result, locate, stopLocating };
}
