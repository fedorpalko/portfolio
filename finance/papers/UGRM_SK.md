## Téza

V tejto práci sa pokúšam preskúmať a rozvinúť samostatný a jednoduchý vzorec pre EV (expected value – očakávanú hodnotu) na jeden obchod. Mojím cieľom je nakoniec definovať $G$ ako štandardný univerzálny model miery rastu – teda percento, o ktoré váš kapitál narastie pri každom obchode. $G$ zohľadňuje zložené úročenie, erózriu spôsobenú poplatkami, volatilitu a neistotu ohľadom miery úspešnosti. Chcem to urobiť tak, aby to bolo zároveň dostatočne jednoduché na pochopenie pre kohokoľvek, no zároveň dostatočne komplexné na to, aby bolo štatisticky správne a použiteľné pre reálne obchodné stratégie – vrátane mojich vlastných.

## Sekcie

1. [Uniformný model EV](#1-uniformný-model-ev)
2. [Uniformný model EV (Poplatky a provízie)](#2-uniformný-model-ev-poplatky-a-provízie)
3. [Volatilný model EV](#3-volatilný-model-ev)
4. [Volatilný model EV (Neistá miera úspešnosti)](#4-volatilný-model-ev-neistá-miera-úspešnosti)
5. [Univerzálny model miery rastu](#5-univerzálny-model-miery-rastu)
6. [Záver](#6-záver)

---

## 1. Uniformný model EV

### Téza

Začíname jednoduchým Uniformným modelom EV, ktorý vracia očakávaný zisk na jeden obchod v dolároch alebo inej zvolene mene.
Vychádza z jednoduchu definície očakávanej hodnoty pre obchody: očakávaná hodnota je súčet všetkých možných výsledkov vynásobených ich pravdepodobnosťami.

Definujme si premenné:
- $\omega$ – pravdepodobnosť výhry v obchode
- $\bar{R}$ – hodnota odmeny pri fixnom pomere riziko/odmena (príklad: RR je 1:1,5, teda $\bar{R} = 1,5$)
- $S$ – stávka na obchod, napr. veľkosť pozície v reálnej mene
- $L$ – páka na zosilnenie veľkosti pozície, ako prirodzené číslo
- $\rho$ – naša očakávaná hodnota na jeden obchod

### Definícia

Teraz môžeme definovať vzorec pre $\rho$:

$$\boxed{\rho = (\omega \cdot S \cdot L \cdot \bar{R}) - ((1 - \omega) \cdot S \cdot L)}$$

Tento vzorec je intuitívny, no nezohľadňuje poplatky ani volatilitu. Dá sa použiť v backtestoch ako hrubý odhad, ak už máte definovanú mieru úspešnosti a všetky potrebné informácie – jednoducho chcete EV za predpokladu, že sa všetko odohralo presne takto.

### Príklad

Povedzme, že máme stratégiu, ktorú sme backtestovali a dostali sme nasledovné výsledky:
- Miera úspešnosti: 60 %
- Pomer odmena:riziko (RR): 1:2
- Stávka: 50 $
- Páka: 2x

Teraz vypočítame EV pomocou nášho vzorca:

$$\rho = (0{,}60 \cdot \$50 \cdot 2 \cdot 2) - ((1 - 0{,}60) \cdot \$50 \cdot 2)$$
$$\rho = (0{,}60 \cdot \$200) - (0{,}40 \cdot \$100)$$
$$\rho = \$120 - \$40$$
$$\rho = \$80$$

To znamená, že v priemere môžeme očakávať zisk 80 $ na každý obchod pri tejto stratégii. Aj keď by sme z toho mohli jasať, akákoľvek stratégia, ktorá na papieri vyzerá robustne, môže ľahko zlyhať – pretože trh je nelineárny.

---

## 2. Uniformný model EV (Poplatky a provízie)

### Téza

$\rho$ už máme definované, čo nám tu veľmi pomôže. V tejto sekcii zavedieme do výpočtov EV poplatky a provízie. Pozrime sa najprv na pôvodný vzorec:

$$\boxed{\rho = (\omega \cdot S \cdot L \cdot \bar{R}) - ((1 - \omega) \cdot S \cdot L)}$$

### Definícia

Ak chceme zahrnúť poplatky, musíme definovať $f$ – premennú reprezentujúcu, koľko reálnej meny stratíme na jeden obchod z dôvodu poplatkov burzy.

$$\boxed{f = (f_e + f_x) \cdot S}$$

Tu $f_e$ je sadzba vstupného poplatku burzy vyjadrená ako desatinné číslo, $f_x$ je sadzba výstupného poplatku burzy vyjadrená ako desatinné číslo a $S$ je naša stávka.

Kombináciou oboch dostaneme výsledný Uniformný model EV (UM):

$$\boxed{UM = (\omega \cdot S \cdot L \cdot \bar{R}) - ((1 - \omega) \cdot S \cdot L) - f}$$

Alebo v rozvinutom tvare:

$$\boxed{UM = (\omega \cdot S \cdot L \cdot \bar{R}) - ((1 - \omega) \cdot S \cdot L) - (f_e + f_x) \cdot S \cdot L}$$

Pôvodný model sme úspešne rozšírili a teraz sme do výpočtov zahrnuli poplatky a provízie. Môžeme predpokladať, že tento model vracia presnejšie výsledky, no v podstate je to stále len pôvodný uniformný model – akurát teraz realistickejší.

### Príklad

Povedzme, že máme stratégiu, ktorú sme backtestovali a dostali nasledovné výsledky:
- Miera úspešnosti: 60 %
- Pomer odmena:riziko (RR): 1:2
- Stávka: 50 $
- Páka: 2x
- Poplatky burzy: 0,2 % vstup a 0,2 % výstup

Teraz vypočítame očakávanú hodnotu $\rho$ pomocou nášho vzorca:

$$\rho = (0{,}60 \cdot \$50 \cdot 2 \cdot 2) - ((1 - 0{,}60) \cdot \$50 \cdot 2) - (0{,}002 + 0{,}002) \cdot \$50$$
$$\rho = (0{,}60 \cdot \$200) - (0{,}40 \cdot \$100) - (0{,}004) \cdot \$50 \cdot 2$$
$$\rho = \$120 - \$40 - \$0{,}4$$
$$\rho = \$80 - \$0{,}4$$
$$\rho = \$79{,}6$$

V porovnaní s naším pôvodným výsledkom UM dostávame číslo síce len o 0,40 $ nižšie – ale predstavte si, čo by to znamenalo pri stratégii obchodujúcej s 50 000 000 $. Poplatok by bol 400 000 $. Astronomické. Ďalšie sekcie ukážu, ako poplatky a ich postupnú eróziu zohľadniť dôkladnejšie.

---

## 3. Volatilný model EV

### Téza

Reálny trh nie je lineárny. Dokonca aj pri dobre backtestovanej stratégii sa výsledky jednotlivých obchodov budú odchyľovať od očakávanej hodnoty $\rho$ kvôli volatilite – predčasným výstupom, sklzu (slippage), náhlym trhovým pohybom a šumu. Uniformný model EV predpokladá, že každý víťazný obchod vráti presne $S \cdot L \cdot \bar{R}$ a každý stratový obchod stratí presne $S \cdot L$. Je to užitočná abstrakcia, ale nie je to realita.

Táto sekcia zavádza $\sigma$ – smerodajnú odchýlku výsledkov P&L (zisk/strata) na jeden obchod odvodenej z backtestových dát – ako mieru tejto odchýlky. Kľúčové je, že volatilita nie je neutrálna: hoci $\varepsilon$ je podľa definície symetrické okolo nuly, záporné odchýlky sa skladajú asymetricky a erodujú kapitál rýchlejšie, než ho ekvivalentné kladné odchýlky dokážu obnoviť. Výsledný model uvažuje s P&L každého obchodu ako s náhodnou premennou namiesto fixného výsledku – čo z tejto sekcie robí prvú, ktorá vyžaduje reálne backtestové dáta namiesto predpokladaných parametrov (nebojte sa však – po backteste ich ľahko odvodíte!).

Preto dostávame niečo, čo funguje naprieč viacerými obchodmi a lepšie vypovedá o sile stratégie.

### Premenné

Nadväzujúc na všetky premenné zo sekcií 1 a 2, zavádzame:

- $\sigma$ – smerodajná odchýlka výsledkov P&L na jeden obchod, odvodená z backtestových dát
- $\varepsilon$ – náhodná perturbácia na jeden obchod, vybraná z normálneho rozdelenia so strednou hodnotou $0$ a rozptylom $\sigma^2$ – v podstate náhodný šum okolo $\rho$
- $\tilde{\rho}$ – volatilná očakávaná hodnota na jeden obchod (náhodná premenná vyberaná z rozdelenia)
- $n$ – počet obchodov v backtestovej vzorke
- $r_i$ – P&L $i$-teho obchodu v backtest

### Odvodenie $\sigma$

Chceme kvantifikovať, ako veľmi sa výsledky jednotlivých obchodov rozptýlia okolo priemeru P&L $\bar{r}$. Prirodzenou mierou rozptylu je **rozptyl (variancia)** – priemerná kvadratická odchýlka od priemeru naprieč všetkými obchodmi v našej backtestovej vzorke:

$$\text{Var} = \frac{1}{n-1}\sum_{i=1}^{n}(r_i - \bar{r})^2$$

Poznamenajme, že delíme $n-1$ namiesto $n$. Toto je tzv. **Besselova korekcia** – pri odhadovaní rozptylu zo vzorky namiesto celej populácie dáva delenie $n-1$ nestranný odhad. Delenie $n$ by systematicky podceňovalo skutočný rozptyl.

Keďže rozptyl je vyjadrený v kvadratických jednotkách meny, nie je priamo interpretovateľný. Odmocnením sa vrátime späť do pôvodných jednotiek:

$$\boxed{\sigma = \sqrt{\frac{1}{n-1} \sum_{i=1}^{n}(r_i - \bar{r})^2}}$$

Toto je štandardná smerodajná odchýlka vzorky – dobre etablovaná štatistická miera. Väčšia $\sigma$ indikuje chaotickejšiu stratégiu so širšími výkyvmi výsledkov; menšia $\sigma$ indikuje tesnejšie a predvídateľnejšie výsledky obchodov.

### Definícia

Náhodnú perturbáciu $\varepsilon$ definujeme ako hodnotu vyberanú z normálneho rozdelenia – symetrickej zvonkovej krivky – sústredene okolo nuly s rozptylom určeným hodnotou $\sigma$:

$$\varepsilon \sim \mathcal{N}(0, \sigma^2)$$

Zápis $\mathcal{N}(\mu, \sigma^2)$ označuje normálne rozdelenie so strednou hodnotou $\mu$ a rozptylom $\sigma^2$. Stredná hodnota nula znamená, že predpokladáme žiadne systematické smerové skreslenie – iba náhodný šum okolo očakávaného výsledku. Kladné $\varepsilon$ znamená, že obchod prekonával $\rho$; záporné $\varepsilon$ znamená, že zaostal za $\rho$.

Volatilná očakávaná hodnota na jeden obchod je potom:

$$\boxed{\tilde{\rho} = (\omega \cdot S \cdot L \cdot \bar{R}) - ((1 - \omega) \cdot S \cdot L) - (f_e + f_x) \cdot S \cdot L + \varepsilon}$$

Z toho vyplýva, že $\mathbb{E}[\tilde{\rho}] = \rho$ – v priemere volatilný model vracia rovnaký výsledok ako sekcia 2. Každý jednotlivý obchod však môže signifikantne odchýliť v oboch smeroch. Dostatočne záporné $\varepsilon$ môže premeniť teoreticky ziskový obchod na stratu a naprieč mnohými zloženými obchodmi sa táto variancia kumuluje do zmysluplnej erózie kapitálu – aj keď $\rho > 0$.

### Príklad

S rovnakými parametrami ako predtým:
- Miera úspešnosti: 60 %
- RR: 1:2
- Stávka: 50 $
- Páka: 2x
- Poplatky: 0,2 % vstup, 0,2 % výstup
- Backtestová $\sigma$: 15 $ (odhadnutá z histórie obchodov)

Zo sekcie 2 už vieme, že $\rho = \$79{,}92$. Teraz jeden obchod môže realisticky dosiahnuť:

$$\tilde{\rho} = \$79{,}92 + \varepsilon, \quad \varepsilon \sim \mathcal{N}(0, 15^2)$$

Každý jednotlivý obchod teda môže skončiť výrazne nad alebo pod $\rho$. Séria obchodov so záporným $\varepsilon$ môže spôsobiť prepad (drawdown) napriek tomu, že stratégia je v očakávaní zisková. Práve preto je $\rho$ samo o sebe nedostatočnou mierou kvality stratégie – a preto sekcia 5 zavádza $G$, mieru rastu, ktorá penalizuje stratégie za ich volatilitu, nielen za ich priemerný výnos.

Ako vidíme, $\tilde{\rho}$ nie je pevné číslo, ale náhodná premenná a – čo je dôležitejšie – náhodné rozdelenie. Je to iná úroveň oproti sekciám 1 a 2, kde sme pracovali s diskrétnou matematikou. Toto budeme potrebovať na skutočné definovanie $G$.

---

## 4. Volatilný model EV (Neistá miera úspešnosti)

### Téza

Volatilný model zo sekcie 3 zaviedol $\varepsilon$ na zohľadnenie skutočnosti, že výsledky jednotlivých obchodov sa odchyľujú od $\rho$ kvôli trhovému šumu. Napriek tomu stále uvažuje s $\omega$ – mierou úspešnosti – ako s fixnou, známou veličinou. V praxi je $\omega$ samotné odhadom odvodeným z konečnej backtestovej vzorky. Stratégia backtestovaná na 20 obchodoch dáva oveľa menej spoľahlivý odhad miery úspešnosti ako tá backtestovaná na 2000 obchodoch, no model zo sekcie 3 zaobchádza s oboma identicky.

Táto sekcia to rieši modelovaním $\omega$ ako normálne rozdelené náhodnej premennej namiesto fixného vstupu. Výsledkom je model s dvoma vrstvami neistoty: zašumené výsledky obchodov ($\varepsilon$) a zašumená miera úspešnosti ($\omega$). Rovnako ako sekcia 3, aj tento model je zámerne neúplný – zatiaľ stratégiu za tieto nakopené neistoty nepenalizuje. To je úlohou $G$ v sekcii 5.

### Premenné

Nadväzujúc na všetky premenné zo sekcií 1–3, zavádzame:

- $\bar{\omega}$ – priemerná miera úspešnosti, odhadnutá ako jednoduchý priemer z backtestových dát
- $\sigma_\omega$ – smerodajná odchýlka odhadu miery úspešnosti, odvodená z veľkosti backtestovej vzorky
- $\omega$ – miera úspešnosti, teraz uvažovaná ako náhodná premenná vyberaná z $\mathcal{N}(\bar{\omega}, \sigma_\omega^2)$

### Odvodenie $\bar{\omega}$

$\bar{\omega}$ je jednoducho podiel víťazných obchodov v backtestovej vzorke. Ak backtest obsahuje $n$ obchodov, z ktorých $n_w$ bolo víťazných:

$$\boxed{\bar{\omega} = \frac{n_w}{n}}$$

Toto je rovnaké $\omega$ použité v sekciách 1–3, teraz explicitne definované ako vzorkový odhad, nie ako známa konštanta.

### Odvodenie $\sigma_\omega$

Každý obchod modelujeme ako nezávislý Bernoulliho pokus – buď vyhráva s pravdepodobnosťou $\bar{\omega}$, alebo prehráva s pravdepodobnosťou $1 - \bar{\omega}$. Toto je v súlade s predpokladom, ktorý je už zabudovaný v sekcii 1.

Pre podiel odhadnutý z $n$ nezávislých Bernoulliho pokusov je štandardná chyba tohto odhadu dobre etablovaným štatistickým výsledkom:

$$\boxed{\sigma_\omega = \sqrt{\frac{\bar{\omega}(1 - \bar{\omega})}{n}}}$$

Tento vzorec zachytáva intuitívny vzťah medzi veľkosťou vzorky a istotou: väčší backtest dáva menšiu $\sigma_\omega$, čo znamená, že odhad miery úspešnosti je dôveryhodnejší. Menší backtest dáva väčšiu $\sigma_\omega$, čo znamená, že skutočná miera úspešnosti sa môže vierohodne výrazne líšiť od $\bar{\omega}$.

Poznamenajme, že $\sigma_\omega$ je plne určená hodnotami $\bar{\omega}$ a $n$ – obomi sú dostupné priamo z backtestových dát. Nie sú potrebné žiadne ďalšie vstupy.

### Definícia

Miera úspešnosti je teraz modelovaná ako náhodná premenná:

$$\omega \sim \mathcal{N}(\bar{\omega}, \sigma_\omega^2)$$

Zápis $\mathcal{N}(\mu, \sigma^2)$ označuje normálne rozdelenie so strednou hodnotou $\mu$ a rozptylom $\sigma^2$ – rovnakú zvonkovú krivku ako v sekcii 3. Tu je rozdelenie sústredené okolo $\bar{\omega}$ s rozptylom určeným $\sigma_\omega$. Miery úspešnosti ďaleko od $\bar{\omega}$ sú možné, no čoraz menej pravdepodobné.

Dosadením do volatilného modelu zo sekcie 3 dostaneme úplnú neistú volatilnú očakávanú hodnotu na jeden obchod:

$$\boxed{\tilde{\rho} = (\omega \cdot S \cdot L \cdot \bar{R}) - ((1 - \omega) \cdot S \cdot L) - (f_e + f_x) \cdot S \cdot L + \varepsilon}$$

Kde $\omega \sim \mathcal{N}(\bar{\omega}, \sigma_\omega^2)$ aj $\varepsilon \sim \mathcal{N}(0, \sigma^2)$ sú teraz náhodné. Vzorec je štruktúrne identický so sekciou 3 – jediná zmena je, že $\omega$ už nie je fixné číslo.

Z toho stále vyplýva, že $\mathbb{E}[\tilde{\rho}] = \rho$, keďže $\mathbb{E}[\omega] = \bar{\omega}$ a $\mathbb{E}[\varepsilon] = 0$. Rozptyl $\tilde{\rho}$ je však teraz väčší ako v sekcii 3, pretože neistota v $\omega$ pridáva druhú vrstvu rozptylu na vrch $\varepsilon$.

### Príklad

S rovnakými parametrami ako predtým, tentokrát s malým backtestom:
- $\bar{\omega} = 0{,}60$, $n = 30$ obchodov
- RR: 1:2, Stávka: 50 $, Páka: 2x
- Poplatky: 0,2 % vstup, 0,2 % výstup
- Backtestová $\sigma$: 15 $

Najprv odvodíme $\sigma_\omega$:

$$\sigma_\omega = \sqrt{\frac{0{,}60 \cdot 0{,}40}{30}} = \sqrt{\frac{0{,}24}{30}} = \sqrt{0{,}008} \approx 0{,}0894$$

Skutočná miera úspešnosti teda môže realisticky padnúť kdekoľvek od ~42 % do ~78 % v rámci dvoch smerodajných odchýlok od $\bar{\omega}$. Pre stratégiu, ktorej ziskovosť závisí od udržania 60 % miery úspešnosti, je toto signifikantná neistota – a taká, ktorú 30-obchodný backtest jednoducho nedokáže vyriešiť.

Porovnajme s backtestom na 1000 obchodov:

$$\sigma_\omega = \sqrt{\frac{0{,}60 \cdot 0{,}40}{1000}} = \sqrt{0{,}00024} \approx 0{,}0155$$

Teraz je miera úspešnosti spoľahlivo v rozsahu ~57 % až ~63 % – oveľa tesnejší a dôveryhodnejší odhad. To ilustruje, prečo veľkosť backtestovej vzorky nie je len technická záležitosť, ale kľúčový vstup do hodnotenia stratégie – a prečo $G$ zo sekcie 5 musí s ňou počítať.

---

## 5. Univerzálny model miery rastu

### Téza

Sekcie 1 až 4 postupne pridávali jednu vrstvu realizmu k pôvodnému vzorcu EV. Sekcia 1 ustanovila základný očakávaný zisk na jeden obchod $\rho$. Sekcia 2 zaviedla eróziu spôsobenú poplatkami. Sekcia 3 zaviedla volatilitu prostredníctvom $\sigma$. Sekcia 4 zaviedla neistotu miery úspešnosti prostredníctvom $\sigma_\omega$. Každý model bol zámerne neúplný – odrazovým mostíkom, nie cieľom.

Táto sekcia je tým cieľom.

$G$ je Univerzálna miera rastu – priemerné percento, o ktoré váš kapitál narastie na jeden obchod, s prihliadnutím na výhodu (edge), poplatky, eróziu spôsobenú volatilitou a neistotu miery úspešnosti súčasne. Je to jediné číslo, ktoré určuje, či sa stratégia oplatí prevádzkovať. $G > 0$ znamená, že váš kapitál rastie. $G < 0$ znamená, že váš kapitál eroduje – aj keď $\rho > 0$. $G = 0$ znamená, že ste na nule po zohľadnení všetkých zdrojov erózie.

Toto je tiež prvá sekcia, ktorá operuje v inom matematickom priestore ako S1–S4. Predošlé sekcie vracali výsledky v surovej mene – očakávaný zisk v dolároch. $G$ je miera (rate), a miery vyžadujú kapitálovú základňu na normalizáciu. To si vyžaduje zavedenie novej premennej $C$, definovanej tu a nie spätne vsadenej do predošlých sekcií, pretože S1–S4 ju nepotrebovali. Toto rozlíšenie je zámerné a čisté.

### Premenné

Nadväzujúc na všetky premenné zo sekcií 1–4, zavádzame jednu novú premennú:

- $C$ – celkový obchodný kapitál v mene. Toto je celková veľkosť vášho účtu, nie suma nasadená na jeden obchod.

Tiež predefinujeme $S$ v kontexte $G$:

- $S$ – veľkosť pozície ako desatinný zlomok z $C$, kde $S \in (0, 1)$. Napríklad $S = 0{,}10$ znamená, že na jeden obchod je nasadených 10 % kapitálu. Skutočná nasadená suma v mene je teda $S \cdot C$.

Toto predefinovanie nie je v rozpore s S1–S4, kde bol $S$ pre jednoduchosť uvádzaný ako surová suma v mene. V tých sekciách bol $S$ konkrétna čiastka v dolároch, pretože výstupom boli tiež doláre. Tu sa $S$ stáva zlomkom, pretože výstupom je miera. Obe použitia sú konzistentné v ich príslušných matematických kontextoch.

### Odvodenie G

$G$ je skonštruované z troch komponentov, z ktorých každý reprezentuje odlišnú silu pôsobiacu na váš kapitál.

**Komponent 1 — Základná miera rastu**

Prvý komponent je jednoducho váš očakávaný zisk na jeden obchod $\rho$ zo sekcie 2, normalizovaný celkovým kapitálom $C$:

$$G_1 = \frac{\rho}{C} = \frac{(\omega \cdot S \cdot C \cdot L \cdot \bar{R}) - ((1 - \omega) \cdot S \cdot C \cdot L) - (f_e + f_x) \cdot S \cdot C \cdot L}{C}$$

Toto je surová výhoda vašej stratégie ako zlomok kapitálu. Poznamenajme, že poplatky sú tu už zabudované ako tretí člen v čitateli – priamo znižujú $G_1$. Stratégia musí generovať dostatočnú výhodu na pokrytie poplatkov, než bude $G_1$ vôbec kladné.

Tento komponent je špeciálnym prípadom $G$, keď $\sigma = 0$ a $\sigma_\omega = 0$ – dokonalá istota, žiadna volatilita. V tom idealizovanom svete $G = G_1 = \frac{\rho}{C}$.

**Komponent 2 — Erózia spôsobená volatilitou**

Druhý komponent penalizuje $G$ za rozptyl výsledkov na jeden obchod. Ako bolo ustanovené v sekcii 3, zložené úročenie je multiplikatívne – strata 50 % vyžaduje zisk 100 % na zotavenie. Volatilita teda ničí geometrický rast aj vtedy, keď je aritmetické EV kladné.

Penalizácia je odvodená z teórie lognormálneho rastu, kde je geometrický priemerný výnos aproximovaný ako aritmetický priemer mínus polovica rozptylu, normalizovaná kvadrátom kapitálu:

$$G_2 = -\frac{\sigma^2}{2C^2}$$

Väčšia $\sigma$ – chaotickejšia stratégia – vedie k väčšej penalizácii. Tento člen je vždy záporný alebo nulový, nikdy kladný. Je to čistý náklad.

**Komponent 3 — Erózia spôsobená neistotou miery úspešnosti**

Tretí komponent penalizuje $G$ za neistotu v odhade miery úspešnosti $\bar{\omega}$. Ako bolo ustanovené v sekcii 4, $\sigma_\omega$ meria, o koľko sa skutočná miera úspešnosti môže vierohodne odchýliť od backtestovaného odhadu. Táto neistota sa prenáša do $\rho$, pretože $\omega$ priamo určuje rovnováhu medzi víťaznými a stratovými obchodmi.

Citlivosť $\rho$ na zmeny v $\omega$ je celkový výkyv P&L na jeden obchod – suma získaná pri výhre plus suma stratená pri prehre:

$$\Delta = S \cdot C \cdot L \cdot (\bar{R} + 1)$$

Tu $\bar{R}$ je multiplikátor odmeny pri výhre a $1$ reprezentuje úplnú stratu nasadenej sumy pri prehre. Čím väčší je tento výkyv, tým škodlivejšia je neistota miery úspešnosti. Penalizácia je:

$$G_3 = -\frac{\sigma_\omega^2 \cdot (S \cdot C \cdot L \cdot (\bar{R} + 1))^2}{2C^2}$$

Rovnako ako $G_2$, aj tento člen je vždy záporný alebo nulový. Je to tiež čistý náklad.

### Definícia

Kombináciou všetkých troch komponentov je Univerzálna miera rastu:

$$\boxed{G = \frac{(\omega \cdot S \cdot C \cdot L \cdot \bar{R}) - ((1 - \omega) \cdot S \cdot C \cdot L) - (f_e + f_x) \cdot S \cdot C \cdot L}{C} - \frac{\sigma^2}{2C^2} - \frac{\sigma_\omega^2 \cdot (S \cdot C \cdot L \cdot (\bar{R} + 1))^2}{2C^2}}$$

Tento vzorec je zámerne ponechaný v nezjednodušenom tvare, aby každý člen bol priamo sledovateľný k svojmu pôvodu v S1–S4 a aby sa dal priamo implementovať v kóde dosadzovaním hodnôt zľava doprava.

$G$ je vyjadrené ako desatinné číslo. Výsledok $0{,}03$ znamená, že váš kapitál rastie v priemere o cca 3 % na jeden obchod. Výsledok $-0{,}01$ znamená, že váš kapitál eroduje v priemere o cca 1 % na jeden obchod, exponenciálne.

### Ako používať G

$G$ je metrika uskutočniteľnosti stratégie, nie predpoveď. Nehovorí vám, čo sa stane pri konkrétnom obchode – to je úloha $\tilde{\rho}$ zo sekcie 4. Hovorí vám dlhodobú trajektóriu vášho kapitálu, ak budete túto stratégiu opakovane prevádzkovať.

**Prahová hodnota, na ktorej záleží, je $G = 0$:**

- $G > 0$ – stratégia je uskutočniteľná. Váš kapitál v priemere rastie na jeden obchod po zohľadnení všetkých nákladov a neistôt. Vyššie $G$ indikuje silnejšiu a robustnejšiu stratégiu.
- $G = 0$ – stratégia je na nule. Vaša výhoda je presne vyvážená poplatkami, eróziou z volatility a eróziou z neistoty miery úspešnosti dohromady. Neoplatí sa prevádzkovať.
- $G < 0$ – stratégia nie je uskutočniteľná. Váš kapitál sa časom eroduje. Kriticky dôležité: toto môže nastať aj keď $\rho > 0$ – stratégia s kladným očakávaným ziskom na jeden obchod môže stále ničiť kapitál, ak je volatilita alebo neistota miery úspešnosti dostatočne veľká v porovnaní s výhodou.

Tento posledný prípad je najdôležitejším poznatkom práce. Kladné $\rho$ je nutná, ale nie postačujúca podmienka pre životaschopnú stratégiu. $G > 0$ je postačujúca podmienka.

**Praktické použitie:**

1. Spustite backtest a extrahujte $\bar{\omega}$, $n$, $\sigma$, $\bar{R}$, $S$, $L$, $f_e$, $f_x$
2. Definujte svoj celkový kapitál $C$
3. Odvoďte $\sigma_\omega = \sqrt{\frac{\bar{\omega}(1-\bar{\omega})}{n}}$
4. Dosaďte všetky hodnoty do $G$
5. Ak $G > 0$, stratégia spĺňa prah uskutočniteľnosti. Ak $G \leq 0$, upravte parametre stratégie alebo zozbierajte viac backtestových dát na sprísnenie $\sigma_\omega$

### Príklad

Používame konzistentné parametre:
- $\bar{\omega} = 0{,}60$, $n = 30$ obchodov
- $\bar{R} = 2$, $S = 0{,}10$, $C = \$1000$, $L = 2$
- $f_e = 0{,}002$, $f_x = 0{,}002$
- Backtestová $\sigma = \$15$

Najprv odvodíme $\sigma_\omega$:

$$\sigma_\omega = \sqrt{\frac{0{,}60 \cdot 0{,}40}{30}} \approx 0{,}0894$$

Teraz vypočítame každý komponent:

$$G_1 = \frac{(0{,}60 \cdot 0{,}10 \cdot 1000 \cdot 2 \cdot 2) - (0{,}40 \cdot 0{,}10 \cdot 1000 \cdot 2) - (0{,}004 \cdot 0{,}10 \cdot 1000 \cdot 2)}{1000}$$
$$G_1 = \frac{240 - 80 - 0{,}8}{1000} = \frac{159{,}2}{1000} = 0{,}1592$$

$$G_2 = -\frac{15^2}{2 \cdot 1000^2} = -\frac{225}{2000000} = -0{,}0001125$$

$$G_3 = -\frac{0{,}0894^2 \cdot (0{,}10 \cdot 1000 \cdot 2 \cdot 3)^2}{2 \cdot 1000^2} = -\frac{0{,}00799 \cdot 360000}{2000000} \approx -0{,}001438$$

$$G = 0{,}1592 - 0{,}0001125 - 0{,}001438 \approx 0{,}1577$$

Stratégia vracia cca 15,77 % rast kapitálu na jeden obchod. $G > 0$, takže pohodlne spĺňa prah uskutočniteľnosti.

Teraz sledujte, čo sa stane so zle backtestovanou stratégiou – rovnaké parametre, ale $n = 10$ obchodov:

$$\sigma_\omega = \sqrt{\frac{0{,}60 \cdot 0{,}40}{10}} \approx 0{,}1549$$

$$G_3 = -\frac{0{,}1549^2 \cdot 360000}{2000000} = -\frac{0{,}02399 \cdot 360000}{2000000} \approx -0{,}004318$$

$$G \approx 0{,}1592 - 0{,}0001125 - 0{,}004318 \approx 0{,}1548$$

Stále kladné, ale erózia spôsobená neistotou miery úspešnosti narástla trojnásobne. Pre stratégiu s tenším edge by backtest na 10 obchodov mohol ľahko stlačiť $G$ pod nulu – čo by na papieri vyzeralo uskutočniteľne, no pri dôkladnom preskúmaní by bolo preukázateľne neuskutočniteľné.

A jedna záverečná kontrola: uvažujme $n = 10000$ obchodov, rovnaké parametre:

$$\sigma_\omega = \sqrt{\frac{0{,}60 \cdot 0{,}40}{10000}} \approx 0{,}0049$$

$$G_3 = -\frac{0{,}0049^2 \cdot 360000}{2000000} = -\frac{0{,}00002401 \cdot 360000}{2000000} \approx -0{,}00000432$$

$$G \approx 0{,}1592 - 0{,}0001125 - 0{,}00000432 \approx 0{,}1591$$

Podobný výsledok ako pri $n = 30$, len s oveľa menšou eróziou z neistoty miery úspešnosti.
Práve preto veľkosť backtestovej vzorky nie je technická záležitosť. Je to priamy vstup do $G$.

---

## 6. Záver

Podarilo sa nám skonštruovať jednotný matematický rámec na hodnotenie dlhodobej životaschopnosti krypto obchodnej stratégie – všetko z jednoduchého vzorca EV na jeden obchod, ktorý pôvodne nezohľadňoval poplatky.

Ak chcete vypočítať svoje $G$ s nejakými backtestovanými dátami, ale nechcete ručne zadávať zdĺhavý vzorec, môžete použiť [tento skript](G_script.py) priamo tu. Jednoducho ho otvorte, upravte parametre, spustite `python G_script.py` v priečinku, kde sa skript nachádza, a uvidíte svoje $G$.
