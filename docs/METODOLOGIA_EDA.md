# Metodologia eksploracyjnej analizy publikacji

Analiza eksploracyjna stanowi uzupełnienie przeglądu literatury dotyczącego projektowania systemów informatycznych wspierających inkluzywność, ze szczególnym uwzględnieniem reprezentacji tożsamości użytkownika w systemach organizacyjnych. Jej celem nie jest przeprowadzenie pełnego systematycznego przeglądu literatury, lecz wstępne rozpoznanie skali i struktury pola badawczego oraz wskazanie potencjalnej luki na styku badań nad inkluzywnością, doświadczeniami osób transpłciowych, systemami HR oraz architekturą zarządzania tożsamością.

Źródłem danych są bazy OpenAlex, Crossref oraz PubMed. W projekcie zachowano dotychczasowy zbiór `openalex_workplace_inclusion.csv`, obejmujący publikacje z lat 2000-2025 wyszukane na podstawie terminów związanych z inkluzywnością, różnorodnością oraz środowiskiem pracy. Ponieważ zbiór ten zawiera jedynie tytuł, rok publikacji i liczbę cytowań, jego wyniki należy traktować jako analizę sygnałów tematycznych, a nie jako kompletną analizę treści publikacji.

Na potrzeby artykułu przygotowano również dedykowane kolektory danych: `src/api/openalex_identity_overlay.py`, `src/api/crossref_identity_overlay.py` oraz `src/api/pubmed_identity_overlay.py`. Rozszerzają one wyszukiwanie o zapytania bliższe problemowi badawczemu, obejmujące m.in. digital identity, user identity, preferred name, pronouns, transgender workplace, Identity and Access Management, identity lifecycle management, federated identity, Value Sensitive Design oraz marital/civil/legal status w systemach informacyjnych.

Wyniki z poszczególnych źródeł są sprowadzane do wspólnego schematu obejmującego tytuł, rok, liczbę cytowań, DOI lub identyfikator zewnętrzny, źródło publikacji, autorów, abstrakt, grupę zapytania oraz nazwę bazy. Następnie rekordy są łączone i deduplikowane na podstawie DOI albo pary tytuł-rok.

Analiza klasyfikuje publikacje do grup tematycznych odpowiadających głównym wątkom draftu:

- reprezentacja tożsamości użytkownika,
- doświadczenia osób transpłciowych w środowisku pracy,
- IAM i architektura systemów tożsamości,
- systemy HR i systemy organizacyjne,
- projektowanie inkluzywne oraz Value Sensitive Design,
- relacyjny i prawny status użytkownika,
- ryzyka związane z AI, automatyzacją i dyskryminacją.

Dla każdej grupy obliczana jest liczba publikacji, udział w zbiorze, suma i mediana cytowań oraz zakres lat. Dodatkowo generowane są trendy roczne, macierz współwystępowania tematów oraz lista publikacji najbardziej zgodnych z ramą artykułu, przeznaczona do ręcznej selekcji literatury.

Wyniki eksploracyjne mogą zostać wykorzystane do uzasadnienia luki badawczej: literatura dotycząca inkluzywności i doświadczeń osób transpłciowych w organizacjach jest widoczna, podobnie jak osobne nurty dotyczące projektowania inkluzywnego i technologii organizacyjnych, natomiast techniczna reprezentacja tożsamości użytkownika w architekturze systemów organizacyjnych pozostaje słabiej zintegrowana z badaniami nad bezpieczeństwem, prywatnością i społecznym funkcjonowaniem użytkowników.
