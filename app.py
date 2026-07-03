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
                st.error("حدث خطأ أثناء الحفظ.")
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

    # عرض البطاقات الإحصائية بالريال السعودي
    c1, c2, c3 = st.columns(3)
    c1.metric("إجمالي الواردات", f"{total_income} ر.س")
    c2.metric("إجمالي المصاريف", f"{total_expense} ر.س", delta_color="inverse")
    c3.metric("الرصيد الحالي", f"{current_balance} ر.س")

    st.divider()

    # --- القسم الثالث: جدول العمليات السابقة ---
    st.header("📑 آخر العمليات")
    
    # تجهيز نسخة من البيانات للعرض بشكل أنيق
    display_df = df[['id', 'created_at', 'transaction_type', 'amount', 'description']].copy()
    display_df['created_at'] = pd.to_datetime(display_df['created_at']).dt.strftime('%Y-%m-%d %H:%M')
    
    # تغيير أسماء الأعمدة للغة العربية
    display_df = display_df.rename(columns={
        'id': 'رقم العملية', 
        'created_at': 'التاريخ', 
        'transaction_type': 'النوع', 
        'amount': 'المبلغ (ر.س)', 
        'description': 'البيان'
    })
    
    # عرض الجدول باستخدام dataframe لإخفاء الفهرس (Index) وجعله أجمل
    st.dataframe(display_df, hide_index=True, use_container_width=True)

    st.divider()

    # --- القسم الرابع: حذف عملية ---
    st.header("🗑️ حذف عملية مسبقة")
    with st.expander("اضغط هنا لفتح خيارات الحذف", expanded=False):
        # تصميم دالة بسيطة لعرض تفاصيل العملية في القائمة المنسدلة بوضوح
        def format_transaction(trans_id):
            row = df[df['id'] == trans_id].iloc[0]
            return f"رقم {trans_id} | {row['transaction_type']} | {row['amount']} ر.س | {row['description']}"

        selected_id = st.selectbox(
            "اختر العملية التي تريد حذفها بشكل نهائي:",
            options=df['id'].tolist(),
            format_func=format_transaction
        )

        if st.button("حذف العملية المحددة", type="primary"):
            # إرسال طلب الحذف (DELETE) إلى Supabase بناءً على رقم الـ ID
            delete_url = f"{url}?id=eq.{selected_id}"
            del_response = requests.delete(delete_url, headers=headers)
            
            if del_response.status_code in [200, 204]:
                st.success("تم الحذف بنجاح! جاري تحديث الأرصدة...")
                st.rerun()
            else:
                st.error("حدث خطأ، لم يتم الحذف.")

else:
    st.info("لا توجد عمليات مسجلة بعد. ابدأ بإضافة رصيد افتتاحي.")
