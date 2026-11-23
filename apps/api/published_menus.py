"""Selected public menu entries; no inferred ingredients, nutrition or availability."""

from dataclasses import dataclass
from typing import Literal

from apps.api.real_sources import VILLAGE_PRODUCT

CSO_FILES = "https://cso.hkust.edu.hk/sites/default/files/"


@dataclass(frozen=True)
class MenuSnapshot:
    branches: tuple[tuple[str, str], ...]
    source_url: str
    source_scope: Literal["branch", "brand"]
    note: str
    dishes: tuple[tuple[str, float | None], ...]


SNAPSHOTS = [
    MenuSnapshot((("hkust", "Donburi Bowl"),),
                 CSO_FILES + "2026-08/DONBURI%20Bowls%20Menu.pdf", "branch",
                 "HKUST reference menu. The printed prices are not live.", (
                     ("Teriyaki grilled chicken don · 照燒煎雞丼", 37),
                     ("Beef and grilled chicken don · 牛肉煎雞丼", 41),
                     ("Kimchi grilled chicken don · 泡菜煎雞丼", 39),
                     ("Japanese curry chicken don · 日式咖喱煎雞丼", 39),
                     ("Japanese curry beef don · 日式咖喱牛肉丼", 41),
                     ("Mala grilled chicken don · 麻辣醬煎雞丼", 39),
                     ("Grilled chicken skewers (3) · 炭燒雞串", 15),
                     ("Sesame coleslaw and cherry tomato salad · 胡麻醬椰菜絲車厘茄沙律", 12),
                 )),
    MenuSnapshot((("hkust", "Ebeneezer's"),),
                 CSO_FILES + "2026-08/Ebeneezers_Menu_2026-Sep.pdf", "branch",
                 "HKUST reference menu, September 2026 filename.", (
                     ("Chicken biryani", 44), ("Chicken tikka biryani", 47),
                     ("Chicken bites biryani", 48), ("Fish curry with rice", 40),
                     ("Chana masala with rice", 41), ("Dal makhani with rice", 41),
                     ("Vegetable curry with rice", 39), ("Chicken curry with rice", 40),
                 )),
    MenuSnapshot((("hkust", "Gold Rice Bowl"),),
                 CSO_FILES + "2024-08/GRB%20Menu%202024-09.pdf", "branch",
                 "Historical HKUST menu, September 2024. Confirm the current selection.", (
                     ("Melon and duck leg rice soup · 瓜粒鴨腿湯飯", None),
                     ("Fatty beef and egg rice soup · 蛋花肥牛湯飯", None),
                     ("Chashiu ramen or rice · 日式叉燒拉麵或飯", None),
                     ("Pork cutlet ramen or rice · 日式吉列豬扒拉麵或飯", None),
                     ("Baked pork chop rice or spaghetti · 懷舊焗豬扒飯或意粉", None),
                     ("Curry beef brisket rice or spaghetti · 咖喱牛腩飯或意粉", None),
                     ("Beef fried rice noodles · 乾炒牛河", None),
                     ("Scrambled egg and beef rice · 滑蛋牛肉飯", None),
                 )),
    MenuSnapshot((("hkust", "JoA"),), CSO_FILES + "2026-08/JoA%20Menu_2026-09.pdf", "branch",
                 "HKUST reference menu, September 2026 filename.", (
                     ("Beef bulgogi kimbap (small)", 16), ("Beef bulgogi kimbap (large)", 35),
                     ("Kimchi and pork kimbap (small)", 16), ("Vegetable kimbap", 16),
                     ("Korean beef japchae", 16), ("Tteokbokki", 16), ("Seaweed soup", 8),
                     ("Seafood and tofu soup", 25), ("Bibimbap", 45), ("Kimbap lunchbox", 53),
                 )),
    MenuSnapshot((("hkust", "HFT Life"),),
                 CSO_FILES + "2026-08/HFT%20Lift_UST_Product%20list_Aug%202026.pdf", "branch",
                 "HKUST August 2026 product list. Prices use the regular-price column.", (
                     ("Chicken and kale salad · 羽衣甘藍雞胸沙律", 45),
                     ("Spicy pork and wood ear siu mai · 麻辣木耳豬肉燒賣", 16),
                     ("Mushroom meatballs in pork bone soup · 豬骨濃湯貢丸", 18),
                     ("Hemp seed latte, hot · 熱火麻仁拿鐵", 30),
                     ("Mango deluxe smoothie · 楊枝甘露沙冰", 35),
                 )),
    MenuSnapshot((("hkust", "American Diner"),),
                 CSO_FILES + "2024-07/AmericanDiner%20Menu_Eng_Chin_2024-07-22-2_1.pdf", "branch",
                 "Historical HKUST reference menu, July 2024. Confirm the current selection.", (
                     ("Signature beef burger · 傳統芝士牛肉漢堡", None),
                     ("Chicken and honey mustard burger · 蜜糖芥末雞扒漢堡", None),
                     ("Hawaiian chicken burger · 夏威夷雞肉漢堡", None),
                     ("BBQ pulled pork burger · 手撕豬肉漢堡", None),
                 )),
    MenuSnapshot((("hkust", "Seafront Cafeteria"),),
                 CSO_FILES + "2025-10/Seafront%202025%20new%20price.pdf", "branch",
                 "HKUST reference price list, 2025 edition. Confirm current prices.", (
                     ("Braised chicken and potato rice · 薯仔炆雞飯", 32),
                     ("Yeung Chow fried rice · 揚州炒飯", 32),
                     ("Seafood and tofu rice · 滑豆腐海鮮飯", 35),
                     ("Baked black pepper chicken rice · 黑椒雞扒焗飯", 36),
                     ("Tomato and cheese baked pork chop rice · 鮮茄芝士豬扒焗飯", 36),
                     ("Beef fried rice noodles · 乾炒牛河", 35),
                     ("Shredded pork fried noodles · 肉絲炒麵", 35),
                     ("Chicken congee · 美味雞粥", 18),
                 )),
    MenuSnapshot((("hkust", "Oliver's Super Sandwiches"),),
                 CSO_FILES + "2026-10/OSS_Ful%20Menu_2026-10-08_0.pdf", "branch",
                 "Menu linked by HKUST, October 2026. Check current prices and variants.", (
                     ("Spaghetti bolognese", None), ("Truffle mushroom spaghetti", None),
                     ("Smoked salmon and clam spaghetti with dill", None),
                     ("Roast chicken leg udon in pork broth", None),
                     ("Roast chicken leg udon in spicy tomato soup", None),
                 )),
    MenuSnapshot((("hkust", "Can.teen II"), ("hkust", "Asia Pacific Catering")),
                 "https://sust.hkust.edu.hk/events/waste-reduction-program-hkust-canteens",
                 "branch",
                 "Historical HKUST examples of meal types. Check the current branch menu.", (
                     ("Rice meals · 碟頭飯", None),
                 )),
    MenuSnapshot((("hkust", "McDonald's"), ("lohas", "McDonald's")),
                 "https://www.mcdonalds.com.hk/en/full-menu/", "brand",
                 "Hong Kong brand menu. Confirm price and stock with the branch.", (
                     ("Big Mac · 巨無霸", None), ("Filet-O-Fish · 魚柳包", None),
                     ("McSpicy · 麥辣雞腿包", None), ("Egg & Cheese Burger · 烘蛋芝士包", None),
                     ("Sausage McMuffin with Egg · 豬柳蛋漢堡", None), ("Caesar salad", None),
                 )),
    MenuSnapshot((("hkust", "TamJai SamGor"), ("tko", "TamJai SamGor · Park Central")),
                 "https://www.tjsamgor.com/hk/menu/", "brand",
                 "Hong Kong brand menu. Confirm price and stock with the branch.", (
                     ("Custom mixian · 自選米線", None),
                     ("Crossing-bridge mixian · 過橋米線", None),
                     ("Hunan chicken wings · 湖南土匪雞翼", None),
                     ("Grilled pork neck · 香烤豬頸肉", None),
                 )),
    MenuSnapshot((("tko", "Fairwood · Park Central"), ("tko", "Fairwood · MCP Discovery"),
                  ("tko", "Fairwood · Metro Town"), ("tko", "Fairwood · Bauhinia Garden"),
                  ("hang_hau", "Fairwood · The Lane")),
                 "https://www.fairwood.com.hk/en/food_menus?tab=lunch", "brand",
                 "Published lunch menu and reference prices. Branch menus may differ.", (
                     ("Baked pork chop rice", 51), ("Curry chicken rice", 55),
                     ("Curry beef brisket and tendon rice", 61),
                     ("Sweet corn and diced pork rice", 45),
                     ("Sweet and sour pork with rice", 50), ("Spaghetti bolognese", 48),
                 )),
    MenuSnapshot((("lohas", "Genki Sushi"), ("tko", "Genki Sushi · Park Central"),
                  ("hang_hau", "Genki Sushi · East Point City")),
                 "https://order.genkisushi.com.hk/en/dine-in-menu/core-menu-may-2026", "brand",
                 "May 2026 Hong Kong menu snapshot. Confirm branch price and selection.", (
                     ("Smoked duck breast sushi", 12), ("Salmon salad gunkan", 12),
                     ("Crab roe salad gunkan", 12), ("Scallop skirt gunkan", 12),
                     ("Fried shrimp sushi with tartar sauce", 12),
                 )),
    MenuSnapshot((("tko", "Saizeriya · TKO Plaza"), ("tko", "Saizeriya · TKO Spot"),
                  ("tko", "Saizeriya · MCP Central")),
                 "https://www.saizeriya.com.hk/wp-content/uploads/20250714_TakeoutMenu.pdf",
                 "brand",
                 "July 2025 takeaway menu snapshot. Current branch prices may differ.", (
                     ("Margherita pizza · 水牛芝士薄餅", 30), ("Meat doria · 肉醬多利亞", 30),
                     ("Squid ink spaghetti · 墨魚汁意粉", 35),
                 )),
    MenuSnapshot((("tko", "Café de Coral · PopCorn 2"), ("lohas", "Cafe de Coral")),
                 "https://www.eatcdc.com/tch/main/terms.jsp?id=3220T231I0S4E0M121G6K1Q544J1G677",
                 "brand", "Hong Kong brand promotion lists these dishes. Branch supply may vary.", (
                     ("Baked pork chop rice · 一哥焗豬扒飯", None),
                     ("Baked seafood rice with lobster sauce · 龍蝦汁海鮮焗飯", None),
                 )),
    MenuSnapshot((("tko", "Soup Plus · PopWalk"),), "https://ifoodcourt.com.hk/soupplus", "brand",
                 "Operator's featured dishes. Confirm the selection at the PopWalk branch.", (
                     ("Duck leg rice soup with aged tangerine peel · 陳皮鴨腿湯飯", None),
                     ("Red wine oxtail rice soup · 紅酒牛尾湯飯", None),
                 )),
    MenuSnapshot((("tai_po_tsai", "7-Eleven · Tai Po Tsai"),), VILLAGE_PRODUCT, "branch",
                 "This branch appears on the retailer’s product distribution list. Stock varies.", (
                     ("KiKi sesame and pepper mixed noodles · KiKi 椒香麻醬拌麵", None),
                 )),
    MenuSnapshot((("tai_po_tsai", "7-Eleven · Tai Po Tsai"),),
                 "https://www.7-eleven.com.hk/sites/default/files/assets/EatEastStoreAddress.pdf",
                 "branch", "The retailer lists the branch for this range. Selection varies.", (
                     ("Eat East packaged meals · 波仔飯盒系列", None),
                 )),
]
