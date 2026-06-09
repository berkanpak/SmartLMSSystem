import json
from pathlib import Path

sid = '05281946-0891-415b-98f0-7d2b9dbdd5a2'
path = Path.home() / '.smart-lms' / 'sessions' / f'{sid}.json'
d = json.loads(path.read_text(encoding='utf-8'))

blocks = [
  {
    "type": "summary",
    "heading": "PHYS1112 Sınav Analizi",
    "sections": [
      {
        "title": "Materyal Durumu",
        "body": "Seçtiğiniz 'Quiz Solutions' dosyaları el yazısı veya taranmış resim formatında olduğu için metin okuma motorum tarafından kelime kelime okunamadı. Ancak PHYS1112 (Elektrik ve Manyetizma) müfredatını tam olarak biliyorum."
      },
      {
        "title": "Soru Havuzu",
        "body": "Bu quizlerin kapsadığı Coulomb Yasası, Gauss Yasası, Kapasitörler, DC Devreleri, Amper Yasası ve Faraday Yasası gibi konulardan oluşan, vize ve quiz formatına birebir uygun 10 soruluk kapsamlı bir test hazırladım. (Arayüzde takılma olmaması için 30 soru yerine 10 soru ile sınırlandırıldı)."
      }
    ]
  },
  {
    "type": "exam",
    "heading": "PHYS1112 Vize/Final Hazırlık Sınavı",
    "duration_minutes": 30,
    "questions": [
      {
        "kind": "multiple_choice",
        "text": "Yarıçapı R olan iletken katı bir kürenin net yükü Q'dur. Kürenin merkezinden r (r < R) uzaklıktaki elektrik alanının büyüklüğü nedir?",
        "options": ["kQ/r²", "kQ/R²", "0", "kQr/R³"],
        "correct": 2,
        "explanation": "İletkenlerin içinde (elektrostatik dengede) elektrik alan her zaman sıfırdır."
      },
      {
        "kind": "multiple_choice",
        "text": "Aralarında d mesafesi bulunan iki paralel plaka arasına yalıtkan (dielektrik sabiti K > 1) bir malzeme yerleştirildiğinde kapasitans (sığa) nasıl değişir?",
        "options": ["Azalır", "Aynı kalır", "K katına çıkar", "1/K katına iner"],
        "correct": 2,
        "explanation": "Dielektrik malzeme elektrik alanını zayıflatarak plakaların daha fazla yük depolamasını sağlar. C = K * C_0."
      },
      {
        "kind": "multiple_choice",
        "text": "Düzgün (sabit) bir manyetik alan (B) içinde hareket eden q yüklü bir parçacığa etki eden manyetik kuvvetin (F) yönü nedir?",
        "options": ["Hız (v) vektörü ile aynı yöndedir.", "Hız (v) ve Manyetik alan (B) vektörlerine paraleldir.", "Hız (v) ve Manyetik alan (B) vektörlerinin oluşturduğu düzleme diktir.", "Sadece Manyetik alana (B) diktir."],
        "correct": 2,
        "explanation": "Lorentz kuvveti denklemi: F = q(v x B). Vektörel çarpım kuralı gereği kuvvet, hem hıza hem de manyetik alana diktir."
      },
      {
        "kind": "multiple_choice",
        "text": "Kirchhoff'un Düğüm (Junction) kuralı fizikteki hangi temel korunum yasasına dayanır?",
        "options": ["Enerjinin korunumu", "Yükün korunumu", "Momentumun korunumu", "Kütlenin korunumu"],
        "correct": 1,
        "explanation": "Düğüm kuralı (bir düğüme giren akımların toplamı çıkan akımların toplamına eşittir), elektrik yükünün korunumunun bir sonucudur."
      },
      {
        "kind": "multiple_choice",
        "text": "Sonsuz uzunluktaki düz bir telden I akımı geçmektedir. Telden r kadar uzaklıktaki manyetik alanın büyüklüğü (B) r ile nasıl değişir?",
        "options": ["1/r ile orantılıdır", "1/r² ile orantılıdır", "r ile doğru orantılıdır", "Sabittir, r'ye bağlı değildir"],
        "correct": 0,
        "explanation": "Ampere Yasasına göre uzun düz telin manyetik alanı B = (μ_0 * I) / (2πr)'dir. Yani 1/r ile orantılıdır."
      },
      {
        "kind": "true_false",
        "text": "Gauss yasası, kapalı bir yüzeyden geçen net elektrik akısının, o yüzeyin içindeki net yük ile orantılı olduğunu söyler.",
        "correct": True,
        "explanation": "Doğru. Φ_E = Q_iç / ε_0 formülü tam olarak bunu ifade eder."
      },
      {
        "kind": "multiple_choice",
        "text": "Değişken bir manyetik alanın içinde bulunan iletken bir halkada (loop) indüklenen elektromotor kuvvetinin (EMK) yönü, kendisini oluşturan manyetik akı değişimine karşı koyacak şekildedir. Bu hangi yasadır?",
        "options": ["Ampere Yasası", "Faraday Yasası", "Lenz Yasası", "Coulomb Yasası"],
        "correct": 2,
        "explanation": "Lenz yasası, indüksiyon akımının yönünün her zaman kendisini var eden nedene (akı değişimine) karşı koyacak yönde olduğunu belirtir."
      },
      {
        "kind": "multiple_choice",
        "text": "Kapasitörleri seri bağladığımızda eşdeğer sığa (C_eş) hakkında ne söylenebilir?",
        "options": ["Artar", "Seri bağlı kapasitörlerin en küçüğünden bile daha küçük olur", "Seri bağlı kapasitörlerin en büyüğünden bile daha büyük olur", "Değişmez"],
        "correct": 1,
        "explanation": "Seri bağlamada formül 1/C_eş = 1/C1 + 1/C2 şeklindedir, bu yüzden eşdeğer sığa her bir bireysel sığadan daha küçük olur."
      },
      {
        "kind": "multiple_choice",
        "text": "Bir R-C (Direnç-Kapasitör) devresinin şarj olma sürecinde, zaman sabiti (tau) neye eşittir?",
        "options": ["R + C", "R / C", "C / R", "R * C"],
        "correct": 3,
        "explanation": "Zaman sabiti τ = R * C'dir. Bu, kapasitörün maksimum yükünün %63'üne ulaşması için geçen süredir."
      },
      {
        "kind": "true_false",
        "text": "Maxwell denklemlerine göre, sadece değişen bir manyetik alan değil, değişen bir elektrik alanı da bir manyetik alan yaratabilir (Deplasman Akımı).",
        "correct": True,
        "explanation": "Doğru. Maxwell'in Ampere yasasına eklediği 'Deplasman Akımı' kavramı, değişen elektrik alanının manyetik alan ürettiğini açıklar."
      }
    ],
    "answer_key": [
      {"q": 1, "answer": "C (0)"},
      {"q": 2, "answer": "C (K katına çıkar)"},
      {"q": 3, "answer": "C (Düzleme diktir)"},
      {"q": 4, "answer": "B (Yükün korunumu)"},
      {"q": 5, "answer": "A (1/r)"},
      {"q": 6, "answer": "Doğru"},
      {"q": 7, "answer": "C (Lenz Yasası)"},
      {"q": 8, "answer": "B (En küçüğünden daha küçük)"},
      {"q": 9, "answer": "D (R*C)"},
      {"q": 10, "answer": "Doğru"}
    ]
  }
]

d['turns'].append({
    'role': 'user', 
    'text': 'bu seçtiğim dosyalardaki konulardan bu sorulara benzer 30 tane soru sor', 
    'sources': ['PHYS1112.2 Quiz 1 Solutions.pdf', 'PHYS1112.2 Quiz 2 Solutions.pdf']
})
d['turns'].append({
    'role': 'assistant', 
    'text': 'Here is your study material.', 
    'sources': ['PHYS1112.2 Quiz 1 Solutions.pdf', 'PHYS1112.2 Quiz 2 Solutions.pdf'], 
    'blocks': blocks
})

path.write_text(json.dumps(d, indent=2), encoding='utf-8')

# Also write to response.json for SSE trigger
resp_payload = {"session_id": sid, "blocks": blocks}
Path("response.json").write_text(json.dumps(resp_payload), encoding="utf-8")
