"""Small, attributed venue directory verified against official listings on 2026-10-28.

These are places, not verified menus. Do not infer dishes, prices or nutrition from them.
External notes paraphrase linked public discussions and are not NourishLoop user posts.
"""

from datetime import date

CHECKED_AT = date(2026, 10, 28)
HKUST_SOURCE = "https://cso.hkust.edu.hk/locations/restaurants"
LOHAS_SOURCE = "https://www.thelohasmall.com/en/search-result?tag=Dining"

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
