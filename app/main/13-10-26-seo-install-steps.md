# Jambo SEO install steps (13-10-26)

Tested on a scratch copy of your repo: `/robots.txt`, `/sitemap.xml`, and the head tags on home, room list, room detail, hidden room and other pages all render correctly. Nothing in your own files has been changed. Apply these by hand, since your local `base.html` already has the PWA lines.

## 1. Add the new file

Copy `seo.py` to `app/main/seo.py`. (Exception to the date-prefix naming rule: Python needs an importable name.)

## 2. Register it in `app/__init__.py`

Next to the other blueprint imports:
```python
        from app.main.seo import seo
```
Next to the other `register_blueprint` calls:
```python
        app.register_blueprint(seo)
```

## 3. `app/templates/base.html`

a) Change line 2 to:
```html
<html lang="{{ current_language or 'en' }}">
```

b) Replace the whole `{% if title %} ... {% endif %}` title block (lines 8 to 13) AND the `<meta name="keywords" ...>` tag below `csrf-token` with this. Leave your `csrf-token` meta and your favicon/manifest lines as they are.
```html
  <title>{% block page_title %}{% if title %}{{ _("Jambo") }} - {{ _(title) }}{% else %}{{ _("Jambo") }}{% endif %}{% endblock %}</title>

  <!-- SEO: description, canonical, social cards. Pages override the
       blocks below (see roomdetails.html); everything else inherits
       these defaults. -->
  <meta name="description" content="{% block meta_description %}{{ _('Book rooms, residences and short stays across Africa. Starting in Abidjan, Côte d\'Ivoire. Pay securely in CFA francs.') }}{% endblock %}" />
  <link rel="canonical" href="{{ canonical_url }}" />
  {% block meta_robots %}{% endblock %}
  <meta property="og:site_name" content="Jambo" />
  <meta property="og:type" content="{% block og_type %}website{% endblock %}" />
  <meta property="og:url" content="{{ canonical_url }}" />
  <meta property="og:title" content="{{ self.page_title() }}" />
  <meta property="og:description" content="{{ self.meta_description() }}" />
  <meta property="og:image" content="{% block og_image %}{{ abs_url(url_for('static', filename='img/pwa/11-10-26-jambo-icon-512.png')) }}{% endblock %}" />
  <meta name="twitter:card" content="summary" />
  {% if google_site_verification %}<meta name="google-site-verification" content="{{ google_site_verification }}" />{% endif %}
  {% if bing_site_verification %}<meta name="msvalidate.01" content="{{ bing_site_verification }}" />{% endif %}
  {% block seo_jsonld %}{% endblock %}
```
The generic `keywords` tag ("bootstrap, dashboard, ui kit...") is removed on purpose: search engines ignore keywords, and that text describes a template, not Jambo.

## 4. `app/templates/pages/roomdetails.html`

Your first lines are `{% extends ... %} {% from ... %} {% from ... import ... %} {%` then `block head_css %}` on the next line. Put a new line break right before that last `{%` (the one that starts `block head_css`) and paste this there:
```html
{% block page_title %}{{ roominfo.room_name }} - {{ roominfo.room_category }}, {{ roominfo.borough }}, {{ roominfo.room_location }} | Jambo{% endblock %}
{% block meta_description %}{{ _('%(room)s in %(place)s: %(desc)s. From %(price)s per night. Book on Jambo.', room=roominfo.room_name, place=roominfo.borough ~ ', ' ~ roominfo.room_location, desc=roominfo.short_desc|trim('. '), price=roominfo.room_currency ~ ' ' ~ ('%g'|format(roominfo.price|float))) }}{% endblock %}
{% block meta_robots %}{% if roominfo.status != 'Available' %}<meta name="robots" content="noindex, nofollow" />{% endif %}{% endblock %}
{% block og_image %}{{ abs_url(get_room_image_url(roominfo.image1)) }}{% endblock %}
{% block seo_jsonld %}
{% set ld = {
  "@context": "https://schema.org",
  "@type": "LodgingBusiness",
  "name": roominfo.room_name,
  "description": roominfo.short_desc,
  "url": canonical_url,
  "image": abs_url(get_room_image_url(roominfo.image1)),
  "priceRange": roominfo.room_currency ~ " " ~ ("%g"|format(roominfo.price|float)),
  "address": {
    "@type": "PostalAddress",
    "addressLocality": roominfo.room_location,
    "addressRegion": roominfo.borough,
    "addressCountry": roominfo.room_country
  }
} %}
{% if roominfo.latitude is not none and roominfo.longitude is not none %}
{% set _u = ld.update({"geo": {"@type": "GeoCoordinates", "latitude": roominfo.latitude, "longitude": roominfo.longitude}}) %}
{% endif %}
{% if totalrev %}
{% set _u = ld.update({"aggregateRating": {"@type": "AggregateRating", "ratingValue": revscore, "reviewCount": totalrev}}) %}
{% endif %}
<script type="application/ld+json">{{ ld|tojson }}</script>
{% endblock %}
```

## 5. `app/templates/pages/homes.html`

The first line is `{% extends "base.html" %} {% block head_css %} {{ super() }}`. Put a line break between `{% extends "base.html" %}` and `{% block head_css %}` and paste this in between:
```html
{% block page_title %}{{ _('Jambo | Rooms and short stays in Abidjan and across Africa') }}{% endblock %}
{% block seo_jsonld %}
<script type="application/ld+json">{{ {
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Jambo",
  "url": site_url,
  "logo": abs_url(url_for('static', filename='img/pwa/11-10-26-jambo-icon-512.png'))
}|tojson }}</script>
{% endblock %}
```

## 6. French translations

Add the entries from `13-10-26-seo-fr-translations.po.txt` to `app/translations/fr/LC_MESSAGES/messages.po`, then run `pybabel compile -d app/translations`.

## 7. After deploy

1. Open `https://jambo.tbossci.com/robots.txt` and `/sitemap.xml` and check both load.
2. In Search Console, add the property, choose the HTML tag method, copy the `content` value, and set it on the VPS as `GOOGLE_SITE_VERIFICATION=<value>` in your Docker env file, then restart the container. The tag appears automatically. (Same for Bing with `BING_SITE_VERIFICATION`.) Click Verify.
3. Sitemaps, then submit `sitemap.xml`.
4. URL Inspection, paste your home page URL and "Request indexing". Do the same for 2 or 3 room pages.
5. Test a room page in Google's Rich Results Test.
