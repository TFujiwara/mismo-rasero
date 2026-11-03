from video.ingest import detectar_tipo, es_claim_verificable


def test_detectar_tipo_urls():
    assert detectar_tipo("https://www.youtube.com/watch?v=abc") == "YOUTUBE"
    assert detectar_tipo("https://youtu.be/abc") == "YOUTUBE"
    assert detectar_tipo("https://www.atresplayer.com/x") == "ATRESPLAYER"
    assert detectar_tipo("https://www.mitele.es/x") == "MITELE"
    assert detectar_tipo("https://www.rtve.es/play/x") == "RTVE"
    assert detectar_tipo("https://www.tiktok.com/@x/video/1") == "TIKTOK"
    assert detectar_tipo("https://algo.tdt/playlist.m3u8") == "HLS"


def test_es_claim_verificable():
    assert es_claim_verificable("El gobierno central ha subido el IBI un 20%")
    assert es_claim_verificable("El Ayuntamiento de Vila-real bajará el IRPF")
    assert es_claim_verificable("El ministro aprobará la ley el martes")
    assert not es_claim_verificable("Buenas tardes, pasamos ahora al tiempo.")


def test_reglas_duras_video():
    """El módulo nunca sirve vídeo: solo estados de texto (§12)."""
    import inspect

    from video import ingest

    src = inspect.getsource(ingest)
    assert "clip_desmentido" not in src
    assert "s3_path" not in src
