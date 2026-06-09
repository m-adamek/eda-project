import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
VISUALS_DIR = PROJECT_ROOT / "visuals"

# Setup style
sns.set_theme(style="whitegrid", context="notebook")

# Colors
BLUE_DARK = "#3AA0D8"
BLUE_LIGHT = "#8CD8F8"
PINK_DARK = "#D87A8C"
PINK_LIGHT = "#F8B9C5"
GREY = "#8F9CA6"

# Load data
first_seen_path = PROCESSED_DIR / "product_feature_first_seen.csv"
topic_year_path = PROCESSED_DIR / "conference_topic_year_counts.csv"

# 1. Product Features First Seen Plot
if first_seen_path.exists():
    df_first = pd.read_csv(first_seen_path)
    
    plt.figure(figsize=(10, 5))
    # Map features to pretty labels and colors
    feature_labels = {
        "chosen_or_preferred_names": "Chosen/Preferred Names",
        "display_names": "Display Names",
        "identity_attributes": "Identity Attributes",
        "pronouns": "Pronouns"
    }
    df_first["feature_pretty"] = df_first["feature"].map(feature_labels)
    
    feature_colors = {
        "Chosen/Preferred Names": BLUE_DARK,
        "Display Names": BLUE_LIGHT,
        "Identity Attributes": GREY,
        "Pronouns": PINK_DARK
    }
    
    # Scatter plot for milestones
    sns.scatterplot(
        data=df_first,
        x="first_year",
        y="product",
        hue="feature_pretty",
        palette=feature_colors,
        s=300,
        style="feature_pretty",
        markers=["o", "s", "D", "^"],
        zorder=3
    )
    
    # #annotacje z latami
    # for idx, row in df_first.iterrows():
    #     plt.text(
    #         row["first_year"],
    #         row["product"],
    #         f" {row['first_year']}",
    #         va="center",
    #         ha="left",
    #         fontsize=10,
    #         fontweight="bold",
    #         color="#333333"
    #     )
        
    plt.title("Pierwsze odnotowane wdrożenie funkcji inkluzywnych w produktach", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Rok wdrożenia", fontsize=12)
    plt.ylabel("Produkt", fontsize=12)
    plt.xlim(2008, 2028)
    plt.xticks(range(2010, 2028, 2))
    plt.legend(title="Funkcja", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(VISUALS_DIR / "04_product_feature_milestones.png", dpi=180)
    plt.close()

# 2. Conference Topics Distribution Plot (Percentage Share)
if topic_year_path.exists():
    df_topics = pd.read_csv(topic_year_path)
    
    # Pivot to get a table of years x topics
    pivot_df = df_topics.pivot_table(
        index="year",
        columns="topic",
        values="sessions",
        aggfunc="sum"
    ).fillna(0)
    
    # Calculate percentage share
    pivot_pct = pivot_df.div(pivot_df.sum(axis=1), axis=0) * 100
    
    plt.figure(figsize=(12, 6))
    
    # Custom colors for topics (matching previous style or extended palette)
    topic_colors = {
        "identity_management": BLUE_DARK,
        "identity_representation": PINK_DARK,
        "access_governance": GREY,
        "hr_technology": BLUE_LIGHT,
        "ai_and_automation": "#5B6A8C",  # Slate blue
        "inclusion_and_diversity": PINK_LIGHT,
        "privacy_and_risk": "#DDA0DD"  # Plum/purple
    }
    
    # Rename columns for display
    topic_labels = {
        "identity_management": "Identity Management (IAM)",
        "identity_representation": "Identity Representation",
        "access_governance": "Access Governance / IGA",
        "hr_technology": "HR Technology",
        "ai_and_automation": "AI & Automation",
        "inclusion_and_diversity": "Inclusion & Diversity",
        "privacy_and_risk": "Privacy, Security & Risk"
    }
    
    colors = [topic_colors.get(col, "#cccccc") for col in pivot_df.columns]
    
    pivot_pct = pivot_pct.rename(columns=topic_labels)
    
    pivot_pct.plot(
        kind="bar",
        stacked=True,
        color=colors,
        ax=plt.gca(),
        width=0.6
    )
    
    plt.title("Udział tematów w agendach konferencji w latach 2021-2026", fontsize=14, fontweight="bold", pad=15)
    plt.xlabel("Rok konferencji", fontsize=12)
    plt.ylabel("Udział procentowy (%)", fontsize=12)
    plt.xticks(rotation=0)
    plt.ylim(0, 100)
    plt.legend(title="Tematyka", bbox_to_anchor=(1.02, 1), loc="upper left")
    plt.tight_layout()
    plt.savefig(VISUALS_DIR / "05_conference_topic_distribution.png", dpi=180)
    plt.close()

print("Scraping visuals generated successfully.")
