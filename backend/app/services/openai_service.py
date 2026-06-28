import json
import logging
import base64
import asyncio
from typing import Any, Optional, AsyncGenerator
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

FEATURE_KEYS = ["age", "sex", "cp", "trestbps", "chol", "fbs", "restecg", "thalach", "exang", "oldpeak", "slope", "ca", "thal"]

FEATURE_RANGES = {
    "age": (1, 120),
    "sex": (0, 1),
    "cp": (0, 3),
    "trestbps": (80, 250),
    "chol": (80, 600),
    "fbs": (0, 1),
    "restecg": (0, 2),
    "thalach": (60, 220),
    "exang": (0, 1),
    "oldpeak": (-3, 10),
    "slope": (0, 2),
    "ca": (0, 4),
    "thal": (0, 3),
}

FEATURE_LABELS_AR = {
    "age": "العمر",
    "sex": "الجنس",
    "cp": "نوع ألم الصدر",
    "trestbps": "ضغط الدم",
    "chol": "الكوليسترول",
    "fbs": "سكر الصيام",
    "restecg": "تخطيط القلب",
    "thalach": "أقصى نبض",
    "exang": "ذبحة مجهدة",
    "oldpeak": "انخفاض ST",
    "slope": "ميل ST",
    "ca": "الأوعية الملونة",
    "thal": "الثلاسيميا",
}

FEATURE_LABELS_EN = {
    "age": "Age",
    "sex": "Sex",
    "cp": "Chest Pain Type",
    "trestbps": "Resting BP",
    "chol": "Cholesterol",
    "fbs": "Fasting BS",
    "restecg": "Resting ECG",
    "thalach": "Max HR",
    "exang": "Exercise Angina",
    "oldpeak": "ST Depression",
    "slope": "ST Slope",
    "ca": "Vessels",
    "thal": "Thalassemia",
}

SYSTEM_PROMPT = """أنت مساعد طبي ذكي متخصص في تشخيص الأمراض والكشف المبكر.
تعمل كأداة مساعدة للطاقم الطبي لمتابعة حالة المريض وتشخيصها عبر خطة تشخيصية منظمة.

خطة التشخيص (Diagnostic Plan Flow):
1. مرحلة استقصاء الأعراض والشكوى (Intake & Symptoms):
   - يجب عليك في بداية الجلسة مراجعة شكوى المريض الرئيسية، مدتها، الأعراض المصاحبة، والتاريخ الطبي المرفوع.
   - إذا كانت المعلومات السريرية أو الأعراض غير كافية أو غير واضحة، لا تستدعِ دالة provide_diagnosis فوراً.
   - قم بطرح أسئلة سريرية محددة وموجهة (سؤالين أو ثلاثة بحد أقصى في كل مرة) لاستيضاح حالة المريض (مثل نوع الألم، العوامل التي تزيده أو تخففه، الأعراض المصاحبة الإضافية).
2. مرحلة تحليل الملفات والفحوصات (Files Analysis):
   - قم بمراجعة وتفسير أي ملفات مرفوعة (تحاليل مخبرية، تقارير، أو صور طبية) وربطها بأعراض المريض.
3. مرحلة التشخيص والتقييم النهائي (Final Assessment):
   - بمجرد اكتمال الصورة السريرية وحصولك على إجابات كافية، أو إذا طلب منك الطبيب ذلك بوضوح، قم باستدعاء دالة provide_diagnosis لتقديم تشخيص منظم متكامل.

قواعد هامة لتحديث المؤشرات:
- عند قيام المريض أو الطبيب بذكر أي من المؤشرات السريرية الـ 13 (مثل ضغط الدم، الكوليسترول، نبض القلب، السكر، أو تفاصيل تخطيط القلب) أثناء الحوار، أو عند اكتشافها من خلال التقارير المرفقة التي لم تفهرس بعد، قم باستدعاء دالة update_clinical_indicators لتحديث هذه المؤشرات فوراً في النظام ليقوم النموذج المحلي بإعادة حساب نسبة الخطر.

قواعد عامة:
- استخدم العربية كلغة رئيسية، ويمكنك استخدام الإنجليزية للمصطلحات الطبية.
- لا تصدر قراراً علاجياً نهائياً — أنت تقدم "رأي طبي مساعد".
- إذا ظهرت أي علامات خطيرة (Red Flags) تستدعي الطوارئ، نبه إليها فوراً وبشكل بارز.
- قم بتحليل كل ملف مرفوع بعناية واذكر استنتاجاتك منه بوضوح.
- تذكر أن هدفك هو الوصول إلى تشخيص دقيق بالاعتماد على التفاعل وطرح الأسئلة الذكية أولاً بدلاً من التخمين العشوائي بمستوى ثقة منخفض."""

DIAGNOSIS_FUNCTION = {
    "type": "function",
    "function": {
        "name": "provide_diagnosis",
        "description": "قدم تشخيصاً منظماً بعد جمع معلومات كافية. استدعِ هذه الدالة فقط عندما تكون لديك بيانات كافية للتشخيص.",
        "parameters": {
            "type": "object",
            "properties": {
                "primary_diagnosis": {
                    "type": "string",
                    "description": "التشخيص الرئيسي الأكثر احتمالاً",
                },
                "differential_diagnoses": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "تشخيصات تفريقية محتملة أخرى",
                },
                "severity": {
                    "type": "string",
                    "enum": ["low", "moderate", "high", "critical"],
                    "description": "مستوى الخطورة",
                },
                "confidence": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "مستوى الثقة في التشخيص",
                },
                "findings": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "النتائج الملاحظة من التحاليل والفحوصات",
                },
                "possible_causes": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "الأسباب المحتملة",
                },
                "recommendations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "التوصيات والخطوات التالية",
                },
                "additional_tests": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "فحوصات إضافية موصى بها",
                },
                "red_flags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "علامات تحذيرية تستدعي تدخلاً فورياً",
                },
                "follow_up_questions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "أسئلة متابعة قد تكون مطلوبة لاحقاً",
                },
            },
            "required": ["primary_diagnosis", "severity", "confidence", "findings", "recommendations", "red_flags"],
        },
    },
}

UPDATE_CLINICAL_INDICATORS_FUNCTION = {
    "type": "function",
    "function": {
        "name": "update_clinical_indicators",
        "description": "تحديث المؤشرات السريرية للمريض للنموذج المحلي عند ذكرها من المريض أو عند استخراجها من التقارير.",
        "parameters": {
            "type": "object",
            "properties": {
                "age": {"type": "number", "description": "العمر بالسنين"},
                "sex": {"type": "number", "description": "الجنس (1=ذكر، 0=أنثى)"},
                "cp": {"type": "number", "description": "نوع ألم الصدر (0: typical angina، 1: atypical angina، 2: non-anginal pain، 3: asymptomatic)"},
                "trestbps": {"type": "number", "description": "ضغط الدم الانقباضي عند الراحة بالـ mmHg"},
                "chol": {"type": "number", "description": "الكوليسترول بالـ mg/dL"},
                "fbs": {"type": "number", "description": "سكر الدم الصائم أكبر من 120 (1=نعم، 0=لا)"},
                "restecg": {"type": "number", "description": "تخطيط القلب الكهربائي عند الراحة (0: طبيعي، 1: ST-T wave abnormality، 2: left ventricular hypertrophy)"},
                "thalach": {"type": "number", "description": "أقصى معدل لضربات القلب تم تسجيله (النبض)"},
                "exang": {"type": "number", "description": "ذبحة صدرية ناتجة عن الجهد (1=نعم، 0=لا)"},
                "oldpeak": {"type": "number", "description": "انخفاض ST لتخطيط القلب الناتج عن المجهود (مثال: 1.5)"},
                "slope": {"type": "number", "description": "ميل شريحة ST في ذروة المجهود (0: downsloping، 1: flat، 2: upsloping)"},
                "ca": {"type": "number", "description": "عدد الأوعية الدموية الرئيسية الملونة بفحص الفلوروسكوبي (0-4)"},
                "thal": {"type": "number", "description": "نوع الثلاسيميا (0: طبيعي، 1: fixed defect، 2: reversible defect، 3: reversible)"},
            },
        },
    },
}

TOOLS = [DIAGNOSIS_FUNCTION, UPDATE_CLINICAL_INDICATORS_FUNCTION]


def build_context_message(patient: dict, vitals_summary: str, files_context: str, ml_prediction: Optional[dict] = None) -> str:
    ml_section = ""
    if ml_prediction:
        ml_section = f"""
=== توقع النموذج المحلي (Gradient Boosting) ===
التنبؤ: {ml_prediction.get('prediction_label', 'غير محدد')}
نسبة الخطر: {ml_prediction.get('risk_score', 'N/A')}
مستوى الخطر: {ml_prediction.get('risk_level', 'N/A')}
دقة النموذج: {ml_prediction.get('model_accuracy', 'N/A')}
أهم العوامل المساهمة: {', '.join(f.get('feature','') for f in ml_prediction.get('top_features', [])[:3])}

ملاحظة: هذا توقع من نموذج تعلم آلي محلي مدرب على بيانات أمراض القلب.
استخدمه كإشارة مساعدة إضافية بجانب تحليلك السريري."""

    context = f"""=== بيانات المريض ===
الاسم: {patient.get('name', 'غير محدد')}
العمر: {patient.get('age', 'غير محدد')}
الجنس: {patient.get('gender', 'غير محدد')}
التشخيص الحالي: {patient.get('diagnosis', 'غير محدد')}

=== العلامات الحيوية ===
{vitals_summary}

=== الفحوصات والتحاليل المرفوعة ===
{files_context}
{ml_section}

=== ملاحظة ===
حلل البيانات أعلاه بعناية. قم بتحليل كل ملف مرفوع واذكر ما لاحظته.
استدعِ دالة provide_diagnosis لتقديم تشخيص منظم بناءً على المعلومات المتاحة.
إذا كانت المعلومات غير كافية، قدم تشخيصاً بمستوى ثقة منخفض واذكر ما تحتاجه من معلومات إضافية."""
    return context


def encode_image_for_vision(image_bytes: bytes, mime_type: str = "image/png") -> str:
    return base64.b64encode(image_bytes).decode("utf-8")


def build_messages(
    context: str,
    conversation: list[dict],
    file_images: Optional[list[dict]] = None,
) -> list[dict]:
    messages: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]

    user_content: list[dict] = [{"type": "text", "text": context}]
    if file_images:
        for img in file_images:
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{img['mime_type']};base64,{img['data']}",
                    "detail": "high",
                },
            })
    messages.append({"role": "user", "content": user_content})

    for msg in conversation:
        messages.append({"role": msg["role"], "content": msg["content"]})

    return messages


async def chat_with_ai(
    context: str,
    conversation: list[dict],
    file_images: Optional[list[dict]] = None,
) -> dict[str, Any]:
    messages = build_messages(context, conversation, file_images)

    payload = {
        "model": settings.OPENAI_MODEL,
        "messages": messages,
        "tools": TOOLS,
        "tool_choice": "auto",
        "temperature": 0.3,
        "max_tokens": 2000,
    }

    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

    choice = data["choices"][0]
    message = choice["message"]

    result: dict[str, Any] = {
        "reply": message.get("content") or "",
        "tool_calls": [],
        "diagnosis": None,
        "finish_reason": choice.get("finish_reason", "stop"),
        "extracted_indicators": None,
    }

    if message.get("tool_calls"):
        for tc in message["tool_calls"]:
            if tc["function"]["name"] == "provide_diagnosis":
                try:
                    args = json.loads(tc["function"]["arguments"])
                    result["diagnosis"] = args
                    if not result["reply"]:
                        result["reply"] = "لقد أكملت التحليل. ستجد التشخيص المنظم أدناه."
                except json.JSONDecodeError:
                    logger.warning("Failed to parse diagnosis function args")
            elif tc["function"]["name"] == "update_clinical_indicators":
                try:
                    args = json.loads(tc["function"]["arguments"])
                    result["extracted_indicators"] = args
                except json.JSONDecodeError:
                    logger.warning("Failed to parse update_clinical_indicators function args")

    return result


async def chat_with_ai_stream(
    context: str,
    conversation: list[dict],
    file_images: Optional[list[dict]] = None,
):
    messages = build_messages(context, conversation, file_images)

    payload = {
        "model": settings.OPENAI_MODEL,
        "messages": messages,
        "tools": TOOLS,
        "tool_choice": "auto",
        "temperature": 0.3,
        "max_tokens": 2000,
        "stream": True,
    }

    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            "https://api.openai.com/v1/chat/completions",
            json=payload,
            headers=headers,
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    chunk = line[6:]
                    if chunk == "[DONE]":
                        break
                    try:
                        data = json.loads(chunk)
                        delta = data["choices"][0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            yield {"type": "content", "text": content}
                        if delta.get("tool_calls"):
                            yield {"type": "delta_tool_calls", "tool_calls": delta["tool_calls"]}
                        if data["choices"][0].get("finish_reason") == "tool_calls":
                            yield {"type": "tool_call", "message": data["choices"][0]}
                    except json.JSONDecodeError:
                        continue


async def extract_indicators_from_text_and_images(
    text: str,
    file_images: Optional[list[dict]] = None,
) -> dict:
    """Extract the 13 heart-disease indicators from text + images via OpenAI.

    Returns a detailed report:
      {
        "indicators": { key: value, ... },      # only successfully extracted, validated
        "details": [ { key, label, value, status, source }, ... ],
        "summary": { extracted_count, missing_count, invalid_count, extracted_keys, missing_keys, invalid_keys },
        "message_ar": " human-readable Arabic summary ",
      }

    Reliability:
      - Retries up to 3 times on network/HTTP/parse errors.
      - Validates every value against FEATURE_RANGES; out-of-range values are flagged invalid.
      - Never raises: always returns a report dict (even on total failure).
    """
    prompt = """أنت خبير تحليل تقارير وفحوصات طبية.
مهمتك هي مراجعة محتوى الفحوصات والتقارير الطبية المرفقة (سواء كانت نصاً مستخرجاً أو صوراً) واستخراج أي من المؤشرات الـ 13 التالية الخاصة بصحة القلب والشرايين:

1. age: العمر (عدد)
2. sex: الجنس (1=ذكر، 0=أنثى)
3. cp: نوع ألم الصدر (0: typical angina، 1: atypical angina، 2: non-anginal، 3: asymptomatic)
4. trestbps: ضغط الدم الانقباضي عند الراحة بالـ mmHg (عدد)
5. chol: الكوليسترول بالـ mg/dL (عدد)
6. fbs: سكر الدم الصائم أكبر من 120 (1=نعم، 0=لا)
7. restecg: تخطيط القلب عند الراحة (0: طبيعي، 1: ST-T wave abnormality، 2: left ventricular hypertrophy)
8. thalach: أقصى معدل لضربات القلب (عدد)
9. exang: ذبحة صدرية ناتجة عن المجهود (1=نعم، 0=لا)
10. oldpeak: انخفاض ST لتخطيط القلب الناتج عن المجهود (مثال: 1.5)
11. slope: ميل شريحة ST في ذروة المجهود (0: downsloping، 1: flat، 2: upsloping)
12. ca: عدد الأوعية الدموية الرئيسية الملونة بفحص الفلوروسكوبي (0-4)
13. thal: نوع الثلاسيميا (0: طبيعي، 1: fixed defect، 2: reversible defect، 3: reversible)

شروط هامة:
- استخرج فقط القيم المذكورة صراحة أو المفهومة سريرياً بشكل واضح من الملفات.
- لا تخترع أو تخمن أي قيم غير موجودة في المستندات. اترك أي قيمة غير موجودة كقيمة null أو لا ترجعها.
- أرجع الناتج ككائن JSON يحتوي على هذه الحقول فقط وبقيم رقمية مناسبة أو null."""

    messages = [
        {"role": "system", "content": prompt},
    ]

    user_content = [{"type": "text", "text": f"محتوى التقارير النصية المستخرجة:\n\n{text}"}]
    if file_images:
        for img in file_images:
            user_content.append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:{img['mime_type']};base64,{img['data']}",
                    "detail": "high",
                },
            })

    messages.append({"role": "user", "content": user_content})

    payload = {
        "model": settings.OPENAI_MODEL,
        "messages": messages,
        "response_format": {"type": "json_object"},
        "temperature": 0.0,
    }

    headers = {
        "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    raw_extracted: dict = {}
    last_error: Optional[str] = None
    max_retries = 3

    for attempt in range(1, max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    json=payload,
                    headers=headers,
                )
                resp.raise_for_status()
                data = resp.json()

            content = data["choices"][0]["message"]["content"]
            raw_extracted = json.loads(content)
            last_error = None
            break
        except httpx.HTTPStatusError as e:
            last_error = f"HTTP {e.response.status_code}: {e.response.text[:200]}"
            logger.warning("Extract indicators attempt %d failed (HTTP): %s", attempt, last_error)
        except (httpx.RequestError, json.JSONDecodeError, KeyError, IndexError) as e:
            last_error = f"{type(e).__name__}: {e}"
            logger.warning("Extract indicators attempt %d failed: %s", attempt, last_error)
        if attempt < max_retries:
            await asyncio.sleep(2 * attempt)

    indicators: dict[str, float] = {}
    details: list[dict] = []
    extracted_keys: list[str] = []
    missing_keys: list[str] = []
    invalid_keys: list[str] = []

    for key in FEATURE_KEYS:
        lo, hi = FEATURE_RANGES[key]
        label_ar = FEATURE_LABELS_AR.get(key, key)
        label_en = FEATURE_LABELS_EN.get(key, key)
        raw_val = raw_extracted.get(key) if raw_extracted else None

        if raw_val is None:
            missing_keys.append(key)
            details.append({"key": key, "label_ar": label_ar, "label_en": label_en, "value": None, "status": "missing", "source": None})
            continue

        try:
            val = float(raw_val)
        except (ValueError, TypeError):
            invalid_keys.append(key)
            details.append({"key": key, "label_ar": label_ar, "label_en": label_en, "value": None, "status": "invalid", "source": "ai", "raw": str(raw_val)})
            continue

        if val < lo or val > hi:
            invalid_keys.append(key)
            details.append({"key": key, "label_ar": label_ar, "label_en": label_en, "value": None, "status": "invalid", "source": "ai", "raw": val, "range": [lo, hi]})
            continue

        indicators[key] = val
        extracted_keys.append(key)
        details.append({"key": key, "label_ar": label_ar, "label_en": label_en, "value": val, "status": "extracted", "source": "ai"})

    extracted_count = len(extracted_keys)
    missing_count = len(missing_keys)
    invalid_count = len(invalid_keys)
    total_count = len(FEATURE_KEYS)
    complete = missing_count == 0 and invalid_count == 0

    invalid_labels_ar = "، ".join(FEATURE_LABELS_AR.get(k, k) for k in invalid_keys)
    invalid_labels_en = ", ".join(FEATURE_LABELS_EN.get(k, k) for k in invalid_keys)
    missing_labels_ar = "، ".join(FEATURE_LABELS_AR.get(k, k) for k in missing_keys)
    missing_labels_en = ", ".join(FEATURE_LABELS_EN.get(k, k) for k in missing_keys)

    if complete and not last_error:
        message_ar = f"✓ تم استخراج جميع المؤشرات السريرية الـ {total_count} بنجاح. النموذج المحلي جاهز للحساب."
        message_en = f"✓ All {total_count} clinical indicators extracted successfully. The local model is ready for prediction."
    elif last_error and not indicators:
        message_ar = (
            f"تعذّر استخراج المؤشرات من الملفات بعد {max_retries} محاولات.\n"
            f"السبب: {last_error}\n\n"
            f"يجب توفير جميع المؤشرات الـ {total_count} يدوياً قبل إجراء التشخيص."
        )
        message_en = (
            f"Failed to extract indicators after {max_retries} attempts.\n"
            f"Reason: {last_error}\n\n"
            f"All {total_count} indicators must be provided manually before running the diagnosis."
        )
    else:
        parts_ar = []
        parts_en = []
        parts_ar.append(f"تم استخراج {extracted_count} من {total_count} مؤشر سريري.")
        parts_en.append(f"Extracted {extracted_count} of {total_count} clinical indicators.")

        if invalid_count > 0:
            parts_ar.append(f"⚠ تم استبعاد {invalid_count} مؤشر لقيم خارج النطاق المسموح: {invalid_labels_ar}.")
            parts_en.append(f"⚠ {invalid_count} excluded for out-of-range values: {invalid_labels_en}.")

        if missing_count > 0:
            parts_ar.append(f"✗ المؤشرات التالية مفقودة ويجب توفيرها: {missing_labels_ar}.")
            parts_en.append(f"✗ The following indicators are missing and must be provided: {missing_labels_en}.")

        if last_error:
            parts_ar.append(f"ملاحظة: حدث خطأ مؤقت أثناء إحدى المحاولات ({last_error}).")
            parts_en.append(f"Note: a transient error occurred during one attempt ({last_error}).")

        if missing_count > 0 or invalid_count > 0:
            parts_ar.append("لا يمكن إجراء التشخيص حتى تكتمل جميع المؤشرات.")
            parts_en.append("Diagnosis cannot proceed until all indicators are complete.")

        message_ar = "\n".join(parts_ar)
        message_en = "\n".join(parts_en)

    return {
        "indicators": indicators,
        "details": details,
        "summary": {
            "extracted_count": extracted_count,
            "missing_count": missing_count,
            "invalid_count": invalid_count,
            "total_count": total_count,
            "complete": complete,
            "can_predict": complete,
            "extracted_keys": extracted_keys,
            "missing_keys": missing_keys,
            "invalid_keys": invalid_keys,
            "missing_labels_ar": missing_labels_ar,
            "missing_labels_en": missing_labels_en,
            "had_error": last_error is not None,
            "error": last_error,
        },
        "message_ar": message_ar,
        "message_en": message_en,
    }
