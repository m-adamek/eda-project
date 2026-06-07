from __future__ import annotations

from datetime import datetime
from itertools import combinations
from pathlib import Path
import re

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Ten moduł wykonuje eksploracyjną analizę danych (EDA).
# EDA = Exploratory Data Analysis, czyli wstępne rozpoznanie danych:
# - ile mamy publikacji,
# - z jakich źródeł pochodzą,
# - jak rozkładają się w czasie,
# - jakie tematy pojawiają się najczęściej,
# - które tematy współwystępują.
#
# Biblioteki:
# - pandas: praca z tabelami danych, podobnie jak arkusz kalkulacyjny,
# - matplotlib/seaborn: tworzenie wykresów,
# - pathlib.Path: wygodne i bezpieczne budowanie ścieżek do plików,
# - re: wyrażenia regularne, czyli dopasowywanie wzorców tekstu.

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
FALLBACK_DATA = RAW_DIR / "openalex_workplace_inclusion.csv"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
VISUALS_DIR = PROJECT_ROOT / "visuals"
ANALYSIS_START_YEAR = 2000
ANALYSIS_END_YEAR = max(2025, datetime.now().year)


TOPIC_KEYWORDS = {
    # Każdy klucz to nazwa kategorii tematycznej.
    # Każda lista zawiera słowa/frazy, których szukamy w tytule i abstrakcie.
    # Jeśli publikacja zawiera choć jedną frazę z listy, dostaje flagę True
    # dla danej kategorii.
    "identity_representation": [
        "identity",
        "user identity",
        "representation",
        "digital identity",
        "legal identity",
        "display identity",
        "preferred name",
        "pronouns",
        "self presentation",
    ],
    "transgender_workplace_experience": [
        "transgender",
        "transsexual",
        "gender identity",
        "gender transition",
        "misgendering",
        "deadnaming",
        "outing",
        "lgbt",
        "lgbtq",
        "sexual orientation",
    ],
    "iam_and_architecture": [
        "identity and access management",
        "iam",
        "access management",
        "identity management",
        "federated identity",
        "provisioning",
        "attribute",
        "rbac",
        "abac",
        "authentication",
    ],
    "hr_and_organizational_systems": [
        "human resource",
        "hr",
        "workplace",
        "employee",
        "organization",
        "organizational",
        "enterprise system",
        "information system",
        "collaboration platform",
    ],
    "inclusive_design_and_vsd": [
        "inclusive design",
        "inclusion",
        "diversity",
        "equity",
        "value sensitive design",
        "human centered",
        "user centered",
        "participatory design",
        "accessibility",
    ],
    "relational_and_legal_status": [
        "marital status",
        "same-sex marriage",
        "civil status",
        "legal status",
        "relationship",
        "family",
        "spouse",
    ],
    "ai_bias_and_digital_risk": [
        "artificial intelligence",
        "ai",
        "algorithmic",
        "bias",
        "discrimination",
        "automated decision",
        "recruitment",
    ],
}


FOCUS_TOPICS = [
    # Te kategorie są najbliżej głównej tezy artykułu.
    # Suma tych flag tworzy draft_relevance_score, czyli prosty wynik trafności
    # względem draftu.
    "identity_representation",
    "transgender_workplace_experience",
    "iam_and_architecture",
    "hr_and_organizational_systems",
    "inclusive_design_and_vsd",
]


def _keyword_pattern(keyword: str) -> re.Pattern[str]:
    # Tworzy wzorzec wyrażenia regularnego dla słowa lub frazy.
    # re.escape zabezpiecza znaki specjalne, np. nawiasy albo plusy.
    # (?<![a-z0-9]) i (?![a-z0-9]) pilnują granic słowa:
    # dzięki temu "ai" nie dopasuje się przypadkiem jako część dłuższego słowa.
    escaped = re.escape(keyword.lower())
    return re.compile(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])")


def discover_publication_files() -> list[Path]:
    # Szukamy wszystkich nowych eksportów wieloźródłowych.
    # glob("*identity_overlay*.csv") oznacza: znajdź pliki CSV, których nazwa
    # zawiera identity_overlay.
    targeted_files = sorted(RAW_DIR.glob("*identity_overlay*.csv"))
    if targeted_files:
        return targeted_files

    # Jeśli nie ma nowych eksportów, używamy starego lokalnego zbioru OpenAlex.
    return [FALLBACK_DATA]


def _dedupe_publications(df: pd.DataFrame) -> pd.DataFrame:
    # Ta funkcja usuwa duplikaty publikacji po scaleniu źródeł.
    # Ten sam artykuł może pojawić się np. w OpenAlex i Crossref.
    df = df.copy()

    # Normalizujemy DOI: małe litery, usunięty prefiks URL, obcięte spacje.
    # DOI jest najlepszym identyfikatorem publikacji, jeśli jest dostępny.
    df["doi_norm"] = (
        df["doi"]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.replace("https://doi.org/", "", regex=False)
        .str.strip()
    )

    # Jeśli DOI brakuje, używamy awaryjnie tytułu i roku.
    # title_norm usuwa znaki interpunkcyjne i sprowadza tytuł do porównywalnej formy.
    df["title_norm"] = (
        df["title"]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.replace(r"[^a-z0-9]+", " ", regex=True)
        .str.strip()
    )

    # Rekordy z DOI deduplikujemy po DOI.
    with_doi = df[df["doi_norm"] != ""].drop_duplicates(subset=["doi_norm"], keep="first")

    # Rekordy bez DOI deduplikujemy po tytule i roku.
    without_doi = df[df["doi_norm"] == ""].drop_duplicates(subset=["title_norm", "year"], keep="first")

    # Łączymy obie części i usuwamy pomocnicze kolumny normalizacyjne.
    return pd.concat([with_doi, without_doi], ignore_index=True).drop(columns=["doi_norm", "title_norm"])


def load_publications(path: Path | None = None) -> pd.DataFrame:
    # Ładuje dane publikacji z CSV.
    # Jeśli path podano ręcznie, czytamy tylko ten plik.
    # Jeśli path=None, automatycznie znajdujemy wszystkie źródła w data/raw/.
    use_discovery = path is None
    paths = [path] if path is not None else discover_publication_files()
    frames = []
    for publication_path in paths:
        # pd.read_csv czyta plik CSV do DataFrame.
        frame = pd.read_csv(publication_path)

        # raw_file pozwala potem sprawdzić, z którego pliku pochodzi rekord.
        frame["raw_file"] = publication_path.name
        frames.append(frame)

    # pd.concat skleja wiele tabel w jedną dużą tabelę.
    df = pd.concat(frames, ignore_index=True)

    # Jeśli nowe pliki istnieją, ale są puste, wracamy do starego zbioru.
    if df.empty and use_discovery and FALLBACK_DATA.exists() and FALLBACK_DATA not in paths:
        df = pd.read_csv(FALLBACK_DATA)
        df["raw_file"] = FALLBACK_DATA.name

    # Minimalny wymagany zestaw kolumn.
    expected = {"title", "year", "citations"}
    missing = expected.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

    # dropna usuwa wiersze bez tytułu albo roku, bo takich rekordów nie da się
    # sensownie analizować czasowo ani tematycznie.
    df = df.dropna(subset=["title", "year"]).copy()
    df["title"] = df["title"].astype(str).str.strip()

    # Starszy zbiór ma mniej kolumn niż nowe eksporty, więc uzupełniamy brakujące
    # kolumny pustymi wartościami lub etykietą legacy.
    if "abstract" not in df.columns:
        df["abstract"] = ""
    if "query_group" not in df.columns:
        df["query_group"] = "legacy_workplace_inclusion"
    if "source_database" not in df.columns:
        df["source_database"] = "openalex_legacy"
    if "doi" not in df.columns:
        df["doi"] = ""
    if "external_id" not in df.columns:
        df["external_id"] = ""

    # search_text to tekst, w którym szukamy słów kluczowych.
    # Łączymy tytuł i abstrakt, bo sam tytuł bywa za krótki.
    df["abstract"] = df["abstract"].fillna("").astype(str)
    df["title_lower"] = df["title"].str.lower()
    df["search_text"] = (df["title"].fillna("") + " " + df["abstract"]).str.lower()

    # pd.to_numeric konwertuje rok i cytowania na liczby.
    # errors="coerce" zamienia niepoprawne wartości na NaN, które potem można usunąć.
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["citations"] = pd.to_numeric(df["citations"], errors="coerce").fillna(0).astype(int)
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)

    # Zakres bazowy artykułu zaczyna się w 2000 roku. Górną granicę rozszerzamy
    # do bieżącego roku, aby praktyczne źródła webowe i dokumentacja produktów
    # z najnowszymi wersjami nie wypadały z analizy.
    df = df[df["year"].between(ANALYSIS_START_YEAR, ANALYSIS_END_YEAR)].copy()

    df = _dedupe_publications(df)

    # decade tworzy etykiety dekad, np. 2000s, 2010s.
    df["decade"] = (df["year"] // 10 * 10).astype(str) + "s"
    return df


def add_topic_flags(df: pd.DataFrame) -> pd.DataFrame:
    # Dodaje do tabeli kolumny True/False dla każdej kategorii tematycznej.
    # Przykład: jeśli search_text zawiera "preferred name", kolumna
    # identity_representation będzie True.
    df = df.copy()
    for topic, keywords in TOPIC_KEYWORDS.items():
        # Najpierw kompilujemy wzorce regex dla słów kluczowych danej kategorii.
        patterns = [_keyword_pattern(keyword) for keyword in keywords]

        # apply uruchamia funkcję dla każdego wiersza/tekstu w kolumnie.
        # any(...) zwraca True, jeśli przynajmniej jeden wzorzec pasuje.
        df[topic] = df["search_text"].apply(
            lambda text: any(pattern.search(text) for pattern in patterns)
        )

    # matched_topic_count mówi, ile kategorii pasuje do publikacji.
    df["matched_topic_count"] = df[list(TOPIC_KEYWORDS)].sum(axis=1)

    # draft_relevance_score liczy tylko najważniejsze kategorie dla artykułu.
    df["draft_relevance_score"] = df[FOCUS_TOPICS].sum(axis=1)
    return df


def build_topic_summary(df: pd.DataFrame) -> pd.DataFrame:
    # Buduje tabelę zbiorczą: ile publikacji pasuje do każdej kategorii,
    # jaki mają udział w całym zbiorze i ile mają cytowań.
    rows = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        subset = df[df[topic]]
        rows.append(
            {
                "topic": topic,
                "publications": int(len(subset)),
                "share_of_dataset": round(len(subset) / len(df), 4),
                "citations_total": int(subset["citations"].sum()),
                "citations_median": float(subset["citations"].median()) if len(subset) else 0.0,
                "first_year": int(subset["year"].min()) if len(subset) else None,
                "latest_year": int(subset["year"].max()) if len(subset) else None,
                "keyword_scope": ", ".join(keywords),
            }
        )

    # sort_values porządkuje kategorie od najliczniejszej do najmniej licznej.
    return pd.DataFrame(rows).sort_values("publications", ascending=False)


def build_topic_year_counts(df: pd.DataFrame) -> pd.DataFrame:
    # Buduje tabelę do wykresów trendów rocznych.
    # Dla każdej kategorii liczy liczbę publikacji w każdym roku.
    frames = []
    for topic in TOPIC_KEYWORDS:
        yearly = (
            df[df[topic]]
            # groupby("year") grupuje rekordy według roku.
            .groupby("year")
            # size() liczy liczbę wierszy w każdej grupie.
            .size()
            .rename("publications")
            .reset_index()
        )
        yearly["topic"] = topic
        frames.append(yearly)
    return pd.concat(frames, ignore_index=True)


def build_cooccurrence(df: pd.DataFrame) -> pd.DataFrame:
    # Buduje macierz współwystępowania tematów.
    # Komórka [A, B] mówi, ile publikacji pasuje jednocześnie do A i B.
    topics = list(TOPIC_KEYWORDS)
    matrix = pd.DataFrame(0, index=topics, columns=topics)

    # Przekątna macierzy to liczba publikacji w samej kategorii.
    for topic in topics:
        matrix.loc[topic, topic] = int(df[topic].sum())

    # combinations(topics, 2) tworzy wszystkie pary tematów bez powtórzeń.
    for left, right in combinations(topics, 2):
        count = int((df[left] & df[right]).sum())
        matrix.loc[left, right] = count
        matrix.loc[right, left] = count
    return matrix


def build_top_articles(df: pd.DataFrame, limit: int = 40) -> pd.DataFrame:
    # Wybiera publikacje potencjalnie najważniejsze do ręcznego przejrzenia.
    # Najpierw sortujemy po draft_relevance_score, potem po cytowaniach i roku.
    columns = ["title", "year", "citations", "source_database", "source", "url", "draft_relevance_score", *TOPIC_KEYWORDS.keys()]
    columns = [column for column in columns if column in df.columns]
    return (
        df[df["draft_relevance_score"] > 0]
        .sort_values(["draft_relevance_score", "citations", "year"], ascending=[False, False, False])
        .loc[:, columns]
        .head(limit)
    )


def save_visuals(df: pd.DataFrame, topic_year: pd.DataFrame, cooccurrence: pd.DataFrame) -> None:
    # Tworzy pliki PNG z wykresami.
    # Używamy kolorystyki opartej na barwach flagi transpłciowej (niebieski, różowy, biały/szary).
    # Barwy zostały dostosowane pod kątem nasycenia i jasności, aby zachować kontrast i czytelność na jasnym tle.
    from matplotlib.colors import LinearSegmentedColormap

    sns.set_theme(style="whitegrid", context="notebook")
    VISUALS_DIR.mkdir(parents=True, exist_ok=True)

    # Definicje kolorów 
    TRANS_BLUE_DARK = "#3AA0D8"   # Ciemniejszy niebieski dla kontrastu linii
    TRANS_BLUE_LIGHT = "#8CD8F8"  # Jasnoniebieski z flagi
    TRANS_PINK_DARK = "#D87A8C"   # Ciemniejszy różowy dla kontrastu linii
    TRANS_PINK_LIGHT = "#F8B9C5"  # Jasnoróżowy z flagi
    TRANS_GREY = "#8F9CA6"        # Szary/srebrny reprezentujący biel na jasnym tle

    # Figure 1: ogólny trend liczby publikacji rocznie.
    annual = df.groupby("year").size().rename("publications").reset_index()

    # rolling(3).mean() liczy średnią kroczącą z 3 lat, co wygładza pojedyncze skoki.
    annual["rolling_3y"] = annual["publications"].rolling(3, min_periods=1).mean()

    plt.figure(figsize=(10, 5))
    sns.lineplot(data=annual, x="year", y="publications", color=TRANS_BLUE_DARK, linewidth=2.5, label="Publikacje")
    sns.lineplot(data=annual, x="year", y="rolling_3y", color=TRANS_PINK_DARK, linewidth=2.5, linestyle="--", label="Średnia 3-letnia")
    plt.title("Publikacje źródłowe związane z inkluzywnością i systemami organizacji")
    plt.xlabel("Rok")
    plt.ylabel("Liczba publikacji")
    plt.tight_layout()
    plt.savefig(VISUALS_DIR / "01_publication_trend.png", dpi=180)
    plt.close()

    # Figure 2: trendy tylko dla najważniejszych kategorii artykułu.
    focus_year = topic_year[topic_year["topic"].isin(FOCUS_TOPICS)]
    plt.figure(figsize=(11, 6))

    # Paleta mapująca kategorie na odcienie flagi trans
    trans_palette = {
        "identity_representation": TRANS_BLUE_DARK,
        "transgender_workplace_experience": TRANS_PINK_DARK,
        "iam_and_architecture": TRANS_GREY,
        "hr_and_organizational_systems": TRANS_BLUE_LIGHT,
        "inclusive_design_and_vsd": TRANS_PINK_LIGHT
    }

    sns.lineplot(data=focus_year, x="year", y="publications", hue="topic", palette=trans_palette, marker="o", linewidth=2.5)
    plt.title("Trendy tematów kluczowych dla artykułu")
    plt.xlabel("Rok")
    plt.ylabel("Liczba publikacji")
    plt.legend(title="Temat", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(VISUALS_DIR / "02_topic_trends.png", dpi=180)
    plt.close()

    # Figure 3: heatmapa współwystępowania tematów.
    # Tworzymy niestandardową skalę kolorów: od bieli, przez jasny błękit i jasny róż, aż po nasycony róż
    cmap_colors = ["#FFFFFF", "#C5EBFD", "#FAD5DB", "#D87A8C"]
    trans_cmap = LinearSegmentedColormap.from_list("trans_flag_heatmap", cmap_colors)

    plt.figure(figsize=(9, 7))
    sns.heatmap(cooccurrence, annot=True, fmt="d", cmap=trans_cmap, cbar_kws={"label": "Liczba publikacji"})
    plt.title("Współwystępowanie tematów w tytułach publikacji")
    plt.tight_layout()
    plt.savefig(VISUALS_DIR / "03_topic_cooccurrence.png", dpi=180)
    plt.close()


def run_analysis() -> None:
    # Główna funkcja analityczna. To ją wywołuje main.py.
    # Kolejność jest następująca:
    # 1. wczytaj publikacje,
    # 2. dodaj flagi tematyczne,
    # 3. zbuduj tabele wynikowe,
    # 4. zapisz CSV i wykresy.
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df = add_topic_flags(load_publications())

    # Podsumowanie według źródła danych: ile rekordów pochodzi z OpenAlex,
    # Crossref i PubMed.
    source_summary = (
        df.groupby("source_database")
        .agg(publications=("title", "count"), first_year=("year", "min"), latest_year=("year", "max"))
        .reset_index()
        .sort_values("publications", ascending=False)
    )

    # Tabele analityczne używane potem w opisie wyników i na posterze.
    topic_summary = build_topic_summary(df)
    topic_year = build_topic_year_counts(df)
    cooccurrence = build_cooccurrence(df)
    top_articles = build_top_articles(df)

    # Lista kolumn do głównego pliku wynikowego.
    enriched_columns = ["title", "year", "citations", "decade", "source_database", "raw_file", "query_group", "matched_topic_count", "draft_relevance_score"]
    optional_columns = [column for column in ["doi", "external_id", "source", "url", "authors", "topics", "abstract"] if column in df.columns]
    enriched_columns += optional_columns
    enriched_columns += list(TOPIC_KEYWORDS)

    # Każdy to_csv zapisuje jedną tabelę wynikową do data/processed/.
    df.loc[:, enriched_columns].to_csv(PROCESSED_DIR / "identity_overlay_enriched.csv", index=False)
    source_summary.to_csv(PROCESSED_DIR / "source_summary.csv", index=False)
    topic_summary.to_csv(PROCESSED_DIR / "topic_summary.csv", index=False)
    topic_year.to_csv(PROCESSED_DIR / "topic_year_counts.csv", index=False)
    cooccurrence.to_csv(PROCESSED_DIR / "topic_cooccurrence.csv")
    top_articles.to_csv(PROCESSED_DIR / "top_relevant_articles.csv", index=False)

    save_visuals(df, topic_year, cooccurrence)

    print("Exploratory analysis finished.")
    print(f"Rows analysed: {len(df)}")
    print(f"Processed tables: {PROCESSED_DIR}")
    print(f"Visuals: {VISUALS_DIR}")
    print("\nTopic summary:")
    print(topic_summary[["topic", "publications", "share_of_dataset", "first_year", "latest_year"]].to_string(index=False))
