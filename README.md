# Atölye Yerleşim Optimizasyonu (QAP) – Gurobi

###### Makine ve tezgâh yerleşimini Quadratic Assignment Problem yaklaşımıyla optimize eden bir uygulama.

###### Kullanıcıdan koordinatlar ve akış matrisi (spagetti diyagramı) alınır, sabit işaretlenen birimler yerinde tutulur, toplam taşıma maliyeti en aza indirilerek atamalar ve görsel plan üretilir.

###### En az bir pozisyonun (0,0) olması şartı kontrol edilir.

## 

## Özellikler



Koordinat girişi (sabit ve boş pozisyonlar)



5×5 veya NxN akış matrisi girişi



Sabit birim işaretleme



Metin çıktı: Birim → Pozisyon → Koordinat



Görsel çıktı: Yerleşim planı (matplotlib)



## Hızlı Başlangıç (Windows)



Bu depoyu indir.



run.bat’a çift tıkla.



İlk çalıştırmada otomatik olarak sanal ortam kurulur ve bağımlılıklar yüklenir.



Tarayıcıda http://localhost:8501 açılır.

### 

### İlk Çalıştırma Notu

Streamlit ilk açılışta Email isteyebilir. Boş bırakıp Enter yapılabilir.



### Gereksinimler

Python 3.8+



Gurobi



Windows (run.bat için)



### Manuel Kurulum (alternatif)



python -m venv .venv

.venv\\Scripts\\activate

pip install --upgrade pip

pip install -r requirements.txt

python -m streamlit run app.py



## Dosya Yapısı



app.py → Uygulama kodu



requirements.txt → Bağımlılıklar



run.bat → Tek tıkla çalıştırma betiği

## 

## Sık Karşılaşılan Sorunlar



PowerShell ExecutionPolicy engeli: Yönetici PowerShell →

Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned



Port dolu:

python -m streamlit run app.py --server.port 8502



Matplotlib hatası:

pip uninstall -y matplotlib \&\& pip cache purge \&\& pip install matplotlib --upgrade

