import streamlit as st
import pandas as pd
import requests

# --- إعدادات الصفحة ---
st.set_page_config(page_title="حسابات الديوانية", page_icon="💰", layout="wide")

# --- إعدادات الاتصال المباشر (REST API) ---
url = "https://zttkamtuccxgkugqzhwr.supabase.co/rest/v1/transactions"
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
        amount = st.number_input("المبلغ (ر.س)", min_value=0.0, step=1.0)
    with col3:
        desc = st.text_input("التفاصيل (البيان)")

    if st.button("حفظ العملية"):
        if amount > 0:
            data = {
                "transaction_type": t_type,
                "amount": amount,
                "description": desc
            }
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code in [200, 201]:
                st.success("تم تسجيل العملية بنجاح!")
                st.rerun() 
            else:
                st.error(f"حدث خطأ أثناء الحفظ: {response.text}")
        else:
            st.error("يرجى إدخال مبلغ أكبر من صفر.")

st.divider()

# --- القسم الثاني: جلب وعرض البيانات ---
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
    c1.metric("إجمالي الواردات", f"{total_income} ر.س")
    c2.metric("إجمالي المصاريف", f"{total_expense} ر.س", delta_color="inverse")
    c3.metric("الرصيد الحالي", f"{current_balance} ر.س")

    st.divider()

    # --- القسم الثالث: جدول العمليات الملون ---
    st.header("📑 آخر العمليات")
    
    # تصميم عناوين الجدول
    h1, h2, h3, h4, h5 = st.columns([2, 1.5, 1.5, 3, 1])
    h1.write("**التاريخ**")
    h2.write("**النوع**")
    h3.write("**المبلغ**")
    h4.write("**البيان**")
    h5.write("**إجراء**")
    
    st.markdown("---")
    
    # المرور على كل عملية وعرضها بالألوان
    for index, row in df.iterrows():
        c1, c2, c3, c4, c5 = st.columns([2, 1.5, 1.5, 3, 1])
        
        dt = pd.to_datetime(row['created_at']).strftime('%Y-%m-%d %H:%M')
        t_type_val = row['transaction_type']
        amt_val = row['amount']
        desc_val = row['description']
        
        # تحديد الألوان والعلامات بناءً على نوع العملية
        if t_type_val == "مصاريف":
            colored_type = f":red[🔻 {t_type_val}]"
            colored_amt = f":red[- {amt_val} ر.س]"
        elif t_type_val == "واردات":
            colored_type = f":green[🔼 {t_type_val}]"
            colored_amt = f":green[+ {amt_val} ر.س]"
        else: # رصيد افتتاحي
            colored_type = f":blue[💠 {t_type_val}]"
            colored_amt = f":blue[{amt_val} ر.س]"
        
        # طباعة البيانات في الأعمدة
        c1.write(dt)
        c2.markdown(colored_type)
        c3.markdown(colored_amt)
        c4.write(desc_val)
        
        # زر الحذف
        if c5.button("🗑️", key=f"del_{row['id']}", help="حذف هذه العملية"):
            delete_url = f"{url}?id=eq.{row['id']}"
            del_response = requests.delete(delete_url, headers=headers)
            
            if del_response.status_code in [200, 204]:
                st.rerun()
            else:
                st.error(f"فشل الحذف. سبب الرفض: {del_response.text}")
else:
    st.info("لا توجد عمليات مسجلة بعد. ابدأ بإضافة رصيد افتتاحي.")
