import os
import pathlib
from typing import List

import requests
from PIL import Image
from bs4 import BeautifulSoup

from wiki_page import WikiPage
from mod_repository import ModRepository

# assembles all pages and provides internal wiki links
class ModWiki:
    def __init__(self, source_dir):
        self.source_dir: str = source_dir
        self.vanity_source_dir: str = os.path.join(source_dir, "Items", "Vanity", "")
        self.package_name = "generate_terraria_mod_wiki"
        self.wiki_url_base: str = "/Qubus0/JourneyTrend/wiki/"
        self.repo_url_base: str = "/Qubus0/JourneyTrend/tree/master/"
        self.repo_url_file_base: str = "/Qubus0/JourneyTrend/blob/master/"
        self.pages: List[WikiPage] = list()
        self.item_id_table = self.get_id_table_from_terraria_wiki("https://terraria.fandom.com/Item_IDs")
        self.npc_id_table = self.get_id_table_from_terraria_wiki("https://terraria.fandom.com/wiki/NPC_IDs")
        self.mod_repository = ModRepository(self.source_dir)


    @staticmethod
    def get_id_table_from_terraria_wiki(wiki_url):
        page = requests.get(wiki_url)
        soup = BeautifulSoup(page.content, "html.parser")
        table = soup.find(class_="sortable")
        return table

    @staticmethod
    def _build_web_link(text: str, url: str) -> str:
        separator = ""
        return separator.join(["[", text, "]", "(", url, ")"])

    def build_mod_wiki_web_link(self, text: str, page_name: str) -> str:
        return self._build_web_link(text, self.wiki_url_base + page_name)

    @staticmethod
    def _build_image(text: str, url: str) -> str:
        separator = ""
        return separator.join(["![", text, "]", "(", url, ")"])

    def build_repo_image_link(self, text: str, rest_path: str) -> str:
        return self._build_image(text, self.repo_url_file_base + rest_path)

    def build_terraria_wiki_link(self, text: str, path: str) -> str:
        return self._build_web_link(text, f"https://terraria.fandom.com{path}")

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



    def transfer_coin_images(self):
        wiki_coin_dir = os.path.join("wiki", "images", "coins")
        pathlib.Path(wiki_coin_dir).mkdir(parents=True, exist_ok=True)
        coin_dir = os.path.join(self.package_name, "coins")
        for root, directories, files in os.walk(coin_dir):
            for file in files:
                coin = Image.open(os.path.join(coin_dir, file))
                coin.save(os.path.join(wiki_coin_dir, file))

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

    def build_image_from_path(self, alt_text: str, image_path: str) -> str:
        if pathlib.Path(image_path).exists():
            return self._build_image(alt_text, os.path.join("../", image_path))
        else:
            print(f"file not found at: {image_path}")
            return "-"


    def build_full_set_image(self, set_name: str) -> None:
        pass
        final_image = Image.new("RGBA", (40, 56), (0, 0, 0, 0))
        parts = ["head", "body", "legs", "hands", "hair", "altHair"]
        for part in parts:
            if ModRepository.has_texture(set_name, part):
                temp = Image.open(os.path.join(self.package_name, "player", part.capitalize() + ".png"))
                final_image.paste(temp, (0, 0), temp.convert("RGBA"))

        wiki_dir = os.path.join("wiki", "images")
        pathlib.Path(wiki_dir).mkdir(parents=True, exist_ok=True)
        base_path = ModRepository.get_set_item_base_path_from_name(set_name)
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
        self.build_set_catalog()
        self.build_set_pages()
        self.output_pages()


    def get_set_variants_images(self, set_name: str):
        parts = {
            "head": [],
            "body": [],
            "legs": [],
            "bag": []
        }
        directory_path = ModRepository.get_set_directory_path_from_name(set_name)
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
        unsorted_sets = os.listdir(self.vanity_source_dir)
        return sorted(unsorted_sets, key=lambda s: s.casefold())

    def build_set_catalog(self):
        num_sets = 0
        page = WikiPage("Vanity Set Catalog")
        alphabetical_list = self.get_sorted_sets()
        page.add_table_header(": :", "Set Name")
        for vanity_set in alphabetical_list:
            num_sets += 1
            link = self.build_mod_wiki_web_link(vanity_set, vanity_set)
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
            page.add_row("---")
            previous_index = index - 1
            next_index = (index + 1) % len(alphabetical_list)
            previous_vanity_set = alphabetical_list[previous_index].capitalize()
            next_vanity_set = alphabetical_list[next_index].capitalize()
            previous_text = "Previous (%s)" % previous_vanity_set
            next_text = "Next (%s)" % next_vanity_set
            previous_link = self.build_mod_wiki_web_link(previous_text, previous_vanity_set)
            next_link = self.build_mod_wiki_web_link(next_text, next_vanity_set)
            page.add_table_header(previous_link, next_link)
            page.add_section_break()
            catalog_link = self.build_mod_wiki_web_link("< Back to Vanity set Catalog", "Vanity-Set-Catalog")
            page.add_table_header(catalog_link)
            self.pages.append(page)
            # break  # a break here generates a single set page for testing


    def build_vanity_set_page(self, vanity_set_name):
        # vanity_set_name = "Granite"  #                testing a specific set
        print(f"generating page for {vanity_set_name} ")
        page = WikiPage(vanity_set_name)
        self.build_full_set_image(vanity_set_name)
        # base set image, artist info
        un_pascal_cased_name = "".join([f" {char}" if char.isupper() else char for char in vanity_set_name]).lstrip(" ")
        heading = f"# {un_pascal_cased_name}"
        page.add_row(heading)
        vanity_set = self._build_image(vanity_set_name, os.path.join("images", vanity_set_name + ".png"))
        page.add_table_header(":" + vanity_set + ":")
        artist = ModRepository.get_artist_credit(self.mod_repository, vanity_set_name)
        assistants = ModRepository.get_assistant_credit(self.mod_repository, vanity_set_name)
        page.add_table_row(f"`{artist}` <br> {assistants}")
        page.add_section_break()

        section_heading = "## Set"
        page.add_row(section_heading)
        page.add_table_header("Name", ": :", "Tooltip")
        set_parts = ["head", "body", "legs", "bag"]
        for part in set_parts:
            name = ModRepository.get_item_name_from_set_name_and_part(vanity_set_name, part)
            tooltip = ModRepository.get_item_tooltip_from_set_name_and_part(vanity_set_name, part)
            item_image = self.build_item_image_link_from_set_name_and_part(vanity_set_name, part)
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
        page.add_row("### Obtaining")
        if ModRepository.is_crafted(vanity_set_name):
            page.add_row("#### Crafting")
            page.add_table_header(":Part:", "Ingredients", "Crafting Station", "Near Liquid")
            set_parts = ["head", "body", "legs"]
            for part in set_parts:
                item_image = self.build_item_image_link_from_set_name_and_part(vanity_set_name, part)
                ingredients, craftingStation, liquids = "-", "-", "-"
                if item_image != "-":
                    ingredients, craftingStation, liquids = ModRepository.get_crafting_recipe_from_set_name_and_part(
                        vanity_set_name, part)
                page.add_table_row(item_image, ingredients, craftingStation, liquids)
        elif ModRepository.is_bought(vanity_set_name):
            page.add_row("#### Bought")
            page.add_table_header(":Part:", ":NPC:", "Price")
            set_parts = ["head", "body", "legs"]
            for part in set_parts:
                item_image = self.build_item_image_link_from_set_name_and_part(vanity_set_name, part)
                npc_wiki_image_and_link, price = ModRepository.get_shop_info(vanity_set_name, part)
                page.add_table_row(item_image, npc_wiki_image_and_link, price)
        elif ModRepository.is_dropped(vanity_set_name):
            page.add_row("#### Dropped by")
            page.add_table_header(":Part:", ":Entity:", ":Rate:")
            set_parts = ["head", "body", "legs", "bag"]
            for part in set_parts:
                item_image = self.build_item_image_link_from_set_name_and_part(vanity_set_name, part)
                droprate_and_entity_list = ModRepository.get_droprate_and_entity_wiki_info_from_loots_file(vanity_set_name, part)
                for droprate_and_entity in droprate_and_entity_list:
                    page.add_table_row(item_image, droprate_and_entity[0], droprate_and_entity[1])
        return page


