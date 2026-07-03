# Source Quality Skill

## Ucel

Tento skill pouziva Analysis/Synthesis Agent pro hodnoceni kvality zdroju nalezenych Research Agentem.

## Kdy skill pouzit

Pouzij ho vzdy, kdyz Analysis Agent dostane seznam webovych zdroju a ma rozhodnout, jak moc se o ne muze finalni odpoved opirat.

## Rubrika hodnoceni zdroje

Kazdy zdroj ohodnot skore 1-5:

- 5: Primarni nebo vysoce autoritativni zdroj. Napriklad oficialni dokumentace, statni instituce, akademicky paper, oficialni firemni report nebo puvodni data.
- 4: Duveryhodny sekundarni zdroj s jasnym autorem, datem a odkazy na puvodni zdroje.
- 3: Bezny odborny clanek, blog nebo media clanek, ktery muze byt uzitecny, ale tvrzeni je vhodne overit jinde.
- 2: Marketingovy, nejasny nebo jednostranny zdroj. Pouzij jen pro kontext, ne pro silne zavery.
- 1: Slaby zdroj bez jasne autority, data, autora nebo s podezrenim na spekulace.

## Faktory

Pri hodnoceni sleduj:

- Autorita: kdo zdroj vydal a zda ma k tematu primarni vztah.
- Aktualnost: zda je zdroj dostatecne novy pro danou otazku.
- Relevance: zda zdroj odpovida primo na otazku uzivatele.
- Overitelnost: zda obsahuje konkretni fakta, data, odkazy nebo metodiku.
- Bias: zda jde hlavne o marketing, PR nebo jednostranny pohled.

## Vystup pro agenta

U kazdeho zdroje vrat:

- nazev zdroje,
- URL, pokud je k dispozici,
- skore 1-5,
- jednovetny duvod hodnoceni.

Pokud je zdroju malo nebo jsou slabe, Analysis Agent to musi zapsat do `risks_or_uncertainties`.

