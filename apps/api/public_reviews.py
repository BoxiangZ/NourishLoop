"""Short, attributed summaries of public diner reviews and local discussions."""

REDDIT = "https://www.reddit.com"
OPENRICE = "https://www.openrice.com"
OPENRICE_REVIEW = OPENRICE + "/zh/hongkong/review/"

# Keep a summary of what the diner reported, without importing the author's profile or rating.
LOCAL_FOOD_REVIEWS = [
    (
        "hkust", "Eating at the canteen on a student budget",
        "In an exchange student thread, one reply described their canteen meal as filling and "
        "recalled many campus options costing under HK$50.",
        "Reddit", REDDIT + "/r/HKUST/comments/1wn3wxi/hi_everyone/",
    ),
    (
        "hkust", "Late dinners at LG7 and Seafront",
        "A student who sometimes ate late at LG7 or Seafront started a discussion about "
        "what the canteens could do with surplus food around closing time.",
        "Reddit", REDDIT + "/r/HKUST/comments/1nfpd66/",
    ),
    (
        "tko", "TeaWood at PopCorn 1: a dinner for two",
        "A diner liked the crisp salt-and-pepper chicken with minced pork rice and found "
        "the seating roomy enough for two people to linger over dinner.",
        "OpenRice", OPENRICE + "/zh-cn/hongkong/review/"
        "%E9%A9%9A%E5%96%9C%E6%99%9A%E9%A4%90-e6505776",
    ),
    (
        "tko", "Krapow at PopCorn: sharing the Thai set",
        "A diner enjoyed the crisp prawn cakes and pineapple seafood fried rice. The grilled "
        "beef was rarer than they preferred, though they liked its flavour with the sour sauce.",
        "OpenRice", OPENRICE + "/en/hongkong/review/"
        "%E6%9C%83%E5%86%8D%E8%A8%AA%E5%98%85%E6%B3%B0%E8%8F%9C-e6230582",
    ),
    (
        "tko", "Thai Grill at PopWalk: tom yum noodles",
        "One lunch review liked the coconut aroma and balance of sourness and heat in the "
        "seafood tom yum noodles. The diner also noted that the room did not have many seats.",
        "OpenRice", OPENRICE + "/zh-cn/hongkong/review/--e6604182",
    ),
    (
        "hang_hau", "Hama Sushi at East Point City: a weekday lunch",
        "A repeat visitor liked the cod roe and shiso gunkan and the choice of sushi toppings. "
        "They reported no wait on their weekday lunch visit.",
        "OpenRice", OPENRICE_REVIEW + "--e6519426",
    ),
    (
        "hang_hau", "Katsuo Udon at East Point City: the opening queues",
        "A reviewer said they saw evening queues when the bonito broth udon shop first opened. "
        "That observation was from their visits during the opening period.",
        "OpenRice", OPENRICE_REVIEW + "%E8%B1%AC%E5%90%8C%E9%B4%A8%E8%AC%9B-"
        "%E6%9D%B1%E6%B8%AF%E5%9F%8E%E6%96%B0%E9%96%8B%E9%B0%B9%E7%83%8F%E5%86%AC-e6364882",
    ),
    (
        "hang_hau", "Finding more dinner options in Hang Hau",
        "In a neighbourhood thread, one commenter preferred the range of food choices in "
        "Hang Hau and mentioned taking a minibus there from near LOHAS Park.",
        "Reddit", REDDIT + "/r/Hong_Kong/comments/1wkplxy/any_proscons_of_living_at_lohas_park/",
    ),
    (
        "lohas", "Asam Chicken Rice: chicken rice and laksa",
        "A diner described their companion's Hainanese chicken rice as tender and liked the "
        "coconut flavour of their own laksa. The broth was still hot near the end of the meal.",
        "OpenRice", OPENRICE + "/zh-cn/hongkong/dish/"
        "%E4%BA%9E%E5%8F%83%E5%8E%BB%E9%AA%A8%E6%B5%B7%E5%8D%97%E9%9B%9E%E9%A3%AF-"
        "%E4%BA%9E%E5%8F%83%E9%9B%9E%E9%A3%AF-the-lohas%E5%BA%B7%E5%9F%8E-d447905",
    ),
    (
        "lohas", "Nabe Urawa: a lunch visit at THE LOHAS",
        "A diner went to the LOHAS branch for lunch and felt the meal was good value.",
        "OpenRice", OPENRICE + "/en/hongkong/review/--e6360204",
    ),
    (
        "tai_po_tsai", "Food options near Tai Po Tsai Village",
        "In a 2022 housing discussion, someone who had worked at HKUST described the village "
        "7-Eleven as one of the few nearby food options and pointed to Hang Hau and Tseung Kwan O "
        "for a wider choice of meals and groceries.",
        "Reddit", REDDIT + "/r/HongKong/comments/vuz5bd/",
    ),
]
