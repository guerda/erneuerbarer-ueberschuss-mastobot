# Erneuerbarer Überschuss Mastodon Bot

Dieser Bot auf Mastodon informiert jeden Tag ungefähr um 9 Uhr morgens, falls die Vorhersage für erneuerbare Energien über 100% liegt.
Die Prognose-Daten stammen von https://energy-charts.info.

Das Script nutzt die API von Energy Charts (https://api.energy-charts.info/).

Der Bot läuft aktuell unter https://ruhr.social/@erneuerbarer_ueberschuss

Permissions
===========
Diese Permissions braucht die Mastodon-Applikation, um Beiträge mit Medien zu veröffentlichen:

* read
* write:statuses
* write:media

Installation
============

pipenv install oder pipenv install --dev sollte ausreichen

Danach muss für die Screenshots Folgendes ausgeführt werden:

pipenv shell
playwright install

Damit wird Chromium installiert, mit dem die Screenshots erzeugt werden.