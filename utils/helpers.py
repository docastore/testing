def extract_amount(data: str) -> float:
    """
    Converte 'recar_50' → 50.0
    """
    try:
        return float(data.split("_")[1])
    except:
        return 0.0
