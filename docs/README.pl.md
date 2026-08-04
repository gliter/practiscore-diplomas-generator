# Generator dyplomów PractiScore

Program odczytuje eksport PractiScore `.pcs` lub `.psc`, wybiera zdobywców dyplomów na podstawie konfiguracji YAML i generuje jeden dokument DOCX z dyplomami.

## Uruchomienie w Windows

Uruchom `practiscore-diplomas.exe` w PowerShellu, będąc w folderze programu. Program nie wymaga zainstalowanego Pythona ani `uv`. Folder `configs` i szablon DOCX możesz trzymać obok programu albo podać do nich pełne ścieżki.

## Język

Pomoc jest wybierana na podstawie ustawień systemu. Dla polskiego systemu używany jest język polski, a dla pozostałych angielski. Język można wymusić opcją `--language` przed lub po komendzie:

```powershell
practiscore-diplomas --language pl --help
practiscore-diplomas parse --language en --help
```

## Parsowanie meczu

Konfiguracja jest wymagana:

```powershell
practiscore-diplomas parse `
  -i "match-export.pcs" `
  -c "configs\gpa_t1_config.yaml"
```

Można też podać rozpakowany katalog zawierający `match_def.json` i `match_scores.json`. Domyślnie powstają pliki:

```text
shooters-summary-<nazwa-meczu>.yaml
diplomas-data-<nazwa-meczu>.yaml
```

Spacje i niedozwolone znaki nazwy meczu są zamieniane na łączniki lub podkreślenia. Ścieżki można ustawić jawnie:

```powershell
practiscore-diplomas parse -i "match-export.pcs" `
  -c "competition.yaml" `
  -s "results\summary.yaml" `
  -d "results\diplomas.yaml"
```

Podsumowanie strzelców jest indeksowane przez `sh_uid` z PractiScore. Zawiera `shooter_id`, imię, nazwisko, dywizję, klasę, kategorie, czas surowy, kary, punkty w dół, nietrafienia stalowych celów, czas całkowity oraz statusy DNF i DQ. Usunięci strzelcy i osoby bez aktualnych wyników nie są wybierane. Brakujące tory oraz niezaliczone Chrono mogą oznaczyć strzelca jako DNF.

## Dwa tryby pracy

Program można używać na dwa sposoby:

1. `parse` → `render`: najpierw parsujesz mecz, przeglądasz wygenerowany plik `diplomas-data-<nazwa-meczu>.yaml` i możesz ręcznie go zmienić, a dopiero potem generujesz dokument DOCX. Ten tryb jest właściwy, gdy chcesz poprawić nazwisko, zmienić wyświetlaną wartość, usunąć wybrany dyplom albo wprowadzić inną świadomą korektę przed wydrukiem.
2. Bezpośredni `render`: podajesz eksport meczu, konfigurację i szablon DOCX, a program parsuje mecz, zapisuje oba pliki pośrednie YAML i generuje dokument w jednym kroku. Wybierz ten tryb, gdy chcesz wykonać wszystko jednym poleceniem, ale nadal mieć dane do sprawdzenia.

Tryb dwuetapowy przydaje się także wtedy, gdy te same dane dyplomów chcesz później wyrenderować z innym szablonem.

## Konfiguracja

Konfiguracja zawiera mapy `maps` oraz serie w sekcji `series`. Minimalna seria wygląda tak:

```yaml
series:
  best_in_division:
    type: best_shooter
    group_by: [division]
    min_competitors: [1, 6, 11]
    exclude_dq: true
    exclude_dnf: true
    ineligible_penalties: []
    text:
      first_line: "{{ division }} DIVISION"
      second_line: "{{ place }}"
```

Obsługiwane typy serii to `best_shooter`, `most_accurate` i `fastest`. `group_by` może zawierać `division`, `class` i `category`. Lista progów jest kumulatywna: `[1, 6, 11]` oznacza jeden dyplom dla 1-5 uprawnionych zawodników, dwa dla 6-10 i trzy od 11. Próg `1` zapobiega utworzeniu dyplomu dla pustej grupy.

Filtry są wyrażeniami regularnymi. `include` ogranicza wartości, a `exclude` je usuwa. Brak filtra oznacza uwzględnienie wszystkiego, a brak `exclude` oznacza brak wykluczeń. Gdy istnieje `include`, `exclude` dla tego samego wymiaru nie jest potrzebne.

```yaml
filters:
  divisions:
    include: ["CCP|CDP|ESP|SSP"]
  categories:
    exclude: ["Lady"]
```

Pola `exclude_shooters.surnames` i `exclude_shooters.ids` na najwyższym poziomie przyjmują listy regexów. `mark_chrono_failure_as_dnf` ma domyślnie wartość `true`; ustaw `false`, jeżeli niezaliczenie Chrono nie ma wpływać na kwalifikację.

Mapy zamieniają wartości eksportu na tekst wyświetlany na dyplomie. Mapy tekstowe używają kluczy regex, a mapy miejsc liczb całkowitych:

```yaml
maps:
  division_code:
    "CO": CO
  division_place:
    1: CHAMPION
```

Tekst może korzystać z `division`, `category`, `class`, `place`, `type`, `shooter.<pole>` oraz wywołań map, np. `{{ division_code(division) }}`. Brak mapowania jest błędem konfiguracji.

## Szablon DOCX

Wygenerowane dane dyplomów renderuje się przy pomocy szablonu DOCX:

```powershell
practiscore-diplomas render `
  -d "diplomas-data-Plata-o-Plomo-2025.yaml" `
  -t "diploma-template.docx" `
  -o "diplomas.docx"
```

Szablon jest kopiowany dla każdego rekordu dyplomu w kolejności serii i rankingu. Wynikiem jest jeden dokument DOCX z jedną stroną na dyplom. Zmienne w akapitach i tabelach mają składnię `{{ pole }}`.

Można też parsować i renderować bezpośrednio z eksportu meczu. W tym trybie konfiguracja jest wymagana. Polecenie zapisze również obok dokumentu pliki `shooters-summary-<nazwa-meczu>.yaml` i `diplomas-data-<nazwa-meczu>.yaml`, które można przejrzeć lub ręcznie zmienić:

```powershell
practiscore-diplomas render `
  -i "match-export.pcs" `
  -c "configs\gpa_t1_config.yaml" `
  -t "szablon-dyplomu.docx"
```

Domyślny plik wynikowy to `diplomas.docx` dla opcji `-d` oraz `diplomas-<nazwa-meczu>.docx` dla opcji `-i`. Opcja `-o` pozwala zmienić ścieżkę.

Dostępne pola dyplomu to `first_line`, `second_line`, opcjonalne `third_line` i `fourth_line`, `place`, `division`, `category`, `class` oraz `metric_value`. Pola strzelca zapisuje się np. jako `{{ shooter.first_name }}`, `{{ shooter.last_name }}`, `{{ shooter.raw_time }}` i `{{ shooter.points_down }}`. Brakujące opcjonalne linie są puste; brak pozostałych pól lub nieznana zmienna kończy się błędem.

## Przykładowy szablon

W folderze programu znajduje się `example-diploma-template.docx`, czyli minimalny szablon zawierający tylko linie dyplomu oraz imię i nazwisko strzelca. Użyj go, aby sprawdzić cały proces przed przygotowaniem własnego szablonu.
