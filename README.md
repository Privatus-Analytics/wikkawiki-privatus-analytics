# Privatus Analytics for WikkaWiki

**Real visitor numbers for your wiki. No cookies, no cookie pop-up, no bots.**

You want to know if people read your wiki. But Google Analytics uses cookies,
so in many countries you must show a cookie pop-up first (the box that asks
visitors to say yes to cookies). Many people click no, so they never show up in
your numbers. Bots add fake visits on top.

This action adds the Privatus Analytics script to your WikkaWiki pages. You add
one line to your theme and two lines to your settings file. Your own visits are
not counted while you are logged in as an admin, unless you turn that off. The
script sets no cookies and keeps no IP addresses. Bots are filtered out before
they are counted.

So you see how many real people came, which pages they read and where they
came from, on one simple dashboard. A report comes to your inbox each week, and
you can set alerts for when traffic jumps or drops.

**Free plan, no card:** 10,000 events a month (an event is a page view or an action you track) on up to 3 sites. [Start free at privatusanalytics.com](https://privatusanalytics.com).

- **No cookies.** No cookies and no hidden IDs on your visitors' devices, and no IP
  addresses are kept. Laws differ by country, so check your own legal advice.
- **Real people, not bots.** Known bots, data centers and spam visits are left
  out on every plan.
- **Small and fast.** The script is about 3 KB when compressed.

## Requirements

- WikkaWiki 1.3 or later (tested on 1.4.2 with PHP 7.4).
- A Privatus Analytics site ID. It starts with `pa_`. You find it in Privatus
  Analytics under Site settings, Tracking.

## Install

1. Download the [main branch zip](https://github.com/Privatus-Analytics/wikkawiki-privatus-analytics/archive/main.zip).
2. Copy the folder `plugins/actions/privatusanalytics` into the `plugins/actions`
   folder of your wiki.
3. Open `wikka.config.php` and add your site ID inside the `$wakkaConfig` array:

   ```php
   'privatus_site_id' => 'pa_YOURSITEID',
   ```

4. Open `templates/<your theme>/header.php` (the theme is `light` unless you
   changed it) and add this line just before `</head>`:

   ```php
   <?php echo $this->Action('privatusanalytics'); ?>
   ```

Open your wiki in a private window and look at the page source. You will see
the script just before `</head>`.

## Settings

All settings go in `wikka.config.php`.

| Setting | Default | What it does |
|---|---|---|
| `privatus_site_id` | empty | Your site ID, like `pa_ABC123`. Leave it empty to turn tracking off. |
| `privatus_modules` | `engage,auto,vitals,clicks,ask` | Extra tracking to load. Leave out any you don't want. |
| `privatus_skip_admins` | `1` | Set to `0` to count admins too. |

The modules:

| Module | What it tracks |
|---|---|
| `engage` | Time on page and scroll depth |
| `auto` | Clicks on outside links, file downloads, form sends and 404 pages |
| `vitals` | Page speed (Core Web Vitals) |
| `clicks` | Click maps |
| `ask` | Short on-site surveys |

The action prints this tag:

```html
<script defer src="https://privatusstats.com/js/pa.js" data-site="pa_YOURSITEID" data-modules="engage,auto,vitals,clicks,ask"></script>
```

A site ID that does not match `pa_` plus letters and numbers is ignored, so a
typo can never break your page. The tag is printed once per page, even if the
action is called twice.

## Using it on one page only

You can also put the action in a page instead of the theme:

```
{{privatusanalytics site="pa_YOURSITEID" modules="engage,vitals"}}
```

Then only that page is tracked. Both parts are optional when the settings file
has them.

## Development

```sh
php tests/ActionTest.php        # tag builder tests
./scripts/verify-docker.sh      # real WikkaWiki 1.4.2 + MariaDB in Docker
```

`verify-docker.sh` runs the Wikka installer, adds the line to the theme, and
checks the page as a visitor and as a logged-in admin.

## Licence

MIT, see [LICENSE](LICENSE). Copyright (c) 2026 Two Phase LLC.
