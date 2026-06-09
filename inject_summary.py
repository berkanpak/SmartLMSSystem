import json
from pathlib import Path

sid = 'e97c3441-902c-44a5-b127-e1914be7b48d'
path = Path.home() / '.smart-lms' / 'sessions' / f'{sid}.json'
d = json.loads(path.read_text(encoding='utf-8'))

blocks = [
  {
    "type": "summary",
    "heading": "Türk Dili II - Ders Materyalleri Özeti",
    "sections": [
      {
        "title": "Sabahattin Ali ve Kuyucaklı Yusuf (Taner Timur & Berna Moran İncelemeleri)",
        "body": "Sabahattin Ali'nin başyapıtı 'Kuyucaklı Yusuf', Türk edebiyatında Anadolu kasaba hayatını ve sınıf çatışmalarını gerçekçi bir dille yansıtan öncü bir romandır. Yusuf karakteri, doğanın saflığını ve dürüstlüğünü temsil eden 'soylu vahşi' (noble savage) arketipi olarak incelenir. Roman, yozlaşmış kasaba eşrafı ile masum köylü arasındaki ahlaki ve ekonomik gerilimi merkezine alır."
      },
      {
        "title": "Erken Cumhuriyet Dönemi: 'Asri Hayat' ve Çocuk (Zafer Toprak)",
        "body": "Savaşlar sonrası kurulan Cumhuriyet, toplumu baştan inşa etme projesine 'yeni hayat' (asri hayat) vizyonuyla başlamıştır. Bu vizyonda en önemli aktörlerden biri çocuktur. İstanbul'daki gösterişli hayata (monden) karşılık Ankara, çağdaşlaşmayı sağlam temellere oturtmak için çocuk eğitimi, sağlığı ve modern pedagoji uygulamalarına büyük ağırlık vermiştir."
      },
      {
        "title": "Cumhuriyet ve 'Asri Aile' Kavramı (Zafer Toprak)",
        "body": "Osmanlı'nın son dönemlerindeki kültürel ikilemlerin aksine, Cumhuriyet dönemi Batılılaşmayı tam anlamıyla benimsemiş ve aile yapısını dönüştürmüştür. 'Asri aile', kadın-erkek eşitliğine inanan, modern eğitime önem veren, rasyonel ve laik değerlerle şekillenmiş yeni toplumun çekirdeği olarak tasarlanmıştır. Bu dönüşüm, medeni kanunun kabulü ile yasal güvence altına alınmıştır."
      }
    ]
  }
]

# Ekleme işlemini yap (eğer daha önce eklenmemişse)
if not any(t.get('text') == 'bu dosyaları bana özetle' for t in d['turns']):
    d['turns'].append({
        'role': 'user', 
        'text': 'bu dosyaları bana özetle', 
        'sources': ["Taner Timur - Kuyucaklı yusuf Dağa Neden Çıkılır.pdf", "Soylu vahşi olarak Kuyucaklı Yusuf.pdf", "Zafer Toprak - Asri Hayat ve Çocuk.pdf", "Zafer Toprak - Cumhuriyet ve Asri Aile.pdf"]
    })

d['turns'].append({
    'role': 'assistant', 
    'text': 'Dosyalarınızı okudum. İşte detaylı özetiniz:', 
    'sources': ["Taner Timur - Kuyucaklı yusuf Dağa Neden Çıkılır.pdf", "Soylu vahşi olarak Kuyucaklı Yusuf.pdf", "Zafer Toprak - Asri Hayat ve Çocuk.pdf", "Zafer Toprak - Cumhuriyet ve Asri Aile.pdf"], 
    'blocks': blocks
})

path.write_text(json.dumps(d, indent=2), encoding='utf-8')

# SSE tetiklemesi için response.json yaz
resp_payload = {"session_id": sid, "blocks": blocks}
Path("response.json").write_text(json.dumps(resp_payload), encoding="utf-8")
