"""Curated image links from the original sources. Images are not bundled or proxied."""

from apps.api.real_sources import VILLAGE_PRODUCT

MC_MENU = "https://www.mcdonalds.com.hk/en/full-menu/"
MC_ASSETS = "https://assets-au-01.kc-usercontent.com/6b1dcbdb-cbf5-02d2-e44a-38cd8619186a/"
FAIRWOOD_MENU = "https://www.fairwood.com.hk/en/food_menus?tab=lunch"
GENKI_MENU = "https://order.genkisushi.com.hk/en/dine-in-menu/core-menu-may-2026"
GENKI_ASSETS = "https://order.genkisushi.com.hk/media/catalog/product/2/0/"
GENKI_GUNKAN = "https://order.genkisushi.com.hk/en/gunkan.html"
TAMJAI_MENU = "https://www.tjsamgor.com/hk/menu/"
TAMJAI_ASSETS = "https://www.tjsamgor.com/hk/wp-content/uploads/"
ACE = "https://www.acefitness.org/resources/everyone/exercise-library/"
ACE_ASSETS = "https://ik.imagekit.io/02fmeo4exvw/exercise-library/large/"


def _photo(url: str, source_url: str, alt: str, credit: str) -> dict[str, str]:
    return {"url": url, "source_url": source_url, "alt": alt, "credit": credit}


# Keying by menu and item distinguishes identically named dishes from different operators.
DISH_PHOTOS = {
    MC_MENU: {
        name: _photo(MC_ASSETS + asset, f"https://www.mcdonalds.com.hk/en/product/{slug}/",
                     name, "Product photo · McDonald's Hong Kong")
        for name, slug, asset in (
            ("Big Mac · 巨無霸", "big-mac",
             "3b629dc6-bf9d-461e-8a0c-8c69f497cb33/MCD_GLBL21_BigMac_A_3Q_1-original.png"),
            ("Filet-O-Fish · 魚柳包", "filet-o-fish",
             "f4257ee8-ec06-4496-a163-cc6804d9dda3/MCD_GLBL21_FiletOFish_3Q-original.png"),
            ("McSpicy · 麥辣雞腿包", "mcspicy",
             "878ce2f7-cfb4-475c-869c-7fc78a778e43/MS260914_EK-1_1.png"),
            ("Egg & Cheese Burger · 烘蛋芝士包", "egg-cheese-burger",
             "647ad37c-d383-4386-aaf5-25ba2ac09f70/McD_Egg_Cheese_Burger_R1_Artpaper.png"),
            ("Sausage McMuffin with Egg · 豬柳蛋漢堡", "sausage-mcmuffin-with-egg",
             "9d499b25-e8de-4f74-9327-333cb50c28ff/McD-Sausage-Egg-Muffin-Limbo.png"),
            ("Caesar salad", "caesar-salad", "46a888cc-d90c-4ec1-8fd4-b4831b7750b7/Salad.png"),
        )
    },
    FAIRWOOD_MENU: {
        name: _photo(url, FAIRWOOD_MENU, name, "Product photo · Fairwood")
        for name, url in (
            ("Baked pork chop rice", "https://image.aigens.com/"
             "IQpswpFLr7prTSKizEvzNQP0m_Ms1CXwTgcVTBACAne3t4qbisBIyWFu_018MS-6xtcpYkJZ6raBKJcotMhRBSZ7eAFlTshkjcCAOFY"),
            ("Curry chicken rice", "https://lh3.googleusercontent.com/"
             "Ju2H7ERYVks5ypPDvBaxXaE0y-sDOSdyoS2ig-PdilWb0dxyRUS-78ulmTtLEmwHw7SLqpyMNkFZ_oyi8KHJTNDYN-ohlsUF1U3ZFbE"),
            ("Curry beef brisket and tendon rice", "https://lh3.googleusercontent.com/"
             "VLq7Y_NkCIXJq5KcNgSxObKY-o3AqZF3HzxEbyG2-GkFRJJkgrbep-G5WR4U2iQjikUerSlWj7mDJ9mCgWVmpipfXFQAGTSVSPVL1A"),
            ("Sweet corn and diced pork rice",
             "https://content.aigens.com/image/Uqie1rPrMJTUOCitFJVrralaOBIRe5taxgMGERNYcws=w512.png"),
            ("Sweet and sour pork with rice", "https://lh3.googleusercontent.com/"
             "6F9beCtB1vDjV-oTFallX2O97OVLOx2lRhJ31SftKgdUgpcCxFZruTnW5ExAwlv8Tgma4zGnJLZPciKa6dS6GZtk3nnQRbuDmX5h4O8"),
            ("Spaghetti bolognese",
             "https://content.aigens.com/image/i4nqiq80oovdQAb8hqRgmjBGRJPK3YfDy0JSR_88s60=w512.png"),
        )
    },
    GENKI_MENU: {
        name: _photo(GENKI_ASSETS + asset, source, name, "Product photo · Genki Sushi Hong Kong")
        for name, asset, source in (
            ("Salmon salad gunkan", "2026_core_menu_ordering_site_plp_salmon_salad.png",
             GENKI_GUNKAN),
            ("Scallop skirt gunkan", "2026_core_menu_ordering_site_plp_scallop_skirt-07.png",
             GENKI_GUNKAN),
            ("Fried shrimp sushi with tartar sauce",
             "2026_core_menu_ordering_site_plp_deep-fried_shrimp_with_tartar_sauce.png",
             "https://order.genkisushi.com.hk/en/sushi.html"),
        )
    },
    TAMJAI_MENU: {
        "Hunan chicken wings · 湖南土匪雞翼": _photo(
            TAMJAI_ASSETS + "2019/08/%E6%B9%96%E5%8D%97%E5%9C%9F%E5%8C%AA%E9%9B%9E%E7%BF%BC.png",
            TAMJAI_MENU, "Hunan chicken wings", "Product photo · TamJai SamGor",
        ),
        "Grilled pork neck · 香烤豬頸肉": _photo(
            TAMJAI_ASSETS + "2024/10/20241014_3G-Website-item_520x400_"
            "%E8%90%BD%E2%BC%92%E7%82%BA%E4%BD%A0%E7%83%A4%E8%B1%AC%E9%A0%B8%E2%BE%81.jpg",
            TAMJAI_MENU, "Grilled pork neck", "Product photo · TamJai SamGor",
        ),
    },
    VILLAGE_PRODUCT: {
        "KiKi sesame and pepper mixed noodles · KiKi 椒香麻醬拌麵": _photo(
            "https://tritrade-tw.com/archive/image/product3/images/1566803096_thumb_630_617.jpg",
            "https://tritrade-tw.com/product_d.php?id=1166&lang=tw&tb=3",
            "KiKi spicy sesame paste noodle packaging", "Package photo · Tri Trade",
        ),
    },
}

EXERCISE_PHOTOS = {
    name: _photo(f"{ACE_ASSETS}{number}-1.jpg", f"{ACE}{number}/{slug}/",
                 f"{name} demonstration", "Movement photo · ACE")
    for name, number, slug in (
        ("Seated row", 168, "seated-row"),
        ("Seated lat pulldown", 158, "seated-lat-pulldown"),
        ("Seated high back row", 46, "seated-high-back-row"),
        ("Reverse fly", 353, "reverse-fly"),
        ("Seated machine close-grip shoulder press", 187,
         "seated-machine-close-grip-shoulder-press"),
        ("Bent-knee push-up", 13, "bent-knee-push-up"),
        ("Dumbbell chest press", 19, "chest-press"),
        ("Push-up", 41, "push-up"),
        ("Bodyweight squat", 135, "bodyweight-squat"),
        ("Seated leg press", 154, "seated-leg-press"),
        ("Forward lunge", 94, "forward-lunge"),
        ("Seated incline cable press", 167, "seated-incline-cable-press"),
        ("Seated leg extension", 183, "seated-leg-extension"),
        ("Glute bridge", 49, "glute-bridge"),
        ("Side plank with bent knees", 100, "side-plank-with-bent-knee"),
    )
}
