import os
import sys
import re
import pathlib
from PIL import Image
import requests
from typing import List
from bs4 import BeautifulSoup



class Repo:
    def __init__(self, source_dir):
        self.source_dir: str = source_dir
        self.vanity_source_dir: str = os.path.join(source_dir, "Items", "Vanity", "")

    # def analyze_repo(self):
    #     for root, directories, files in os.walk(self.source_dir):
    #         for file in files:
    #             pass

    # def get_vanity_sets(self):
    #     for directories in os.walk(self.source_dir):
    #         for file in directories:
    #             pass


class Wiki:
    def __init__(self, source_dir):
        self.source_dir: str = source_dir
        self.vanity_source_dir: str = os.path.join(source_dir, "Items", "Vanity")
        self.repo: Repo = None
        self.package_name = "generate_terraria_mod_wiki"
        self.wiki_url_base: str = "/Qubus0/JourneyTrend/wiki/"
        self.repo_url_base: str = "/Qubus0/JourneyTrend/tree/master/"
        self.repo_url_file_base: str = "/Qubus0/JourneyTrend/blob/master/"
        self.pages: List[Page] = list()
        self.item_id_table = self.get_id_table_from_terraria_wiki('https://terraria.fandom.com/Item_IDs')
        self.npc_id_table = self.get_id_table_from_terraria_wiki('https://terraria.fandom.com/wiki/NPC_IDs')
        with open(os.path.join(source_dir, "NPCs", "NPCLoots.cs")) as open_file:
            self.loots = re.split(r'if\s*?\(', open_file.read())[1:]
        with open(os.path.join(source_dir, "NPCs", "NPCShops.cs")) as open_file:
            self.shops = open_file.read().split("SetupShop")[1].split("SetupTravelShop")
            self.normal_shops = self.shops[0].split("case")[1:]
            self.travel_shop = self.shops[1]

    @staticmethod
    def get_id_table_from_terraria_wiki(wiki_url):
        page = requests.get(wiki_url)
        soup = BeautifulSoup(page.content, 'html.parser')
        table = soup.find(class_="sortable")
        return table

    @staticmethod
    def _build_link(text: str, url: str) -> str:
        separator = ""
        return separator.join(["[", text, "]", "(", url, ")"])

    def build_wiki_link(self, text: str, page_name: str) -> str:
        return self._build_link(text, self.wiki_url_base + page_name)

    @staticmethod
    def _build_image(text: str, url: str) -> str:
        separator = ""
        return separator.join(["![", text, "]", "(", url, ")"])

    def build_repo_image_link(self, text: str, rest_path: str) -> str:
        return self._build_image(text, self.repo_url_file_base + rest_path)

    def build_terraria_wiki_link(self, text: str, path: str) -> str:
        return self._build_link(text, f"https://terraria.fandom.com{path}")

    @staticmethod
    def get_item_name_from_file(file: str) -> str:
        with open(file) as open_file:
            file_content = open_file.read()
            item_name = ""
            item_name_in_code = re.findall('(?sm)^\s*DisplayName\.SetDefault\(\s*\"[^"]*\"\);', file_content)
            if item_name_in_code:
                item_name = re.findall('(?sm)\"[^"]*\"*', item_name_in_code[0])[0].replace('"', '')
        return item_name

    @staticmethod
    def get_item_tooltip_from_file(file: str) -> str:
        with open(file) as open_file:
            file_content = open_file.read()
            tooltip = ""
            tooltip_in_code = re.findall('(?sm)^\s*Tooltip\.SetDefault\(\s*\"[^"]*\"\);', file_content)
            if tooltip_in_code:
                tooltip = re.findall('(?sm)\"[^"]*\"*', tooltip_in_code[0])[0].replace('"', '')
        return tooltip

    def get_terraria_wiki_item_link(self, item_id):
        table_rows = self.item_id_table.find_all("tr")
        for row in table_rows:
            table_item_id = row.code
            if table_item_id and table_item_id.contents[0] == item_id:
                link_tag = row.find("a")
                item_path = link_tag.attrs["href"]
                title = link_tag.contents[0]
                link = self.build_terraria_wiki_link(title, item_path)
                return link

    # match_results = re.search(f"(?sm).*(href=\".{0, 200}?>{item}</code>)", table)  // over-engineered regex

    def get_crafting_recipe_from_file(self, file: str) -> (str, str, str):
        ingredients = ""
        craftingStations = ""
        liquids = ""
        with open(file) as open_file:
            file_content = open_file.read()
            ingr = []
            groups = []
            cStation = []
            liq = []
            recipe_in_code = re.search('(?sm)ModRecipe\((.*?)recipe\.AddRecipe\(\);', file_content)
            if recipe_in_code:
                ingr += re.findall('AddIngredient\(ItemID\.(.*?)\);', recipe_in_code[0])
                groups += re.findall('AddRecipeGroup\((.*?)\);', recipe_in_code[0].replace('"', ''))
                cStation += re.findall('(?sm)recipe\.AddTile\(TileID\.(.*?)\);', recipe_in_code[0])
                liq += re.findall('need(.*?)\s=\strue;', recipe_in_code[0])
        if ingr:
            for ingredient in ingr:
                item, *amount = ingredient.split(", ")
                amount = amount[0] if amount else "1"
                ingredientLink = self.get_terraria_wiki_item_link(item)
                ingredients += f"{ingredientLink} ({amount}) <br>"
        else:
            ingredients += "-"
        for group in groups:
            item, *amount = group.split(", ")
            amount = amount[0] if amount else "1"
            groupLink = self.build_terraria_wiki_link(f"Any {item}", '/Alternative_crafting_ingredients')
            ingredients += f"{groupLink} ({amount}) <br>"
        if cStation:
            if cStation[0] == "Anvils":
                cStation[0] = "IronAnvil"
            craftingStationLink = self.get_terraria_wiki_item_link(cStation[0])
            craftingStations += craftingStationLink
        else:
            craftingStations += self.build_terraria_wiki_link("By Hand", "/By_Hand")
        if liq:
            for liquid in liq:
                liquidLink = self.build_terraria_wiki_link(liquid, f"/{liquid}")
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

    def is_crafted(self, set_name: str, part: str = "head") -> bool:
        base_path = self.get_set_item_base_path_from_name(set_name)
        file = base_path + part.capitalize() + ".cs"
        with open(file) as open_file:
            file_content = open_file.read()
            recipe = re.search('(?sm)ModRecipe\((.*?)recipe\.AddRecipe\(\);', file_content)
        if recipe:
            return True
        else:
            return False

    def is_dropped(self, set_name: str) -> bool:
        for loot in self.loots:
            if loot.__contains__(set_name):
                return True
        return False

    def is_bought(self, set_name: str) -> bool:
        for shop in self.shops:
            if shop.__contains__(set_name):
                return True

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
            npc_wiki_image_and_link = self.build_item_image_and_wiki_link(npc)

        base_path = self.get_set_item_base_path_from_name(set_name)
        file = base_path + part.capitalize() + ".cs"
        if pathlib.Path(file).exists():
            with open(file) as open_file:
                file_content = open_file.read()
                price = re.findall(r"item\.value\s*?=\s*?(\d+?);", file_content)[0]
        coin_price = self.convert_price_to_coin_price(price)

        return npc_wiki_image_and_link, coin_price

    def convert_price_to_coin_price(self, price):
        self.transfer_coin_images()
        coin_price = ""
        coin_price = self.append_coins(coin_price, price[:-6], "platinum")
        coin_price = self.append_coins(coin_price, price[-6:-4], "gold")
        coin_price = self.append_coins(coin_price, price[-4:-2], "silver")
        coin_price = self.append_coins(coin_price, price[-2:], "copper")
        return coin_price

    def append_coins(self, coin_price, coin_value, coin_type):
        if coin_value and not coin_value == "00":
            coin_price += coin_value + self._build_image(coin_type.capitalize(),
                                                         os.path.join("images", "coins", coin_type + ".png")) + " "
        return coin_price

    def transfer_coin_images(self):
        wiki_coin_dir = os.path.join("wiki", "images", "coins")
        pathlib.Path(wiki_coin_dir).mkdir(parents=True, exist_ok=True)
        coin_dir = os.path.join(self.package_name, "coins")
        for root, directories, files in os.walk(coin_dir):
            for file in files:
                coin = Image.open(os.path.join(coin_dir, file))
                coin.save(os.path.join(wiki_coin_dir, file))

    def build_item_image_and_wiki_link(self, entity):
        image = "img not found"
        link = "link not found"
        table_rows = self.npc_id_table.find_all("tr")
        for row in table_rows:
            table_npc_id = row.code
            if table_npc_id and table_npc_id.contents[0] == entity:
                link_tag = row.find("a")
                item_path = link_tag.attrs["href"]
                item_name = link_tag.contents[0]
                link = self.build_terraria_wiki_link(item_name, item_path)
                npcimg = row.find("span", "npcimg")
                img = npcimg.img.attrs["src"]
                image = self._build_image(item_name, img)
        return f"{image} <br> {link}"

    # def build_wiki_link(self, text: str, page_name: str) -> str:
    #     return self._build_link(text, self.wiki_url_base + page_name)

    def get_set_directory_path_from_name(self, set_name):
        return self.repo.vanity_source_dir + set_name

    def get_set_item_base_path_from_name(self, set_name):
        return os.path.join(self.get_set_directory_path_from_name(set_name), set_name)

    def build_image_from_path(self, alt_text: str, image_path: str) -> str:
        if pathlib.Path(image_path).exists():
            return self._build_image(alt_text, os.path.join("../", image_path))
        else:
            print(f"file not found at: {image_path}")
            return '-'

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
                    if part == "head" and not re.findall('(?sm)DrawHead\(\).*?\{.*?(return\sfalse;).*?\}',
                                                         file_content) == ['return false;']:
                        return True
        elif part == "body" or part == "hands":
            file = base_path + "Body.cs"
            if pathlib.Path(file).exists():
                with open(file) as open_file:
                    file_content = open_file.read()
                    if part == "hands" and file_content.__contains__("drawHands = true;"):
                        return True
                    if part == "body" and not re.findall('(?sm)DrawBody\(\).*?\{.*?(return\sfalse;).*?\}',
                                                         file_content) == ['return false;']:
                        return True
        elif part == "legs":
            file = base_path + "Legs.cs"
            if pathlib.Path(file).exists():
                with open(file) as open_file:
                    file_content = open_file.read()
                    if not re.findall('(?sm)DrawLegs\(\).*?\{.*?(return\sfalse;).*?\}', file_content) == [
                        'return false;']:
                        return True
        else:
            return False

    def build_full_set_image(self, set_name: str) -> None:
        final_image = Image.new("RGBA", (40, 56), (0, 0, 0, 0))
        parts = ["head", "body", "legs", "hands", "hair", "altHair"]
        for part in parts:
            if self.has_texture(set_name, part):
                temp = Image.open(os.path.join(self.package_name, "player", part.capitalize() + ".png"))
                final_image.paste(temp, (0, 0), temp.convert('RGBA'))

        wiki_dir = os.path.join("wiki", "images")
        pathlib.Path(wiki_dir).mkdir(parents=True, exist_ok=True)
        base_path = self.get_set_item_base_path_from_name(set_name)
        parts = ["legs", "body", "head"]
        for part in parts:
            image_ending = f"{part.capitalize()}_{part.capitalize()}.png"
            image_path = base_path + image_ending
            if pathlib.Path(image_path).is_file():
                current_image = Image.open(image_path)
                image_frame = (0, 0, 40, 56)
                current_image = current_image.crop(image_frame)
                final_image.paste(current_image, (0, 0), current_image.convert("RGBA"))
                final_image.save(os.path.join("wiki", "images", set_name + ".png"))
                current_image.close()
            else:
                print(f"set part file not found at: {image_path}")
        final_image.close()

    def build_item_image_link_from_set_name_and_part(self, set_name: str, part: str):
        part_name = set_name + part.capitalize()
        return self.build_repo_image_link(part_name, os.path.join("Items", "Vanity", set_name, part_name + ".png"))

    def build_wiki(self):
        self.repo = Repo(self.source_dir)
        self.build_set_catalog()
        self.build_set_pages()
        self.output_pages()

    def get_item_name_from_set_name_and_part(self, set_name: str, part: str) -> str:
        base_path = self.get_set_item_base_path_from_name(set_name)
        path = base_path + part.capitalize() + ".cs"
        if pathlib.Path(path).exists():
            return self.get_item_name_from_file(path)
        else:
            return "-"

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
        for line in tooltip.split('\\n'):
            if not line.__contains__("{") and not line.__contains__("Made by"):
                split_tooltip.append(line + " <br> ")
        return "".join(split_tooltip)

    def get_item_name_and_tooltip_and_image(self, set_name: str, part: str) -> (str, str, str):
        display_name = self.get_item_name_from_set_name_and_part(set_name, part)
        tooltip = self.get_item_tooltip_from_set_name_and_part(set_name, part)
        image = self.build_item_image_link_from_set_name_and_part(set_name, part)
        return display_name, tooltip, image

    def get_artist_info(self, set_name: str) -> str:
        base_path = self.get_set_item_base_path_from_name(set_name)
        artist = ""
        assistants = ""
        tootltip = self.get_item_tooltip_from_file(f"{base_path}Head.cs")
        for line in tootltip.split("\\n"):
            if line.__contains__("Made by"):
                artist = line
        tootltip = self.get_item_tooltip_from_file(f"{base_path}Bag.cs")
        for line in tootltip.split("\\n"):
            if line.__contains__("assisted"):
                assistants = line
        return f"`{artist}` <br> {assistants}"

    def get_set_variants_images(self, set_name: str):
        parts = {
            "head": [],
            "body": [],
            "legs": [],
            "bag": []
        }
        directory_path = self.get_set_directory_path_from_name(set_name)
        for root, directories, files in os.walk(directory_path):
            for file in files:
                for part in parts.keys():
                    if any(set_name + part.capitalize() + str(i) + ".png" in file for i in range(10)):
                        parts[part].append(
                            self.build_repo_image_link(file, os.path.join("Items", "Vanity", set_name, file)))
                        parts[part].sort()
        return parts["head"], parts["body"], parts["legs"], parts["bag"]

    def output_pages(self):
        for page in self.pages:
            page.output_page()

    def get_sorted_sets(self):
        unsorted_sets = os.listdir(self.repo.vanity_source_dir)
        return sorted(unsorted_sets, key=lambda s: s.casefold())

    def build_set_catalog(self):
        num_sets = 0
        page = Page("Vanity Set Catalog")
        alphabetical_list = self.get_sorted_sets()
        page.add_table_header(": :", "Set Name")
        for vanity_set in alphabetical_list:
            num_sets += 1
            link = self.build_wiki_link(vanity_set, vanity_set)
            head = self.build_item_image_link_from_set_name_and_part(vanity_set, "head")
            page.add_table_row(head, link)
        page.add_table_row("", "")
        page.add_table_row(str(num_sets), "Vanity sets in total")
        self.pages.append(page)

    def build_set_pages(self):
        alphabetical_list = self.get_sorted_sets()
        for index, vanity_set in enumerate(alphabetical_list):
            page = self.build_vanity_set_page(vanity_set)
            # buttons for prev/next set
            page.add_section_break()
            previous_index = index - 1
            next_index = (index + 1) % len(alphabetical_list)
            previous_vanity_set = alphabetical_list[previous_index].capitalize()
            next_vanity_set = alphabetical_list[next_index].capitalize()
            previous_text = "Previous (%s)" % previous_vanity_set
            next_text = "Next (%s)" % next_vanity_set
            previous_link = self.build_wiki_link(previous_text, previous_vanity_set)
            next_link = self.build_wiki_link(next_text, next_vanity_set)
            page.add_table_header(previous_link, next_link)
            self.pages.append(page)
            # break  # a break here generates a single set page for testing

    def build_vanity_set_page(self, vanity_set_name):
        # vanity_set_name = "Granite"  #                testing a specific set
        print(f"generating page for {vanity_set_name} ")
        page = Page(vanity_set_name)
        self.build_full_set_image(vanity_set_name)

        # base set image, artist info
        heading = f"# {''.join([f' {char}' if char.isupper() else char for char in vanity_set_name]).lstrip(' ')}"
        page.add_row(heading)
        vanity_set = self._build_image(vanity_set_name, os.path.join("images", vanity_set_name + ".png"))
        page.add_table_header(":" + vanity_set + ":")
        self.get_artist_info(vanity_set_name)
        artist_info = self.get_artist_info(vanity_set_name)
        page.add_table_row(artist_info)
        page.add_section_break()

        section_heading = "## Set"
        page.add_row(section_heading)
        page.add_table_header("Name", ": :", "Tooltip")
        set_parts = ["head", "body", "legs", "bag"]
        for part in set_parts:
            name, tooltip, item_image = self.get_item_name_and_tooltip_and_image(vanity_set_name, part)
            page.add_table_row(name, item_image, tooltip)

        # variations
        head_vari, body_vari, legs_vari, bag_vari = self.get_set_variants_images(vanity_set_name)
        biggest = (len(head_vari), len(body_vari))[len(head_vari) < len(body_vari)]
        table_size = (len(legs_vari), biggest)[len(legs_vari) < biggest]
        if table_size > 0:
            section_heading = "### Set Variants"
            page.add_row(section_heading)
            page.add_table_header(*[":" + str(index + 1) + ":" for index in range(0, table_size)])
            page.add_table_row(*head_vari)
            page.add_table_row(*body_vari)
            page.add_table_row(*legs_vari)
            page.add_table_row(*bag_vari)

        page.add_section_break()
        page.add_row('### Obtaining')
        if self.is_crafted(vanity_set_name):
            page.add_row('#### Crafting')
            page.add_table_header(":Part:", "Ingredients", "Crafting Station", "Near Liquid")
            set_parts = ["head", "body", "legs"]
            for part in set_parts:
                name, tooltip, item_image = self.get_item_name_and_tooltip_and_image(vanity_set_name, part)
                ingredients, craftingStation, liquids = "-", "-", "-"
                if item_image != "-":
                    ingredients, craftingStation, liquids = self.get_crafting_recipe_from_set_name_and_part(
                        vanity_set_name, part)
                page.add_table_row(item_image, ingredients, craftingStation, liquids)
        elif self.is_bought(vanity_set_name):
            page.add_row('#### Bought')
            page.add_table_header(":Part:", ":NPC:", "Price")
            set_parts = ["head", "body", "legs"]
            for part in set_parts:
                name, tooltip, item_image = self.get_item_name_and_tooltip_and_image(vanity_set_name, part)
                npc_wiki_image_and_link, price = self.get_shop_info(vanity_set_name, part)
                page.add_table_row(item_image, npc_wiki_image_and_link, price)
        elif self.is_dropped(vanity_set_name):
            page.add_row('#### Dropped by')
            page.add_table_header(":Part:", ":Entity:", ":Rate:")
            set_parts = ["head", "body", "legs", "bag"]
            for part in set_parts:
                name, tooltip, item_image = self.get_item_name_and_tooltip_and_image(vanity_set_name, part)
                droprate_and_entity_list = self.get_droprate_and_entity_wiki_info_from_loots_file(vanity_set_name, part)
                for droprate_and_entity in droprate_and_entity_list:
                    page.add_table_row(item_image, droprate_and_entity[0], droprate_and_entity[1])
        return page


class Page:
    def __init__(self, name: str):
        self.name: str = name
        self.content = list()

    def __str__(self):
        return self.name + self._build_page()

    def _build_page(self):
        return "\n".join(self.content)

    def add_row(self, row: str):
        self.content.append(row)

    def add_table_header(self, *args):
        column_separator = " | "
        header = column_separator + column_separator.join(args).replace(":", "")
        divider = column_separator
        for arg in args:
            d = ["----"]
            for pos in re.finditer(":", arg):
                if pos.start() == 0:
                    d.insert(0, ":")
                if pos.start() == len(arg) - 1:
                    d.append(":")
            divider += "".join(d) + column_separator

        # divider = column_separator.join(["----"] * len(args))
        self.content.append(header)
        self.content.append(divider)

    def add_table_row(self, *args):
        column_separator = " | "
        if args:
            row = column_separator + column_separator.join(args)
            self.content.append(row)

    def add_section_break(self):
        self.content.append("")

    def output_page(self):
        separator = "-"
        file_name = separator.join(self.name.split()) + ".md"
        dump_dir = 'wiki'
        pathlib.Path(dump_dir).mkdir(parents=True, exist_ok=True)
        output_file = open(os.path.join(dump_dir, file_name), "w+")
        output_file.write(self._build_page())
        output_file.close()


def main():
    if len(sys.argv) > 1:
        wiki = Wiki(sys.argv[1])
        wiki.build_wiki()
    else:
        print("Please supply an input path")


if __name__ == '__main__':
    main()
