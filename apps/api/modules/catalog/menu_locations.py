"""OpenStreetMap landmarks for sites with sourced menu entries."""

from dataclasses import dataclass

from apps.api.modules.catalog.schemas import FoodArea

OSM = "https://www.openstreetmap.org/"


@dataclass(frozen=True)
class MenuLocation:
    id: str
    name: str
    scope: FoodArea
    latitude: float
    longitude: float
    source_url: str
    branches: tuple[str, ...] = ()


MENU_LOCATIONS = {location.id: location for location in (
    MenuLocation("hkust-campus", "HKUST campus", "hkust", 22.33872, 114.26190,
                 OSM + "node/4353417424"),
    MenuLocation("tai-po-tsai", "Tai Po Tsai Village · 大埔仔村", "tai_po_tsai",
                 22.33627, 114.25952, OSM + "node/2723599935"),
    MenuLocation("the-lohas", "THE LOHAS · 康城", "lohas", 22.29482, 114.26996,
                 OSM + "way/607534710"),
    MenuLocation("east-point-city", "East Point City · 東港城", "hang_hau", 22.31639, 114.26548,
                 OSM + "way/28125742", ("Genki Sushi · East Point City",)),
    MenuLocation("the-lane", "The Lane · 連理街", "hang_hau", 22.31598, 114.26422,
                 OSM + "node/3183946464", ("Fairwood · The Lane",)),
    MenuLocation("park-central", "Park Central · 將軍澳中心", "tko", 22.30700, 114.25719,
                 OSM + "way/126689007", ("Fairwood · Park Central", "Genki Sushi · Park Central",
                                         "TamJai SamGor · Park Central")),
    MenuLocation("popcorn-2", "PopCorn 2", "tko", 22.30863, 114.26150,
                 OSM + "way/126392613", ("Café de Coral · PopCorn 2",)),
    MenuLocation("popwalk", "PopWalk · 天晉滙", "tko", 22.30631, 114.26081,
                 OSM + "way/242553900", ("Soup Plus · PopWalk",)),
    MenuLocation("tko-plaza", "TKO Plaza · 將軍澳廣場", "tko", 22.30893, 114.26260,
                 OSM + "way/28104309", ("Saizeriya · TKO Plaza",)),
    MenuLocation("tko-spot", "TKO Spot · 尚德廣場", "tko", 22.31099, 114.25883,
                 OSM + "way/28104224", ("Saizeriya · TKO Spot",)),
    MenuLocation("mcp-discovery", "MCP Discovery · 新都城一期", "tko", 22.32122, 114.25726,
                 OSM + "way/302740028", ("Fairwood · MCP Discovery",)),
    MenuLocation("mcp-central", "MCP Central · 新都城二期", "tko", 22.32321, 114.25825,
                 OSM + "way/302740025", ("Saizeriya · MCP Central",)),
    MenuLocation("metro-town", "Metro Town · 都會駅", "tko", 22.30436, 114.25200,
                 OSM + "way/27993207", ("Fairwood · Metro Town",)),
    MenuLocation("bauhinia-garden", "Bauhinia Garden · 寶盈花園", "tko", 22.30621, 114.26227,
                 OSM + "way/28104191", ("Fairwood · Bauhinia Garden",)),
)}
