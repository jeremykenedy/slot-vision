# Configuration

The app launcher opens remote-friendly settings. D-pad Up and Down move between rows, Select opens choices or preview, and Back closes preview or settings. The scene contains no text overlay.

The app-owned provider is `content://com.jeremykenedy.reelatrium.settings`. Query `/schema` for `key`, `title`, `type`, `default`, `choices` and `randomAllowed`; query `/settings` for current `key` and `value`. Update `/settings` with `key` and `value` strings. Unknown routes, keys and values are rejected. The provider deliberately exposes visual preferences to local host apps; no identity or private data is stored there.

| Key | Values | Default |
| --- | --- | --- |
| game | classic, palace, garden, random | classic |
| season | atrium, spring, summer, autumn, winter, random | atrium |
| speed | relaxed, natural, lively, random | natural |
| brightness | dim, cinematic, bright, random | cinematic |
| camera | gentle, wide, random | gentle |
| background | lounge, casino, random | lounge |
| view | cabinet, fullscreen, random | cabinet |

Changes apply when the scene next starts. Random resolves independently for the selected setting. Cabinet mode keeps a continuous slow drift. Fullscreen mode fills the display with the spinning reels, without a cabinet, scenery or fixed overlay. The cabinet camera follows an approximately 90 second front orbit with independent horizontal and vertical drift. Brightness scales the cabinet lighting. Seasonal themes change cabinet lighting and metal colors. Classic uses traditional BAR and 7 artwork; palace and garden use seasonal symbols. Classic pays the center horizontal line. Palace pays three horizontal and two V shaped lines. Garden pays five horizontal lines. Matching symbols from the leftmost reel trigger simulated payouts and proportional coin bursts, with up to 64 instances for ordinary wins and up to 192 for jackpots. Jackpot showers continually replenish coins for ten seconds; smaller wins have shorter showers. The first round and every twelfth round show a jackpot; at least every third round shows a win. These are decorative outcomes without stored currency, wagers or purchases.

Integration identity: ID `slot-vision`, package `com.jeremykenedy.reelatrium`, dream `com.jeremykenedy.reelatrium/.ReelAtriumDreamService`, settings `com.jeremykenedy.reelatrium/.SettingsActivity`, minimum API 23. Release assets are `slot-vision.apk` and `slot-vision.apk.sha256` in `jeremykenedy/slot-vision`.
