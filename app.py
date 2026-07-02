import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- إعدادات الصفحة ---
st.set_page_config(page_title="حسابات الديوانية", page_icon="💰", layout="wide")

# --- الاتصال بقاعدة البيانات (جلب المفاتيح من الإعدادات السرية) ---
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("💰 تطبيق حسابات الديوانية")

# --- القسم الأول: إضافة عملية جديدة ---
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
            response = supabase.table("transactions").insert(data).execute()
            st.success(f"تم تسجيل {t_type} بمبلغ {amount} بنجاح!")
            st.rerun() # لإعادة تحديث الحسابات فوراً
        else:
            st.error("يرجى إدخال مبلغ أكبر من صفر")

st.divider()

# --- القسم الثاني: جلب البيانات والحسابات ---
# جلب كل البيانات لحساب الرصيد (أو آخر 100 لعرضها)
response = supabase.table("transactions").select("*").order("created_at", desc=True).execute()
df = pd.DataFrame(response.data)

if not df.empty:
    # حساب الرصيد الحالي
    total_income = df[df['transaction_type'] == 'واردات']['amount'].sum()
    total_expense = df[df['transaction_type'] == 'مصاريف']['amount'].sum()
    initial_balance = df[df['transaction_type'] == 'رصيد افتتاحي']['amount'].sum()
    
    current_balance = (initial_balance + total_income) - total_expense

    # عرض البطاقات التعريفية للرصيد
    c1, c2, c3 = st.columns(3)
    c1.metric("إجمالي الواردات", f"{total_income} د.ع")
    c2.metric("إجمالي المصاريف", f"{total_expense} د.ع", delta_color="inverse")
    c3.metric("الرصيد الحالي", f"{current_balance} د.ع")

    st.divider()

    # --- القسم الثالث: عرض آخر 100 عملية ---
    st.header("📑 آخر 100 عملية")
    # نأخذ أول 100 سطر فقط
    recent_df = df.head(100)[['created_at', 'transaction_type', 'amount', 'description']]
    # تحسين شكل عرض التاريخ
    recent_df['created_at'] = pd.to_datetime(recent_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
    
    st.table(recent_df) # عرضها كجدول بسيط وواضح
else:
    st.info("لا توجد عمليات مسجلة بعد. ابدأ بإضافة رصيد افتتاحي.")
