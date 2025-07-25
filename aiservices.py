def summarize_reviews_with_gemini(reviews_text: str, drug_name: str) -> str:
    if not model:
        return "Yapay zeka servisi başlatılamadı."
    if not reviews_text.strip():
        return "Özetlenecek yorum bulunamadı."

    prompt = f"""
GÖREV: Aşağıda '{drug_name}' isimli ilaca ait kullanıcı yorumları bulunmaktadır. Bu yorumları dikkatlice inceleyip, aşağıdaki kurallara göre Türkçe, net, anlaşılır ve kullanıcı dostu bir özet çıkarınız.

KURALLAR:
- Lütfen, kesinlikle tıbbi tavsiye vermeyiniz.
- Yorumları objektif ve tarafsız bir şekilde özetleyiniz.
- Eğer yorumlar yeterli bilgi içermiyorsa veya konu dışıysa, "Bu konuda yeterli bilgi bulunamadı." ifadesini kullanınız.
- Özetiniz aşağıdaki formatta olmalıdır ve sadece bu başlıkları içermelidir. Başka hiçbir içerik eklemeyiniz.
- Cevabınız tamamen Türkçe olmalıdır.

İstenen Özet Formatı:
İlaç Adı: {drug_name}

1. Genel Değerlendirme:
2. Yaygın Olumlu Etkiler:
3. Yaygın Yan Etkiler:
4. Önemli Notlar:

Kullanıcı Yorumları:
{reviews_text}

Lütfen yukarıdaki formatta, başlıkları kullanarak özetinizi yazınız.
"""
    try:
        result = _safe_generate_content(prompt)
        return result.strip()
    except Exception as e:
        print(f"Gemini özetleme hatası (tüm denemelerden sonra): {e}")
        return "Yorumlar özetlenirken bir hata oluştu. Lütfen daha sonra tekrar deneyin."
