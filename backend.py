
import pandas as pd
import openai
import os

openai.api_key = os.getenv("OPENAI_API_KEY")
DATA_PATH = "data/drug_reviews.csv"

if os.path.exists(DATA_PATH):
    df = pd.read_csv(DATA_PATH)
else:
    df = pd.DataFrame(columns=["drugName", "review"])
    df.to_csv(DATA_PATH, index=False)

def get_reviews_for_drug(drug_name):
    return df[df['drugName'].str.lower() == drug_name.lower()]['review'].tolist()

def summarize_reviews_with_gpt(drug_name, reviews):
    if reviews:
        content = "\n\n".join(reviews[:10])
        prompt = f"Aşağıdaki kullanıcı yorumlarına göre '{drug_name}' adlı ilacın genel etkilerini, kullanım alanlarını ve dikkat edilmesi gerekenleri kısa ve anlaşılır bir şekilde özetle:\n\nYorumlar:\n{content}"
    else:
        prompt = f"'{drug_name}' adlı ilaç hakkında genel bilgi ver. Özellikle ne için kullanılır, yan etkileri nelerdir, hamilelikte kullanımı güvenli midir gibi konularda sade bir açıklama yap."

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Kullanıcıya tıbbi konularda bilgi veren, dikkatli ve sade konuşan bir asistansın."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.6,
        max_tokens=400
    )

    return response.choices[0].message["content"]

def save_new_drug(drug_name, gpt_generated_text):
    global df
    if drug_name.lower() in [d.lower() for d in df["drugName"].unique()]:
        return
    new_row = {"drugName": drug_name, "review": gpt_generated_text}
    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(DATA_PATH, index=False)
