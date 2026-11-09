"""
Core Quick-Commerce Taxonomy for ShopLens Search V2.
13 Macro-Categories and 50 Granular Sub-Categories.
"""

TAXONOMY_CATEGORIES = [
    (1, "Dairy, Bread & Eggs", "Fresh milk, butter, paneer, curd, bread, eggs, and morning breakfast staples"),
    (2, "Snacks & Munchies", "Chips, crisps, namkeen, roasted snacks, wafers, and savory munchies"),
    (3, "Bakery & Biscuits", "Glucose biscuits, cream cookies, rusk, muffins, cakes, and artisan breads"),
    (4, "Sweet Tooth & Confectionery", "Chocolates, candy, toffees, Indian mithai, ice creams, and dessert treats"),
    (5, "Drinks & Juices", "Carbonated cold drinks, fruit juices, energy drinks, mineral water, and sodas"),
    (6, "Tea, Coffee & Health Drinks", "Leaf tea, instant coffee, herbal green tea, malt drinks, and hot beverages"),
    (7, "Instant & Frozen Food", "Instant noodles, pasta, ready-to-eat meals, frozen snacks, and cooking sauces"),
    (8, "Atta, Rice, Oil & Dals", "Wheat flour, basmati rice, pulses, cooking oils, desi ghee, and grains"),
    (9, "Masala, Spices & Dry Fruits", "Whole and ground spices, salt, sugar, jaggery, almonds, cashews, and nuts"),
    (10, "Fresh Fruits & Vegetables", "Fresh seasonal fruits, daily vegetables, potatoes, onions, and organic greens"),
    (11, "Personal Care & Hygiene", "Bathing soaps, body washes, shampoos, toothpastes, skincare, and deodorants"),
    (12, "Cleaning & Household Essentials", "Laundry detergents, dishwash liquids, surface cleaners, and paper products"),
    (13, "Baby Care & Pet Supplies", "Baby diapers, gentle baby wipes, baby food, dog food, and pet accessories"),
]

# 50 Sub-Categories: (id, category_id, name, description, synonyms)
TAXONOMY_SUB_CATEGORIES = [
    (1, 1, "Milk", "Fresh pouch milk, cow milk, toned milk, and full cream milk", ["milk", "doodh", "dudh", "dairy", "cow milk", "toned milk", "fresh milk", "liquid drink", "beverage", "dairy drink"]),
    (2, 1, "Butter & Ghee", "Table butter, white butter, and pure desi cow ghee", ["butter", "makhan", "makkhan", "ghee", "desi ghee", "table butter", "salted butter", "dairy fat"]),
    (3, 1, "Paneer & Curd", "Fresh malai paneer, set curd, dahi, and Greek yogurt", ["paneer", "curd", "dahi", "yogurt", "malai paneer", "dairy", "chhena", "chaas", "buttermilk"]),
    (4, 1, "Bread & Pav", "White bread, brown bread, whole wheat bread, buns, and burger pav", ["bread", "pav", "paav", "loaf", "brown bread", "bakery", "roti", "bun", "white bread"]),
    (5, 1, "Eggs", "Farm fresh white eggs, brown eggs, and organic protein eggs", ["eggs", "egg", "ande", "anda", "white eggs", "brown eggs", "protein", "poultry"]),
    (6, 1, "Cheese & Dips", "Cheese slices, cheese cubes, mozzarella, and sandwich spreads", ["cheese", "cheddar", "mozzarella", "cheese slice", "dips", "spread", "dairy"]),

    (7, 2, "Chips & Crisps", "Potato chips, potato wafers, and flavored crisps", ["chips", "crisps", "wafers", "potato chips", "crunchy", "salted chips", "savory", "potato wafers"]),
    (8, 2, "Namkeen & Savory", "Bhujia, sev, mixture, chana jor, and Indian traditional namkeen", ["namkeen", "bhujia", "sev", "mixture", "farsan", "spicy namkeen", "savory", "snack"]),
    (9, 2, "Nachos & Popcorn", "Corn tortilla nachos, cheese dips, and butter microwave popcorn", ["nachos", "popcorn", "tortilla", "corn chips", "cheese nachos", "savory snack"]),
    (10, 2, "Roasted & Healthy Snacks", "Roasted makhana, diet mixture, murmura, and healthy seeds", ["makhana", "roasted", "diet snack", "healthy", "pumpkin seeds", "flax seeds", "healthy snack"]),

    (11, 3, "Cookies & Biscuits", "Digestive biscuits, glucose biscuits, cream cookies, and butter cookies", ["biscuit", "biscuits", "cookies", "biskut", "sweet cookies", "digestive", "cream biscuit", "chai time"]),
    (12, 3, "Rusks & Toasts", "Crispy suji rusk, milk toast, and tea-time crunchies", ["rusk", "toast", "suji rusk", "chai toast", "crispy rusk", "bakery"]),
    (13, 3, "Cakes & Muffins", "Fruit cakes, chocolate muffins, plum cakes, and Swiss rolls", ["cake", "muffin", "plum cake", "cupcake", "brownie", "sweet cake", "bakery dessert"]),

    (14, 4, "Chocolates", "Milk chocolates, dark chocolates, chocolate bars, and chocolate gift boxes", ["chocolate", "chocolates", "candy", "dairy milk", "dark chocolate", "silk", "sweet", "cadbury", "cocoa", "dessert"]),
    (15, 4, "Candies & Toffees", "Caramel toffees, fruit lollipops, mints, and chewy candies", ["candy", "candies", "toffee", "toffees", "lollipop", "mint", "chew", "sweet", "mitha"]),
    (16, 4, "Indian Mithai & Desserts", "Gulab jamun, rasgulla, kaju katli, soan papdi, and festive sweets", ["mithai", "sweets", "meetha", "mitha", "gulab jamun", "rasgulla", "kaju katli", "soan papdi", "dessert"]),
    (17, 4, "Ice Creams & Kulfi", "Vanilla ice cream, chocolate tubs, kulfi bars, and ice cream cones", ["ice cream", "kulfi", "icecream", "chocobar", "cone", "cold dessert", "sweet tub"]),

    (18, 5, "Soft Drinks & Sodas", "Cola, lemon soda, orange drink, and sparkling carbonated beverages", ["cold drink", "soft drink", "soda", "coke", "cola", "pepsi", "fizzy", "carbonated", "drink", "beverage", "liquid drink"]),
    (19, 5, "Fruit Juices & Nectars", "Apple juice, mixed fruit juice, mango nectar, and coconut water", ["juice", "fruit juice", "mango juice", "real juice", "coconut water", "nectar", "drink", "liquid", "beverage"]),
    (20, 5, "Energy & Sports Drinks", "Energy drinks, electrolyte rehydration drinks, and sports beverages", ["energy drink", "red bull", "sting", "electrolyte", "sports drink", "beverage", "liquid drink", "drink"]),
    (21, 5, "Water & Tonic Water", "Packaged drinking mineral water, club soda, and tonic water", ["water", "mineral water", "packaged water", "club soda", "sparkling water", "liquid", "drink", "beverage"]),

    (22, 6, "Tea & Chai Patti", "Assam tea leaves, green tea, masala chai, and English breakfast tea", ["tea", "chai", "chai patti", "green tea", "black tea", "masala tea", "hot drink", "beverage"]),
    (23, 6, "Coffee", "Instant coffee powder, roast and ground coffee, and cold coffee brew", ["coffee", "nescafe", "bru", "instant coffee", "filter coffee", "espresso", "hot beverage", "drink"]),
    (24, 6, "Health & Malt Drinks", "Horlicks, Bournvita, Complan, hot chocolate, and protein health powders", ["health drink", "horlicks", "bournvita", "malt", "complan", "hot chocolate", "milk drink", "beverage"]),

    (25, 7, "Noodles & Vermicelli", "Instant 2-minute noodles, cup noodles, hakka noodles, and seviyan", ["noodles", "maggi", "ramen", "instant noodles", "chowmein", "vermicelli", "seviyan"]),
    (26, 7, "Pasta & Macaroni", "Penne pasta, fusilli, durum wheat macaroni, and spaghetti", ["pasta", "macaroni", "penne", "spaghetti", "durum wheat", "italian"]),
    (27, 7, "Ready to Eat & Mixes", "Instant poha, idli dosa batter, ready curries, and soup packets", ["ready to eat", "batter", "poha", "instant mix", "soup", "instant meal"]),
    (28, 7, "Frozen Snacks & Peas", "French fries, frozen green peas, frozen paneer, and veg nuggets", ["frozen", "green peas", "matar", "french fries", "nuggets", "frozen snacks"]),
    (29, 7, "Sauces & Spreads", "Tomato ketchup, mayonnaise, chocolate spread, schezwan sauce, and jams", ["ketchup", "sauce", "mayonnaise", "jam", "chutney", "peanut butter", "spread"]),

    (30, 8, "Atta & Flours", "Chakki fresh whole wheat atta, maida, besan, and sooji", ["atta", "wheat flour", "maida", "besan", "sooji", "suji", "chakki atta", "staple"]),
    (31, 8, "Rice & Rice Products", "Basmati rice, daily kolam rice, poha, and puffed rice kurmura", ["rice", "basmati", "poha", "chawal", "kurmura", "biryani rice", "staple"]),
    (32, 8, "Cooking Oils & Ghee", "Mustard oil, refined sunflower oil, desi cow ghee, and olive oil", ["oil", "cooking oil", "ghee", "desi ghee", "mustard oil", "sunflower oil", "cooking fat"]),
    (33, 8, "Dals & Pulses", "Toor dal, moong dal, chana dal, urad dal, rajma, and kabuli chana", ["dal", "daal", "pulses", "toor dal", "moong dal", "rajma", "chana", "staple"]),

    (34, 9, "Whole & Ground Spices", "Haldi turmeric, red chilli powder, dhania coriander, garam masala, and jeera", ["masala", "spices", "haldi", "chilli powder", "dhaniya", "garam masala", "jeera"]),
    (35, 9, "Salt, Sugar & Jaggery", "Iodised salt, rock salt sendha namak, refined sugar, and pure desi jaggery gur", ["salt", "namak", "sugar", "cheeni", "jaggery", "gur", "sendha namak"]),
    (36, 9, "Dry Fruits & Nuts", "California almonds, cashews kaju, walnuts akhrot, raisins kismis, and pistachios", ["dry fruits", "badam", "almonds", "kaju", "cashews", "kismis", "walnuts", "nuts"]),

    (37, 10, "Fresh Vegetables", "Potatoes, red onions, hybrid tomatoes, ginger, garlic, and daily cooking greens", ["vegetables", "sabzi", "potato", "aloo", "onion", "pyaz", "tomato", "tamatar", "fresh"]),
    (38, 10, "Fresh Fruits", "Fresh apples, ripe bananas, sweet oranges, papaya, and seasonal fresh fruits", ["fruits", "fruit", "phal", "apple", "banana", "orange", "papaya", "fresh fruits"]),
    (39, 10, "Herbs & Seasonings", "Fresh coriander leaves, green chillies, mint pudina, curry leaves, and lemon", ["coriander", "dhaniya", "chilli", "lemon", "nimbu", "mint", "pudina", "herbs"]),

    (40, 11, "Bathing Soaps & Body Wash", "Beauty bathing bars, herbal soap, antibacterial soaps, and shower gels", ["soap", "sabun", "bath", "body wash", "bathing bar", "shower gel", "skincare", "personal care"]),
    (41, 11, "Hair Care & Shampoos", "Anti-dandruff shampoo, hair conditioning cream, coconut hair oil, and serum", ["shampoo", "hair oil", "conditioner", "hair care", "anti dandruff"]),
    (42, 11, "Oral Care", "Anticavity toothpaste, soft toothbrushes, herbal toothpaste, and mouthwash", ["toothpaste", "toothbrush", "oral care", "dant", "mouthwash", "colgate", "fresh breath"]),
    (43, 11, "Face & Skin Care", "Moisturising cold cream, face wash, sunscreens, and petroleum jelly", ["face wash", "moisturiser", "cream", "skin care", "lotion", "sunscreen"]),
    (44, 11, "Deodorants & Perfumes", "Body spray deodorants, pocket perfumes, and roll-on antiperspirants", ["deodorant", "deo", "perfume", "body spray", "fragrance"]),

    (45, 12, "Laundry Detergents & Bars", "Washing machine liquid detergent, surf powder, and stain remover bars", ["detergent", "washing powder", "surf", "laundry", "stain remover", "fabric wash", "cleaning"]),
    (46, 12, "Dishwashing", "Dishwash gel, lemon scrub bars, and dishwasher tablets", ["dishwash", "vim", "dishwash bar", "dishwash gel", "utensil cleaner", "cleaning"]),
    (47, 12, "Surface Cleaners & Disinfectants", "Floor cleaner liquid, toilet bowl cleaner, glass spray, and disinfectant wipes", ["cleaner", "floor cleaner", "toilet cleaner", "harpic", "lizol", "disinfectant", "cleaning"]),
    (48, 12, "Pooja Needs & Agarbatti", "Scented incense sticks agarbatti, camphor kapoor, brass diya wicks, and pooja oil", ["pooja", "agarbatti", "incense", "kapoor", "camphor", "diya", "dhoop", "prayer"]),

    (49, 13, "Diapers & Baby Wipes", "Newborn pant style diapers, sensitive baby wet wipes, and rash cream", ["diapers", "baby wipes", "pampers", "baby care", "huggies", "baby"]),
    (50, 13, "Pet Food & Accessories", "Dry dog food, adult cat food pouches, pet biscuits, and bird food", ["pet food", "dog food", "pedigree", "cat food", "whiskas", "dog biscuits"]),
]
