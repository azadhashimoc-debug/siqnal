from radar.normalize import normalize_url, clean_html


def test_normalize_strips_tracking():
    assert normalize_url("https://a.az/x?utm_source=fb&id=5&fbclid=z") == "https://a.az/x?id=5"


def test_clean_html():
    assert clean_html("<p>Qiymət &amp; vergi</p>") == "Qiymət & vergi"
