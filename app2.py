import pandas as pd
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import html
import time
from fastapi.middleware.cors import CORSMiddleware

from app.core import security
from app.db import models, schemas, crud
from app.db.database import engine, get_db
from app.services import ai_service, nlp_service, interaction_service

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="PharmAI API",
    description="Yapay Zeka Destekli İlaç Rehberi API'si",
    version="Final v2"
)

origins = ["http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def summarize_reviews_with_gemini(reviews_text: str, drug_name: str) -> str:
    prompt = f"""
Kullanıcılardan gelen aşağıdaki yorumlara dayanarak '{drug_name}' isimli ilaç hakkında kısa, net ve kullanıcı dostu bir özet oluştur:

- İlacın genel etkileri neler?
- Hangi rahatsızlıklar için kullanılmış?
- En sık karşılaşılan yan etkiler neler?
- Kullanıcılar memnun mu, değil mi?
- Kısa bir genel değerlendirme yap.

Yorumlar:
{reviews_text}

Çıktı formatı şöyle olmalı:
İlaç Adı: {drug_name}
Kullanım Alanı: [...]
Genel Etki: [...]
Yan Etkiler: [...]
Kullanıcı Memnuniyeti: [...]
Genel Değerlendirme: [...]
""".strip()
    try:
        result = ai_service.gemini_client.generate_text(prompt)  # Gemini client fonksiyonu
        return result.strip()
    except Exception as e:
        return f"Özetleme sırasında hata oluştu: {str(e)}"

# Global DataFrame
df_drugs = None

def _run_preprocessing():
    print("İşlenmiş veri bulunamadı. Veri işleniyor...")
    data_dir = Path(__file__).parent / "data"
    df_train = pd.read_csv(data_dir / "drugsComTrain_raw.tsv", sep='\t')
    df_test = pd.read_csv(data_dir / "drugsComTest_raw.tsv", sep='\t')
    df = pd.concat([df_train, df_test], ignore_index=True)
    df.rename(columns={"drugName": "drug_name", "usefulCount": "useful_count"}, inplace=True)
    df.dropna(subset=['drug_name', 'condition', 'review'], inplace=True)

    unique_raw_drugs = df['drug_name'].unique()
    valid_drugs = []
    for i, drug in enumerate(unique_raw_drugs):
        if interaction_service.get_rxcui(drug):
            valid_drugs.append(drug)
        time.sleep(0.1)

    df_filtered = df[df['drug_name'].isin(valid_drugs)].copy()
    review_counts = df_filtered['drug_name'].value_counts()
    drugs_with_enough_reviews = review_counts[review_counts >= 10].index.tolist()
    df_final = df_filtered[df_filtered['drug_name'].isin(drugs_with_enough_reviews)].copy()
    df_final['review'] = df_final['review'].apply(lambda x: html.unescape(str(x)))
    df_final['condition'] = df_final['condition'].apply(lambda x: html.unescape(str(x)))
    df_final.to_csv(data_dir / "processed_drug_data.tsv", sep='\t', index=False)
    return df_final

@app.on_event("startup")
def load_data():
    global df_drugs
    data_path = Path(__file__).parent / "data/processed_drug_data.tsv"
    if data_path.exists():
        df_drugs = pd.read_csv(data_path, sep='\t')
    else:
        df_drugs = _run_preprocessing()
    if 'uniqueID' not in df_drugs.columns:
        df_drugs.reset_index(drop=True, inplace=True)
        df_drugs['uniqueID'] = df_drugs.index

# Auth
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Geçersiz kimlik")
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise HTTPException(status_code=401, detail="Geçersiz token")
    user = crud.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı")
    return user

@app.get("/")
def root():
    return {"message": "PharmAI API'ye hoşgeldiniz!"}

@app.post("/token", response_model=schemas.Token)
def login(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Hatalı giriş")
    access_token = security.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Bu e-posta zaten kayıtlı")
    return crud.create_user(db, user)

@app.get("/users/me", response_model=schemas.User)
def read_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@app.get("/drugs")
def get_all_drugs():
    if df_drugs is None or df_drugs.empty:
        raise HTTPException(status_code=503, detail="Veri mevcut değil")
    return {"drugs": sorted(df_drugs['drug_name'].unique().tolist())}

@app.get("/drugs/{drug_name}/summary")
def get_drug_summary(drug_name: str, db: Session = Depends(get_db)):
    cached = crud.get_summary_from_cache(db, drug_name=drug_name)
    if cached:
        return {"drug_name": drug_name, "summary": cached.summary_text, "source": "cache"}

    if df_drugs is None or df_drugs.empty:
        raise HTTPException(status_code=503, detail="Veri yüklenemedi")

    drug_data = df_drugs[df_drugs['drug_name'].str.lower() == drug_name.lower()]
    if drug_data.empty:
        raise HTTPException(status_code=404, detail=f"'{drug_name}' bulunamadı")

    top_reviews = drug_data.sort_values(by='useful_count', ascending=False).head(5)
    if top_reviews.empty:
        raise HTTPException(status_code=404, detail="Yeterli yorum yok")

    reviews_text = "\n".join([f"- {str(r).strip()[:400]}" for r in top_reviews['review'].tolist()])

    try:
        summary = summarize_reviews_with_gemini(reviews_text, drug_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Özetleme hatası: {str(e)}")

    if not summary or "hata" in summary.lower():
        raise HTTPException(status_code=500, detail="Yapay zeka özeti başarısız")

    crud.add_summary_to_cache(db, drug_name=drug_name, summary_text=summary)
    return {"drug_name": drug_name, "summary": summary, "source": "ai_generated"}
