import os
import json
import re
import pandas as pd
import streamlit as st
import requests
import html as html_lib
import streamlit.components.v1 as components
from datetime import datetime

st.set_page_config(
    page_title="LexAssist - AI Legal & Tax Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Constants ---
API_URL = os.getenv("API_URL", "http://localhost:8000")
PAGE_SIZE = 10
MAX_QUERY_CHARS = 2000
TIMEOUT_SHORT = 10
TIMEOUT_MEDIUM = 30
TIMEOUT_LONG = 120

# --- Multilingual Support Constants & Translation Dictionary ---
LANGUAGE_OPTIONS = {
    "English": "English",
    "हिन्दी": "Hindi",
    "ગુજરાતી": "Gujarati",
    "મરાઠી": "Marathi",
    "বাংলা": "Bengali",
    "தமிழ்": "Tamil",
    "తెలుగు": "Telugu",
    "ಕನ್ನಡ": "Kannada",
    "മലയാളം": "Malayalam",
    "ਪੰਜਾਬੀ": "Punjabi"
}

TRANSLATIONS = {
    "English": {
        "nav_home": "Home", "nav_legal": "Legal Question", "nav_tax": "Tax Assistant",
        "nav_general": "General Assistant", "nav_doc_exp": "Document Analysis",
        "nav_risk": "Risk Analyzer", "nav_compare": "Compare Contracts",
        "nav_draft": "Draft Document", "nav_case_law": "Case Law Search",
        "nav_section": "Section Lookup", "nav_timeline": "Legal Timeline",
        "nav_penalty": "Penalty Calculator", "nav_glossary": "Legal Glossary",
        "nav_history": "Query History", "nav_bookmarks": "Bookmarks",
        "nav_stats": "My Stats", "nav_admin": "Admin Analytics", "nav_profile": "Profile",
        "nav_about": "About", "language": "Language",
        "hero_title": "How can LexAssist help you today?",
        "hero_subtitle": "AI-powered legal assistance grounded in Indian legal documents.",
        "badge_legal_assistant": "⚖️ AI LEGAL ASSISTANT — Grounded in Indian Legal Documents",
        "try_asking": "TRY ASKING",
        "explore_lexassist": "Explore LexAssist",
        "sugg_1": "What are my rights as a tenant?",
        "sugg_2": "Explain Section 420 in simple terms",
        "sugg_3": "Can an employer terminate without notice?",
        "sugg_4": "What tax deductions can I claim?",
        "card_legal_title": "⚖️ Legal Assistant",
        "card_legal_desc": "Ask questions about Indian law.",
        "card_doc_title": "📄 Document Analysis",
        "card_doc_desc": "Upload and understand legal documents.",
        "card_risk_title": "⚠️ Contract Risk Analyzer",
        "card_risk_desc": "Identify potentially risky contract clauses.",
        "card_compare_title": "📊 Compare Contracts",
        "card_compare_desc": "Compare two legal documents side by side.",
        "card_caselaw_title": "🔍 Case Law Search",
        "card_caselaw_desc": "Find relevant Indian judgments and case law.",
        "card_tax_title": "💰 Tax Assistant",
        "card_tax_desc": "Get assistance with Indian tax-related questions.",
        "open_feature": "Open →",
        "trust_privacy": "🔒 Privacy-focused",
        "trust_rag": "⚡ RAG-powered",
        "trust_indian_law": "🇮🇳 Built for Indian Law",
        "disclaimer_text": "LexAssist provides AI-generated legal information for educational and informational purposes and does not replace advice from a qualified legal professional.",
        "ask_question": "Ask a Question",
        "ask_legal_q": "Ask a Legal Question",
        "ask_tax_q": "Ask a Tax Question",
        "ask_general_q": "Ask a General Question",
        "chat_placeholder": "Type your question here and press Enter...",
        "send": "Send", "clear_chat": "Clear Chat", "new_chat": "New Chat",
        "sources": "Sources & References", "suggested_questions": "Suggested follow-up questions",
        "ask_with_voice": "Ask with Voice",
        "rag_badge": "RAG-Enhanced answers from Indian legal documents",
        "upload_doc": "Upload Document", "explain_doc": "Explain Document",
        "search": "Search", "logout": "Logout"
    },
    "Hindi": {
        "nav_home": "होम", "nav_legal": "कानूनी प्रश्न पूछें", "nav_tax": "कर (टैक्स) सहायक",
        "nav_general": "सामान्य सहायक", "nav_doc_exp": "दस्तावेज़ विश्लेषण",
        "nav_risk": "अनुबंध जोखिम विश्लेषक", "nav_compare": "अनुबंध तुलना",
        "nav_draft": "दस्तावेज़ ड्राफ्ट", "nav_case_law": "केस लॉ खोज",
        "nav_section": "धारा (Section) खोज", "nav_timeline": "कानूनी समय-सीमा",
        "nav_penalty": "दंड कैलकुलेटर", "nav_glossary": "कानूनी शब्दावली",
        "nav_history": "प्रश्न इतिहास", "nav_bookmarks": "बुकमार्क",
        "nav_stats": "मेरे आँकड़े", "nav_admin": "एडमिन विश्लेषण", "nav_profile": "प्रोफ़ाइल",
        "nav_about": "हमारे बारे में", "language": "भाषा",
        "hero_title": "आज LexAssist आपकी कैसे सहायता कर सकता है?",
        "hero_subtitle": "भारतीय कानूनी दस्तावेज़ों पर आधारित AI-संचालित कानूनी सहायता।",
        "badge_legal_assistant": "⚖️ AI कानूनी सहायक — भारतीय कानूनी दस्तावेज़ों पर आधारित",
        "try_asking": "यह पूछकर देखें",
        "explore_lexassist": "LexAssist की सुविधाएँ देखें",
        "sugg_1": "एक किराएदार के रूप में मेरे क्या अधिकार हैं?",
        "sugg_2": "धारा 420 (Section 420) को सरल शब्दों में समझाइए",
        "sugg_3": "क्या नियोक्ता बिना नोटिस के नौकरी से निकाल सकता है?",
        "sugg_4": "मैं कौन सी टैक्स कटौती (Tax Deductions) का दावा कर सकता हूँ?",
        "card_legal_title": "⚖️ कानूनी सहायक",
        "card_legal_desc": "भारतीय कानून से संबंधित प्रश्न पूछें।",
        "card_doc_title": "📄 दस्तावेज़ विश्लेषण",
        "card_doc_desc": "कानूनी दस्तावेज़ अपलोड करें और समझें।",
        "card_risk_title": "⚠️ अनुबंध जोखिम विश्लेषक",
        "card_risk_desc": "अनुबंधों में संभावित जोखिम वाली शर्तों की पहचान करें।",
        "card_compare_title": "📊 अनुबंध तुलना",
        "card_compare_desc": "दो कानूनी दस्तावेज़ों की साथ-साथ तुलना करें।",
        "card_caselaw_title": "🔍 केस लॉ खोज",
        "card_caselaw_desc": "महत्वपूर्ण भारतीय अदालती फैसले खोजें।",
        "card_tax_title": "💰 कर सहायक",
        "card_tax_desc": "भारतीय कर से संबंधित प्रश्नों में सहायता पाएं।",
        "open_feature": "खोलें →",
        "trust_privacy": "🔒 गोपनीयता-केंद्रित",
        "trust_rag": "⚡ RAG-संचालित",
        "trust_indian_law": "🇮🇳 भारतीय कानून के लिए निर्मित",
        "disclaimer_text": "LexAssist शैक्षणिक और सूचनात्मक उद्देश्यों के लिए AI-जनरेटेड कानूनी जानकारी प्रदान करता है और यह किसी योग्य कानूनी पेशेवर की सलाह का विकल्प नहीं है।",
        "ask_question": "प्रश्न पूछें",
        "ask_legal_q": "कानूनी प्रश्न पूछें",
        "ask_tax_q": "कर (टैक्स) प्रश्न पूछें",
        "ask_general_q": "सामान्य प्रश्न पूछें",
        "chat_placeholder": "अपना प्रश्न यहाँ लिखें और एंटर दबाएँ...",
        "send": "भेजें", "clear_chat": "चैट साफ़ करें", "new_chat": "नई चैट",
        "sources": "स्रोत और संदर्भ", "suggested_questions": "सुझाए गए आगामी प्रश्न",
        "ask_with_voice": "आवाज़ से पूछें",
        "rag_badge": "भारतीय कानूनी दस्तावेज़ों से RAG-संवर्धित उत्तर",
        "upload_doc": "दस्तावेज़ अपलोड करें", "explain_doc": "दस्तावेज़ समझाइए",
        "search": "खोजें", "logout": "लॉगआउट"
    },
    "Gujarati": {
        "nav_home": "હોમ", "nav_legal": "કાનૂની પ્રશ્ન પૂછો", "nav_tax": "ટેક્સ સહાયક",
        "nav_general": "સામાન્ય સહાયક", "nav_doc_exp": "દસ્તાવેજ પૃથક્કરણ",
        "nav_risk": "કરાર જોખમ વિશ્લેષક", "nav_compare": "કરાર સરખામણી",
        "nav_draft": "દસ્તાવેજ ડ્રાફ્ટ", "nav_case_law": "કેસ લો શોધ",
        "nav_section": "કલમ (Section) શોધો", "nav_timeline": "કાનૂની ટાઇમલાઇન",
        "nav_penalty": "દંડ કેલ્ક્યુલેટર", "nav_glossary": "કાનૂની શબ્દકોશ",
        "nav_history": "પ્રશ્ન ઇતિહાસ", "nav_bookmarks": "બુકમાર્ક્સ",
        "nav_stats": "મારા આંકડા", "nav_admin": "એડમિન પૃથક્કરણ", "nav_profile": "પ્રોફાઇલ",
        "nav_about": "અમારા વિશે", "language": "ભાષા",
        "hero_title": "આજે LexAssist તમને કેવી રીતે મદદ કરી શકે?",
        "hero_subtitle": "ભારતીય કાનૂની દસ્તાવેજો પર આધારિત AI કાનૂની સહાયક.",
        "badge_legal_assistant": "⚖️ AI કાનૂની સહાયક — ભારતીય કાનૂની દસ્તાવેજો પર આધારિત",
        "try_asking": "આ પૂછી જુઓ",
        "explore_lexassist": "LexAssist ના ફીચર્સ જુઓ",
        "sugg_1": "ભાડૂઆત તરીકે મારા અધિકારો શું છે?",
        "sugg_2": "કલમ 420 (Section 420) સરળ શબ્દોમાં સમજાવો",
        "sugg_3": "શું નોકરીદાતા નોટિસ વિના નોકરીમાંથી કાઢી શકે?",
        "sugg_4": "હું કયા ટેક્સ કપાત (Tax Deductions) નો દાવો કરી શકું?",
        "card_legal_title": "⚖️ કાનૂની સહાયક",
        "card_legal_desc": "ભારતીય કાયદા વિશે પ્રશ્નો પૂછો.",
        "card_doc_title": "📄 દસ્તાવેજ પૃથક્કરણ",
        "card_doc_desc": "કાનૂની દસ્તાવેજો અપલોડ કરો અને સમજો.",
        "card_risk_title": "⚠️ કરાર જોખમ વિશ્લેષક",
        "card_risk_desc": "કરારોમાં જોખમી શરતો ઓળખો.",
        "card_compare_title": "📊 કરાર સરખામણી",
        "card_compare_desc": "બે દસ્તાવેજોની સાથે-સાથે સરખામણી કરો.",
        "card_caselaw_title": "🔍 કેસ લો શોધ",
        "card_caselaw_desc": "મહત્વપૂર્ણ ભારતીય કોર્ટના ચુકાદાઓ શોધો.",
        "card_tax_title": "💰 ટેક્સ સહાયક",
        "card_tax_desc": "ભારતીય ટેક્સ સંબંધિત પ્રશ્નોમાં મદદ મેળવો.",
        "open_feature": "ખોલો →",
        "trust_privacy": "🔒 ગોપનીયતા-કેન્દ્રિત",
        "trust_rag": "⚡ RAG-સંચાલિત",
        "trust_indian_law": "🇮🇳 ભારતીય કાયદા માટે નિર્મિત",
        "disclaimer_text": "LexAssist શૈક્ષણિક હેતુઓ માટે AI-જનરેટેડ કાનૂની માહિતી પૂરી પાડે છે અને તે કાનૂની સલાહનો વિકલ્પ નથી.",
        "ask_question": "પ્રશ્ન પૂછો",
        "ask_legal_q": "કાનૂની પ્રશ્ન પૂછો",
        "ask_tax_q": "ટેક્સ પ્રશ્ન પૂછો",
        "ask_general_q": "સામાન્ય પ્રશ્ન પૂછો",
        "chat_placeholder": "તમારો પ્રશ્ન અહીં લખો અને એન્ટર દબાવો...",
        "send": "મોકલો", "clear_chat": "ચેટ સાફ કરો", "new_chat": "નવી ચેટ",
        "sources": "સંદર્ભ અને સ્રોત", "suggested_questions": "સૂચવેલા આગામી પ્રશ્નો",
        "ask_with_voice": "અવાજથી પૂછો",
        "rag_badge": "ભારતીય કાનૂની દસ્તાવેજો પર આધારિત RAG ઉત્તરો",
        "upload_doc": "દસ્તાવેજ અપલોડ કરો", "explain_doc": "દસ્તાવેજ સમજાવો",
        "search": "શોધો", "logout": "લૉગઆઉટ"
    },
    "Marathi": {
        "nav_home": "मुख्यपृष्ठ", "nav_legal": "कायदेशीर प्रश्न विचारा", "nav_tax": "कर (टॅक्स) सहाय्यक",
        "nav_general": "सामान्य सहाय्यक", "nav_doc_exp": "कागदपत्र विश्लेषण",
        "nav_risk": "करारात धोका विश्लेषक", "nav_compare": "करार तुलना",
        "nav_draft": "कागदपत्र मसुदा", "nav_case_law": "केस लॉ शोध",
        "nav_section": "कलम (Section) शोध", "nav_timeline": "कायदेशीर वेळापत्रक",
        "nav_penalty": "दंड कॅल्क्युलेटर", "nav_glossary": "कायदेशीर शब्दकोश",
        "nav_history": "प्रश्न इतिहास", "nav_bookmarks": "बुकमार्क",
        "nav_stats": "माझी आकडेवारी", "nav_admin": "ॲडमिन विश्लेषण", "nav_profile": "प्रोफाइल",
        "nav_about": "आमच्याबद्दल", "language": "भाषा",
        "hero_title": "आज LexAssist तुम्हाला कशी मदत करू शकते?",
        "hero_subtitle": "भारतीय कायदेशीर कागदपत्रांवर आधारित AI कायदेशीर सहाय्यक.",
        "badge_legal_assistant": "⚖️ AI कायदेशीर सहाय्यक — भारतीय कायदेशीर कागदपत्रांवर आधारित",
        "try_asking": "हे विचारून पहा",
        "explore_lexassist": "LexAssist ची वैशिष्ट्ये पहा",
        "sugg_1": "भाडेकरू म्हणून माझे अधिकार काय आहेत?",
        "sugg_2": "कलम ४२० (Section 420) सोप्या शब्दांत समजावून सांगा",
        "sugg_3": "मालक नोटीस न देता नोकरीवरून काढू शकतो का?",
        "sugg_4": "मी कोणत्या कर सवलतींचा (Tax Deductions) दावा करू शकतो?",
        "card_legal_title": "⚖️ कायदेशीर सहाय्यक",
        "card_legal_desc": "भारतीय कायद्यांबद्दल प्रश्न विचारा.",
        "card_doc_title": "📄 कागदपत्र विश्लेषण",
        "card_doc_desc": "कायदेशीर कागदपत्रे अपलोड करा आणि समजून घ्या.",
        "card_risk_title": "⚠️ करारात धोका विश्लेषक",
        "card_risk_desc": "करारातील संभाव्य धोके ओळखा.",
        "card_compare_title": "📊 करार तुलना",
        "card_compare_desc": "दोन करारांची शेजारी-शेजारी तुलना करा.",
        "card_caselaw_title": "🔍 केस लॉ शोध",
        "card_caselaw_desc": "महत्त्वाचे भारतीय न्यायालयीन निकाल शोधा.",
        "card_tax_title": "💰 कर सहाय्यक",
        "card_tax_desc": "भारतीय करांशी संबंधित प्रश्नांमध्ये मदत मिळवा.",
        "open_feature": "उघडा →",
        "trust_privacy": "🔒 गोपनीयता-केंद्रित",
        "trust_rag": "⚡ RAG-आधारित",
        "trust_indian_law": "🇮🇳 भारतीय कायद्यासाठी बनवलेले",
        "disclaimer_text": "LexAssist केवळ माहिती आणि शैक्षणिक उद्देशांसाठी AI-जनरेट केलेली कायदेशीर माहिती प्रदान करते.",
        "ask_question": "प्रश्न विचारा",
        "ask_legal_q": "कायदेशीर प्रश्न विचारा",
        "ask_tax_q": "कर (टॅक्स) प्रश्न विचारा",
        "ask_general_q": "सामान्य प्रश्न विचारा",
        "chat_placeholder": "तुमचा प्रश्न येथे लिहा आणि एंटर दाबा...",
        "send": "पाठवा", "clear_chat": "चॅट साफ करा", "new_chat": "नवीन चॅट",
        "sources": "संदर्भ आणि स्त्रोत", "suggested_questions": "सुचवलेले पुढील प्रश्न",
        "ask_with_voice": "आवाजाने विचारा",
        "rag_badge": "भारतीय कायदेशीर कागदपत्रांवर आधारित RAG उत्तरे",
        "upload_doc": "कागदपत्र अपलोड करा", "explain_doc": "कागदपत्र स्पष्ट करा",
        "search": "शोधा", "logout": "लॉगआउट"
    },
    "Bengali": {
        "nav_home": "হোম", "nav_legal": "আইনি প্রশ্ন জিজ্ঞাসা করুন", "nav_tax": "ট্যাক্স সহায়ক",
        "nav_general": "সাধারণ সহায়ক", "nav_doc_exp": "নথি বিশ্লেষণ",
        "nav_risk": "চুক্তি ঝুঁকি বিশ্লেষক", "nav_compare": "চুক্তি তুলনা",
        "nav_draft": "নথি ড্রাফট", "nav_case_law": "কেস ল অনুসন্ধান",
        "nav_section": "ধারা (Section) সন্ধান", "nav_timeline": "আইনি সময়রেখা",
        "nav_penalty": "জরিমানা ক্যালকুলেটর", "nav_glossary": "আইনি শব্দকোষ",
        "nav_history": "প্রশ্ন ইতিহাস", "nav_bookmarks": "বুকমার্ক",
        "nav_stats": "আমার পরিসংখ্যান", "nav_admin": "এডমিন বিশ্লেষণ", "nav_profile": "প্রোফাইল",
        "nav_about": "আমাদের সম্পর্কে", "language": "ভাষা",
        "hero_title": "আজ LexAssist কীভাবে আপনাকে সাহায্য করতে পারে?",
        "hero_subtitle": "ভারতীয় আইনি নথির উপর ভিত্তি করে AI আইনি সহায়ক।",
        "badge_legal_assistant": "⚖️ AI আইনি সহায়ক — ভারতীয় আইনি নথির উপর ভিত্তি করে",
        "try_asking": "এগুলি জিজ্ঞাসা করে দেখুন",
        "explore_lexassist": "LexAssist এর বৈশিষ্ট্যগুলি দেখুন",
        "sugg_1": "ভাড়াটিয়া হিসেবে আমার অধিকারগুলি কী কী?",
        "sugg_2": "ধারা ৪২০ (Section 420) সহজ ভাষায় ব্যাখ্যা করুন",
        "sugg_3": "নিয়োগকর্তা কি নোটিশ ছাড়াই চাকরি থেকে বরখাস্ত করতে পারেন?",
        "sugg_4": "আমি কোন কোন ট্যাক্স ছাড়ের (Tax Deductions) দাবি করতে পারি?",
        "card_legal_title": "⚖️ আইনি সহায়ক",
        "card_legal_desc": "ভারতীয় আইন সম্পর্কে প্রশ্ন জিজ্ঞাসা করুন।",
        "card_doc_title": "📄 নথি বিশ্লেষণ",
        "card_doc_desc": "আইনি নথি আপলোড করুন এবং বুঝুন।",
        "card_risk_title": "⚠️ চুক্তি ঝুঁকি বিশ্লেষক",
        "card_risk_desc": "চুক্তিতে সম্ভাব্য ঝুঁকিপূর্ণ শর্তাবলী শনাক্ত করুন।",
        "card_compare_title": "📊 চুক্তি তুলনা",
        "card_compare_desc": "পাশাপাশি দুটি আইনি নথির তুলনা করুন।",
        "card_caselaw_title": "🔍 কেস ল অনুসন্ধান",
        "card_caselaw_desc": "গুরুত্বপূর্ণ ভারতীয় আদালতের রায় খুঁজুন।",
        "card_tax_title": "💰 ট্যাক্স সহায়ক",
        "card_tax_desc": "ভারতীয় ট্যাক্স সংক্রান্ত প্রশ্নে সাহায্য পান।",
        "open_feature": "খুলুন →",
        "trust_privacy": "🔒 গোপনীয়তা-কেন্দ্রিক",
        "trust_rag": "⚡ RAG-চালিত",
        "trust_indian_law": "🇮🇳 ভারতীয় আইনের জন্য তৈরি",
        "disclaimer_text": "LexAssist শুধুমাত্র তথ্যের জন্য AI-তৈরি আইনি তথ্য প্রদান করে।",
        "ask_question": "প্রশ্ন করুন",
        "ask_legal_q": "আইনি প্রশ্ন করুন",
        "ask_tax_q": "ট্যাক্স প্রশ্ন করুন",
        "ask_general_q": "সাধারণ প্রশ্ন করুন",
        "chat_placeholder": "আপনার প্রশ্নটি লিখুন এবং এন্টার চাপুন...",
        "send": "পাঠান", "clear_chat": "চ্যাট মুছে ফেলুন", "new_chat": "নতুন চ্যাট",
        "sources": "উৎস এবং রেফারেন্স", "suggested_questions": "প্রস্তাবিত পরবর্তী প্রশ্ন",
        "ask_with_voice": "ভয়েস দিয়ে জিজ্ঞাসা করুন",
        "rag_badge": "ভারতীয় আইনি নথি ভিত্তিক RAG উত্তর",
        "upload_doc": "নথি আপলোড করুন", "explain_doc": "নথি ব্যাখ্যা করুন",
        "search": "অনুসন্ধান", "logout": "লগআউট"
    },
    "Tamil": {
        "nav_home": "முகப்பு", "nav_legal": "சட்டக் கேள்வி கேட்கவும்", "nav_tax": "வரி உதவியாளர்",
        "nav_general": "பொது உதவியாளர்", "nav_doc_exp": "ஆவண பகுப்பாய்வு",
        "nav_risk": "ஒப்பந்த ஆபத்து பகுப்பாய்வி", "nav_compare": "ஒப்பந்த ஒப்பீடு",
        "nav_draft": "ஆவண வரைவு", "nav_case_law": "வழக்கு சட்டத் தேடல்",
        "nav_section": "பிரிவு (Section) தேடல்", "nav_timeline": "சட்ட காலவரிசை",
        "nav_penalty": "அபராதக் கணிப்பான்", "nav_glossary": "சட்டச் சொல்லகராதி",
        "nav_history": "கேள்வி வரலாறு", "nav_bookmarks": "புத்தகக்குறிகள்",
        "nav_stats": "என் புள்ளிவிவரங்கள்", "nav_admin": "நிர்வாகி பகுப்பாய்வு", "nav_profile": "சுயவிவரம்",
        "nav_about": "எங்களைப் பற்றி", "language": "மொழி",
        "hero_title": "LexAssist இன்று உங்களுக்கு எவ்வாறு உதவ முடியும்?",
        "hero_subtitle": "இந்திய சட்ட ஆவணங்களை அடிப்படையாகக் கொண்ட AI சட்ட உதவியாளர்.",
        "badge_legal_assistant": "⚖️ AI சட்ட உதவியாளர் — இந்திய சட்ட ஆவணங்களை அடிப்படையாகக் கொண்டது",
        "try_asking": "இவற்றைக் கேட்டுப் பாருங்கள்",
        "explore_lexassist": "LexAssist அம்சங்களை ஆராயுங்கள்",
        "sugg_1": "வாடகைதாரராக என் உரிமைகள் என்ன?",
        "sugg_2": "பிரிவு 420 (Section 420) எளிய சொற்களில் விளக்கவும்",
        "sugg_3": "அறிவிப்பு இன்றி வேலை வழங்குநர் பணிநீக்கம் செய்ய முடியுமா?",
        "sugg_4": "நான் என்ன வரி விலக்குகளைப் (Tax Deductions) பெற முடியும்?",
        "card_legal_title": "⚖️ சட்ட உதவியாளர்",
        "card_legal_desc": "இந்திய சட்டம் பற்றிய கேள்விகளைக் கேட்கவும்.",
        "card_doc_title": "📄 ஆவண பகுப்பாய்வு",
        "card_doc_desc": "சட்ட ஆவணங்களைப் பதிவேற்றிப் புரிந்துகொள்ளுங்கள்.",
        "card_risk_title": "⚠️ ஒப்பந்த ஆபத்து பகுப்பாய்வி",
        "card_risk_desc": "ஒப்பந்தங்களில் உள்ள ஆபத்தான விவாதங்களைக் கண்டறியவும்.",
        "card_compare_title": "📊 ஒப்பந்த ஒப்பீடு",
        "card_compare_desc": "இரண்டு ஆவணங்களை அருகருகே ஒப்பிட்டுப் பாருங்கள்.",
        "card_caselaw_title": "🔍 வழக்கு சட்டத் தேடல்",
        "card_caselaw_desc": "முக்கிய இந்திய நீதிமன்றத் தீர்ப்புகளைத் தேடுங்கள்.",
        "card_tax_title": "💰 வரி உதவியாளர்",
        "card_tax_desc": "இந்திய வரி தொடர்பான கேள்விகளுக்கு உதவி பெறுங்கள்.",
        "open_feature": "திறக்க →",
        "trust_privacy": "🔒 தனியுரிமை மையக் கட்டுப்பாடு",
        "trust_rag": "⚡ RAG-இயக்கப்படும்",
        "trust_indian_law": "🇮🇳 இந்திய சட்டத்திற்காக உருவாக்கப்பட்டது",
        "disclaimer_text": "LexAssist கல்வி மற்றும் தகவல் நோக்கங்களுக்காக மட்டுமே AI சட்டத் தகவலை வழங்குகிறது.",
        "ask_question": "கேள்வி கேட்கவும்",
        "ask_legal_q": "சட்டக் கேள்வி கேட்கவும்",
        "ask_tax_q": "வரிக் கேள்வி கேட்கவும்",
        "ask_general_q": "பொதுக் கேள்வி கேட்கவும்",
        "chat_placeholder": "உங்கள் கேள்வியை இங்கே தட்டச்சு செய்து என்டர் அழுத்தவும்...",
        "send": "அனுப்பு", "clear_chat": "அரட்டையை அழி", "new_chat": "புதிய அரட்டை",
        "sources": "ஆதாரங்கள் மற்றும் மேற்கோள்கள்", "suggested_questions": "பரிந்துரைக்கப்பட்ட அடுத்த கேள்விகள்",
        "ask_with_voice": "குரல் மூலம் கேட்கவும்",
        "rag_badge": "இந்திய சட்ட ஆவணங்கள் அடிப்படையிலான RAG பதில்கள்",
        "upload_doc": "ஆவணத்தைப் பதிவேற்றவும்", "explain_doc": "ஆவணத்தை விளக்குக",
        "search": "தேடு", "logout": "வெளியேறு"
    },
    "Telugu": {
        "nav_home": "హోమ్", "nav_legal": "చట్టపరమైన ప్రశ్న అడగండి", "nav_tax": "పన్ను (టాక్స్) సహాయకుడు",
        "nav_general": "సాధారణ సహాయకుడు", "nav_doc_exp": "పత్రం విశ్లేషణ",
        "nav_risk": "ఒప్పంద ప్రమాద విశ్లేషకుడు", "nav_compare": "ఒప్పందాల పోలిక",
        "nav_draft": "పత్రం డ్రాఫ్ట్", "nav_case_law": "కేసు లా శోధన",
        "nav_section": "సెక్షన్ శోధన", "nav_timeline": "చట్టపరమైన టైమ్‌లైన్",
        "nav_penalty": "పెనాల్టీ కాలిక్యులేటర్", "nav_glossary": "చట్టపరమైన పదకోశం",
        "nav_history": "ప్రశ్నల చరిత్ర", "nav_bookmarks": "బుక్‌మార్క్‌లు",
        "nav_stats": "నా గణాంకాలు", "nav_admin": "అడ్మిన్ విశ్లేషణ", "nav_profile": "ప్రొఫైల్",
        "nav_about": "మా గురించి", "language": "భాష",
        "hero_title": "LexAssist నేడు మీకు ఎలా సహాయపడుతుంది?",
        "hero_subtitle": "భారతీయ చట్టపరమైన పత్రాలపై ఆధారపడిన AI చట్ట సహాయకుడు.",
        "badge_legal_assistant": "⚖️ AI చట్ట సహాయకుడు — భారతీయ చట్టపరమైన పత్రాలపై ఆధారపడింది",
        "try_asking": "ఇవి అడిగి చూడండి",
        "explore_lexassist": "LexAssist ఫీచర్లను పరిశీలించండి",
        "sugg_1": "కిరాయిదారుగా నా హక్కులు ఏమిటి?",
        "sugg_2": "సెక్షన్ 420 (Section 420) సులభమైన మాటల్లో వివరించండి",
        "sugg_3": "యజమాని నోటీసు లేకుండా ఉద్యోగం నుండి తీసివేయవచ్చా?",
        "sugg_4": "నేను ఏ పన్ను మినహాయింపులను (Tax Deductions) క్లెయిమ్ చేయవచ్చు?",
        "card_legal_title": "⚖️ చట్ట సహాయకుడు",
        "card_legal_desc": "భారతీయ చట్టాల గురించి ప్రశ్నలు అడగండి.",
        "card_doc_title": "📄 పత్రం విశ్లేషణ",
        "card_doc_desc": "చట్టపరమైన పత్రాలను అప్‌లోడ్ చేసి అర్థం చేసుకోండి.",
        "card_risk_title": "⚠️ ఒప్పంద ప్రమాద విశ్లేషకుడు",
        "card_risk_desc": "ఒప్పందాలలో ఉన్న ప్రమాదకరమైన నిబంధనలను గుర్తించండి.",
        "card_compare_title": "📊 ఒప్పందాల పోలిక",
        "card_compare_desc": "రెండు పత్రాలను పక్కపక్కనే పోల్చి చూడండి.",
        "card_caselaw_title": "🔍 కేసు లా శోధన",
        "card_caselaw_desc": "ముఖ్యమైన భారతీయ కోర్టు తీర్పులను శోధించండి.",
        "card_tax_title": "💰 పన్ను సహాయకుడు",
        "card_tax_desc": "భారతీయ పన్ను సంబంధిత ప్రశ్నలకు సహాయం పొందండి.",
        "open_feature": "తెరువు →",
        "trust_privacy": "🔒 గోప్యత ఆధారితం",
        "trust_rag": "⚡ RAG ఆధారితం",
        "trust_indian_law": "🇮🇳 భారతీయ చట్టం కోసం నిర్మించబడింది",
        "disclaimer_text": "LexAssist విద్యా మరియు సమాచార ప్రయోజనాల కోసం మాత్రమే AI సమాచారాన్ని అందిస్తుంది.",
        "ask_question": "ప్రశ్న అడగండి",
        "ask_legal_q": "చట్టపరమైన ప్రశ్న అడగండి",
        "ask_tax_q": "పన్ను ప్రశ్న అడగండి",
        "ask_general_q": "సాధారణ ప్రశ్న అడగండి",
        "chat_placeholder": "మీ ప్రశ్నను ఇక్కడ టైప్ చేసి ఎంటర్ నొక్కండి...",
        "send": "పంపండి", "clear_chat": "చాట్ క్లియర్ చేయండి", "new_chat": "కొత్త చాట్",
        "sources": "మూలాలు మరియు సూచనలు", "suggested_questions": "సూచించబడిన తదుపరి ప్రశ్నలు",
        "ask_with_voice": "వాయిస్‌తో అడగండి",
        "rag_badge": "భారతీయ చట్ట పత్రాల ఆధారిత RAG సమాధానాలు",
        "upload_doc": "పత్రాన్ని అప్‌లోడ్ చేయండి", "explain_doc": "పత్రాన్ని వివరించండి",
        "search": "శోధించండి", "logout": "లాగ్‌అవుట్"
    },
    "Kannada": {
        "nav_home": "ಮುಖಪುಟ", "nav_legal": "ಕಾನೂನು ಪ್ರಶ್ನೆ ಕೇಳಿ", "nav_tax": "ತೆರಿಗೆ ಸಹಾಯಕ",
        "nav_general": "ಸಾಮಾನ್ಯ ಸಹಾಯಕ", "nav_doc_exp": "ದಾಖಲೆ ವಿಶ್ಲೇಷಣೆ",
        "nav_risk": "ಒಪ್ಪಂದ ಅಪಾಯ ವಿಶ್ಲೇಷಕ", "nav_compare": "ಒಪ್ಪಂದ ಹೋಲಿಕೆ",
        "nav_draft": "ದಾಖಲೆ ಕರಡು", "nav_case_law": "ಪ್ರಕರಣ ಕಾನೂನು ಹುಡುಕಾಟ",
        "nav_section": "ಸೆಕ್ಷನ್ ಹುಡುಕಾಟ", "nav_timeline": "ಕಾನೂನು ಕಾಲಾವಧಿ",
        "nav_penalty": "ದಂಡ ಲೆಕ್ಕಾಚಾರ", "nav_glossary": "ಕಾನೂನು ಪದಕೋಶ",
        "nav_history": "ಪ್ರಶ್ನೆ ಇತಿಹಾಸ", "nav_bookmarks": "ಬುಕ್‌ಮಾರ್ಕ್‌ಗಳು",
        "nav_stats": "ನನ್ನ ಅಂಕಿಅಂಶಗಳು", "nav_admin": "ಅಡ್ಮಿನ್ ವಿಶ್ಲೇಷಣೆ", "nav_profile": "ಪ್ರೊಫೈಲ್",
        "nav_about": "ನಮ್ಮ ಬಗ್ಗೆ", "language": "ಭಾಷೆ",
        "hero_title": "LexAssist ಇಂದು ನಿಮಗೆ ಹೇಗೆ ಸಹಾಯ ಮಾಡಬಹುದು?",
        "hero_subtitle": "ಭಾರತೀಯ ಕಾನೂನು ದಾಖಲೆಗಳನ್ನು ಆಧರಿಸಿದ AI ಕಾನೂನು ಸಹಾಯಕ.",
        "badge_legal_assistant": "⚖️ AI ಕಾನೂನು ಸಹಾಯಕ — ಭಾರತೀಯ ಕಾನೂನು ದಾಖಲೆಗಳ ಆಧಾರಿತ",
        "try_asking": "ಇದನ್ನು ಕೇಳಿ ನೋಡಿ",
        "explore_lexassist": "LexAssist ವೈಶಿಷ್ಟ್ಯಗಳನ್ನು ಅನ್ವೇಷಿಸಿ",
        "sugg_1": "ಬಾಡಿಗೆದಾರನಾಗಿ ನನ್ನ ಹಕ್ಕುಗಳು ಯಾವುವು?",
        "sugg_2": "ಸೆಕ್ಷನ್ 420 (Section 420) ಸರಳ ಪದಗಳಲ್ಲಿ ವಿವರಿಸಿ",
        "sugg_3": "ಮಾಲೀಕರು ನೋಟಿಸ್ ನೀಡದೆ ಕೆಲಸದಿಂದ ತೆಗೆದುಹಾಕಬಹುದೇ?",
        "sugg_4": "ನಾನು ಯಾವ ತೆರಿಗೆ ವಿನಾಯಿತಿಗಳನ್ನು (Tax Deductions) ಪಡೆಯಬಹುದು?",
        "card_legal_title": "⚖️ ಕಾನೂನು ಸಹಾಯಕ",
        "card_legal_desc": "ಭಾರತೀಯ ಕಾನೂನುಗಳ ಬಗ್ಗೆ ಪ್ರಶ್ನೆಗಳನ್ನು ಕೇಳಿ.",
        "card_doc_title": "📄 ದಾಖಲೆ ವಿಶ್ಲೇಷಣೆ",
        "card_doc_desc": "ಕಾನೂನು ದಾಖಲೆಗಳನ್ನು ಅಪ್‌ಲೋಡ್ ಮಾಡಿ ಮತ್ತು ಅರ್ಥಮಾಡಿಕೊಳ್ಳಿ.",
        "card_risk_title": "⚠️ ಒಪ್ಪಂದ ಅಪಾಯ ವಿಶ್ಲೇಷಕ",
        "card_risk_desc": "ಒಪ್ಪಂದಗಳಲ್ಲಿನ ಅಪಾಯಕಾರಿ ಷರತ್ತುಗಳನ್ನು ಗುರುತಿಸಿ.",
        "card_compare_title": "📊 ಒಪ್ಪಂದ ಹೋಲಿಕೆ",
        "card_compare_desc": "ಎರಡು ದಾಖಲೆಗಳನ್ನು ಅಕ್ಕಪಕ್ಕ ಹೋಲಿಸಿ ನೋಡಿ.",
        "card_caselaw_title": "🔍 ಪ್ರಕರಣ ಕಾನೂನು ಹುಡುಕಾಟ",
        "card_caselaw_desc": "ಪ್ರಮುಖ ಭಾರತೀಯ ನ್ಯಾಯಾಲಯದ ತೀರ್ಪುಗಳನ್ನು ಹುಡುಕಿ.",
        "card_tax_title": "💰 ತೆರಿಗೆ ಸಹಾಯಕ",
        "card_tax_desc": "ಭಾರತೀಯ ತೆರಿಗೆ ಸಂಬಂಧಿತ ಪ್ರಶ್ನೆಗಳಲ್ಲಿ ಸಹಾಯ ಪಡೆಯಿರಿ.",
        "open_feature": "ತೆರೆಯಿರಿ →",
        "trust_privacy": "🔒 ಗೌಪ್ಯತೆ-ಆಧಾರಿತ",
        "trust_rag": "⚡ RAG-ಚಾಲಿತ",
        "trust_indian_law": "🇮🇳 ಭಾರತೀಯ ಕಾನೂನಿಗಾಗಿ ನಿರ್ಮಿಸಲಾಗಿದೆ",
        "disclaimer_text": "LexAssist ಶೈಕ್ಷಣಿಕ ಮತ್ತು ಮಾಹಿತಿ ಉದ್ದೇಶಗಳಿಗಾಗಿ ಮಾತ್ರ AI ಕಾನೂನು ಮಾಹಿತಿಯನ್ನು ಒದಗಿಸುತ್ತದೆ.",
        "ask_question": "ಪ್ರಶ್ನೆ ಕೇಳಿ",
        "ask_legal_q": "ಕಾನೂನು ಪ್ರಶ್ನೆ ಕೇಳಿ",
        "ask_tax_q": "ತೆರಿಗೆ ಪ್ರಶ್ನೆ ಕೇಳಿ",
        "ask_general_q": "ಸಾಮಾನ್ಯ ಪ್ರಶ್ನೆ ಕೇಳಿ",
        "chat_placeholder": "ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಇಲ್ಲಿ ಟೈಪ್ ಮಾಡಿ ಮತ್ತು ಎಂಟರ್ ಒತ್ತಿರಿ...",
        "send": "ಕಳುಹಿಸಿ", "clear_chat": "ಚಾಟ್ ತೆರವುಗೊಳಿಸಿ", "new_chat": "ಹೊಸ ಚಾಟ್",
        "sources": "ಮೂಲಗಳು ಮತ್ತು ಉಲ್ಲೇಖಗಳು", "suggested_questions": "ಸೂಚಿಸಲಾದ ಮುಂದಿನ ಪ್ರಶ್ನೆಗಳು",
        "ask_with_voice": "ಧ್ವನಿಯ ಮೂಲಕ ಕೇಳಿ",
        "rag_badge": "ಭಾರತೀಯ ಕಾನೂನು ದಾಖಲೆಗಳ ಆಧಾರಿತ RAG ಉತ್ತರಗಳು",
        "upload_doc": "ದಾಖಲೆ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ", "explain_doc": "ದಾಖಲೆಯನ್ನು ವಿವರಿಸಿ",
        "search": "ಹುಡುಕಿ", "logout": "ಲಾಗ್‌ಔಟ್"
    },
    "Malayalam": {
        "nav_home": "ഹോം", "nav_legal": "നിയമപരമായ ചോദ്യം ചോദിക്കുക", "nav_tax": "ടാക്സ് അസിസ്റ്റന്റ്",
        "nav_general": "ജനറൽ അസിസ്റ്റന്റ്", "nav_doc_exp": "രേഖ വിശകലനം",
        "nav_risk": "കരാർ റിസ്ക് അനലൈസർ", "nav_compare": "കരാർ താരതമ്യം",
        "nav_draft": "രേഖ ഡ്രസാഫ്റ്റ്", "nav_case_law": "കേസ് ലാ തിരച്ചിൽ",
        "nav_section": "സെക്ഷൻ തിരച്ചിൽ", "nav_timeline": "നിയമപരമായ ടൈംലൈൻ",
        "nav_penalty": "പെനാൽറ്റി കാൽക്കുലേറ്റർ", "nav_glossary": "നിയമ നിഘണ്ടു",
        "nav_history": "ചോദ്യ ചരിത്രം", "nav_bookmarks": "ബുക്ക്മാർക്കുകൾ",
        "nav_stats": "എന്റെ കണക്കുകൾ", "nav_admin": "അഡ്മിൻ അനലിറ്റിക്സ്", "nav_profile": "പ്രൊഫൈൽ",
        "nav_about": "ഞങ്ങളെ കുറിച്ച്", "language": "ഭാഷ",
        "hero_title": "LexAssist ഇന്ന് നിങ്ങളെ എങ്ങനെ സഹായിക്കും?",
        "hero_subtitle": "ഇന്ത്യൻ നിയമ രേഖകളെ അടിസ്ഥാനമാക്കിയുള്ള AI നിയമ സഹായി.",
        "badge_legal_assistant": "⚖️ AI നിയമ സഹായി — ഇന്ത്യൻ നിയമ രേഖകളെ അടിസ്ഥാനമാക്കിയുള്ളത്",
        "try_asking": "ഇത് ചോദിച്ചു നോക്കൂ",
        "explore_lexassist": "LexAssist സവിശേഷതകൾ കാണുക",
        "sugg_1": "ഒരു വാടകക്കാരൻ എന്ന നിലയിൽ എന്റെ അവകാശങ്ങൾ എന്തൊക്കെയാണ്?",
        "sugg_2": "സെക്ഷൻ 420 (Section 420) ലളിതമായ വാക്കുകളിൽ വിശദീകരിക്കുക",
        "sugg_3": "നോട്ടീസ് ഇല്ലാതെ തൊഴിലുടമയ്ക്ക് പിരിച്ചുവിടാനാകുമോ?",
        "sugg_4": "എനിക്ക് ഏതൊക്കെ നികുതി ഇളവുകൾ (Tax Deductions) ക്ലെയിം ചെയ്യാം?",
        "card_legal_title": "⚖️ നിയമ സഹായി",
        "card_legal_desc": "ഇന്ത്യൻ നിയമത്തെക്കുറിച്ചുള്ള ചോദ്യങ്ങൾ ചോദിക്കുക.",
        "card_doc_title": "📄 രേഖ വിശകലനം",
        "card_doc_desc": "നിയമ രേഖകൾ അപ്‌ലോഡ് ചെയ്ത് മനസ്സിലാക്കുക.",
        "card_risk_title": "⚠️ കരാർ റിസ്ക് അനലൈസർ",
        "card_risk_desc": "കരാറുകളിലെ അപകടകരമായ വ്യവസ്ഥകൾ തിരിച്ചറിയുക.",
        "card_compare_title": "📊 കരാർ താരതമ്യം",
        "card_compare_desc": "രണ്ട് രേഖകൾ വശങ്ങളിലായി താരതമ്യം ചെയ്യുക.",
        "card_caselaw_title": "🔍 കേസ് ലാ തിരച്ചിൽ",
        "card_caselaw_desc": "പ്രധാനപ്പെട്ട ഇന്ത്യൻ കോടതി വിധികൾ തിരയുക.",
        "card_tax_title": "💰 ടാക്സ് അസിസ്റ്റന്റ്",
        "card_tax_desc": "ഇന്ത്യൻ നികുതി സംബന്ധിയായ ചോദ്യങ്ങളിൽ സഹായം നേടുക.",
        "open_feature": "തുറക്കുക →",
        "trust_privacy": "🔒 സ്വകാര്യത കേന്ദ്രീകൃതം",
        "trust_rag": "⚡ RAG അധിഷ്ഠിതം",
        "trust_indian_law": "🇮🇳 ഇന്ത്യൻ നിയമത്തിനായി നിർമ്മിച്ചത്",
        "disclaimer_text": "LexAssist വിവരങ്ങൾക്കും വിദ്യാഭ്യാസ ആവശ്യങ്ങൾക്കുമായി മാത്രം AI നിയമ വിവരങ്ങൾ നൽകുന്നു.",
        "ask_question": "ചോദ്യം ചോദിക്കുക",
        "ask_legal_q": "നിയമപരമായ ചോദ്യം ചോദിക്കുക",
        "ask_tax_q": "നികുതി ചോദ്യം ചോദിക്കുക",
        "ask_general_q": "പൊതു ചോദ്യം ചോദിക്കുക",
        "chat_placeholder": "നിങ്ങളുടെ ചോദ്യം ഇവിടെ ടൈപ്പ് ചെയ്ത് എന്റർ അമർത്തുക...",
        "send": "അയക്കുക", "clear_chat": "ചാറ്റ് ക്ലിയർ ചെയ്യുക", "new_chat": "പുതിയ ചാറ്റ്",
        "sources": "ഉറവിടങ്ങളും സൂചനകളും", "suggested_questions": "നിർദ്ദേശിച്ച അടുത്ത ചോദ്യങ്ങൾ",
        "ask_with_voice": "ശബ്ദം ഉപയോഗിച്ച് ചോദിക്കുക",
        "rag_badge": "ഇന്ത്യൻ നിയമ രേഖകൾ അധിഷ്ഠിതമായ RAG ഉത്തരങ്ങൾ",
        "upload_doc": "രേഖ അപ്‌ലോഡ് ചെയ്യുക", "explain_doc": "രേഖ വിശദീകരിക്കുക",
        "search": "തിരയുക", "logout": "ലോഗ് ഔട്ട്"
    },
    "Punjabi": {
        "nav_home": "ਹੋਮ", "nav_legal": "ਕਾਨੂੰਨੀ ਸਵਾਲ ਪੁੱਛੋ", "nav_tax": "ਟੈਕਸ ਸਹਾਇਕ",
        "nav_general": "ਆਮ ਸਹਾਇਕ", "nav_doc_exp": "ਦਸਤਾਵੇਜ਼ ਵਿਸ਼ਲੇਸ਼ਣ",
        "nav_risk": "ਕਰਾਰ ਜੋਖਮ ਵਿਸ਼ਲੇਸ਼ਕ", "nav_compare": "ਕਰਾਰ ਤੁਲਨਾ",
        "nav_draft": "ਦਸਤਾਵੇਜ਼ ਡਰਾਫਟ", "nav_case_law": "ਕੇਸ ਲਾਅ ਖੋਜ",
        "nav_section": "ਧਾਰਾ (Section) ਖੋਜ", "nav_timeline": "ਕਾਨੂੰਨੀ ਸਮਾਂ-ਸੀਮਾ",
        "nav_penalty": "ਜੁਰਮਾਨਾ ਕੈਲਕੁਲੇਟਰ", "nav_glossary": "ਕਾਨੂੰਨੀ ਸ਼ਬਦਾਵਲੀ",
        "nav_history": "ਸਵਾਲ ਇਤਿਹਾਸ", "nav_bookmarks": "ਬੁੱਕਮਾਰਕ",
        "nav_stats": "ਮੇਰੇ ਅੰਕੜੇ", "nav_admin": "ਐਡਮਿਨ ਵਿਸ਼ਲੇਸ਼ਣ", "nav_profile": "ਪ੍ਰੋਫਾਈਲ",
        "nav_about": "ਸਾਡੇ ਬਾਰੇ", "language": "ਭਾਸ਼ਾ",
        "hero_title": "LexAssist ਅੱਜ ਤੁਹਾਡੀ ਕਿਵੇਂ ਮਦਦ ਕਰ ਸਕਦਾ ਹੈ?",
        "hero_subtitle": "ਭਾਰਤੀ ਕਾਨੂੰਨੀ ਦਸਤਾਵੇਜ਼ਾਂ 'ਤੇ ਆਧਾਰਿਤ AI ਕਾਨੂੰਨੀ ਸਹਾਇਕ।",
        "badge_legal_assistant": "⚖️ AI ਕਾਨੂੰਨੀ ਸਹਾਇਕ — ਭਾਰਤੀ ਕਾਨੂੰਨੀ ਦਸਤਾਵੇਜ਼ਾਂ 'ਤੇ ਆਧਾਰਿਤ",
        "try_asking": "ਇਹ ਪੁੱਛ ਕੇ ਦੇਖੋ",
        "explore_lexassist": "LexAssist ਦੀਆਂ ਵਿਸ਼ੇਸ਼ਤਾਵਾਂ ਦੇਖੋ",
        "sugg_1": "ਇੱਕ ਕਿਰਾਏਦਾਰ ਵਜੋਂ ਮੇਰੇ ਕੀ ਅਧਿਕਾਰ ਹਨ?",
        "sugg_2": "ਧਾਰਾ 420 (Section 420) ਨੂੰ ਸਰਲ ਸ਼ਬਦਾਂ ਵਿੱਚ ਸਮਝਾਓ",
        "sugg_3": "ਕੀ ਮਾਲਕ ਬਿਨਾਂ ਨੋਟਿਸ ਦੇ ਨੌਕਰੀ ਤੋਂ ਕੱਢ ਸਕਦਾ ਹੈ?",
        "sugg_4": "ਮੈਂ ਕਿਹੜੀਆਂ ਟੈਕਸ ਕਟੌਤੀਆਂ (Tax Deductions) ਦਾ ਦਾਅਵਾ ਕਰ ਸਕਦਾ ਹਾਂ?",
        "card_legal_title": "⚖️ ਕਾਨੂੰਨੀ ਸਹਾਇਕ",
        "card_legal_desc": "ਭਾਰਤੀ ਕਾਨੂੰਨ ਬਾਰੇ ਸਵਾਲ ਪੁੱਛੋ।",
        "card_doc_title": "📄 ਦਸਤਾਵੇਜ਼ ਵਿਸ਼ਲੇਸ਼ਣ",
        "card_doc_desc": "ਕਾਨੂੰਨੀ ਦਸਤਾਵੇਜ਼ ਅਪਲੋਡ ਕਰੋ ਅਤੇ ਸਮਝੋ।",
        "card_risk_title": "⚠️ ਕਰਾਰ ਜੋਖਮ ਵਿਸ਼ਲੇਸ਼ਕ",
        "card_risk_desc": "ਕਰਾਰਾਂ ਵਿੱਚ ਸੰਭਾਵੀ ਜੋਖਮ ਵਾਲੀਆਂ ਸ਼ਰਤਾਂ ਦੀ ਪਛਾਣ ਕਰੋ।",
        "card_compare_title": "📊 ਕਰਾਰ ਤੁਲਨਾ",
        "card_compare_desc": "ਦੋ ਦਸਤਾਵੇਜ਼ਾਂ ਦੀ ਨਾਲ-ਨਾਲ ਤੁਲਨਾ ਕਰੋ।",
        "card_caselaw_title": "🔍 ਕੇਸ ਲਾਅ ਖੋਜ",
        "card_caselaw_desc": "ਮਹੱਤਵਪੂਰਨ ਭਾਰਤੀ ਅਦਾਲਤੀ ਫੈਸਲੇ ਖੋਜੋ।",
        "card_tax_title": "💰 ਟੈਕਸ ਸਹਾਇਕ",
        "card_tax_desc": "ਭਾਰਤੀ ਟੈਕਸ ਨਾਲ ਸੰਬੰਧਿਤ ਸਵਾਲਾਂ ਵਿੱਚ ਮਦਦ ਲਓ।",
        "open_feature": "ਖੋਲ੍ਹੋ →",
        "trust_privacy": "🔒 ਪ੍ਰਾਈਵੇਸੀ-ਕੇਂਦਰਿਤ",
        "trust_rag": "⚡ RAG-ਸੰਚਾਲਿਤ",
        "trust_indian_law": "🇮🇳 ਭਾਰਤੀ ਕਾਨੂੰਨ ਲਈ ਨਿਰਮਿਤ",
        "disclaimer_text": "LexAssist ਸਿਰਫ਼ ਜਾਣਕਾਰੀ ਅਤੇ ਵਿਦਿਅਕ ਉਦੇਸ਼ਾਂ ਲਈ AI ਕਾਨੂੰਨੀ ਜਾਣਕਾਰੀ ਪ੍ਰਦਾਨ ਕਰਦਾ ਹੈ।",
        "ask_question": "ਸਵਾਲ ਪੁੱਛੋ",
        "ask_legal_q": "ਕਾਨੂੰਨੀ ਸਵਾਲ ਪੁੱਛੋ",
        "ask_tax_q": "ਟੈਕਸ ਸਵਾਲ ਪੁੱਛੋ",
        "ask_general_q": "ਆਮ ਸਵਾਲ ਪੁੱਛੋ",
        "chat_placeholder": "ਆਪਣਾ ਸਵਾਲ ਇੱਥੇ ਲਿਖੋ ਅਤੇ ਐਂਟਰ ਦਬਾਓ...",
        "send": "ਭੇਜੋ", "clear_chat": "ਚੈਟ ਸਾਫ਼ ਕਰੋ", "new_chat": "ਨਵੀਂ ਚੈਟ",
        "sources": "ਸਰੋਤ ਅਤੇ ਹਵਾਲੇ", "suggested_questions": "ਸੁਝਾਏ ਗਏ ਅਗਲੇ ਸਵਾਲ",
        "ask_with_voice": "ਆਵਾਜ਼ ਨਾਲ ਪੁੱਛੋ",
        "rag_badge": "ਭਾਰਤੀ ਕਾਨੂੰਨੀ ਦਸਤਾਵੇਜ਼ਾਂ 'ਤੇ ਆਧਾਰਿਤ RAG ਉੱਤਰ",
        "upload_doc": "ਦਸਤਾਵੇਜ਼ ਅਪਲੋਡ ਕਰੋ", "explain_doc": "ਦਸਤਾਵੇਜ਼ ਸਮਝਾਓ",
        "search": "ਖੋਜੋ", "logout": "ਲੌਗਆਊਟ"
    }
}

def get_native_lang_name(lang_code: str) -> str:
    for native_name, code in LANGUAGE_OPTIONS.items():
        if code == lang_code:
            return native_name
    return "English"

def get_translation(key: str, default: str = None) -> str:
    lang = st.session_state.get("chat_language", "English")
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS["English"])
    return lang_dict.get(key, TRANSLATIONS["English"].get(key, default or key))

def get_lang_index(current_lang: str) -> int:
    for idx, (label, code) in enumerate(LANGUAGE_OPTIONS.items()):
        if code == current_lang:
            return idx
    return 0

# --- Session State Initialization ---
for key, default in {
    "query_history": [], "logged_in": False, "user_id": None,
    "username": None, "token": None,
    "legal_messages": [], "tax_messages": [], "general_messages": [],
    "legal_prefill": "", "tax_prefill": "", "general_prefill": "",
    "history_page": 0, "history_filter": "All", "history_search": "",
    "auth_alert": None, "dark_mode": True,
    "legal_draft": "", "tax_draft": "", "general_draft": "",
    "current_page": "Home",
    "profile_alert": None,
    "chat_language": "English",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

def auth_headers():
    return {"X-Auth-Token": st.session_state.token} if st.session_state.token else {}

def toast(msg: str, icon: str = "ℹ️"):
    st.toast(msg, icon=icon)

def clean_ai_response(text: str) -> str:
    if not text or not isinstance(text, str):
        return ""

    # 1. Strip internal reasoning tags (<think>...</think>)
    cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
    if not cleaned and text:
        cleaned = text.strip()

    # 2. Decode raw literal unicode escape sequences (\uXXXX)
    def _u_replace(m):
        try:
            return chr(int(m.group(1), 16))
        except Exception:
            return m.group(0)

    cleaned = re.sub(r'\\u([0-9a-fA-F]{4})', _u_replace, cleaned)

    # 3. Replace escaped characters
    cleaned = cleaned.replace('\\"', '"').replace("\\'", "'").replace('\\n', '\n').replace('\\t', '\t')

    # 4. Convert HTML <br>, <br/>, <br /> to newlines
    cleaned = re.sub(r'<br\s*/?>', '\n', cleaned, flags=re.IGNORECASE)

    # 5. Convert basic HTML formatting tags to Markdown
    cleaned = re.sub(r'</?(?:strong|b)\b[^>]*>', '**', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'</?(?:em|i)\b[^>]*>', '*', cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r'</?p\b[^>]*>', '\n\n', cleaned, flags=re.IGNORECASE)

    # 6. Remove remaining raw HTML tags
    cleaned = re.sub(r'<(?!http|https)[^>]+>', '', cleaned)

    # 7. Normalize multiple blank lines
    cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)

    return cleaned.strip()

# ── Theme CSS ──────────────────────────────────────────────────────────────
def _build_theme_css(dark: bool) -> str:
    css_file = os.path.join(os.path.dirname(__file__), "style.css")
    base_css = ""
    if os.path.exists(css_file):
        with open(css_file, "r", encoding="utf-8") as f:
            base_css = f.read()

    if dark:
        bg = "#0B0F1A"
        surface = "#121829"
        surface_hover = "#1A2238"
        border = "#232B45"
        primary = "#7C5CFF"
        text = "#E8EAF6"
        muted = "#8B93B0"
    else:
        bg = "#F8FAFC"
        surface = "#FFFFFF"
        surface_hover = "#F1F5F9"
        border = "#E2E8F0"
        primary = "#7C3AED"
        text = "#0F172A"
        muted = "#64748B"

    dynamic_override = f"""
    :root {{
        --bg: {bg};
        --surface: {surface};
        --surface-hover: {surface_hover};
        --border: {border};
        --primary: {primary};
        --text: {text};
        --muted: {muted};
    }}
    """
    return f"<style>\n{base_css}\n{dynamic_override}\n</style>"

# Inject custom CSS theme on every run
st.markdown(_build_theme_css(st.session_state.dark_mode), unsafe_allow_html=True)


def _char_counter_html(text: str) -> str:
    n = len(text)
    cls = "over" if n > MAX_QUERY_CHARS else "warn" if n > int(MAX_QUERY_CHARS * 0.85) else ""
    return f'<div class="char-counter {cls}">{n} / {MAX_QUERY_CHARS}</div>'

def _response_actions_bar(text: str, key: str):
    escaped_text = html_lib.escape(text, quote=True)
    json_text = json.dumps(text)
    components.html(
        f"""
        <style>
          * {{
            box-sizing: border-box !important;
            margin: 0;
            padding: 0;
          }}
          html, body {{
            margin: 0 !important;
            padding: 0 !important;
            background: transparent !important;
            overflow: hidden !important;
            font-family: 'Inter', system-ui, sans-serif;
            height: 100% !important;
            width: 100% !important;
          }}
          .actions-wrap {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 2px 0;
            height: 100%;
          }}
          .btn-icon {{
            background: transparent;
            color: #b4b4b4;
            border: none;
            padding: 3px 8px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.8rem;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            transition: all 0.15s ease;
            outline: none !important;
          }}
          .btn-icon:hover {{
            background: #2f2f2f;
            color: #ececec;
          }}
        </style>
        <div class="actions-wrap">
          <textarea id="cb_{key}" style="position:fixed; top:-1000px; left:-1000px; opacity:0; width:1px; height:1px; pointer-events:none;">{escaped_text}</textarea>
          <button class="btn-icon" title="Copy response" onclick="
              var t=document.getElementById('cb_{key}'); t.select(); t.setSelectionRange(0, 99999);
              navigator.clipboard.writeText(t.value).then(function(){{
                  this.innerText='✓ Copied'; var b=this;
                  setTimeout(function(){{ b.innerText='📋 Copy'; }}, 1500);
              }}.bind(this)).catch(function(){{
                  document.execCommand('copy');
                  this.innerText='✓ Copied'; var b=this;
                  setTimeout(function(){{ b.innerText='📋 Copy'; }}, 1500);
              }}.bind(this));">
              📋 Copy
          </button>
        </div>
        """,
        height=28,
    )

def _copy_button(text: str, key: str):
    _response_actions_bar(text, key)

def show_login_page():
    dark = st.session_state.dark_mode
    card_bg     = "#161b22" if dark else "#ffffff"
    card_bdr    = "#2e4a6a" if dark else "#dde6f0"
    card_shadow = "0 8px 32px rgba(0,0,0,0.45)" if dark else "0 4px 24px rgba(0,0,0,0.10)"
    feat_bg     = "#1e2a3a" if dark else "#f0f6ff"
    feat_bdr    = "#2e4a6a" if dark else "#cce0ff"
    feat_text   = "#e5e7eb" if dark else "#1a2a3a"
    feat_sub    = "#9ca3af" if dark else "#4a6080"
    page_bg     = "#0e1117" if dark else "#f0f4f8"

    st.markdown(f"""
    <style>
    .block-container {{
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
        max-width: 100% !important;
    }}
    .stApp, [data-testid="stAppViewContainer"], .main {{
        background: {page_bg} !important;
    }}
    .la-login-wrap {{
        background: {card_bg};
        border: 1px solid {card_bdr};
        border-radius: 18px;
        box-shadow: {card_shadow};
        padding: 2.2rem 2rem 1.8rem;
        margin-top: 0;
    }}
    .la-brand-icon {{ text-align: center; display: flex; justify-content: center; margin-bottom: 0.4rem; }}
    .la-brand-name {{
        text-align: center; font-size: 1.9rem; font-weight: 800;
        background: linear-gradient(90deg, #3b82f6, #60a5fa);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin-bottom: 0.1rem;
    }}
    .la-brand-sub {{
        text-align: center; color: {feat_sub}; font-size: 0.88rem; margin-bottom: 1.4rem;
    }}
    .la-feat-card {{
        background: {feat_bg}; border: 1px solid {feat_bdr};
        border-radius: 14px; padding: 1.1rem 1rem;
        text-align: center; height: 100%;
        transition: transform 0.15s;
    }}
    .la-feat-card:hover {{ transform: translateY(-3px); }}
    .la-feat-title {{ font-size: 0.95rem; font-weight: 700; color: {feat_text}; margin-bottom: 0.25rem; }}
    .la-feat-desc  {{ font-size: 0.8rem; color: {feat_sub}; line-height: 1.5; }}
    .la-trust {{
        text-align: center; color: {feat_sub}; font-size: 0.78rem;
        margin-top: 1rem; padding-top: 0.9rem;
        border-top: 1px solid {card_bdr};
    }}
    .la-trust span {{ margin: 0 0.5rem; }}
    </style>
    """, unsafe_allow_html=True)

    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown(
            '<div class="la-login-wrap">'
            '<div class="la-brand-icon">'
            '<svg width="38" height="38" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="M12 3L3 7l9 4 9-4-9-4z"/><path d="M3 12l9 4 9-4"/><path d="M3 17l9 4 9-4"/>'
            '</svg></div>'
            '<div class="la-brand-name">LexAssist</div>'
            '<div class="la-brand-sub">AI-powered legal &amp; tax assistant for Indian law</div>',
            unsafe_allow_html=True
        )

        tab1, tab2 = st.tabs(["Sign In", "Create Account"])

        with tab1:
            with st.form("login_form"):
                username = st.text_input("Username", placeholder="Enter your username")
                password = st.text_input("Password", type="password", placeholder="Enter your password")
                submit = st.form_submit_button("Sign In →", type="primary", use_container_width=True)

            if submit:
                if username.strip() and password.strip():
                    with st.spinner("Signing you in..."):
                        try:
                            response = requests.post(
                                f"{API_URL}/login",
                                json={"username": username.strip(), "password": password},
                                timeout=TIMEOUT_SHORT
                            )
                            if response.status_code == 200:
                                data = response.json()
                                st.session_state.logged_in = True
                                st.session_state.user_id = data["user_id"]
                                st.session_state.username = data["username"]
                                st.session_state.token = data["token"]
                                st.rerun()
                            elif response.status_code == 429:
                                st.session_state.auth_alert = ("error", "Too many login attempts. Please wait a minute and try again.")
                                st.rerun()
                            else:
                                st.session_state.auth_alert = ("error", "That username or password doesn't look right. Please try again.")
                                st.rerun()
                        except requests.exceptions.ConnectionError:
                            st.session_state.auth_alert = ("error", "Could not reach the server. Please try again shortly.")
                            st.rerun()
                else:
                    st.session_state.auth_alert = ("warning", "Please fill in both your username and password.")
                    st.rerun()

        with tab2:
            with st.form("register_form"):
                new_username = st.text_input("Choose a username", placeholder="Pick something you'll remember")
                new_password = st.text_input("Choose a password", type="password", placeholder="At least 6 characters")
                confirm_password = st.text_input("Confirm your password", type="password", placeholder="Type it again")
                submit_reg = st.form_submit_button("Create Account →", type="primary", use_container_width=True)

            if submit_reg:
                if new_username.strip() and new_password.strip() and confirm_password.strip():
                    if len(new_password) < 6:
                        st.session_state.auth_alert = ("error", "Password should be at least 6 characters long.")
                        st.rerun()
                    elif new_password != confirm_password:
                        st.session_state.auth_alert = ("error", "The passwords you entered don't match. Please try again.")
                        st.rerun()
                    else:
                        with st.spinner("Creating your account..."):
                            try:
                                response = requests.post(
                                    f"{API_URL}/register",
                                    json={"username": new_username.strip(), "password": new_password},
                                    timeout=TIMEOUT_SHORT
                                )
                                if response.status_code == 200:
                                    login_resp = requests.post(
                                        f"{API_URL}/login",
                                        json={"username": new_username.strip(), "password": new_password},
                                        timeout=TIMEOUT_SHORT
                                    )
                                    if login_resp.status_code == 200:
                                        data = login_resp.json()
                                        st.session_state.logged_in = True
                                        st.session_state.user_id = data["user_id"]
                                        st.session_state.username = data["username"]
                                        st.session_state.token = data["token"]
                                        st.rerun()
                                    else:
                                        st.session_state.auth_alert = ("success", "Account created! Head over to Sign In to get started.")
                                        st.rerun()
                                else:
                                    err_detail = "That username is already taken. Try a different one."
                                    try:
                                        res_json = response.json()
                                        if "detail" in res_json:
                                            d = res_json["detail"]
                                            if isinstance(d, list) and len(d) > 0 and "msg" in d[0]:
                                                err_detail = d[0]["msg"].replace("Value error, ", "")
                                            elif isinstance(d, str):
                                                err_detail = d
                                    except Exception:
                                        pass
                                    st.session_state.auth_alert = ("error", err_detail)
                                    st.rerun()
                            except requests.exceptions.ConnectionError:
                                st.session_state.auth_alert = ("error", "Could not reach the server. Please try again shortly.")
                                st.rerun()
                else:
                    st.session_state.auth_alert = ("warning", "Please fill in all three fields to create your account.")
                    st.rerun()

        st.markdown(
            '<div class="la-trust">'
            '<span>Secure</span><span>Indian Law</span><span>AI-Powered</span><span>Document Analysis</span>'
            '</div></div>',
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)
    _, c1, c2, c3, c4, _ = st.columns([0.5, 1, 1, 1, 1, 0.5])
    features = [
        (c1, "Legal Questions", "Ask anything about IPC, Constitution, or CrPC in plain language."),
        (c2, "Tax Guidance", "Understand Income Tax, GST, and deductions without the jargon."),
        (c3, "Document Analysis", "Upload any legal document and get a simple explanation."),
        (c4, "Contract Risks", "Detect risky clauses and missing terms in any contract."),
    ]
    for col, title, desc in features:
        with col:
            st.markdown(
                f'<div class="la-feat-card">'
                f'<div class="la-feat-title">{title}</div>'
                f'<div class="la-feat-desc">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

def show_chat_page(category: str, page_title: str):
    messages_key = f"{category}_messages"
    prefill_key = f"{category}_prefill"
    draft_key = f"{category}_draft"

    def _do_ask(query: str):
        st.session_state[messages_key].append({"role": "user", "content": query})
        with st.spinner("Generating answer..."):
            try:
                history_to_send = st.session_state[messages_key][:-1]
                resp = requests.post(
                    f"{API_URL}/ask",
                    json={"query": query, "category": category,
                          "history": [{"role": m["role"], "content": m["content"]} for m in history_to_send],
                          "language": st.session_state.chat_language},
                    headers=auth_headers(),
                    timeout=TIMEOUT_LONG
                )
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state[messages_key].append({
                        "role": "assistant",
                        "content": data["response"],
                        "suggestions": data.get("suggested_questions", []),
                        "sources": data.get("sources", []),
                    })
                    st.session_state.query_history.append({
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "query": query, "category": category
                    })
                    toast("Answer ready!", "✅")
                elif resp.status_code == 400:
                    toast("Invalid query — please rephrase.", "⚠️")
                    st.session_state[messages_key].append({"role": "assistant", "content": "Invalid query. Please rephrase your question."})
                elif resp.status_code == 401:
                    toast("Session expired — please log in again.", "🔑")
                    st.session_state[messages_key].append({"role": "assistant", "content": "Session expired. Please log in again."})
                else:
                    err_msg = resp.json().get("detail", "Error processing request") if resp.headers.get("content-type") == "application/json" else "Server error"
                    toast(f"Error: {err_msg}", "❌")
                    st.session_state[messages_key].append({"role": "assistant", "content": f"Error: {err_msg}"})
            except Exception as e:
                toast("Could not reach the server.", "❌")
                st.session_state[messages_key].append({"role": "assistant", "content": f"Could not reach server: {str(e)}"})

    # Auto-execute captured voice query if passed via query params or prefill
    vq_param = st.query_params.get("voice_query", "")
    if vq_param and vq_param.strip():
        try:
            del st.query_params["voice_query"]
        except Exception:
            pass
        _do_ask(vq_param.strip())
        st.rerun()

    prefill_query = st.session_state.get(prefill_key, "")
    if prefill_query:
        st.session_state[prefill_key] = ""
        _do_ask(prefill_query)
        st.rerun()

    st.markdown(f'<div class="main-header">{page_title}</div>', unsafe_allow_html=True)

    ctrl_col, lang_col = st.columns([3, 1])
    with lang_col:
        sel_label = st.selectbox(
            "🌐 Language",
            options=list(LANGUAGE_OPTIONS.keys()),
            index=get_lang_index(st.session_state.chat_language),
            key=f"{category}_lang_select"
        )
        new_lang = LANGUAGE_OPTIONS[sel_label]
        if new_lang != st.session_state.chat_language:
            st.session_state.chat_language = new_lang
            st.rerun()
    with ctrl_col:
        st.markdown('<div class="rag-badge">RAG-Enhanced answers from Indian legal documents</div>', unsafe_allow_html=True)

    components.html(
        f"""
        <style>
        @keyframes pulse-ring_{category} {{
          0% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }}
          70% {{ box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }}
          100% {{ box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }}
        }}
        .mic-active_{category} {{
          animation: pulse-ring_{category} 1.5s infinite !important;
          background: linear-gradient(135deg, #b91c1c, #ef4444) !important;
          border-color: #f87171 !important;
          color: #ffffff !important;
        }}
        </style>
        <div style="margin:4px 0; display:flex; align-items:center; gap:12px;">
          <button id="voiceBtn_{category}" onclick="toggleVoice_{category}()"
            style="background:linear-gradient(135deg, #1e293b, #0f172a); color:#60a5fa;
                   border:1px solid rgba(96,165,250,0.4); padding:8px 18px; border-radius:24px;
                   cursor:pointer; font-size:0.88rem; font-weight:600; font-family:sans-serif;
                   display:inline-flex; align-items:center; gap:8px; box-shadow:0 4px 14px rgba(0,0,0,0.3); transition:all 0.2s ease;">
            <span id="micIcon_{category}" style="font-size:1.1rem">🎙️</span>
            <span id="btnText_{category}">Ask with Voice</span>
          </button>
          <span id="voiceStatus_{category}" style="color:#9ca3af; font-size:0.82rem; font-family:sans-serif;"></span>
        </div>
        <script>
        var activeRec_{category} = null;

        function fixSpokenNumbers(text) {{
          if (!text) return text;
          var t = text.trim();
          t = t.replace(/\\b(section|sec|u\\/s|under section)\\s+(\\d+)\\s+([a-z])\\b/gi, function(m, p1, p2, p3) {{
            return 'Section ' + p2 + p3.toUpperCase();
          }});
          t = t.replace(/\\beighty\\s*c\\b/gi, '80C');
          t = t.replace(/\\b80\\s*c\\b/gi, '80C');
          t = t.replace(/\\b80\\s*d\\b/gi, '80D');
          t = t.replace(/\\bfour\\s*hundred\\s*twenty\\b/gi, '420');
          t = t.replace(/\\bfour\\s*twenty\\b/gi, '420');
          t = t.replace(/\\bthree\\s*hundred\\s*two\\b/gi, '302');
          t = t.replace(/\\bthree\\s*zero\\s*two\\b/gi, '302');
          t = t.replace(/\\bthree\\s*hundred\\s*seventy\\b/gi, '370');
          t = t.replace(/\\bthree\\s*seventy\\b/gi, '370');
          return t;
        }}

        function resetBtn_{category}() {{
          var btn = document.getElementById('voiceBtn_{category}');
          btn.classList.remove('mic-active_{category}');
          document.getElementById('micIcon_{category}').innerText = '🎙️';
          document.getElementById('btnText_{category}').innerText = 'Ask with Voice';
          activeRec_{category} = null;
        }}

        function toggleVoice_{category}() {{
          if (activeRec_{category}) {{
            document.getElementById('voiceStatus_{category}').innerText = 'Stopping & generating answer...';
            try {{ activeRec_{category}.stop(); }} catch(e) {{}}
          }} else {{
            startVoice_{category}();
          }}
        }}

        function startVoice_{category}() {{
          if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {{
            document.getElementById('voiceStatus_{category}').innerText = '⚠️ Speech recognition not supported in this browser.';
            return;
          }}
          var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
          var rec = new SR();
          rec.lang = 'en-IN';
          rec.continuous = false;
          rec.interimResults = false;
          rec.maxAlternatives = 3;
          activeRec_{category} = rec;
          
          var btn = document.getElementById('voiceBtn_{category}');
          btn.classList.add('mic-active_{category}');
          document.getElementById('micIcon_{category}').innerText = '🔴';
          document.getElementById('btnText_{category}').innerText = 'Listening...';
          document.getElementById('voiceStatus_{category}').innerText = 'Listening... Speak clearly, auto-stops on silence.';

          rec.onresult = function(e) {{
            var rawTranscript = e.results[0][0].transcript;
            var cleanTranscript = fixSpokenNumbers(rawTranscript);
            
            document.getElementById('micIcon_{category}').innerText = '⚡';
            document.getElementById('btnText_{category}').innerText = 'Answering...';
            document.getElementById('voiceStatus_{category}').innerHTML = '⚡ <b>Answering:</b> "' + cleanTranscript + '"';
            resetBtn_{category}();
            
            // Inject query directly into Streamlit chat input using React nativeSetter
            try {{
              var parentDoc = window.parent.document;
              var chatBox = parentDoc.querySelector('textarea[data-testid="stChatInputTextArea"]');
              var submitBtn = parentDoc.querySelector('button[data-testid="stChatInputSubmitButton"]');
              if (chatBox && submitBtn) {{
                var nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value").set;
                nativeSetter.call(chatBox, cleanTranscript);
                chatBox.dispatchEvent(new Event('input', {{ bubbles: true }}));
                setTimeout(function() {{
                  submitBtn.disabled = false;
                  submitBtn.removeAttribute('disabled');
                  submitBtn.click();
                }}, 150);
                return;
              }}
            }} catch(err) {{
              console.log('DOM injection error:', err);
            }}

            // Fallback for query param
            try {{
              var url = new URL(window.parent.location.href);
              url.searchParams.set('voice_query', cleanTranscript);
              window.parent.location.href = url.toString();
            }} catch(e) {{}}
          }};

          rec.onerror = function(e) {{
            document.getElementById('voiceStatus_{category}').innerText = 'Error: ' + e.error;
            resetBtn_{category}();
          }};

          rec.onend = function() {{
            if (document.getElementById('btnText_{category}').innerText === 'Listening...') {{
              document.getElementById('voiceStatus_{category}').innerText = 'Silence detected. Ready for next question.';
              resetBtn_{category}();
            }}
          }};

          rec.start();
        }}
        </script>
        """,
        height=65,
    )

    if not st.session_state[messages_key]:
        st.markdown(
            """
            <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding: 2.5rem 1rem 1rem; text-align:center;">
                <h2 style="font-family:'Outfit',sans-serif; font-size: 2.2rem; font-weight: 700; color: #ececec; margin-bottom: 1.2rem; letter-spacing:-0.02em;">
                    What legal or tax question can I help with today?
                </h2>
            </div>
            """,
            unsafe_allow_html=True
        )
        _, mid_col, _ = st.columns([1, 6, 1])
        with mid_col:
            with st.form(f"{category}_center_search_form"):
                mid_q = st.text_input(
                    f"Ask a {category} question...",
                    placeholder=f"Type your {category} question here and press Enter...",
                    label_visibility="collapsed",
                    key=f"{category}_center_q"
                )
                mid_sub = st.form_submit_button("🔍 Search / Ask Question", type="primary", use_container_width=True)
            if mid_sub and mid_q.strip():
                _do_ask(mid_q.strip())
                st.rerun()

        sc1, sc2, sc3 = st.columns(3)
        sample_chips = [
            (sc1, "Analyze contract risks", "Contract Risk Analyzer"),
            (sc2, "Summarize legal document", "Document Explanation"),
            (sc3, "Tax deduction rules", "Tax Assistant"),
        ]
        for col, label, page_target in sample_chips:
            with col:
                if st.button(f"💡 {label}", key=f"{category}_empty_chip_{label}", use_container_width=True):
                    if page_target != page_title:
                        st.session_state.current_page = page_target
                        st.session_state[f"{category}_prefill"] = label
                        st.rerun()
                    else:
                        _do_ask(label)
                        st.rerun()
    else:
        for idx, msg in enumerate(st.session_state[messages_key]):
            raw_c = msg.get("content", "")
            clean_c = clean_ai_response(raw_c) if msg["role"] == "assistant" else raw_c
            with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "⚖️"):
                if msg["role"] == "assistant":
                    st.markdown('<div style="font-size: 0.72rem; font-weight: 700; color: #8B5CF6; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.5rem;">ANSWER</div>', unsafe_allow_html=True)
                    st.markdown(clean_c)
                    if not clean_c.startswith("Error:") and not clean_c.startswith("Could not reach"):
                        _response_actions_bar(clean_c, key=f"{category}_resp_{idx}")
                    if msg.get("sources"):
                        with st.expander(f"📚 Sources & References ({len(msg['sources'])} items)", expanded=False):
                            for si, src in enumerate(msg["sources"], 1):
                                st.markdown(f"**{si}.** {src}")
                    if msg.get("suggestions"):
                        st.markdown('<div style="font-size: 0.78rem; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em; margin: 1rem 0 0.4rem;">Suggested follow-up questions</div>', unsafe_allow_html=True)
                        for i, s in enumerate(msg["suggestions"]):
                            if st.button(s, key=f"{category}_sugg_{idx}_{i}", use_container_width=True):
                                _do_ask(s)
                                st.rerun()
                else:
                    st.markdown(clean_c)

        last_draft = st.session_state.get(draft_key, "")
        if last_draft:
            st.markdown(_char_counter_html(last_draft), unsafe_allow_html=True)

        user_input = st.chat_input(f"Ask a {category} question... (max {MAX_QUERY_CHARS} chars)")
        if user_input:
            stripped = user_input.strip()
            if stripped:
                if len(stripped) > MAX_QUERY_CHARS:
                    st.session_state[draft_key] = stripped
                    toast(f"Query too long — max {MAX_QUERY_CHARS} characters.", "⚠️")
                    st.rerun()
                else:
                    st.session_state[draft_key] = stripped
                    _do_ask(stripped)
                    st.session_state[draft_key] = ""
            st.rerun()

def show_home_page():
    # Hero Section Container (Max width 900px)
    st.markdown(
        f"""
        <div class="hero-container">
            <h1 class="hero-title-main">
                LexAssist
            </h1>
            <div class="hero-badge-wrap">
                <div class="hero-badge">
                    {get_translation('badge_legal_assistant', '⚖️ AI LEGAL ASSISTANT — Grounded in Indian Legal Documents')}
                </div>
            </div>
            <h2 class="hero-headline">
                {get_translation('hero_title', 'How can LexAssist help you today?')}
            </h2>
            <p class="hero-subtitle">
                {get_translation('hero_subtitle', 'AI-powered legal assistance grounded in Indian legal documents.')}
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 1. Compact Centered Language Dropdown (Max width 280px, directly below subtitle)
    l_col1, l_col2, l_col3 = st.columns([1, 1.2, 1])
    with l_col2:
        st.markdown('<div class="lang-selector-container">', unsafe_allow_html=True)
        selected_lang_label = st.selectbox(
            f"🌐 {get_translation('language', 'Language')}",
            options=list(LANGUAGE_OPTIONS.keys()),
            index=get_lang_index(st.session_state.chat_language),
            key="home_page_lang_selector"
        )
        selected_lang_code = LANGUAGE_OPTIONS[selected_lang_label]
        if selected_lang_code != st.session_state.chat_language:
            st.session_state.chat_language = selected_lang_code
            toast(f"Language changed to {selected_lang_code}", "🌐")
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # 2. Suggestion Chips ("TRY ASKING")
    st.markdown(
        f'<div class="try-asking-header">'
        f'{get_translation("try_asking", "TRY ASKING")}'
        f'</div>',
        unsafe_allow_html=True
    )
    
    sc1, sc2, sc3, sc4 = st.columns(4)
    suggs = [
        (sc1, get_translation("sugg_1", "What are my rights as a tenant?"), "Ask Legal Question", "legal_prefill"),
        (sc2, get_translation("sugg_2", "Explain Section 420 in simple terms"), "Ask Legal Question", "legal_prefill"),
        (sc3, get_translation("sugg_3", "Can an employer terminate without notice?"), "Ask Legal Question", "legal_prefill"),
        (sc4, get_translation("sugg_4", "What tax deductions can I claim?"), "Tax Assistant", "tax_prefill"),
    ]
    for idx, (col, label, page_target, p_key) in enumerate(suggs):
        with col:
            st.markdown('<div class="try-ask-chip">', unsafe_allow_html=True)
            if st.button(label, key=f"try_ask_{idx}_{p_key}", use_container_width=True):
                st.session_state[p_key] = label
                st.session_state.current_page = page_target
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # 3. Explore LexAssist Feature Cards
    st.markdown(
        f'<div class="explore-header">'
        f'{get_translation("explore_lexassist", "Explore LexAssist")}'
        f'</div>',
        unsafe_allow_html=True
    )
    
    fc1, fc2, fc3 = st.columns(3)
    feat_cards_row1 = [
        (fc1, get_translation("card_legal_title", "⚖️ Legal Assistant"), get_translation("card_legal_desc", "Ask questions about Indian law."), "Ask Legal Question"),
        (fc2, get_translation("card_doc_title", "📄 Document Analysis"), get_translation("card_doc_desc", "Upload and understand legal documents."), "Document Explanation"),
        (fc3, get_translation("card_risk_title", "⚠️ Contract Risk Analyzer"), get_translation("card_risk_desc", "Identify potentially risky contract clauses."), "Contract Risk Analyzer"),
    ]
    for col, title, desc, page_target in feat_cards_row1:
        with col:
            st.markdown('<div class="explore-card-wrap">', unsafe_allow_html=True)
            card_label = f"**{title}**\n\n{desc}"
            if st.button(card_label, key=f"fc_{page_target}", use_container_width=True):
                st.session_state.current_page = page_target
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    fc4, fc5, fc6 = st.columns(3)
    feat_cards_row2 = [
        (fc4, get_translation("card_compare_title", "📊 Compare Contracts"), get_translation("card_compare_desc", "Compare two legal documents side by side."), "Compare Contracts"),
        (fc5, get_translation("card_caselaw_title", "🔍 Case Law Search"), get_translation("card_caselaw_desc", "Find relevant Indian judgments and case law."), "Case Law Search"),
        (fc6, get_translation("card_tax_title", "💰 Tax Assistant"), get_translation("card_tax_desc", "Get assistance with Indian tax-related questions."), "Tax Assistant"),
    ]
    for col, title, desc, page_target in feat_cards_row2:
        with col:
            st.markdown('<div class="explore-card-wrap">', unsafe_allow_html=True)
            card_label = f"**{title}**\n\n{desc}"
            if st.button(card_label, key=f"fc_{page_target}", use_container_width=True):
                st.session_state.current_page = page_target
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # Trust Indicators & Legal Disclaimer Footer
    st.markdown(
        f"""
        <div style="display:flex; justify-content:center; align-items:center; gap: 2rem; margin: 3rem 0 1.2rem; color: var(--muted); font-size: 0.85rem; font-weight: 500;">
            <span>{get_translation('trust_privacy', '🔒 Privacy-focused')}</span>
            <span>•</span>
            <span>{get_translation('trust_rag', '⚡ RAG-powered')}</span>
            <span>•</span>
            <span>{get_translation('trust_indian_law', '🇮🇳 Built for Indian Law')}</span>
        </div>
        <div style="background: rgba(18, 24, 41, 0.6); border: 1px solid var(--border); border-radius: 12px; padding: 0.9rem 1.2rem; text-align: center; font-size: 0.82rem; color: var(--muted);">
            {get_translation('disclaimer_text', 'LexAssist provides AI-generated legal information for educational and informational purposes and does not replace advice from a qualified legal professional.')}
        </div>
        """,
        unsafe_allow_html=True
    )

def show_contract_risk_analyzer():
    st.markdown('<div class="main-header">⚠️ Contract Risk Analyzer</div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="background:rgba(20,28,41,0.8);border:1px solid #263244;border-radius:14px;padding:1.2rem;margin-bottom:1.2rem;">
        <h4 style="margin:0 0 0.4rem 0;color:#8B5CF6">🛡️ Automated Legal Clause Risk Audit</h4>
        <p style="margin:0;font-size:0.88rem;color:#94A3B8">
            Upload any agreement, NDA, vendor contract, or lease (PDF, TXT, or DOCX). Our RAG engine scans the document under the <b>Indian Contract Act 1872</b> to detect risky clauses, hidden liabilities, missing terms, and generate actionable risk mitigation recommendations.
        </p>
    </div>
    """, unsafe_allow_html=True)

    uploaded_file = st.file_uploader("Choose a contract document", type=["pdf", "txt", "docx"], key="contract_upload")
    if uploaded_file:
        st.info(f"📄 **File Selected:** `{uploaded_file.name}` ({uploaded_file.size:,} bytes)")
        if st.button("🔍 Analyze Contract Risks", type="primary", use_container_width=True):
            with st.spinner("Analyzing contract clauses under Indian Contract Act..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(f"{API_URL}/analyze-contract", files=files, headers=auth_headers(), timeout=TIMEOUT_LONG)
                    if response.status_code == 200:
                        data = response.json()["analysis"]

                        score = data.get("risk_score", 0)
                        color = "🟢 Low Risk" if score <= 3 else "🟡 Moderate Risk" if score <= 6 else "🔴 High Risk"
                        
                        st.markdown(f"### Overall Risk Rating: **{color}** ({score}/10)")
                        st.markdown(f"**Summary:** {data.get('summary', '')}")
                        
                        st.markdown("---")
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown("### ⚠️ Risky Clauses Found")
                            for r in data.get("risky_clauses", []):
                                st.warning(f"**Clause {r.get('clause', '')}:** {r.get('risk', '')}\n\n*Recommendation:* {r.get('recommendation', '')}")
                        with c2:
                            st.markdown("### ❌ Missing Critical Terms")
                            for m in data.get("missing_clauses", []):
                                st.error(f"**Missing:** {m}")

                        recs = data.get("recommendations", [])
                        if recs:
                            st.markdown("---\n### ✅ Actionable Recommendations")
                            for rec in recs:
                                st.markdown(f"- 💡 {rec}")

                        st.markdown('<div class="disclaimer-box"><strong>Disclaimer:</strong> This contract analysis is AI-assisted and provided for informational review only. Always consult a licensed advocate before signing.</div>', unsafe_allow_html=True)
                        toast("Contract analysis complete!", "✅")
                    else:
                        toast("Could not analyze the contract. Please try again.", "❌")
                except Exception:
                    toast("Could not reach the server. Please try again shortly.", "❌")

def show_compare_contracts():
    st.markdown('<div class="main-header">📊 Compare Contracts</div>', unsafe_allow_html=True)
    st.write("Upload two contracts to compare them side by side — clauses, differences, and recommendations.")
    col1, col2 = st.columns(2)
    with col1:
        file1 = st.file_uploader("Contract 1", type=["pdf", "txt", "docx"], key="compare_file1")
    with col2:
        file2 = st.file_uploader("Contract 2", type=["pdf", "txt", "docx"], key="compare_file2")
    if file1 and file2:
        if st.button("Compare Contracts", type="primary"):
            with st.spinner("Comparing contracts..."):
                try:
                    files = {
                        "file1": (file1.name, file1.getvalue(), file1.type),
                        "file2": (file2.name, file2.getvalue(), file2.type),
                    }
                    resp = requests.post(f"{API_URL}/compare-contracts", files=files, headers=auth_headers(), timeout=TIMEOUT_LONG)
                    if resp.status_code == 200:
                        data = resp.json()["comparison"]
                        st.markdown(f"**Summary:** {data.get('summary', '')}")
                        st.markdown(f"**Recommendation:** {data.get('recommendation', '')}")
                        st.markdown("---")
                        d1, d2, d3 = st.columns(3)
                        with d1:
                            st.markdown("### 🔄 Common Clauses")
                            for c in data.get("common_clauses", []):
                                st.markdown(f"- {c}")
                        with d2:
                            st.markdown(f"### 📄 Only in {file1.name}")
                            for c in data.get("unique_to_contract1", []):
                                st.markdown(f"- {c}")
                        with d3:
                            st.markdown(f"### 📄 Only in {file2.name}")
                            for c in data.get("unique_to_contract2", []):
                                st.markdown(f"- {c}")
                        diffs = data.get("key_differences", [])
                        if diffs:
                            st.markdown("---\n### ⚠️ Key Differences")
                            diff_rows = [{"Aspect": d["aspect"], file1.name: d["contract1"], file2.name: d["contract2"]} for d in diffs]
                            st.table(diff_rows)
                        toast("Comparison complete!", "✅")
                    else:
                        toast("Could not compare contracts. Please try again.", "❌")
                except Exception:
                    toast("Could not reach the server.", "❌")
    elif file1 or file2:
        st.info("Please upload both contracts to compare.")

def show_case_law_search():
    st.markdown('<div class="main-header">🔍 Case Law Search</div>', unsafe_allow_html=True)
    st.write("Search relevant Supreme Court and High Court judgments on any Indian legal topic.")
    
    with st.form("case_law_form"):
        query = st.text_input("Enter your legal query", placeholder="e.g. right to privacy, bail conditions, dowry harassment")
        submitted = st.form_submit_button("Search Case Law", type="primary")

    if submitted:
        if not query.strip():
            toast("Please enter a legal query.", "⚠️")
        else:
            with st.spinner("Searching case law..."):
                try:
                    resp = requests.post(f"{API_URL}/case-law-search", json={"query": query.strip()}, headers=auth_headers(), timeout=TIMEOUT_LONG)
                    if resp.status_code == 200:
                        results = resp.json().get("results", [])
                        if results:
                            st.success(f"Found {len(results)} relevant cases")
                            for case in results:
                                court_badge = "🔵" if "Supreme" in case.get("court", "") else "🟢"
                                with st.expander(f"{court_badge} {case.get('case_name', 'Unknown')} ({case.get('year', '')})"):
                                    c1, c2 = st.columns(2)
                                    with c1:
                                        st.markdown(f"**Court:** {case.get('court', 'N/A')}")
                                        st.markdown(f"**Citation:** {case.get('citation', 'N/A')}")
                                    with c2:
                                        st.markdown(f"**Year:** {case.get('year', 'N/A')}")
                                    st.markdown(f"**Summary:** {case.get('summary', '')}")
                                    st.markdown(f"**Relevance:** {case.get('relevance', '')}")
                        else:
                            st.info("No cases found. Try a different query.")
                    else:
                        toast("Search failed. Please try again.", "❌")
                except Exception:
                    toast("Could not reach the server.", "❌")

def show_draft_document():
    st.markdown('<div class="main-header">📝 Draft Document</div>', unsafe_allow_html=True)
    st.write("Generate professional legal document drafts based on your details.")
    doc_type = st.selectbox("Document Type", [
        "Rent Agreement", "Non-Disclosure Agreement (NDA)", "Employment Offer Letter",
        "Legal Notice", "Affidavit", "Partnership Deed", "Sale Agreement",
        "Power of Attorney", "Cease and Desist Letter", "Demand Notice"
    ])
    st.markdown("#### Fill in the details")
    details = {}
    if doc_type == "Rent Agreement":
        c1, c2 = st.columns(2)
        with c1:
            details["Landlord Name"] = st.text_input("Landlord Name")
            details["Tenant Name"] = st.text_input("Tenant Name")
            details["Property Address"] = st.text_input("Property Address")
        with c2:
            details["Monthly Rent"] = st.text_input("Monthly Rent (₹)")
            details["Security Deposit"] = st.text_input("Security Deposit (₹)")
            details["Lease Duration"] = st.text_input("Lease Duration (months)")
        details["Start Date"] = st.text_input("Start Date")
    elif doc_type == "Non-Disclosure Agreement (NDA)":
        c1, c2 = st.columns(2)
        with c1:
            details["Disclosing Party"] = st.text_input("Disclosing Party")
            details["Receiving Party"] = st.text_input("Receiving Party")
        with c2:
            details["Purpose"] = st.text_input("Purpose of Disclosure")
            details["Duration"] = st.text_input("Confidentiality Duration")
    elif doc_type == "Legal Notice":
        c1, c2 = st.columns(2)
        with c1:
            details["Sender Name"] = st.text_input("Sender Name")
            details["Recipient Name"] = st.text_input("Recipient Name")
        with c2:
            details["Subject"] = st.text_input("Subject of Notice")
            details["Relief Sought"] = st.text_input("Relief Sought")
        details["Facts"] = st.text_area("Brief Facts", height=80)
    elif doc_type == "Affidavit":
        details["Deponent Name"] = st.text_input("Deponent Name")
        details["Purpose"] = st.text_input("Purpose of Affidavit")
        details["Facts"] = st.text_area("Facts to be stated", height=80)
        details["Place"] = st.text_input("Place")
    else:
        c1, c2 = st.columns(2)
        with c1:
            details["Party 1"] = st.text_input("Party 1 Name")
            details["Party 2"] = st.text_input("Party 2 Name")
        with c2:
            details["Date"] = st.text_input("Date")
            details["Jurisdiction"] = st.text_input("Jurisdiction/City")
        details["Additional Details"] = st.text_area("Additional Details", height=80)

    if st.button("Generate Draft", type="primary"):
        if not any(v.strip() for v in details.values() if isinstance(v, str)):
            toast("Please fill in at least some details.", "⚠️")
        else:
            with st.spinner("Drafting document..."):
                try:
                    resp = requests.post(f"{API_URL}/draft-document",
                        json={"doc_type": doc_type, "details": details},
                        headers=auth_headers(), timeout=TIMEOUT_LONG)
                    if resp.status_code == 200:
                        draft = resp.json().get("draft", "")
                        st.markdown("---")
                        st.markdown(f"### 📄 {doc_type} Draft")
                        st.text_area("Generated Draft", value=draft, height=400)
                        st.download_button("⬇ Download as TXT", data=draft,
                            file_name=f"{doc_type.replace(' ', '_')}_draft.txt",
                            mime="text/plain")
                        toast("Draft generated!", "✅")
                    else:
                        toast("Could not generate draft. Please try again.", "❌")
                except Exception:
                    toast("Could not reach the server.", "❌")

# --- Helper views for auxiliary modules ---
def show_section_lookup():
    st.markdown('<div class="main-header">📌 Section Lookup</div>', unsafe_allow_html=True)
    st.write("Search details regarding specific IPC sections, Income Tax sections, or Constitutional articles.")
    
    with st.form("section_lookup_form"):
        c1, c2 = st.columns([2, 1])
        with c1:
            act = st.text_input("Act Name", value="Indian Penal Code (IPC)", placeholder="e.g. Indian Penal Code, Income Tax Act, Constitution of India")
        with c2:
            section = st.text_input("Section / Article Number", placeholder="e.g. 302, 80C, 21")
        submitted = st.form_submit_button("Lookup Section", type="primary")

    if submitted:
        if not (act.strip() and section.strip()):
            toast("Please enter both Act Name and Section Number.", "⚠️")
        else:
            with st.spinner("Looking up section..."):
                try:
                    resp = requests.post(
                        f"{API_URL}/section-lookup",
                        json={"act": act.strip(), "section": section.strip()},
                        headers=auth_headers(),
                        timeout=TIMEOUT_MEDIUM
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        st.markdown(f"### 📜 {data.get('act', act)} — Section {data.get('section', section)}")
                        if data.get("title"):
                            st.markdown(f"#### {data.get('title')}")
                        if data.get("text"):
                            st.info(f"**Statutory Text:**\n{data.get('text')}")
                        if data.get("explanation"):
                            st.markdown(f"**Explanation:**\n{data.get('explanation')}")
                        if data.get("punishment"):
                            st.warning(f"**Punishment / Penalty:** {data.get('punishment')}")
                        if data.get("related_sections"):
                            st.markdown(f"**Related Sections:** {', '.join(data.get('related_sections'))}")
                        if data.get("landmark_cases"):
                            st.markdown(f"**Landmark Cases:** {', '.join(data.get('landmark_cases'))}")
                    else:
                        st.info("Section details not found or error looking up section.")
                except Exception:
                    toast("Could not reach the server.", "❌")

def show_legal_timeline():
    st.markdown('<div class="main-header">🗓️ Legal Timeline</div>', unsafe_allow_html=True)
    st.write("Generate a step-by-step legal procedure timeline for any legal scenario or case under Indian law.")
    
    with st.form("timeline_form"):
        situation = st.text_area("Describe your legal situation / procedure needed", placeholder="e.g. Filing a cheque bounce case under Section 138 of NI Act, or registering a private limited company", height=100)
        submitted = st.form_submit_button("Build Legal Timeline", type="primary")

    if submitted:
        if not situation.strip():
            toast("Please describe your legal situation.", "⚠️")
        else:
            with st.spinner("Generating legal process timeline..."):
                try:
                    resp = requests.post(
                        f"{API_URL}/legal-timeline",
                        json={"situation": situation.strip()},
                        headers=auth_headers(),
                        timeout=TIMEOUT_LONG
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        st.markdown(f"### 📍 {data.get('title', 'Legal Process Timeline')}")
                        if data.get("overview"):
                            st.markdown(f"**Overview:** {data.get('overview')}")
                        if data.get("total_estimated_time"):
                            st.info(f"⏱️ **Total Estimated Time:** {data.get('total_estimated_time')}")

                        steps = data.get("steps", [])
                        if steps:
                            st.markdown("### 📋 Procedure Steps")
                            
                            # Render visual Mermaid diagram
                            try:
                                mermaid_nodes = []
                                for idx, s in enumerate(steps):
                                    s_title = s.get("title", f"Step {idx+1}").replace('"', '')
                                    node_id = chr(65 + (idx % 26)) + (str(idx // 26) if idx >= 26 else "")
                                    mermaid_nodes.append((node_id, f"Step {idx+1}: {s_title}"))
                                
                                diagram_lines = ["graph TD"]
                                for i in range(len(mermaid_nodes)):
                                    nid, nlabel = mermaid_nodes[i]
                                    diagram_lines.append(f'    {nid}["{nlabel}"]')
                                    if i < len(mermaid_nodes) - 1:
                                        next_id, _ = mermaid_nodes[i+1]
                                        diagram_lines.append(f'    {nid} --> {next_id}')
                                
                                mermaid_code = "\n".join(diagram_lines)
                                components.html(
                                    f"""
                                    <script type="module">
                                      import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
                                      mermaid.initialize({{ startOnLoad: true, theme: 'dark' }});
                                    </script>
                                    <div class="mermaid" style="text-align:center">
                                    {mermaid_code}
                                    </div>
                                    """,
                                    height=200,
                                )
                            except Exception:
                                pass

                            for step in steps:
                                st_num = step.get("step", "")
                                st_title = step.get("title", "")
                                st_desc = step.get("description", "")
                                st_dur = step.get("duration", "")
                                st_docs = step.get("documents_needed", [])
                                with st.expander(f"Step {st_num}: {st_title} ({st_dur})", expanded=True):
                                    st.write(st_desc)
                                    if st_docs:
                                        st.markdown(f"📄 **Documents Needed:** {', '.join(st_docs)}")

                        notes = data.get("important_notes", [])
                        if notes:
                            st.markdown("---")
                            st.markdown("### ⚠️ Important Notes")
                            for note in notes:
                                st.markdown(f"- {note}")
                    else:
                        toast("Failed to generate legal timeline.", "❌")
                except Exception:
                    toast("Could not reach the server.", "❌")

def show_penalty_calculator():
    st.markdown('<div class="main-header">⚖️ Penalty Calculator</div>', unsafe_allow_html=True)
    st.write("Calculate tax late-filing interest or estimate legal penalties under IPC/BNS sections.")

    tab1, tab2 = st.tabs(["Criminal Penalties (IPC / BNS)", "Tax Interest & Late Fee"])

    with tab1:
        with st.form("penalty_calc_form"):
            c1, c2 = st.columns([1, 2])
            with c1:
                sec_num = st.text_input("IPC / BNS Section Number", placeholder="e.g. 302, 420, 379")
            with c2:
                circ = st.text_input("Specific Circumstances (Optional)", placeholder="e.g. first-time offence, attempt only")
            submitted = st.form_submit_button("Calculate / Estimate Penalty", type="primary")

        if submitted:
            if not sec_num.strip():
                toast("Please enter a Section Number.", "⚠️")
            else:
                with st.spinner("Estimating penalty..."):
                    try:
                        resp = requests.post(
                            f"{API_URL}/penalty-calculator",
                            json={"section": sec_num.strip(), "circumstances": circ.strip()},
                            headers=auth_headers(),
                            timeout=TIMEOUT_MEDIUM
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            st.markdown(f"### ⚖️ IPC/BNS Section {data.get('section', sec_num)}")
                            if data.get("offence"):
                                st.markdown(f"**Offence:** {data.get('offence')}")

                            b1, b2 = st.columns(2)
                            with b1:
                                bail = "🟢 Bailable" if data.get("is_bailable") else "🔴 Non-Bailable"
                                st.markdown(f"**Bail Status:** {bail}")
                            with b2:
                                cog = "🔴 Cognizable" if data.get("is_cognizable") else "🟢 Non-Cognizable"
                                st.markdown(f"**Cognizable Status:** {cog}")

                            st.markdown(f"**Minimum Punishment:** {data.get('minimum_punishment', 'N/A')}")
                            st.markdown(f"**Maximum Punishment:** {data.get('maximum_punishment', 'N/A')}")
                            if data.get("fine"):
                                st.markdown(f"**Fine:** {data.get('fine')}")
                            if data.get("estimated_sentence"):
                                st.info(f"**Estimated Sentence:** {data.get('estimated_sentence')}")

                            agg = data.get("aggravating_factors", [])
                            if agg:
                                st.markdown(f"**Aggravating Factors:** {', '.join(agg)}")
                            mit = data.get("mitigating_factors", [])
                            if mit:
                                st.markdown(f"**Mitigating Factors:** {', '.join(mit)}")
                            if data.get("disclaimer"):
                                st.caption(f"⚠️ {data.get('disclaimer')}")
                        else:
                            toast("Failed to estimate penalty.", "❌")
                    except Exception:
                        toast("Could not reach the server.", "❌")

    with tab2:
        with st.form("tax_penalty_form"):
            st.write("Calculate approximate interest and penalties under Income Tax / GST acts.")
            tax_type = st.selectbox("Category", ["Income Tax (Sec 234A/B/C)", "GST Late Filing", "General Late Interest"])
            amount = st.number_input("Tax Due Amount (₹)", min_value=0.0, value=10000.0)
            delay_months = st.number_input("Delay (Months)", min_value=1, value=3)
            tax_submitted = st.form_submit_button("Calculate Tax Penalty", type="primary")

        if tax_submitted:
            calc = (amount * 0.01) * delay_months
            st.success(f"Estimated Interest Penalty under {tax_type}: ₹{calc:,.2f}")

def show_legal_glossary():
    st.markdown('<div class="main-header">📖 Legal Glossary</div>', unsafe_allow_html=True)
    st.write("Search any legal term or legal maxim in Indian jurisprudence for an AI explanation.")

    with st.form("glossary_form"):
        term_input = st.text_input("Search Legal Term / Maxim", placeholder="e.g. Quo Warranto, Mens Rea, Suo Motu, Estoppel")
        submitted = st.form_submit_button("Define Term", type="primary")

    if submitted:
        if not term_input.strip():
            toast("Please enter a legal term.", "⚠️")
        else:
            with st.spinner("Looking up legal term..."):
                try:
                    resp = requests.post(
                        f"{API_URL}/glossary",
                        json={"term": term_input.strip()},
                        headers=auth_headers(),
                        timeout=TIMEOUT_MEDIUM
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        st.markdown(f"### 📖 {data.get('term', term_input)}")
                        if data.get("pronunciation"):
                            st.caption(f"🗣️ Pronunciation: {data.get('pronunciation')}")
                        if data.get("definition"):
                            st.markdown(f"**Plain Definition:** {data.get('definition')}")
                        if data.get("legal_definition"):
                            st.info(f"**Formal Legal Definition:** {data.get('legal_definition')}")
                        if data.get("origin"):
                            st.markdown(f"**Origin:** {data.get('origin')}")
                        if data.get("example"):
                            st.markdown(f"**Example Usage:** {data.get('example')}")
                        if data.get("used_in"):
                            st.markdown(f"**Used in:** {', '.join(data.get('used_in'))}")
                        if data.get("related_terms"):
                            st.markdown(f"**Related Terms:** {', '.join(data.get('related_terms'))}")
                    else:
                        toast("Could not define term.", "❌")
                except Exception:
                    toast("Could not reach the server.", "❌")

    st.markdown("---")
    st.markdown("### 📚 Popular Legal Maxims & Terms")
    st.markdown("""
    - **Amicus Curiae**: Friend of the court; a neutral legal advisor.
    - **Bail**: Temporary release of an accused person awaiting trial.
    - **Habeas Corpus**: A writ requiring a person under arrest to be brought before a judge or court.
    - **Mens Rea**: The intention or knowledge of wrongdoing that constitutes part of a crime.
    - **Prima Facie**: Based on the first impression; accepted as correct until proven otherwise.
    """)

def show_main_app():
    page = st.session_state.current_page
    dark = st.session_state.dark_mode
    username = st.session_state.get("username", "")

    with st.sidebar:
        # Brand Logo Header
        st.markdown(
            """
            <div style="display:flex; align-items:center; gap:10px; padding: 0.4rem 0.2rem 0.8rem; border-bottom: 1px solid rgba(255,255,255,0.08); margin-bottom: 0.8rem;">
                <span style="font-size: 1.6rem;">⚖️</span>
                <div>
                    <div style="font-family:'Outfit',sans-serif; font-size: 1.25rem; font-weight: 800; background: linear-gradient(135deg, #8B5CF6, #3B82F6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; letter-spacing: 0.03em;">LEXASSIST</div>
                    <div style="font-size: 0.72rem; color: #94A3B8;">AI Legal & Tax Assistant</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if username:
            first_char = username[0].upper() if username else "U"
            st.markdown(
                f"""
                <div class="saas-user-profile">
                    <div class="saas-avatar">{first_char}</div>
                    <div class="saas-username">{username}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        def _nav_button(label: str, target: str, icon: str):
            is_active = (page == target)
            btn_type = "primary" if is_active else "secondary"
            if st.button(f"{icon} {label}", key=f"snav_{target}", type=btn_type, use_container_width=True):
                st.session_state.current_page = target
                st.rerun()

        # Section 1: CORE ASSISTANTS
        st.markdown('<div class="sidebar-sec-title">Core Assistants</div>', unsafe_allow_html=True)
        _nav_button(get_translation("nav_home"), "Home", "🏠")
        _nav_button(get_translation("nav_legal"), "Ask Legal Question", "⚖️")
        _nav_button(get_translation("nav_tax"), "Tax Assistant", "💰")
        _nav_button(get_translation("nav_general"), "General Assistant", "💬")

        # Section 2: DOCUMENT AI
        st.markdown('<div class="sidebar-sec-title">Document AI</div>', unsafe_allow_html=True)
        _nav_button(get_translation("nav_doc_exp"), "Document Explanation", "📄")
        _nav_button(get_translation("nav_risk"), "Contract Risk Analyzer", "⚠️")
        _nav_button(get_translation("nav_compare"), "Compare Contracts", "📊")
        _nav_button(get_translation("nav_draft"), "Draft Document", "📝")

        # Section 3: LEGAL TOOLS
        st.markdown('<div class="sidebar-sec-title">Legal Tools</div>', unsafe_allow_html=True)
        _nav_button(get_translation("nav_case_law"), "Case Law Search", "🔍")
        _nav_button(get_translation("nav_section"), "Section Lookup", "📌")
        _nav_button(get_translation("nav_timeline"), "Legal Timeline", "🗓️")
        _nav_button(get_translation("nav_penalty"), "Penalty Calculator", "⚖️")
        _nav_button(get_translation("nav_glossary"), "Legal Glossary", "📖")

        # Section 4: HISTORY & ACCOUNT
        st.markdown('<div class="sidebar-sec-title">History & Account</div>', unsafe_allow_html=True)
        _nav_button(get_translation("nav_history"), "Query History", "📜")
        _nav_button(get_translation("nav_bookmarks"), "Bookmarks", "⭐")
        _nav_button(get_translation("nav_stats"), "My Stats", "📈")
        _nav_button(get_translation("nav_admin"), "Admin Analytics", "📊")
        _nav_button(get_translation("nav_profile"), "Profile", "👤")
        _nav_button(get_translation("nav_about"), "About", "ℹ️")

        st.markdown('<div style="margin-top: 1.2rem; border-top: 1px solid rgba(255,255,255,0.08); padding-top: 0.8rem;"></div>', unsafe_allow_html=True)

        # Sidebar Language Selector
        sb_lang_label = st.selectbox(
            f"🌐 {get_translation('language')}",
            options=list(LANGUAGE_OPTIONS.keys()),
            index=get_lang_index(st.session_state.chat_language),
            key="sb_language_selector"
        )
        sb_lang_code = LANGUAGE_OPTIONS[sb_lang_label]
        if sb_lang_code != st.session_state.chat_language:
            st.session_state.chat_language = sb_lang_code
            toast(f"Language set to {sb_lang_code}", "🌐")
            st.rerun()

        col_th, col_lg = st.columns(2)
        with col_th:
            if st.button("🌞 Light" if dark else "🌙 Dark", key="snav_theme", use_container_width=True):
                st.session_state.dark_mode = not dark
                st.rerun()
        with col_lg:
            if st.button(f"🚪 {get_translation('logout')}", key="snav_logout", use_container_width=True):
                try:
                    requests.post(f"{API_URL}/logout", headers=auth_headers(), timeout=TIMEOUT_SHORT)
                except Exception:
                    pass
                for k in ["logged_in", "user_id", "username", "token", "query_history",
                          "legal_messages", "tax_messages", "general_messages"]:
                    if k == "logged_in":
                        st.session_state[k] = False
                    elif k in ("query_history", "legal_messages", "tax_messages", "general_messages"):
                        st.session_state[k] = []
                    else:
                        st.session_state[k] = None
                st.rerun()

    # Dispatch views directly via page state
    if page == "Home":
        show_home_page()
    elif page == "Ask Legal Question":
        show_chat_page("legal", "Ask Legal Question")
    elif page == "Tax Assistant":
        show_chat_page("tax", "Tax Assistant")
    elif page == "General Assistant":
        show_chat_page("general", "General Assistant")
    elif page == "Document Explanation":
        st.markdown('<div class="main-header">Document Explanation</div>', unsafe_allow_html=True)
        st.write("Upload a legal or tax document (PDF, TXT, or DOCX) and get a simplified explanation.")
        uploaded_file = st.file_uploader("Choose a document", type=["pdf", "txt", "docx"])
        if uploaded_file:
            st.info(f"File uploaded: {uploaded_file.name} ({uploaded_file.size} bytes)")
            if st.button("Explain Document", type="primary"):
                with st.spinner("Analyzing document..."):
                    try:
                        files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                        response = requests.post(f"{API_URL}/explain-document", files=files, headers=auth_headers(), timeout=TIMEOUT_LONG)
                        if response.status_code == 200:
                            data = response.json()
                            c1, c2, c3, c4 = st.columns(4)
                            with c1:
                                st.metric("Filename", data["filename"])
                            with c2:
                                st.metric("Characters", f"{data['text_length']:,}")
                            with c3:
                                st.metric("Word Count", f"{data.get('word_count', 0):,}")
                            with c4:
                                st.metric("Reading Time", f"{data.get('reading_time_minutes', 1)} min")
                            with st.expander("Extracted Text (Preview)"):
                                st.text(data["extracted_text"])
                            st.markdown(f'<div class="response-box"><h3>AI Explanation</h3>{data["explanation"]}</div>', unsafe_allow_html=True)
                            toast("Document explained successfully!", "✅")
                        else:
                            toast("Could not process the document. Please try again.", "❌")
                    except Exception:
                        toast("Could not reach the server. Please try again shortly.", "❌")
    elif page == "Contract Risk Analyzer":
        show_contract_risk_analyzer()
    elif page == "Compare Contracts":
        show_compare_contracts()
    elif page == "Case Law Search":
        show_case_law_search()
    elif page == "Draft Document":
        show_draft_document()
    elif page == "Section Lookup":
        show_section_lookup()
    elif page == "Legal Timeline":
        show_legal_timeline()
    elif page == "Penalty Calculator":
        show_penalty_calculator()
    elif page == "Legal Glossary":
        show_legal_glossary()
    elif page == "Admin Analytics":
        show_admin_analytics()
    elif page == "Query History":
        st.markdown('<div class="main-header">Query History</div>', unsafe_allow_html=True)
        try:
            col_search, col_filter = st.columns([3, 1])
            with col_search:
                search_input = st.text_input(
                    "🔍 Search queries",
                    value=st.session_state.history_search,
                    placeholder="Type a keyword to search...",
                    key="history_search_input"
                )
            with col_filter:
                filter_category = st.selectbox(
                    "Filter by category:",
                    ["All", "legal", "tax", "general", "document"],
                    index=["All", "legal", "tax", "general", "document"].index(st.session_state.history_filter)
                )

            if search_input != st.session_state.history_search or filter_category != st.session_state.history_filter:
                st.session_state.history_page = 0
                st.session_state.history_search = search_input
                st.session_state.history_filter = filter_category
                st.rerun()

            offset = st.session_state.history_page * PAGE_SIZE
            params = {"limit": PAGE_SIZE, "offset": offset}
            if st.session_state.history_search:
                params["search"] = st.session_state.history_search
            if st.session_state.history_filter and st.session_state.history_filter != "All":
                params["category"] = st.session_state.history_filter

            resp = requests.get(
                f"{API_URL}/history",
                params=params,
                headers=auth_headers(), timeout=TIMEOUT_SHORT
            )
            if resp.status_code == 200:
                data = resp.json()
                history = data["history"]
                total = data["total"]
                total_pages = max(1, -(-total // PAGE_SIZE))

                col_info, col_export = st.columns([3, 1])
                with col_info:
                    label = f"Found {total} quer{'y' if total == 1 else 'ies'}"
                    if st.session_state.history_search:
                        label += f" matching \"{st.session_state.history_search}\""
                    st.info(f"{label} | Page {st.session_state.history_page + 1} of {total_pages}")
                with col_export:
                    export_resp = requests.get(f"{API_URL}/history/export", headers=auth_headers(), timeout=TIMEOUT_MEDIUM)
                    if export_resp.status_code == 200:
                        st.download_button(
                            label="⬇ Download CSV",
                            data=export_resp.content,
                            file_name="lexassist_history.csv",
                            mime="text/csv",
                            use_container_width=True
                        )

                if history:
                    bk_resp = requests.get(f"{API_URL}/bookmarks", headers=auth_headers(), timeout=TIMEOUT_SHORT)
                    bookmarked_ids = {b["id"] for b in bk_resp.json().get("bookmarks", [])} if bk_resp.status_code == 200 else set()

                    for item in history:
                        if filter_category != "All" and item["category"] != filter_category:
                            continue
                        is_bookmarked = item["id"] in bookmarked_ids
                        star = "⭐" if is_bookmarked else "☆"
                        with st.expander(f"{item['timestamp']} - {item['category'].upper()}"):
                            col_q, col_bk, col_del = st.columns([5, 1, 1])
                            with col_q:
                                st.markdown(f"**Query:** {item['query']}")
                            with col_bk:
                                if st.button(f"{star} Bookmark", key=f"bk_{item['id']}"):
                                    toggle_resp = requests.post(
                                        f"{API_URL}/bookmarks/toggle",
                                        json={"query_id": item["id"]},
                                        headers=auth_headers(), timeout=TIMEOUT_SHORT
                                    )
                                    if toggle_resp.status_code == 200:
                                        action = "Bookmarked" if toggle_resp.json().get("bookmarked") else "Removed bookmark"
                                        toast(f"{action}!", "⭐")
                                        st.rerun()
                            with col_del:
                                if st.button("🗑️ Delete", key=f"del_{item['id']}"):
                                    del_resp = requests.delete(
                                        f"{API_URL}/history/{item['id']}",
                                        headers=auth_headers(), timeout=TIMEOUT_SHORT
                                    )
                                    if del_resp.status_code == 200:
                                        toast("Entry deleted.", "🗑️")
                                        st.rerun()
                            st.markdown("---")
                            st.write(item["response"])

                    st.markdown("---")
                    prev_col, page_col, next_col, top_col = st.columns([1, 2, 1, 1])
                    with prev_col:
                        if st.session_state.history_page > 0:
                            if st.button("← Previous", use_container_width=True):
                                st.session_state.history_page -= 1
                                st.rerun()
                    with page_col:
                        st.markdown(f"<div style='text-align:center;padding-top:0.5rem'>Page {st.session_state.history_page + 1} / {total_pages}</div>", unsafe_allow_html=True)
                    with next_col:
                        if st.session_state.history_page + 1 < total_pages:
                            if st.button("Next →", use_container_width=True):
                                st.session_state.history_page += 1
                                st.rerun()
                    with top_col:
                        st.markdown("<a href='#top' style='display:block;text-align:center;padding-top:0.4rem;text-decoration:none;font-size:0.9rem'>⬆️ Top</a>", unsafe_allow_html=True)
                else:
                    if st.session_state.history_search:
                        st.info(f"No queries found matching \"{st.session_state.history_search}\".")
                    else:
                        st.info("No queries yet. Start asking questions!")
            else:
                toast("Failed to load history.", "❌")
        except Exception:
            toast("Could not reach the server. Please try again shortly.", "❌")
    elif page == "Bookmarks":
        st.markdown('<div class="main-header">Bookmarks</div>', unsafe_allow_html=True)
        try:
            resp = requests.get(f"{API_URL}/bookmarks", headers=auth_headers(), timeout=TIMEOUT_SHORT)
            if resp.status_code == 200:
                data = resp.json()
                bookmarks = data["bookmarks"]
                if bookmarks:
                    st.info(f"You have {data['count']} bookmarked queries.")
                    for item in bookmarks:
                        note = item.get("bookmark_note", "") or ""
                        label = f"⭐ {item['timestamp']} - {item['category'].upper()}"
                        if note:
                            label += f" — {note[:40]}"
                        with st.expander(label):
                            col_q, col_rm = st.columns([5, 1])
                            with col_q:
                                st.markdown(f"**Query:** {item['query']}")
                            with col_rm:
                                if st.button("Remove", key=f"rm_bk_{item['id']}"):
                                    toggle_resp = requests.post(
                                        f"{API_URL}/bookmarks/toggle",
                                        json={"query_id": item["id"]},
                                        headers=auth_headers(), timeout=TIMEOUT_SHORT
                                    )
                                    if toggle_resp.status_code == 200:
                                        toast("Bookmark removed.", "🗑️")
                                        st.rerun()
                            new_note = st.text_input(
                                "📝 Note", value=note,
                                placeholder="Add a label or note for this bookmark...",
                                key=f"note_input_{item['id']}"
                            )
                            if st.button("Save Note", key=f"save_note_{item['id']}"):
                                nr = requests.patch(
                                    f"{API_URL}/bookmarks/{item['id']}/note",
                                    json={"note": new_note},
                                    headers=auth_headers(), timeout=TIMEOUT_SHORT
                                )
                                if nr.status_code == 200:
                                    toast("Note saved!", "✅")
                                    st.rerun()
                            st.markdown("---")
                            st.write(item["response"])
                else:
                    st.info("No bookmarks yet. Star queries in Query History to save them here.")
            else:
                toast("Failed to load bookmarks.", "❌")
        except Exception:
            toast("Could not reach the server. Please try again shortly.", "❌")
    elif page == "My Stats":
        st.markdown('<div class="main-header">📈 My Stats</div>', unsafe_allow_html=True)
        try:
            resp = requests.get(f"{API_URL}/stats", headers=auth_headers(), timeout=TIMEOUT_SHORT)
            if resp.status_code == 200:
                s = resp.json()
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("Total Queries", s.get("total_queries", 0))
                with c2:
                    st.metric("Bookmarks", s.get("bookmarks_count", 0))
                with c3:
                    most = s.get("most_active_day", "—") or "—"
                    st.metric("Most Active Day", most)

                st.markdown("---")
                by_cat = s.get("by_category", {})
                if by_cat:
                    st.markdown("### Queries by Category")
                    cat_cols = st.columns(len(by_cat))
                    for col, (cat, count) in zip(cat_cols, by_cat.items()):
                        with col:
                            st.metric(cat.capitalize(), count)

                by_day = s.get("by_day", {})
                if by_day:
                    st.markdown("---")
                    st.markdown("### Activity — Last 30 Days")
                    df = pd.DataFrame(list(by_day.items()), columns=["Date", "Queries"])
                    df["Date"] = pd.to_datetime(df["Date"])
                    df = df.sort_values("Date")
                    st.bar_chart(df.set_index("Date")["Queries"])
            else:
                toast("Failed to load stats.", "❌")
        except Exception:
            toast("Could not reach the server.", "❌")
    elif page == "Profile":
        st.markdown('<div class="main-header">👤 Profile</div>', unsafe_allow_html=True)
        st.markdown(f"**Username:** {st.session_state.get('username', '')}")
        st.markdown("---")
        st.markdown("### Change Password")
        with st.form("change_password_form"):
            old_pw = st.text_input("Current password", type="password")
            new_pw = st.text_input("New password", type="password")
            confirm_pw = st.text_input("Confirm new password", type="password")
            submitted = st.form_submit_button("Update Password", type="primary")
        if submitted:
            if not old_pw or not new_pw or not confirm_pw:
                toast("Please fill in all fields.", "⚠️")
            elif len(new_pw) < 6:
                toast("New password must be at least 6 characters.", "⚠️")
            elif new_pw != confirm_pw:
                toast("New passwords do not match.", "⚠️")
            else:
                try:
                    resp = requests.post(
                        f"{API_URL}/change-password",
                        json={"old_password": old_pw, "new_password": new_pw},
                        headers=auth_headers(), timeout=TIMEOUT_SHORT
                    )
                    if resp.status_code == 200:
                        toast("Password updated successfully!", "✅")
                    else:
                        toast("Current password is incorrect.", "❌")
                except Exception:
                    toast("Could not reach the server.", "❌")
    elif page == "Admin Analytics":
        st.markdown('<div class="main-header">📊 Admin Analytics Dashboard</div>', unsafe_allow_html=True)
        st.write("System performance analytics, query category distributions, and real-time user feedback logs.")
        try:
            resp = requests.get(f"{API_URL}/admin/analytics", headers=auth_headers(), timeout=TIMEOUT_SHORT)
            if resp.status_code == 200:
                data = resp.json()
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    st.metric("Total Users", data.get("total_users", 0))
                with c2:
                    st.metric("Total Queries", data.get("total_queries", 0))
                with c3:
                    st.metric("Positive Ratings 👍", data.get("positive_feedback", 0))
                with c4:
                    st.metric("Negative Ratings 👎", data.get("negative_feedback", 0))
                
                st.markdown("---")
                c_left, c_right = st.columns(2)
                with c_left:
                    st.markdown("### 🏷️ Queries by Category")
                    by_cat = data.get("by_category", {})
                    if by_cat:
                        df_cat = pd.DataFrame(list(by_cat.items()), columns=["Category", "Count"])
                        st.bar_chart(df_cat.set_index("Category"))
                with c_right:
                    st.markdown("### 📈 Daily Activity (14 Days)")
                    daily = data.get("daily_activity", {})
                    if daily:
                        df_daily = pd.DataFrame(list(daily.items()), columns=["Date", "Queries"])
                        df_daily["Date"] = pd.to_datetime(df_daily["Date"])
                        st.line_chart(df_daily.sort_values("Date").set_index("Date"))
                
                st.markdown("---")
                st.markdown("### 💬 Recent User Feedback")
                recent = data.get("recent_feedback", [])
                if recent:
                    for f in recent:
                        icon = "👍" if f.get("rating", 0) > 0 else "👎"
                        st.markdown(f"**{icon} User `{f.get('username')}`**: *\"{f.get('query', '')[:100]}\"*")
                        if f.get("comment"):
                            st.caption(f"Note: {f['comment']}")
                else:
                    st.info("No feedback submitted yet.")
            else:
                toast("Failed to load admin analytics.", "❌")
        except Exception:
            toast("Could not reach the server.", "❌")

    elif page == "About":
        st.markdown('<div class="main-header">About LexAssist</div>', unsafe_allow_html=True)
        st.markdown("""
        ### What is LexAssist?
        LexAssist is an AI-powered legal and tax assistant for Indian law, built with RAG to ground answers in real legal documents.

        ### Knowledge Base
        - Indian Penal Code (IPC)
        - Constitution of India
        - CRPC (Code of Criminal Procedure)
        - Income Tax Bill 2025
        - IndicLegalQA Dataset (10K Q&A pairs)
        - Legal Contract Clauses

        ### Technology Stack
        - Frontend: Streamlit
        - Backend: FastAPI
        - AI: Groq (llama-3.1-8b-instant)
        - RAG: FAISS + fastembed
        - Database: SQLite

        ### Disclaimer
        LexAssist is an informational tool only. Always consult a qualified attorney or tax professional.
        """)
    else:
        show_home_page()

if not st.session_state.logged_in:
    if st.session_state.auth_alert:
        kind, msg = st.session_state.auth_alert
        st.session_state.auth_alert = None
        toast(msg, "✅" if kind == "success" else "⚠️" if kind == "warning" else "❌")
    show_login_page()
else:
    show_main_app()