# JourneyTrend-WikiGenerator

This repository generates and updates the [Journey's Trend Mod Wiki][1] via a python script and GitHub Actions.

Since the Journey's Trend Mod has a rather simple and repeating structure, generating a page for each vanity set isn't too complicated.


The generation process includes:
* gathering the following item data from the Mod files (mostly through regex)
  * credit for the set artist (since this mod is a result of the [Journey's End Vanity Contest][2])
  * the name, tooltips and, if they exist, the crafting recipe or item price from each item file
  * dropchances from the NPCLoots file
  * the npc that sells the item from the NPCShops file
* gathering item images from the mod files and building links to them
* building a preview image of the whole set on a character (with Pillow) by doing the following
  * info about which part of the character is visible when wearing an item is gathered
  * if it is visible, a corresponding image of the character part is pasted
  * all equipped set item images get cropped and pasted on top
* and web scraping [the official Terraria Wiki][3] for in-game names, links and images
  * the [Item ID][4] table for all items in crafting recipies
  * the [NPC ID][5] table for every NPC that drops a modded item


But still, some nuances are left out: for example some sets have aditional items (wings, most of the time), which are not read by the python script.

---
This project was heavily inspired by the [sample-programs-wiki-generator][6].


[1]: https://github.com/Qubus0/JourneyTrend/wiki
[2]: https://forums.terraria.org/index.php?threads/journeys-end-vanity-contest.86211
[3]: https://terraria.fandom.com/wiki/Terraria_Wiki
[4]: https://terraria.fandom.com/Item_IDs
[5]: https://terraria.fandom.com/wiki/NPC_IDs
[6]: https://github.com/TheRenegadeCoder/sample-programs-wiki-generator
