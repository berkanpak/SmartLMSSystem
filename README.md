# SmartLMSSystem 🎓

Öğrenciler için geliştirilmiş, LMS (Learning Management System) entegreli akıllı asistan uygulaması. Bu sistem, ders materyallerini otomatik olarak çeker ve Google Gemini AI kullanarak içerik analizi, özetleme ve soru-cevap desteği sunar.

🤖 An AI-powered automation system for Blackboard LMS that automatically fetches course content, generates smart topic summaries, and creates custom practice quizzes using LLMs.

## 🚀 Özellikler

- **LMS Entegrasyonu:** Kullanıcı bilgileri ile dersleri ve materyalleri (PDF, PPTX) otomatik tarama.
- **Akıllı İçerik Analizi:** Ders notlarını ve slaytları Gemini AI ile analiz etme.
- **Otomatik Özetleme:** Uzun ders materyallerinden kritik noktaları çıkarma.
- **Soru-Cevap:** Materyal içeriğine dayalı spesifik sorulara yanıt üretme.
- **Çoklu Materyal Desteği:** Birden fazla dosyayı aynı anda analiz edebilme.

## 🛠️ Kurulum

1. Depoyu klonlayın:
   ```bash
   git clone https://github.com/berkanpak/SmartLMSSystem.git
   cd SmartLMSSystem
   ```

2. Gerekli kütüphaneleri yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

3. Uygulamayı başlatın:
   ```bash
   streamlit run app.py
   ```

## 🔑 Gereksinimler

- Python 3.8+
- [Google Gemini API Key](https://aistudio.google.com/app/apikey)
- LMS Kullanıcı Bilgileri

## 📄 Lisans

Bu proje MIT Lisansı ile lisanslanmıştır. Detaylar için [LICENSE](LICENSE) dosyasına göz atın.
