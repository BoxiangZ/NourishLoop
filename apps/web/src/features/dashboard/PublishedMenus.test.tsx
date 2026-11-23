import { act, cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import type { MenuLocationRead } from "@nourishloop/api-client/schema";
import PublishedMenus from "./PublishedMenus";

const api = vi.hoisted(() => ({ menuLocations: vi.fn(), publishedDishes: vi.fn() }));
vi.mock("@nourishloop/api-client", () => ({ api }));

const parkCentral: MenuLocationRead = {
  id: "park-central", name: "Park Central", scope: "tko", latitude: 22.307, longitude: 114.25719,
  source_url: "https://www.openstreetmap.org/way/126689007",
};
const popcorn: MenuLocationRead = {
  id: "popcorn-2", name: "PopCorn 2", scope: "tko", latitude: 22.30863, longitude: 114.26150,
  source_url: "https://www.openstreetmap.org/way/126392613",
};

function locationBrowser(state: PermissionState, getCurrentPosition: typeof window.navigator.geolocation.getCurrentPosition) {
  const query = vi.fn().mockResolvedValue({ state });
  vi.stubGlobal("navigator", Object.create(navigator, {
    geolocation: { value: { getCurrentPosition } },
    permissions: { value: { query } },
  }));
  return query;
}

function position(latitude: number, longitude: number): GeolocationPosition {
  return { coords: { latitude, longitude, accuracy: 20,
    altitude: null, altitudeAccuracy: null, heading: null, speed: null }, timestamp: 0 } as GeolocationPosition;
}

beforeEach(() => {
  vi.clearAllMocks();
  api.menuLocations.mockResolvedValue([parkCentral, popcorn]);
  api.publishedDishes.mockResolvedValue([]);
});

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

describe("nearby menus", () => {
  it("automatically loads the nearest mall when location permission is granted", async () => {
    locationBrowser("granted", success => success(position(22.30864, 114.26151)));
    render(<PublishedMenus venue={null} />);
    const nearby = await screen.findByRole("region", { name: "Nearby menu locations" });
    const choices = within(nearby).getAllByRole("button");
    expect(choices[0].textContent).toContain("PopCorn 2");
    expect(choices[0].getAttribute("aria-pressed")).toBe("true");
    expect(api.menuLocations).toHaveBeenCalledWith();
    await waitFor(() => expect(api.publishedDishes).toHaveBeenLastCalledWith(
      expect.objectContaining({ scope: "tko", locationId: "popcorn-2" }),
    ));
    fireEvent.click(choices[1]);
    fireEvent.change(screen.getByLabelText("Search real menus"), { target: { value: "sushi" } });
    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    await waitFor(() => expect(api.publishedDishes).toHaveBeenLastCalledWith(
      expect.objectContaining({ scope: "tko", locationId: "park-central", q: "sushi" }),
    ));
  });

  it("waits for a click before requesting access and supports manual area browsing after denial", async () => {
    const locate = vi.fn<typeof window.navigator.geolocation.getCurrentPosition>((_success, error) => {
      error?.({ code: 1 } as GeolocationPositionError);
    });
    const query = locationBrowser("prompt", locate);
    render(<PublishedMenus venue={null} />);
    await waitFor(() => expect(query).toHaveBeenCalled());
    expect(locate).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Find food near me" }));
    expect(await screen.findByText(/Location access is off/)).toBeTruthy();
    expect(api.menuLocations).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: /Hang Hau/ }));
    await waitFor(() => expect(api.publishedDishes).toHaveBeenLastCalledWith(
      expect.objectContaining({ scope: "hang_hau", locationId: undefined }),
    ));
  });

  it("keeps a manual selection when a pending location fix arrives", async () => {
    let complete: PositionCallback | undefined;
    locationBrowser("granted", success => { complete = success; });
    render(<PublishedMenus venue={null} />);
    expect(await screen.findByRole("button", { name: "Finding nearby menus…" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: /Hang Hau/ }));
    act(() => complete?.(position(22.30864, 114.26151)));
    expect(api.menuLocations).not.toHaveBeenCalled();
    expect(api.publishedDishes).toHaveBeenLastCalledWith(expect.objectContaining({ scope: "hang_hau" }));
  });

  it("shows a map search when the published catalog has no nearby menus", async () => {
    locationBrowser("granted", success => success(position(22.281, 114.159)));
    render(<PublishedMenus venue={null} />);
    expect(await screen.findByText("No published menus within 5 km of your location.")).toBeTruthy();
    expect(screen.getByRole("link", { name: /Search nearby food on Google Maps/ })).toBeTruthy();
    expect(api.publishedDishes).toHaveBeenCalledTimes(1);
  });
});
