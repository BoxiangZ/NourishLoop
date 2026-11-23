"""Attributed venue directory and public discussion summaries.

These are places, not verified menus. Do not infer dishes, prices or nutrition from them.
External notes paraphrase linked public discussions and are not NourishLoop user posts.
"""

from datetime import date

CHECKED_AT = date(2026, 10, 28)
LOCAL_CHECKED_AT = date(2026, 11, 22)
HKUST_SOURCE = "https://cso.hkust.edu.hk/locations/restaurants"
LOHAS_SOURCE = "https://www.thelohasmall.com/en/search-result?tag=Dining"
FAIRWOOD_STORES = "https://www.fairwood.com.hk/en/stores?tab=map"
SAIZERIYA_STORES = "https://www.saizeriya.com.hk/shop-info/"
PARK_CENTRAL = "https://www.park-central.com.hk/en/en-dining/"
EAST_POINT_CITY = "https://www.eastpointcity.com.hk/en/dining/"
VILLAGE_PRODUCT = (
    "https://www.7-eleven.com.hk/sites/default/files/assets/"
    "KiKi%E6%A4%92%E9%A6%99%E9%BA%BB%E9%86%AC%E6%8B%8C%E9%BA%B5"
    "%E9%8A%B7%E5%94%AE%E5%BA%97%E8%88%96%E5%9C%B0%E5%9D%80.pdf"
)

# name, location. The source URL is the official operator's current directory.
HKUST_VENUES = [
    ("China Garden", "G/F, Academic Building"),
    ("Can.teen II", "LG1, Academic Building"),
    ("McDonald's", "LG5, Academic Building"),
    ("McCafé", "LG5, Academic Building"),
    ("Asia Pacific Catering", "LG7 Kitchen 1, Academic Building"),
    ("Gold Rice Bowl", "LG7 Kitchen 2, Academic Building"),
    ("TamJai SamGor", "LG7 Kitchen 3, Academic Building"),
    ("Oliver's Super Sandwiches", "LG7 Kitchen 4, Academic Building"),
    ("UniVeggie & This This Rice", "LG5, Academic Building"),
    ("Passion", "1/F Concourse, Academic Building"),
    ("JoA", "1/F Concourse, Academic Building"),
    ("American Diner", "1/F Concourse, Academic Building"),
    ("Diners @LSKBB", "G/F, Lee Shau Kee Business Building"),
    ("Pacific Coffee", "G/F, Lee Shau Kee Business Building"),
    ("Ebeneezer's", "G/F, Lee Shau Kee Business Building"),
]

LOHAS_VENUES = [
    ("Eiraku Japanese Restaurant", "353A, L3"),
    ("A HAYA", "344, L3"),
    ("Asam Chicken Rice", "428, L4"),
    ("BEANS BAKERY", "319, L3"),
    ("Cafe de Coral", "205A, L2"),
    ("Genki Sushi", "421, L4"),
    ("KFC", "423, L4"),
    ("luckin coffee", "347, L3"),
    ("McDonald's", "431, L4"),
    ("Men Wah Bing Teng", "354, L3"),
    ("Nabe Urawa", "305, L3"),
    ("On Laan by Red Object", "353B, L3"),
    ("Pizza Hut", "203A, L2"),
    ("Praise House Congee & Noodle Cuisine", "203, L2"),
    ("Starbucks", "343, L3"),
    ("Tai Hing", "402, L4"),
    ("TamJai Yunnan Mixian", "424-425, L4"),
    ("Tengachaya", "306, L3"),
    ("Tin Hau Station Beef Brisket", "422, L4"),
    ("TOKENYO Korean BBQ Cuisine", "334, L3"),
]

# scope, display name and disambiguating branch location, venue source.
LOCAL_VENUES = [
    ("hkust", "Donburi Bowl", "2/F Concourse, Academic Building", HKUST_SOURCE),
    ("hkust", "WeBite Space", "G/F, Lee Shau Kee Business Building", HKUST_SOURCE),
    ("hkust", "HFT Life", "G/F, The Shaw Auditorium", HKUST_SOURCE),
    ("hkust", "Starbucks", "The Hong Kong Jockey Club Atrium", HKUST_SOURCE),
    ("hkust", "Subway", "G/F, Cheng Yu Tung Building", HKUST_SOURCE),
    ("hkust", "UniBistro & The UniBar", "G/F, Lo Ka Chung University Center", HKUST_SOURCE),
    ("hkust", "UniQue", "2/F, Conference Lodge", HKUST_SOURCE),
    ("hkust", "Seafront Cafeteria", "G/F, Hall VI", HKUST_SOURCE),
    ("hkust", "Nourish N' Go Green", "LG/F, Martin Ka Shing Lee Innovation Building", HKUST_SOURCE),
    ("hkust", "Hana-musubi", "UG/F, Cheng Yu Tung Building", HKUST_SOURCE),
    ("tko", "Café de Coral · PopCorn 2", "G50A, PopCorn 2, Tseung Kwan O",
     "https://www.popcorntko.com.hk/en/dining/blt3ca5fb316bc4cfa4"),
    ("tko", "Fairwood · Park Central", "B12–13, B1/F, Park Central", PARK_CENTRAL),
    ("tko", "Genki Sushi · Park Central", "118–120, 1/F, Park Central", PARK_CENTRAL),
    ("tko", "TamJai SamGor · Park Central", "B03A, Park Central", PARK_CENTRAL),
    ("tko", "Fairwood · MCP Discovery", "204 & 207A, 2/F, Metro City Phase I, Po Lam",
     FAIRWOOD_STORES),
    ("tko", "Fairwood · Metro Town", "R02, 2/F, Metro Town, Tiu Keng Leng", FAIRWOOD_STORES),
    ("tko", "Fairwood · Bauhinia Garden", "G/F, 11 Tong Chun Street", FAIRWOOD_STORES),
    ("tko", "Saizeriya · TKO Plaza", "L207, 2/F, AEON, Tseung Kwan O Plaza", SAIZERIYA_STORES),
    ("tko", "Saizeriya · TKO Spot", "117, 1/F, Sheung Tak Shopping Centre", SAIZERIYA_STORES),
    ("tko", "Saizeriya · MCP Central", "Metro City Plaza, Po Lam", SAIZERIYA_STORES),
    ("tko", "Soup Plus · PopWalk", "G08, PopWalk, 12 Tong Chun Street",
     "https://www.popwalk.com.hk/sc/shop-and-restaurant/restaurant"),
    ("hang_hau", "Genki Sushi · East Point City", "275A, 2/F, East Point City", EAST_POINT_CITY),
    ("hang_hau", "Fairwood · The Lane", "111, 1/F, The Lane, Hang Hau", FAIRWOOD_STORES),
    ("hang_hau", "Taiwan Bowl · TKO Gateway", "W006–W007, G/F, West Wing, TKO Gateway",
     "https://www.openrice.com/en/hongkong/r-taiwan-bowl-tseung-kwan-o-taiwan-r639110"),
    ("tai_po_tsai", "7-Eleven · Tai Po Tsai",
     "G/F & 1/F, 1 Tai Po Tsai Village, Clear Water Bay Road", VILLAGE_PRODUCT),
    ("tai_po_tsai", "Green Field Cafe · 大埔仔茶餐廳",
     "G/F, 16 Tai Po Tsai Village, Clear Water Bay Road",
     "https://es.restaurantguru.com/Green-Field-Cafe-Hong-Kong"),
]

# scope, title, original summary, source platform, direct discussion URL.
PUBLIC_DISCUSSIONS = [
    (
        "hkust", "What students say about meal budgets",
        "In a public HKUST discussion, students described many campus meals as roughly "
        "HK$30–50. This is a personal estimate, not an official menu price.",
        "Reddit",
        "https://www.reddit.com/r/HKUST/comments/1kbka12/",
    ),
    (
        "hkust", "A student view of campus meals",
        "A commenter preferred campus lunch and dinner options to breakfast and mentioned "
        "the LG1 afternoon tea. This is one person's opinion, not a venue rating.",
        "Reddit",
        "https://www.reddit.com/r/HongKong/comments/17u1ns7/",
    ),
    (
        "lohas", "Food choice around LOHAS Park",
        "Residents in a public thread said that dining choices are concentrated in THE LOHAS mall "
        "and some wished for more variety. These are individual opinions.",
        "Reddit",
        "https://www.reddit.com/r/Hong_Kong/comments/1wkplxy/",
    ),
    (
        "lohas", "Local views on the mall",
        "A public discussion mentions familiar chains and some Japanese restaurants in the mall, "
        "while opinions on the overall selection differ.",
        "Reddit",
        "https://www.reddit.com/r/HongKong/comments/1ssqokr/",
    ),
]
