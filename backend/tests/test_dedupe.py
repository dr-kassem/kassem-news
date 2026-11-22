from app.ingestion.dedupe import is_duplicate, same_event, similarity


def test_identical_titles_are_duplicates():
    title = "البنك المركزي يرفع أسعار الفائدة"
    assert is_duplicate(title, title)
    assert similarity(title, title) >= 1.0


def test_near_duplicate():
    a = "البنك المركزي يرفع أسعار الفائدة اليوم في لبنان"
    b = "البنك المركزي اللبناني يرفع أسعار الفائدة اليوم"
    assert is_duplicate(a, b)


def test_distinct_titles_are_not_duplicates():
    assert not is_duplicate("انهيار سوق الأسهم في طوكيو", "مهرجان فني جديد يفتتح في القاهرة")


def test_same_event_threshold_lower_than_duplicate():
    a = "جلسة طارئة لمجلس الوزراء في بيروت بعد غارة على الضاحية"
    b = "غارة جديدة تستهدف الضاحية الجنوبية ومجلس الوزراء يعقد جلسة طارئة"
    assert same_event(a, b)
    assert not is_duplicate(a, b)