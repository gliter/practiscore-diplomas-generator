# Generator dyplomów PractiScore

Program tworzy jeden dokument z dyplomami na podstawie eksportu meczu z PractiScore. Poniżej opisujemy standardową pracę w graficznej wersji Windows. Dalej znajdziesz też szczegółową instrukcję pracy w terminalu.

**Język instrukcji:** Polski · [English](README.en.md)

Zacznij od opisu pracy w GUI poniżej albo przejdź do [terminala](#użycie-w-terminalu), [konfiguracji nagród](#konfiguracja-nagród), [szablonów](#przygotowanie-szablonu-dyplomu) lub [rozwiązywania problemów](#rozwiązywanie-problemów).

## Generowanie dyplomów w GUI

Przygotuj trzy pliki: końcowy eksport z PractiScore, konfigurację nagród YAML z `configs` (lub własną kopię) i szablon DOCX/ODT z `templates` (lub własny projekt). Przed rozpoczęciem [pobierz najnowszy pakiet Windows](https://github.com/gliter/practiscore-diplomas-generator/releases/latest/download/practiscore-diplomas-generator-windows-x64.zip) i rozpakuj go; Python ani `uv` nie są wymagane.

Kliknij **Pomoc (F1)** w prawym dolnym rogu albo naciśnij **F1** w głównym oknie, aby otworzyć instrukcję offline. Wyświetla ona tę instrukcję: docs/README.pl.md po polsku albo docs/README.en.md po angielsku, zależnie od języka aplikacji. Okno można skalować i maksymalizować. Obie instrukcje i ich zrzuty ekranu są dołączone do EXE i pakietu Pythona; okno pomocy wyświetla obrazki offline.

### 1. Wyeksportuj mecz

W PractiScore zakończ i sprawdź wyniki, a następnie wybierz **Import / Export** → **Export Match**. Zapisz wyeksportowane archiwum. Program obsługuje pliki `.pcs`, `.psc` i `.zip` — wszystkie są archiwami ZIP. W wierszu poleceń można też wskazać rozpakowany katalog eksportu.

Eksport w PractiScore znajdziesz na tych dwóch ekranach:

![Ekran meczu PractiScore: Import / Export](psc-1.png)

![Ekran Import / Export w PractiScore: Export Match](psc-2.png)

### 2. Wybierz mecz, konfigurację i szablon

Kliknij dwukrotnie `practiscore-diplomas.exe`. Listy pokazują pliki meczów z katalogu roboczego, konfiguracje z folderu `configs` oraz szablony DOCX/ODT z folderu `templates`. Wybierz **Wybierz inny plik…**, aby wskazać plik z innego miejsca. Przy korzystaniu z pakietu Windows foldery `configs` i `templates` powinny znajdować się obok pliku EXE.

Po wybraniu meczu program od razu parsuje dane strzelców i zapisuje w katalogu roboczym `shooters-summary-<nazwa-meczu>.yaml`. Jeśli dla tego meczu istnieje już podsumowanie różniące się od świeżego parsowania, zobaczysz ścieżki i czasy modyfikacji obu plików. Wybierz **Dane z .pcs**, aby użyć nowych danych z eksportu, albo **Dane z podsumowania**, aby zachować wcześniej edytowane dane. Jeśli dane są identyczne, pytanie się nie pojawi.

Wybierz konfigurację nagród i szablon dyplomu. Konfiguracja określa, kto kwalifikuje się do nagród i jakie serie dyplomów powstaną. Szablon definiuje wygląd dokumentu. Gdy program ma wymagane dane, w głównej tabeli pojawiają się wiersze dyplomów.

Aby zmienić konfigurację w programie, wybierz ją i kliknij **Edytuj**. **Zastosuj** sprawdza konfigurację i używa zmian w pamięci; **Zapisz** lub **Zapisz jako** zapisuje je do pliku. Przy zamykaniu programu z niezapisanymi zmianami możesz je zapisać, zapisać jako nowy plik, odrzucić albo anulować zamknięcie.

### 3. Sprawdź strzelców i dyplomy

Przycisk **Edytuj dane strzelców** obok listy plików meczów otwiera edytor zawodników. Zmiany pozostają w oknie do kliknięcia **Zapisz zmiany**. Dywizję i klasę wybiera się z list, kategorie i kary mają osobne edytory. Wyliczone sekundy kar i czas łączny są widoczne tylko do podglądu. Zmodyfikowane komórki są podświetlone na pomarańczowo; zamykanie z niezapisanymi zmianami pozwala je zapisać, odrzucić lub anulować zamknięcie. Zapis aktualizuje plik YAML i generuje dane dyplomów ponownie. Jeśli ręcznie zmieniono już wiersze dyplomów, program zapyta, czy odrzucić te zmiany przed przeliczeniem.

Przejrzyj tabelę dyplomów przed utworzeniem dokumentu:

- Dwuklik komórki pozwala ją edytować. Czerwony przycisk **×** usuwa wiersz po potwierdzeniu, a niebieska ikona zmienia przypisanego strzelca. Ikona ołówka otwiera edytor danych strzelców z wyszukiwaniem po UID tego zawodnika. **Nowy wiersz…** pozwala wybrać strzelca i dodać dyplom: miejsce ma wartość 1, a seria, tekst dyplomu i pola metryk są puste.
- Nagłówki kolumn pozwalają sortować i filtrować dane. Filtr może zawierać wiele wartości; kropka w nagłówku oznacza aktywne filtrowanie.
- Wybór strzelca ma taką samą tabelę z sortowaniem i filtrowaniem. Wyszukiwarka znajduje po imieniu, nazwisku, dywizji, kategorii i klasie.
- Wiersze z błędem w szablonie linii są podświetlone na czerwono. W błędnej linii pojawia się krótki komunikat `<błąd: ...>`, a generowanie pozostałych dyplomów trwa dalej. Popraw konfigurację i przelicz dane ponownie albo ręcznie zastąp komunikat właściwym tekstem.

Zmiana danych strzelców lub zastosowanie konfiguracji automatycznie przelicza dyplomy, jeśli nie było ręcznych poprawek w tabeli dyplomów. W przeciwnym razie możesz potwierdzić zastąpienie poprawek lub je zachować. Jeśli je zachowasz, **Przelicz dane dyplomów** podświetli się na pomarańczowo, a status poinformuje o nieaktualnych danych. Kliknij ten przycisk, gdy chcesz wygenerować wiersze od nowa; zastąpi on ręczne poprawki. Aktywny przycisk ma wyraźną pomarańczową ramkę. Przycisk jest nieaktywny, gdy nie ma nic do przeliczenia.

Filtry tabeli służą do przeglądania wierszy; nie wykluczają dyplomów z dokumentu wynikowego. Aby zmienić zawartość wydruku, usuń niepotrzebne wiersze lub zmień konfigurację nagród.

W każdej serii grupy są uporządkowane od największej liczby uprawnionych strzelców do najmniejszej. W obrębie grupy dyplomy są wyświetlane od ostatniego miejsca do pierwszego.

### 4. Wygeneruj dokument

Wybierz **Generuj dyplomy…**, aby zapisać dokument, albo **Generuj dyplomy i otwórz**, aby zapisać go i otworzyć w domyślnej aplikacji systemu. W oknie zapisu wskaż ścieżkę i format. DOCX i ODT są obsługiwane bezpośrednio. PDF i konwersja między formatami wymagają LibreOffice z programem `soffice` dostępnym w `PATH`.

W katalogu roboczym program zapisuje też dwa pliki pomocnicze:

```text
shooters-summary-<nazwa-meczu>.yaml
diplomas-data-<nazwa-meczu>.yaml
```

Zachowaj je razem z dokumentacją meczu. Podsumowanie strzelców zawiera surowe dane zawodników i sekcję `_match_options` z dywizjami, klasami, kategoriami, wartościami kar w sekundach i opcjami punktacji. Sekundy kar oraz czas łączny są wyliczane na potrzeby podglądu i generowania dyplomów. Kluczem rekordu strzelca jest wewnętrzny UID PractiScore; `shooter_id` to osobny, widoczny numer zawodnika GPA lub IDPA.

Plik danych dyplomów zawiera wygenerowane nagrody, podzielone w `diplomas` według serii, z miejscem, grupowaniem, tekstem linii, metryką rankingu i danymi strzelca. W GUI jest aktualizowany automatycznie po każdej zatwierdzonej zmianie komórki, dodaniu lub usunięciu wiersza, zmianie strzelca i przeliczeniu. Ponowne otwarcie meczu lub uruchomienie aplikacji przywraca zapisane wiersze dyplomów zamiast je nadpisywać. Program porównuje zapisane wiersze z dyplomami wyliczonymi z aktualnych danych strzelców i konfiguracji. Jeśli są takie same, **Przelicz dane dyplomów** jest nieaktywny. Jeśli się różnią, okno na środku ekranu pokazuje ścieżkę YAML i przyciski **Użyj danych z pliku** oraz **Wygeneruj ponownie**. Użycie danych z pliku zachowuje poprawki i pozostawia pomarańczowy przycisk; ponowne generowanie zastępuje YAML aktualnymi nagrodami i wyłącza przycisk. Anulowanie pozostawia bieżący mecz bez zmian. Możesz od razu wygenerować dokument z przywróconych wierszy. Przeliczenie wymaga potwierdzenia przed zastąpieniem ich nagrodami obliczonymi z aktualnych danych strzelców i konfiguracji.

## Użycie w terminalu

Pakiet Windows zawiera GUI, interaktywne menu terminalowe i polecenia do automatyzacji. Do uruchamiania pliku EXE nie potrzebujesz Pythona ani `uv`. Otwórz PowerShell w folderze z rozpakowanym programem. Poniższe przykłady używają tego folderu jako katalogu roboczego; ścieżki ze spacjami zapisuj w cudzysłowach.

### Menu interaktywne (`-I`)

```powershell
.\practiscore-diplomas.exe -I
```

Strzałkami góra/dół i klawiszem Enter wybierz sposób pracy:

| Opcja menu | Kiedy jej użyć |
| --- | --- |
| Wygenerować dyplomy z pliku PractiScore | Chcesz utworzyć dokument bezpośrednio z archiwum meczu i konfiguracji nagród. |
| Sparsować plik PractiScore do plików YAML | Chcesz utworzyć podsumowanie strzelców i dane dyplomów do sprawdzenia przed generowaniem dokumentu. |
| Wygenerować dyplomy z pliku YAML z danymi dyplomów | Masz już sprawdzone lub ręcznie poprawione dane dyplomów albo chcesz użyć innego szablonu bez przeliczania nagród. |

Listy wyboru pokazują archiwa meczów i dane YAML z katalogu roboczego, konfiguracje z `configs` oraz szablony DOCX/ODT z `templates`. **Wybierz plik** otwiera systemowe okno wyboru; anulowanie wraca do listy. Przy generowaniu dokumentu okno zapisu pozwala wybrać nazwę i format. Rozszerzenie pliku wynikowego decyduje, czy powstanie DOCX, ODT czy PDF.

Dwuklik pliku EXE lub uruchomienie go bez parametrów otwiera GUI. Opcji `-I` używaj samodzielnie, ewentualnie z `--language`; nie można jej łączyć z `parse` ani `render`.

### Parsowanie, sprawdzenie danych i generowanie dokumentu

Ten sposób pracy pozwala poprawić listę dyplomów przed utworzeniem dokumentu.

1. Utwórz podsumowanie strzelców i dane dyplomów:

   ```powershell
   .\practiscore-diplomas.exe parse `
     -i "mecz.zip" `
     -c "configs\gpa_t1_config.yaml"
   ```

   Wejściem może być archiwum `.pcs`, `.psc` lub `.zip` albo rozpakowany katalog eksportu zawierający `match_def.json` i `match_scores.json`.

2. Sprawdź `diplomas-data-<nazwa-meczu>.yaml` w edytorze tekstu. Możesz zmienić tekst dyplomu, poprawić wyświetlane nazwisko albo usunąć rekord dyplomu. Zachowaj strukturę i wcięcia YAML.
3. Wygeneruj dokument ze sprawdzonego pliku:

   ```powershell
   .\practiscore-diplomas.exe render `
     -d "diplomas-data-Przykladowy-Mecz.yaml" `
     -t "templates\example-diploma-template.docx" `
     -o "dyplomy.docx"
   ```

`render -d` używa przekazanych rekordów dyplomów bez zmian. Nie parsuje meczu ani nie przelicza nagród i nie przyjmuje opcji `-c`. Zachowaj sprawdzony YAML, aby móc ponownie utworzyć dokument. Ponowne uruchomienie `parse` lub `render -i` tworzy dane dyplomów od nowa z eksportu i konfiguracji, nadpisując istniejące pliki pod ścieżkami wynikowymi.

### Generowanie bezpośrednio z meczu

Jeśli dane dyplomów nie wymagają ręcznych poprawek:

```powershell
.\practiscore-diplomas.exe render `
  -i "mecz.zip" `
  -c "configs\gpa_t1_config.yaml" `
  -t "templates\example-diploma-template.docx" `
  --output-docx "dyplomy.docx"
```

Polecenie parsuje mecz, tworzy oba pomocnicze pliki YAML i generuje dokument. Aby użyć rozpakowanego eksportu, zamiast archiwum wskaż katalog, np. `-i "eksporty\przykladowy-mecz"`.

### Ścieżki plików i format wynikowy

Domyślnie `parse` oraz `render -i` zapisują w katalogu roboczym:

```text
shooters-summary-<nazwa-meczu>.yaml
diplomas-data-<nazwa-meczu>.yaml
```

Nazwa pochodzi z definicji meczu; spacje są zamieniane na myślniki, a znaki niedozwolone w nazwach plików na podkreślenia. W `parse` możesz podać własne ścieżki obu plików; brakujące katalogi zostaną utworzone:

```powershell
.\practiscore-diplomas.exe parse `
  --input "mecz.zip" `
  --config "configs\gpa_t1_config.yaml" `
  --summary-output "wyniki\strzelcy.yaml" `
  --diplomas-data "wyniki\dyplomy.yaml"
```

Oba polecenia korzystają z następujących opcji:

| Opcja | `parse` | `render` |
| --- | --- | --- |
| `-i`, `--input PATH` | Wymagane archiwum lub rozpakowany eksport. | Dane meczu, zamiennie z `-d`. |
| `-c`, `--config PATH` | Wymagana konfiguracja nagród. | Wymagana z `-i`; niedozwolona z `-d`. |
| `-s`, `--summary-output PATH` | Własna ścieżka podsumowania strzelców. | Niedostępna; przy wejściu z meczu obowiązują standardowe nazwy YAML. |
| `-d`, `--diplomas-data PATH` | Własna ścieżka **wynikowego** pliku danych dyplomów. | **Wejściowy** plik sprawdzonych danych dyplomów, zamiennie z `-i`. |
| `-t`, `--template PATH` | Nieużywana. | Wymagany szablon DOCX lub ODT. |
| `-o`, `--output-docx [PATH]` | Nieużywana. | Wynikowy dokument DOCX. |
| `--output-odt [PATH]` | Nieużywana. | Wynikowy dokument ODT. |
| `--output-pdf [PATH]` | Nieużywana. | Wynikowy dokument PDF; wymaga LibreOffice. |

`-o` służy wyłącznie do wskazania końcowego dokumentu DOCX. Wybierz najwyżej jedną opcję formatu wynikowego. Ścieżka po niej jest opcjonalna: `--output-pdf` wybiera PDF z domyślną nazwą, a `--output-pdf "wyniki\dyplomy.pdf"` ustawia własną ścieżkę. Użyj rozszerzenia zgodnego z wybranym formatem.

Jeśli pominiesz wszystkie opcje wyjścia, format będzie taki sam jak format szablonu. Domyślne nazwy dokumentów to `diplomas-<nazwa-meczu>.docx` / `.odt` przy `render -i` oraz `diplomas.docx` / `.odt` przy `render -d`. Opcja formatu bez ścieżki odpowiednio zmienia rozszerzenie. PDF i konwersja między DOCX a ODT wymagają LibreOffice z poleceniem `soffice` lub `libreoffice` dostępnym w `PATH`; tworzenie DOCX z DOCX albo ODT z ODT nie wymaga LibreOffice.

### Pomoc i język

```powershell
.\practiscore-diplomas.exe --help
.\practiscore-diplomas.exe parse --help
.\practiscore-diplomas.exe render --help
.\practiscore-diplomas.exe --language pl -I
.\practiscore-diplomas.exe render --language en --help
```

Język pomocy zależy od ustawień systemu. Możesz wybrać `--language en` albo `--language pl`, przed podkomendą lub po niej. Znak grawisu na końcu wiersza PowerShell kontynuuje polecenie w następnym wierszu; nie dodawaj po nim spacji. Każde polecenie można też zapisać w jednym wierszu.

### Uruchamianie ze źródeł przez uv

Jeśli korzystasz z kodu źródłowego, zainstaluj Python 3.10 lub nowszy i `uv`, a następnie uruchom w katalogu repozytorium:

```powershell
uv sync
uv run practiscore-diplomas
uv run practiscore-diplomas -I
```

Drugie polecenie otwiera GUI, a trzecie menu terminalowe. Aby uruchomić ze źródeł dowolny z powyższych przykładów CLI, zamień `.\practiscore-diplomas.exe` na `uv run practiscore-diplomas`; argumenty pozostają takie same.

## Konfiguracja nagród

### Wybierz przykładową konfigurację

W folderze `configs` znajdują się przykładowe reguły nagród:

| Plik | Przeznaczenie |
| --- | --- |
| `gpa_t1_config.yaml` | Mecze GPA Tier 1. |
| `idpa_t1_config.yaml` | Mecze IDPA Tier 1. |
| `idpa_t2_config.yaml` | Mecze IDPA Tier 2. |

Zacznij od konfiguracji najbliższej Twojemu meczowi. Przed zmianami utwórz jej kopię, aby zachować oryginalny przykład.

Konfiguracja określa serie nagród, np. zwycięzców dywizji i kategorii, najszybszego oraz najcelniejszego zawodnika. Ustala również, kto może otrzymać dyplom. Dostarczone konfiguracje domyślnie wykluczają zawodników z DQ i DNF. Niezaliczone Chrono jest traktowane jako DNF, chyba że konfiguracja zmienia tę zasadę.

### Najczęściej Zmieniane Ustawienia

Możesz potrzebować zmienić konfigurację, jeśli mecz ma inne dywizje, kategorie, liczbę nagród lub nazewnictwo. Najważniejsze pojęcia:

| Ustawienie | Znaczenie |
| --- | --- |
| `series` | Serie nagród. Każdy nazwany wpis tworzy osobny ranking. |
| `type` | `best_shooter`, `most_accurate` albo `fastest`. |
| `group_by` | Dzielenie rankingu według `division`, `class` lub `category`. |
| `min_competitors` | Liczba zawodników potrzebna do przyznania kolejnych dyplomów. `[1, 6, 11]` daje 1 dyplom dla 1-5 osób, 2 dla 6-10 i 3 od 11 osób. |
| `filters` | Uwzględnianie lub wykluczanie dywizji, kategorii i klas. Wzorce są wyrażeniami regularnymi. |
| `text` | Linie tekstu drukowane na dyplomie. |

Jeśli pojawi się błąd konfiguracji, sprawdź cudzysłowy, wcięcia i pisownię nazw dywizji lub kategorii. YAML wymaga wcięć spacjami, a nie tabulatorami.

## Szczegółowy Opis Konfiguracji

Pliki konfiguracji używają formatu YAML. Zacznij od skopiowania najbliższego przykładu z folderu `configs`, a następnie edytuj kopię w edytorze tekstu. Zachowuj jednakowe wcięcia: używaj spacji, nigdy klawisza Tab.

Główne części konfiguracji to:

```yaml
exclude_shooters:
  surnames: []
  ids: []
mark_chrono_failure_as_dnf: true
maps: {}
series: {}
```

### Serie Nagród

Każdy wpis w `series` opisuje jeden rodzaj dyplomu. Nazwa wpisu jest tylko wewnętrzną nazwą, dlatego warto nadać jej krótki, zrozumiały opis. Poniższy przykład tworzy nagrody w dywizjach:

```yaml
series:
  best_in_division:
    type: best_shooter
    group_by: [division]
    min_competitors: [1, 6, 11]
    text:
      first_line: "{{ division }} DIVISION"
      second_line: "{{ place }} PLACE"
```

| Ustawienie | Co określa |
| --- | --- |
| `type` | Sposób tworzenia rankingu: `best_shooter` wybiera najlepszy wynik, `most_accurate` wybiera najmniejszą liczbę punktów w dół z doliczeniem chybień do stali według opcji punktacji meczu, a `fastest` najmniejszy czas surowy. |
| `group_by` | Tworzy osobne rankingi dla każdej podanej wartości: `division`, `class` i/lub `category`. Pomiń je, aby utworzyć jeden ranking dla wszystkich. |
| `min_competitors` | Progi przyznawania dyplomów. `[1, 6, 11]` daje jeden dyplom dla 1-5 uprawnionych osób, dwa dla 6-10 i trzy od 11 osób. `[5]` nie daje dyplomu poniżej 5 osób, a od 5 daje jeden. |
| `exclude_dq` | Gdy ma wartość `true`, zawodnik z DQ nie może otrzymać tej nagrody. Domyślnie `true`. |
| `exclude_dnf` | Gdy ma wartość `true`, zawodnik z DNF nie może otrzymać tej nagrody. Domyślnie `true`. |
| `ineligible_penalties` | Lista nazw kar, które wykluczają zawodnika tylko z tej serii. Użyj dokładnej nazwy kary z eksportu. |

Każda seria wymaga `type`, `min_competitors`, `text.first_line` i `text.second_line`. `group_by`, filtry, reguły kar oraz trzecia i czwarta linia tekstu są opcjonalne.

Progi muszą być rosnącymi, nieujemnymi liczbami całkowitymi; można podać najwyżej pięć. Uwzględnij `1`, jeśli grupa bez uprawnionych strzelców nie powinna otrzymać dyplomu.

### Filtry

Filtry ograniczają serię do wybranych dywizji, kategorii albo klas. Korzystają z wyrażeń regularnych. Wzorzec jest dopasowywany do całej wartości z PractiScore, dlatego użyj `.*`, jeżeli po kodzie znajduje się dodatkowy opis rejestracyjny.

```yaml
filters:
  divisions:
    include: ["CPI.*", "CPO.*"]
  categories:
    exclude: ["Lady.*"]
```

Ten przykład uwzględnia dywizje, których nazwa rejestracyjna zaczyna się od `CPI` lub `CPO`, a wyklucza kategorię Lady. Dostępne grupy filtrów to `divisions`, `categories` i `classes`.

| Forma | Znaczenie |
| --- | --- |
| Pominięcie `filters` albo jednej z grup filtrów | Uwzględnia wszystkie wartości. |
| `include` | Uwzględnia wyłącznie wartości pasujące do co najmniej jednego wzorca. |
| `exclude` | Wyklucza wartości pasujące do wzorca. Wykluczenie ma pierwszeństwo przed uwzględnieniem. |
| Prosta lista, np. `divisions: ["CPI.*"]` | Skrócony zapis `include`. |

Wartość `"*"` na liście `include` oznacza wszystkie wartości. Pominięcie `include` również uwzględnia wszystko; pominięcie `exclude` niczego nie wyklucza.

### Mapy I Tekst Linii Dyplomu

Mapy zamieniają wartość z PractiScore na krótszy tekst drukowany na dyplomie. Są przydatne zwłaszcza wtedy, gdy dywizja lub kategoria zawiera szczegóły rejestracyjne, których nie chcesz umieszczać w tytule.

```yaml
maps:
  division_code:
    "CPI.*": CPI
    "CPO.*": CPO
  division_place:
    1: CHAMPION
    2: 2nd PLACE
    3: 3rd PLACE
```

Program sprawdza wpisy mapy od góry do dołu i używa pierwszego pasującego wpisu. Wzorce bardziej szczegółowe umieszczaj przed ogólnymi. Wzorce tekstowe, np. `"CPI.*"`, zapisuj w cudzysłowach; klucze liczbowe, np. miejsca, nie wymagają cudzysłowów.

Sekcja `text` określa maksymalnie cztery linie na dyplomie. Pierwsze dwie są wymagane, a trzecia i czwarta są opcjonalne.

```yaml
text:
  first_line: "{{ division_code(division) }} DIVISION"
  second_line: "{{ division_place(place) }}"
  third_line: "{{ shooter.raw_time }} s"
  fourth_line: "{{ shooter.points_down }} PD"
```

Użyj `{{ pole }}`, aby wstawić wartość, oraz `{{ nazwa_mapy(pole) }}`, aby zastosować mapę. W liniach dyplomu możesz używać następujących wartości:

| Wartość | Znaczenie |
| --- | --- |
| `division`, `category`, `class` | Wartość określająca bieżącą grupę nagrody. |
| `place` | Miejsce w rankingu nagrody. |
| `type` | Rodzaj nagrody: `best_shooter`, `most_accurate` albo `fastest`. |
| `shooter.shooter_id` | Widoczny numer zawodnika GPA albo IDPA. |
| `shooter.first_name`, `shooter.last_name` | Imię i nazwisko zawodnika. |
| `shooter.division`, `shooter.categories`, `shooter.class` | Dane zawodnika zapisane w PractiScore. |
| `shooter.raw_time`, `shooter.points_down`, `shooter.steel_misses`, `shooter.penalty_seconds`, `shooter.total_time` | Wartości wyniku. |
| `shooter.dnf`, `shooter.chrono_failure`, `shooter.dq`, `shooter.shooter_uid` | Status zawodnika, osobny wynik kontroli chrono i wewnętrzny identyfikator. |

Te linie YAML przekazują do szablonu dokumentu wartości `first_line` do `fourth_line`. Pola w pliku DOCX lub ODT opisuje następna sekcja. Wywołania map stosuje się w konfiguracji, a nie bezpośrednio w szablonie dokumentu.

### Wykluczanie Konkretnych Zawodników I Niezaliczonego Chrono

Użyj `exclude_shooters`, aby usunąć ze wszystkich serii zawodników nieturniejowych, rekordy testowe albo rekord czasu PAR. `surnames` oraz `ids` są listami wyrażeń regularnych; każda z nich może być pusta.

```yaml
exclude_shooters:
  surnames: ["(?i)^par$"]
  ids: []
```

`chrono_failure` w podsumowaniu zapisuje, czy kontrola wyposażenia na torze Chrono nie miała statusu Pass. To pole jest niezależne od `dnf`. Podczas generowania danych dyplomów `mark_chrono_failure_as_dnf: true` (domyślnie) traktuje taki błąd jak DNF; `false` pozwala uwzględnić strzelca. Sam parser nie wymaga konfiguracji nagród. Polecenie CLI `parse` wymaga jej, ponieważ generuje również dane dyplomów.

## Przygotowanie Szablonu Dyplomu

Użyj pliku DOCX albo ODT jako szablonu. Wstaw pola w miejscach, w których tekst ma się zmieniać. Na przykład:

```text
{{ first_line }}
{{ second_line }}
{{ shooter.first_name }} {{ shooter.last_name }}
```

Program tworzy kopię szablonu dla każdego dyplomu. Zachowuje formatowanie dokumentu, w tym czcionki, rozmiary, wyrównanie i tabele. W pakiecie znajduje się `templates/example-diploma-template.docx`, czyli niewielki działający przykład.

### Pola Szablonu

| Pole | Znaczenie |
| --- | --- |
| `first_line` | Pierwsza linia określona w konfiguracji nagrody. |
| `second_line` | Druga linia określona w konfiguracji nagrody. |
| `third_line` | Opcjonalna trzecia linia. Jest pusta, gdy seria jej nie określa. |
| `fourth_line` | Opcjonalna czwarta linia. Jest pusta, gdy seria jej nie określa. |
| `place` | Miejsce zawodnika w rankingu danej nagrody. |
| `division` | Dywizja użyta dla nagrody. |
| `category` | Kategoria użyta dla nagrody. |
| `class` | Klasa użyta dla nagrody. |
| `metric_value` | Wartość użyta do ustalenia rankingu, np. czas lub punkty w dół. |
| `shooter.shooter_id` | Widoczny numer zawodnika GPA albo IDPA. |
| `shooter.first_name` | Imię zawodnika. |
| `shooter.last_name` | Nazwisko zawodnika. |
| `shooter.division` | Dywizja zawodnika zapisana w PractiScore. |
| `shooter.categories` | Kategorie zawodnika, wyświetlane po przecinku. |
| `shooter.class` | Klasa zawodnika zapisana w PractiScore. |
| `shooter.raw_time` | Łączny czas surowy przed doliczeniem kar. |
| `shooter.points_down` | Łączna liczba punktów w dół. |
| `shooter.steel_misses` | Łączna liczba nietrafionych celów stalowych. |
| `shooter.penalty_seconds` | Sekundy doliczone za kary. |
| `shooter.total_time` | Czas surowy powiększony o kary. |
| `shooter.dnf` | `True`, gdy zawodnik ma status DNF. |
| `shooter.chrono_failure` | `True`, gdy kontrola wyposażenia na Chrono nie miała statusu Pass. |
| `shooter.dq` | `True`, gdy zawodnik ma status DQ. |
| `shooter.shooter_uid` | Wewnętrzny identyfikator PractiScore. Zwykle nie jest potrzebny na dyplomie. |

Używaj dokładnie takiej pisowni i nawiasów klamrowych jak w tabeli. Nieznane pole w szablonie DOCX/ODT zatrzyma renderowanie z czytelnym błędem. Błąd mapy albo pola w tekście linii konfiguracji pojawi się bezpośrednio w odpowiednim wierszu tabeli dyplomów.

## Formaty wynikowe

| Format | Zastosowanie |
| --- | --- |
| DOCX | Najlepszy wybór, gdy dokument ma być jeszcze edytowany. |
| ODT | Użyj z szablonem ODT lub gdy potrzebujesz edytowalnego pliku ODT. |
| PDF | Wymaga LibreOffice z programem `soffice` dostępnym w `PATH`. |

## Rozwiązywanie Problemów

| Problem | Co sprawdzić |
| --- | --- |
| Pliku meczu nie ma na liście | Sprawdź, czy jest to eksport `.pcs`, `.psc` lub `.zip`, albo użyj **Wybierz plik**. |
| Dywizja lub kategoria nie dostała dyplomu | Sprawdź filtry, `min_competitors` oraz zasady DNF/DQ w konfiguracji. |
| Zawodnik ma nieoczekiwany status DNF | Sprawdź, czy ma wyniki ze wszystkich torów i czy zaliczył Chrono. |
| Pole szablonu powoduje błąd | Sprawdź pisownię w tabeli Pól Szablonu. |
| Nie udaje się utworzyć PDF | Zainstaluj LibreOffice i sprawdź, czy `soffice` jest dostępne w `PATH`. |
| Tekst jest w złym miejscu | Popraw formatowanie akapitu lub tabeli w szablonie, a następnie wygeneruj dokument ponownie. |

## Zapamiętywane ustawienia

Aplikacja zapamiętuje ustawienia okna, ścieżki ostatnio wybranych plików oraz układ tabel, sortowanie i filtry w `%APPDATA%\PractiScore Diplomas\settings.json` w Windows. Zmiany strzelców i konfiguracji nadal wymagają użycia odpowiednich przycisków zapisu; zatwierdzone poprawki tabeli dyplomów są przechowywane osobno w pliku YAML z danymi dyplomów.
