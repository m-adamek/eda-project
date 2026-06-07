from src.analysis.identity_overlay_eda import run_analysis


def main():
    # main.py jest najprostszym punktem startowym projektu.
    # Zamiast trzymać całą logikę tutaj, delegujemy pracę do modułu analitycznego.
    # Dzięki temu:
    # - kod pobierania danych jest w src/api/,
    # - kod analizy jest w src/analysis/,
    # - ten plik pozostaje krótką komendą "uruchom analizę".
    run_analysis()


if __name__ == "__main__":
    # Ten warunek oznacza: wykonaj main() tylko wtedy, gdy plik został uruchomiony
    # bezpośrednio, np. przez:
    #   python main.py
    # Jeśli ktoś importuje ten plik z innego modułu, main() nie uruchomi się sam.
    main()
