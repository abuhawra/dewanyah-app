import streamlit as st
import pandas as pd
import requests

# --- إعدادات الصفحة ---
st.set_page_config(page_title="حسابات الديوانية", page_icon="💰", layout="wide")

# --- إعدادات الاتصال المباشر ---
# الرابط الصحيح الذي تم اختباره بنجاح
url = "https://zttkamtuccxgkugqzhwr.supabase.co/rest/v1/transactions"
# جلب المفتاح من إعدادات Streamlit السرية (التي قمت بإضافتها سابقاً)
key = st.secrets["SUPABASE_KEY"]

headers = {
    "apikey": key,
    "Authorization": f"Bearer {key}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}

st.title("💰 تطبيق حسابات الديوانية")

# --- القسم الأول: تسجيل عملية جديدة ---
st.header("➕ تسجيل عملية جديدة")
with st.container():
    col1, col2, col3 = st.columns(3)
    with col1:
        t_type = st.selectbox("نوع العملية", ["واردات", "مصاريف", "رصيد افتتاحي"])
    with col2:
        amount = st.number_input("المبلغ", min_value=0.0, step=1.0)
    with col3:
        desc = st.text_input("التفاصيل (البيان)")

    if st.button("حفظ العملية"):
        if amount > 0:
            data = {
                "transaction_type": t_type,
                "amount": amount,
                "description": desc
            }
            # إرسال البيانات إلى قاعدة البيانات
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code in [200, 201]:
                st.success("تم تسجيل العملية بنجاح!")
                st.rerun() # إعادة تحميل الصفحة لتحديث الأرصدة
            else:
                st.error("حدث خطأ أثناء الحفظ.")
        else:
            st.error("يرجى إدخال مبلغ أكبر من صفر.")

st.divider()

# --- القسم الثاني: عرض البيانات والحسابات ---
# جلب أحدث العمليات من قاعدة البيانات
get_response = requests.get(f"{url}?select=*&order=created_at.desc", headers=headers)

if get_response.status_code == 200 and len(get_response.json()) > 0:
    df = pd.DataFrame(get_response.json())
    
    # حساب الأرصدة
    total_income = df[df['transaction_type'] == 'واردات']['amount'].sum()
    total_expense = df[df['transaction_type'] == 'مصاريف']['amount'].sum()
    initial_balance = df[df['transaction_type'] == 'رصيد افتتاحي']['amount'].sum()
    
    current_balance = (initial_balance + total_income) - total_expense

    # عرض البطاقات الإحصائية
    c1, c2, c3 = st.columns(3)
    c1.metric("إجمالي الواردات", f"{total_income} د.ع")
    c2.metric("إجمالي المصاريف", f"{total_expense} د.ع", delta_color="inverse")
    c3.metric("الرصيد الحالي", f"{current_balance} د.ع")

    st.divider()

    # --- القسم الثالث: جدول العمليات السابقة ---
    st.header("📑 آخر العمليات")
    recent_df = df[['created_at', 'transaction_type', 'amount', 'description']].copy()
    # تحسين شكل عرض التاريخ ليكون مفهوماً
    recent_df['created_at'] = pd.to_datetime(recent_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
    
    # عرض الجدول
    st.table(recent_df)
else:
    st.info("لا توجد عمليات مسجلة بعد. ابدأ بإضافة رصيد افتتاحي.")
