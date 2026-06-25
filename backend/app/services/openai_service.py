import json
import logging
import base64
from typing import Any, Optional, AsyncGenerator
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

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

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        data = resp.json()

    content = data["choices"][0]["message"]["content"]
    try:
        extracted = json.loads(content)
        result = {}
        for key in ["age", "sex", "cp", "trestbps", "chol", "fbs", "restecg", "thalach", "exang", "oldpeak", "slope", "ca", "thal"]:
            if key in extracted and extracted[key] is not None:
                try:
                    result[key] = float(extracted[key])
                except (ValueError, TypeError):
                    pass
        return result
    except Exception as e:
        logger.error("Failed to parse extracted indicators: %s", e)
        return {}
