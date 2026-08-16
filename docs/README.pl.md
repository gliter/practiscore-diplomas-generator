# Generator dyplomów PractiScore

Program tworzy dokument z dyplomami na podstawie eksportu meczu z PractiScore. Odczytuje wyniki, stosuje reguły nagród i wybiera zawodników, którzy powinni otrzymać dyplom.

Ta instrukcja jest przeznaczona dla organizatorów zawodów. Do korzystania z wersji Windows nie potrzebujesz Pythona ani narzędzi programistycznych.

## Co Przygotować

Przed rozpoczęciem przygotuj:

| Element | Co to jest |
| --- | --- |
| Eksport PractiScore | Plik `.psc` wyeksportowany z PractiScore po zakończeniu meczu. |
| Konfigurację | Plik YAML zawierający reguły przyznawania dyplomów. Gotowe przykłady są w folderze `configs`. |
| Szablon dyplomu | Dokument `.docx` albo `.odt` z polami opisanymi dalej w instrukcji. |

Trzymaj folder `configs` obok `practiscore-diplomas.exe`. Dla wygody plik meczu i szablon możesz umieścić w tym samym folderze.

## Eksport Meczu Z PractiScore

Eksport wykonaj dopiero po zatwierdzeniu wyników i zakończeniu pracy nad meczem.

1. Na głównym ekranie meczu wybierz **Import / Export**.

   ![Główny ekran meczu PractiScore z zaznaczoną opcją Import / Export](psc-1.png)

2. W sekcji **Match Import/Export** wybierz **Export Match**.

   ![Ekran Import / Export w PractiScore z zaznaczoną opcją Export Match](psc-2.png)

3. Zapisz wyeksportowany plik meczu. W generatorze wybierz go jako eksport PractiScore.

## Najszybszy Sposób Na Dyplomy

1. Kliknij dwukrotnie `practiscore-diplomas.exe`.
2. Użyj strzałek góra/dół i klawisza Enter, aby wybrać **Wygenerować dyplomy z pliku PractiScore**.
3. Wybierz konfigurację nagród, eksport meczu `.psc` oraz szablon dyplomu.
4. W oknie zapisu zaakceptuj proponowaną nazwę albo wybierz inną.
5. Po wyświetleniu komunikatu o sukcesie otwórz utworzony dokument i sprawdź kilka pierwszych dyplomów przed drukowaniem.

Listy pokazują pliki znalezione w bieżącym folderze. Wybierz **Wybierz plik**, aby użyć standardowego okna wyboru pliku systemu Windows. Jeśli zamkniesz je bez wskazania pliku, wrócisz do listy.

Ten bezpośredni sposób pracy tworzy obok dokumentu także dwa pliki YAML:

```text
shooters-summary-<nazwa-meczu>.yaml
diplomas-data-<nazwa-meczu>.yaml
```

Służą one do sprawdzenia, kto otrzymał dyplom i dlaczego. Warto zachować je razem z dokumentacją meczu.

## Którą Opcję Menu Wybrać

| Opcja menu | Kiedy jej użyć |
| --- | --- |
| Wygenerować dyplomy z pliku PractiScore | Zwykły wybór. Program parsuje mecz, zapisuje dane do kontroli i od razu tworzy dokument. |
| Sparsować plik PractiScore do plików YAML | Chcesz najpierw sprawdzić albo ręcznie zmienić listę dyplomów. |
| Wygenerować dyplomy z pliku YAML z danymi dyplomów | Masz już sprawdzony plik `diplomas-data-*.yaml` i chcesz ponownie utworzyć dokument, np. z innym szablonem. |

Jeżeli potrzebujesz ręcznych zmian, najpierw wybierz **Sparsować plik PractiScore do plików YAML**. Otwórz `diplomas-data-<nazwa-meczu>.yaml` w edytorze tekstu, wprowadź ostrożne poprawki, a następnie wybierz **Wygenerować dyplomy z pliku YAML z danymi dyplomów**. Ten sposób przydaje się np. do poprawienia wyświetlanego nazwiska, usunięcia pojedynczego dyplomu lub zmiany tekstu przed drukiem.

## Wybór Konfiguracji

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
| `type` | Sposób tworzenia rankingu: `best_shooter` wybiera najlepszy wynik, `most_accurate` wybiera najmniejszą liczbę punktów w dół, a `fastest` najmniejszy czas surowy. |
| `group_by` | Tworzy osobne rankingi dla każdej podanej wartości: `division`, `class` i/lub `category`. Pomiń je, aby utworzyć jeden ranking dla wszystkich. |
| `min_competitors` | Progi przyznawania dyplomów. `[1, 6, 11]` daje jeden dyplom dla 1-5 uprawnionych osób, dwa dla 6-10 i trzy od 11 osób. `[5]` nie daje dyplomu poniżej 5 osób, a od 5 daje jeden. |
| `exclude_dq` | Gdy ma wartość `true`, zawodnik z DQ nie może otrzymać tej nagrody. Domyślnie `true`. |
| `exclude_dnf` | Gdy ma wartość `true`, zawodnik z DNF nie może otrzymać tej nagrody. Domyślnie `true`. |
| `ineligible_penalties` | Lista nazw kar, które wykluczają zawodnika tylko z tej serii. Użyj dokładnej nazwy kary z eksportu. |

Każda seria wymaga `type`, `text.first_line` i `text.second_line`. `group_by`, filtry, reguły kar oraz trzecia i czwarta linia tekstu są opcjonalne.

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
| `shooter.dnf`, `shooter.dq`, `shooter.shooter_uid` | Status zawodnika i wewnętrzny identyfikator. |

Te linie YAML przekazują do szablonu dokumentu wartości `first_line` do `fourth_line`. Pola w pliku DOCX lub ODT opisuje następna sekcja. Wywołania map stosuje się w konfiguracji, a nie bezpośrednio w szablonie dokumentu.

### Wykluczanie Konkretnych Zawodników I Niezaliczonego Chrono

Użyj `exclude_shooters`, aby usunąć ze wszystkich serii zawodników nieturniejowych, rekordy testowe albo rekord czasu PAR. `surnames` oraz `ids` są listami wyrażeń regularnych; każda z nich może być pusta.

```yaml
exclude_shooters:
  surnames: ["(?i)^par$"]
  ids: []
```

`mark_chrono_failure_as_dnf: true` jest ustawieniem domyślnym. Gdy mecz zawiera tor Chrono, zawodnik, którego kontrola wyposażenia nie ma statusu Pass, jest traktowany jako DNF. Zmień wartość na `false` tylko wtedy, gdy regulamin zawodów wymaga innego rozstrzygnięcia.

## Przygotowanie Szablonu Dyplomu

Użyj pliku DOCX albo ODT jako szablonu. Wstaw pola w miejscach, w których tekst ma się zmieniać. Na przykład:

```text
{{ first_line }}
{{ second_line }}
{{ shooter.first_name }} {{ shooter.last_name }}
```

Program tworzy kopię szablonu dla każdego dyplomu. Zachowuje formatowanie dokumentu, w tym czcionki, rozmiary, wyrównanie i tabele. W pakiecie znajduje się `example-diploma-template.docx`, czyli niewielki działający przykład.

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
| `shooter.dq` | `True`, gdy zawodnik ma status DQ. |
| `shooter.shooter_uid` | Wewnętrzny identyfikator PractiScore. Zwykle nie jest potrzebny na dyplomie. |

Używaj dokładnie takiej pisowni i nawiasów klamrowych jak w tabeli. Nieznane pole zatrzyma renderowanie, dzięki czemu literówka nie utworzy błędnego dyplomu bez ostrzeżenia.

## Formaty Wynikowe

| Format | Informacja |
| --- | --- |
| DOCX | Najlepszy wybór dla szablonu DOCX i gdy dokument ma być jeszcze edytowany. |
| ODT | Działa bezpośrednio przy użyciu szablonu ODT. |
| PDF | Wymaga zainstalowanego LibreOffice z programem `soffice` dostępnym w `PATH`. |

Konwersja między DOCX i ODT również wymaga LibreOffice. W trybie interaktywnym format wynikowy zależy od rozszerzenia wybranego w oknie zapisu.

## Użycie Z Wiersza Poleceń

Tryb interaktywny jest zalecany. Poniższe polecenia przydają się, gdy chcesz powtarzać ten sam proces lub automatyzować znany przebieg pracy.

Bezpośrednie generowanie z meczu:

```powershell
practiscore-diplomas render `
  -i "match-export.psc" `
  -c "configs\gpa_t1_config.yaml" `
  -t "diploma-template.docx" `
  --output-docx "diplomas.docx"
```

Tylko utworzenie danych do kontroli:

```powershell
practiscore-diplomas parse `
  -i "match-export.psc" `
  -c "configs\gpa_t1_config.yaml"
```

Generowanie ze sprawdzonych danych:

```powershell
practiscore-diplomas render `
  -d "diplomas-data-Nazwa-Meczu.yaml" `
  -t "diploma-template.docx" `
  --output-docx "diplomas.docx"
```

W razie potrzeby użyj `--output-odt` albo `--output-pdf` zamiast `--output-docx`. Ścieżka po tych opcjach jest opcjonalna; bez niej program utworzy plik o sensownej domyślnej nazwie.

## Rozwiązywanie Problemów

| Problem | Co sprawdzić |
| --- | --- |
| Pliku meczu nie ma na liście | Sprawdź, czy jest to eksport `.psc`, albo użyj **Wybierz plik**. |
| Dywizja lub kategoria nie dostała dyplomu | Sprawdź filtry, `min_competitors` oraz zasady DNF/DQ w konfiguracji. |
| Zawodnik ma nieoczekiwany status DNF | Sprawdź, czy ma wyniki ze wszystkich torów i czy zaliczył Chrono. |
| Pole szablonu powoduje błąd | Sprawdź pisownię w tabeli Pól Szablonu. |
| Nie udaje się utworzyć PDF | Zainstaluj LibreOffice i sprawdź, czy `soffice` jest dostępne w `PATH`. |
| Tekst jest w złym miejscu | Popraw formatowanie akapitu lub tabeli w szablonie, a następnie wygeneruj dokument ponownie. |
