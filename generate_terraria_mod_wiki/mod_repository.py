import os
import pathlib
import re


# retrieves information from the mod repository files
class ModRepository:
    def __init__(self, source_dir):
        self.source_dir: str = source_dir
        self.vanity_source_dir: str = os.path.join(source_dir, "Items", "Vanity", "")
        self.repo_url_base: str = "/Qubus0/JourneyTrend/tree/master/"
        self.repo_url_file_base: str = "/Qubus0/JourneyTrend/blob/master/"
        with open(os.path.join(source_dir, "NPCs", "NPCLoots.cs")) as open_file:
            self.loots = re.split(r"if\s*?\(", open_file.read())[1:]
        with open(os.path.join(source_dir, "NPCs", "NPCShops.cs")) as open_file:
            self.shops = open_file.read().split("SetupShop")[1].split("SetupTravelShop")
            self.normal_shops = self.shops[0].split("case")[1:]
            self.travel_shop = self.shops[1]

    def get_set_directory_path_from_name(self, set_name):
        return self.vanity_source_dir + set_name

    def get_set_item_base_path_from_name(self, set_name):
        return os.path.join(self.get_set_directory_path_from_name(set_name), set_name)

    def get_artist_credit(self, set_name: str) -> str:
        base_path = self.get_set_item_base_path_from_name(set_name)
        artist = ""
        tootltip = self.get_item_tooltip_from_file(f"{base_path}Head.cs")
        for line in tootltip.split("\\n"):
            if line.__contains__("Made by"):
                artist = line
        return artist

    def get_assistant_credit(self, set_name: str) -> str:
        base_path = self.get_set_item_base_path_from_name(set_name)
        assistants = ""
        tootltip = self.get_item_tooltip_from_file(f"{base_path}Bag.cs")
        for line in tootltip.split("\\n"):
            if line.__contains__("assisted"):
                assistants = line
        return assistants


    @staticmethod
    def get_item_name_from_file(file: str) -> str:
        with open(file) as open_file:
            file_content = open_file.read()
            item_name = ""
            item_name_in_code = re.findall(r"(?sm)^\s*DisplayName\.SetDefault\(\s*\"[^\"]*\"\);", file_content)
            if item_name_in_code:
                item_name = re.findall(r"(?sm)\"[^\"]*\"*", item_name_in_code[0])[0].replace("\"", "")
        return item_name

    def get_item_name_from_set_name_and_part(self, set_name: str, part: str) -> str:
        base_path = self.get_set_item_base_path_from_name(set_name)
        path = base_path + part.capitalize() + ".cs"
        if pathlib.Path(path).exists():
            return self.get_item_name_from_file(path)
        else:
            return "-"

    def get_item_tooltip_from_file(self, file: str) -> str:
        with open(file) as open_file:
            file_content = open_file.read()
            tooltip = ""
            tooltip_in_code = re.findall(r"(?sm)^\s*Tooltip\.SetDefault\(\s*\"[^\"]*\"\);", file_content)
            if tooltip_in_code:
                tooltip = re.findall("(?sm)\"[^\"]*\"*", tooltip_in_code[0])[0].replace("\"", "")
        return tooltip

    def get_item_tooltip_from_set_name_and_part(self, set_name: str, part: str) -> str:
        base_path = self.get_set_item_base_path_from_name(set_name)
        path = base_path + part.capitalize() + ".cs"
        if pathlib.Path(path).exists():
            return self.get_formatted_item_tooltip_from_file(path)
        else:
            return "-"

    def get_formatted_item_tooltip_from_file(self, file: str) -> str:
        tooltip = self.get_item_tooltip_from_file(file)
        split_tooltip = []
        for line in tooltip.split("\\n"):
            if not line.__contains__("{") and not line.__contains__("Made by"):
                split_tooltip.append(line + " <br> ")
        return "".join(split_tooltip)

    def is_crafted(self, set_name: str, part: str = "head") -> bool:
        base_path = self.get_set_item_base_path_from_name(set_name)
        file = base_path + part.capitalize() + ".cs"
        with open(file) as open_file:
            file_content = open_file.read()
            recipe = re.search(r"(?sm)ModRecipe\((.*?)recipe\.AddRecipe\(\);", file_content)
        if recipe:
            return True
        else:
            return False

    def get_crafting_recipe_from_file(self, file: str) -> (str, str, str):
        ingredients = ""
        craftingStations = ""
        liquids = ""
        with open(file) as open_file:
            file_content = open_file.read()
            temp_ingredients = []
            groups = []
            cStation = []
            liq = []
            recipe_in_code = re.search(r"(?sm)ModRecipe\((.*?)recipe\.AddRecipe\(\);", file_content)
            if recipe_in_code:
                temp_ingredients += re.findall(r"AddIngredient\(ItemID\.(.*?)\);", recipe_in_code[0])
                groups += re.findall(r"AddRecipeGroup\((.*?)\);", recipe_in_code[0].replace("\"", ""))
                cStation += re.findall(r"(?sm)recipe\.AddTile\(TileID\.(.*?)\);", recipe_in_code[0])
                liq += re.findall(r"need(.*?)\s=\strue;", recipe_in_code[0])
        if temp_ingredients:
            for ingredient in temp_ingredients:
                item, *amount = ingredient.split(", ")
                amount = amount[0] if amount else "1"
                ingredientLink = ModWiki.get_terraria_wiki_item_link(item)
                ingredients += f"{ingredientLink} ({amount}) <br>"
        else:
            ingredients += "-"
        for group in groups:
            item, *amount = group.split(", ")
            amount = amount[0] if amount else "1"
            groupLink = ModWiki.build_terraria_wiki_link(f"Any {item}", "/Alternative_crafting_ingredients")
            ingredients += f"{groupLink} ({amount}) <br>"
        if cStation:
            if cStation[0] == "Anvils":
                cStation[0] = "IronAnvil"
            craftingStationLink = ModWiki.get_terraria_wiki_item_link(cStation[0])
            craftingStations += craftingStationLink
        else:
            craftingStations += ModWiki.build_terraria_wiki_link("By Hand", "/By_Hand")
        if liq:
            for liquid in liq:
                liquidLink = ModWiki.build_terraria_wiki_link(liquid, f"/{liquid}")
                liquids += liquidLink
        else:
            liquids += "-"
        return ingredients, craftingStations, liquids

    def get_crafting_recipe_from_set_name_and_part(self, set_name, part):
        base_path = self.get_set_item_base_path_from_name(set_name)
        path = base_path + part.capitalize() + ".cs"
        if pathlib.Path(path).exists():
            return self.get_crafting_recipe_from_file(path)
        else:
            return "-"

    def is_dropped(self, set_name: str) -> bool:
        for loot in self.loots:
            if loot.__contains__(set_name):
                return True
        return False

    def get_drop_rate_and_entity_wiki_info_from_loots_file(self, set_name, part):
        entity_droprate_tuple_list = []
        full_part = "<" + set_name + part.capitalize()  # the < at the beginning is required to stop overlaps
        single_item = False
        for item in self.loots:
            if item.__contains__(full_part):
                enemies_and_rate = re.findall(
                    r"(?sm)(NPCID\..*?(?=\W).*?)(?<=Main\.rand\.Next\().*?(\d+).*?(?=\).*?(\d+))", item)
                if item.__contains__("dropChooser"):
                    single_item = True

                for enemy_rate_tuple in enemies_and_rate:
                    rate_numerator = int(enemy_rate_tuple[2]) if int(enemy_rate_tuple[2]) > 0 else 1
                    rate_denominator = int(enemy_rate_tuple[1])
                    rate = f"{rate_numerator} in {rate_denominator} ({round(rate_numerator / rate_denominator, 3)}%)"
                    rate += " (single item drop) " if single_item else ""
                    entity_list = re.findall(r"(?<=NPCID\.).*?(?=\W)", enemy_rate_tuple[0])

                    for entity in entity_list:
                        npc_image_and_link = ModWiki.build_item_image_and_wiki_link(entity)
                        entity_droprate_tuple_list.append((npc_image_and_link, rate))
        return entity_droprate_tuple_list

    def is_bought(self, set_name: str) -> bool:
        for shop in self.shops:
            if shop.__contains__(set_name):
                return True

    def get_shop_info(self, set_name, part):
        npc_wiki_image_and_link = ""
        price = ""
        npc = ""
        full_part = "<" + set_name + part.capitalize()  # the < at the beginning is required to stop overlaps
        if self.travel_shop.__contains__(full_part):
            npc = "TravellingMerchant"
        else:
            for sold_set_code in self.normal_shops:
                if sold_set_code.__contains__(full_part):
                    npc = re.findall(r"NPCID\.(.*?(?=\W))", sold_set_code)[0]
        if npc:
            npc_wiki_image_and_link = ModWiki.build_item_image_and_wiki_link(npc)

        base_path = self.get_set_item_base_path_from_name(set_name)
        file = base_path + part.capitalize() + ".cs"
        if pathlib.Path(file).exists():
            with open(file) as open_file:
                file_content = open_file.read()
                price = re.findall(r"item\.value\s*?=\s*?(\d+?);", file_content)[0]
        coin_price = ModWiki.convert_price_to_coin_price(price)

        return npc_wiki_image_and_link, coin_price

    def has_texture(self, set_name, part):
        base_path = self.get_set_item_base_path_from_name(set_name)
        if part == "head" or part == "hair" or part == "altHair":
            file = base_path + "Head.cs"
            if pathlib.Path(file).exists():
                with open(file) as open_file:
                    file_content = open_file.read()
                    if part == "hair" and file_content.__contains__("drawHair = true;"):
                        return True
                    if part == "altHair" and file_content.__contains__("drawAltHair = true;"):
                        return True
                    if part == "head":
                        if not re.findall(r"(?sm)DrawHead\(\).*?{.*?(return\sfalse;).*?}", file_content) == ["return false;"]:
                            return True
        elif part == "body" or part == "hands":
            file = base_path + "Body.cs"
            if pathlib.Path(file).exists():
                with open(file) as open_file:
                    file_content = open_file.read()
                    if part == "hands" and file_content.__contains__("drawHands = true;"):
                        return True
                    if part == "body" and not re.findall(r"(?sm)DrawBody\(\).*?{.*?(return\sfalse;).*?}",
                                                         file_content) == ["return false;"]:
                        return True
        elif part == "legs":
            file = base_path + "Legs.cs"
            if pathlib.Path(file).exists():
                with open(file) as open_file:
                    file_content = open_file.read()
                    if not re.findall(r"(?sm)DrawLegs\(\).*?{.*?(return\sfalse;).*?}",
                                      file_content) == ["return false;"]:
                        return True
        else:
            return False

    def get_droprate_and_entity_wiki_info_from_loots_file(self, set_name, part):
        entity_droprate_tuple_list = []
        full_part = "<" + set_name + part.capitalize()  # the < at the beginning is required to stop overlaps
        single_item = False
        for item in self.loots:
            if item.__contains__(full_part):
                enemies_and_rate = re.findall(
                    r'(?sm)(NPCID\..*?(?=\W).*?)(?<=Main\.rand\.Next\().*?(\d+).*?(?=\).*?(\d+))', item)
                if item.__contains__("dropChooser"):
                    single_item = True

                for enemy_rate_tuple in enemies_and_rate:
                    rate_numerator = int(enemy_rate_tuple[2]) if int(enemy_rate_tuple[2]) > 0 else 1
                    rate_denominator = int(enemy_rate_tuple[1])
                    rate = f"{rate_numerator} in {rate_denominator} ({round(rate_numerator / rate_denominator, 3)}%)"
                    rate += " (single item drop) " if single_item else ""
                    entity_list = re.findall(r'(?<=NPCID\.).*?(?=\W)', enemy_rate_tuple[0])

                    for entity in entity_list:
                        npc_image_and_link = self.build_item_image_and_wiki_link(entity)
                        entity_droprate_tuple_list.append((npc_image_and_link, rate))
        return entity_droprate_tuple_list