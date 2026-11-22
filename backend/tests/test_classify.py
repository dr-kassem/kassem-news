from app.ingestion import classify
from app.models import Sensitivity


def test_detect_region_lebanon():
    assert classify.detect_region("غارة على الضاحية الجنوبية في بيروت") == "lebanon"


def test_detect_region_middle_east():
    assert classify.detect_region("تصعيد عسكري على الحدود السورية") == "middle-east"


def test_detect_category_economy():
    assert classify.detect_category("البنك المركزي يرفع أسعار الفائدة والدولار يتراجع") == "economy"


def test_detect_category_cybersecurity():
    assert classify.detect_category("اختراق بيانات كبرى شركات التكنولوجيا وهجوم قرصنة واسع") == "cybersecurity"


def test_detect_country():
    assert classify.detect_country("مواجهات في رفح جنوب غزة") == "PS"


def test_detect_sensitivity():
    assert classify.detect_sensitivity("غارة إسرائيلية تسفر عن قتلى وجرحى") == Sensitivity.sensitive


def test_not_sensitive_for_routine_news():
    assert classify.detect_sensitivity("وزارة السياحة تعلن أرقام الزوار لهذا الموسم") == Sensitivity.normal


def test_is_breaking():
    assert classify.is_breaking("عاجل: انعقاد مجلس الأمن طارئا")
    assert not classify.is_breaking("تقرير اقتصادي ربع سنوي")


def test_routine_news_is_not_cybersecurity():
    # Regression: the word «إلى» used to collapse to the letter «ي» and match
    # almost every keyword, tagging unrelated news as cybersecurity. Such news
    # now falls back to the «world» catch-all instead.
    assert classify.detect_category(
        "لبنان يقرر استمرار تسيير رحلات طيران الشرق الأوسط إلى السعودية"
    ) == "world"
    assert classify.detect_category("فاركه بعد السقوط أمام آرسنال: أنا محبط!") == "world"
    assert classify.detect_category("الهند تفرض قيودا جديدة لدعم الروبية والحد من تراجعها") == "world"
    assert classify.detect_category(
        "طفرة أدوية إنقاص الوزن.. هل تغلق غرف العمليات إلى الأبد؟"
    ) == "world"


def test_is_breaking_does_not_match_internet():
    assert not classify.is_breaking("مستخدمون يشتكون من انقطاع الإنترنت")
    assert classify.is_breaking("الآن: إعلان نتائج الانتخابات")


def test_is_strike_positive():
    assert classify.is_strike("غارات إسرائيلية على جنوب لبنان")
    assert classify.is_strike("قصف مدفعي على أطراف البلدة")
    assert classify.is_strike("مسيّرة تستهدف موقعاً في الجنوب")
    assert classify.is_strike("صاروخ يسقط في محيط مطار الرياض")


def test_is_strike_negative():
    assert not classify.is_strike("لبنان يستأنف رحلات الطيران إلى السعودية")
    assert not classify.is_strike("وزارة الأشغال تقرر استمرار تسيير الرحلات")
    assert not classify.is_strike("الرئيس يجدد إدانة الاعتداءات على السعودية")
    assert not classify.is_strike("تقرير اقتصادي ربع سنوي")
