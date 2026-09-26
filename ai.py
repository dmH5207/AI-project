"""
AI 模块：维度配置、题目生成、评分、点评、报告生成
"""
import random
import json
import spark_api


def _call_spark(system_prompt, user_prompt, max_tokens=512, temperature=0.3):
    """调用星火 API，失败返回 None"""
    if not spark_api.is_configured():
        return None
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    return spark_api.chat(messages, temperature=temperature, max_tokens=max_tokens)


DIMENSIONS = [
    {"key": "basic",     "name": "AI基础认知",           "name_en": "AI Fundamentals",          "weight": 20},
    {"key": "tools",     "name": "AI工具使用",           "name_en": "AI Tools",                  "weight": 15},
    {"key": "prompt",    "name": "提示词工程",           "name_en": "Prompt Engineering",        "weight": 20},
    {"key": "evaluate",  "name": "AI结果评估与优化",     "name_en": "AI Evaluation",             "weight": 15},
    {"key": "ethics",    "name": "AI伦理与安全",         "name_en": "AI Ethics",                 "weight": 15},
    {"key": "collab",    "name": "人机协同解决问题",     "name_en": "Human-AI Collaboration",    "weight": 15},
]

QUESTION_BANK = {
    "basic": [
        "什么是人工智能？请用一句话描述。",
        "AI 和传统程序的最大区别是什么？",
        "举一个你生活中接触过 AI 的例子。",
    ],
    "basic_en": [
        "What is AI? Describe in one sentence.",
        "What is the biggest difference between AI and traditional programs?",
        "Give an example of AI you've encountered in daily life.",
    ],
    "tools": [
        "你用过哪些 AI 工具？分别用来做什么？",
        "ChatGPT 和搜索引擎有什么不同？",
        "选一个 AI 工具，说明它的适用场景。",
    ],
    "tools_en": [
        "What AI tools have you used? What for?",
        "How is ChatGPT different from a search engine?",
        "Pick an AI tool and explain its use case.",
    ],
    "prompt": [
        "写一段提示词，让 AI 帮你总结一篇文章的要点。",
        "好的提示词应该包含哪些要素？",
        "改写这段提示词使其更清晰：'帮我写个作文'。",
        "用户要求AI：帮我做一个学习计划。请优化该提示词，使AI能输出更精准的结果。要求：明确角色、提供上下文、明确输出格式、加入约束条件。",
    ],
    "prompt_en": [
        "Write a prompt to have AI summarize key points of an article.",
        "What elements should a good prompt contain?",
        "Rewrite this prompt to be clearer: 'Help me write an essay'.",
        "A user asks AI: 'Make me a study plan.' Optimize this prompt for better results. Requirements: clear role, context, output format, and constraints.",
    ],
    "evaluate": [
        "AI 生成的回答一定正确吗？为什么？",
        "你如何判断 AI 给出的信息是否可靠？",
        "什么是 AI 幻觉？举一个例子。",
        "AI生成如下内容：2025年某大学所有学生就业率达到100%。请说明如何判断该信息是否可信。",
    ],
    "evaluate_en": [
        "Is AI-generated answer always correct? Why?",
        "How do you judge if AI-provided information is reliable?",
        "What is AI hallucination? Give an example.",
        "AI claims: 'All students at a university achieved 100% employment in 2025.' How would you verify this?",
    ],
    "ethics": [
        "使用 AI 时需要注意哪些伦理问题？",
        "AI 生成的内容有版权吗？你怎么看？",
        "AI 可能带来哪些偏见？如何减少？",
    ],
    "ethics_en": [
        "What ethical issues should you consider when using AI?",
        "Does AI-generated content have copyright? What do you think?",
        "What biases can AI introduce? How to reduce them?",
    ],
    "collab": [
        "在什么情况下应该让人做决定而非 AI？",
        "描述一次你和 AI 协作完成任务的经历。",
        "人和 AI 各自擅长什么？如何互补？",
        "你需要完成一个校园垃圾分类宣传活动方案。请描述如何利用AI协助完成该任务。要求：体现人机协作流程，避免完全依赖AI。",
    ],
    "collab_en": [
        "When should humans make decisions instead of AI?",
        "Describe a time you collaborated with AI to complete a task.",
        "What do humans and AI each excel at? How to complement?",
        "Design a campus waste sorting campaign. Describe how to use AI for this task. Requirements: show human-AI collaboration, avoid over-reliance on AI.",
    ],
}

KEYWORD_RUBRICS = {
    "basic":   {"high": ["智能", "学习", "数据", "算法", "模型"], "medium": ["程序", "计算机", "自动"], "low": ["机器", "科技"]},
    "tools":   {"high": ["ChatGPT", "通义", "Copilot", "工具", "辅助"], "medium": ["搜索", "问答", "生成"], "low": ["AI", "用"]},
    "prompt":  {"high": ["角色", "任务", "格式", "具体", "清晰"], "medium": ["要求", "说明", "指令"], "low": ["写", "帮"]},
    "evaluate": {"high": ["核实", "验证", "来源", "幻觉", "偏见"], "medium": ["检查", "对比", "参考"], "low": ["看", "想"]},
    "ethics":  {"high": ["隐私", "版权", "偏见", "伦理", "公平"], "medium": ["安全", "责任", "透明"], "low": ["问题", "注意"]},
    "collab":  {"high": ["分工", "协同", "互补", "决策", "判断"], "medium": ["合作", "配合", "各自"], "low": ["一起", "用"]},
}


def get_dimension(index):
    if 0 <= index < len(DIMENSIONS):
        return DIMENSIONS[index]
    return None


def generate_question(dimension_key, lang="zh"):
    if lang == "en":
        questions = QUESTION_BANK.get(dimension_key + "_en", [])
    else:
        questions = QUESTION_BANK.get(dimension_key, [])
    if not questions:
        if lang == "en":
            return "Please share your understanding of this dimension."
        return "请谈谈你对这个维度的理解。"
    return random.choice(questions)


def score_answer(dimension, user_answer, lang="zh"):
    text = (user_answer or "").strip()
    weight = dimension["weight"]
    key = dimension["key"]
    dim_name = dimension.get("name_en", dimension["name"]) if lang == "en" else dimension["name"]

    if not text:
        return 0, ("No answer provided." if lang == "en" else "没有作答。")

    if lang == "en":
        prompt = (
            f"Dimension: {dim_name} (Max {weight} points)\n"
            f"Student answer: {text}\n\n"
            f"Score based on accuracy, depth, and specificity.\n"
            f"Strictly reply in format: score|brief comment\n"
            f"Example: 15|Covers core concepts, well expressed"
        )
        sys_msg = "You are a strict AI literacy scoring teacher. Score objectively. Reply only with score and comment in English."
    else:
        prompt = (
            f"维度：{dimension['name']}（满分 {weight} 分）\n"
            f"学生回答：{text}\n\n"
            f"请根据回答的准确性、深度和具体程度评分。\n"
            f"严格按此格式回复：分数|简短点评\n"
            f"例如：15|涉及核心概念，表述充分"
        )
        sys_msg = "你是一位严格的AI素养评分老师，评分客观公正，只回复分数和点评。"
    result = _call_spark(sys_msg, prompt, max_tokens=128, temperature=0.1)
    if result and "|" in result:
        parts = result.split("|", 1)
        try:
            s = int(parts[0].strip())
            s = max(0, min(weight, s))
            return s, parts[1].strip()
        except ValueError:
            pass

    rubric = KEYWORD_RUBRICS.get(key, {})
    score = 0.0
    reasons = []

    high_hits = [w for w in rubric.get("high", []) if w in text]
    medium_hits = [w for w in rubric.get("medium", []) if w in text]
    low_hits = [w for w in rubric.get("low", []) if w in text]

    if lang == "en":
        if high_hits:
            score += weight * 0.5
            reasons.append("Core concepts: " + ", ".join(high_hits[:3]))
        if medium_hits:
            score += weight * 0.25
            reasons.append("Related terms: " + ", ".join(medium_hits[:2]))
    else:
        if high_hits:
            score += weight * 0.5
            reasons.append("涉及核心概念：" + "、".join(high_hits[:3]))
        if medium_hits:
            score += weight * 0.25
            reasons.append("有相关表述：" + "、".join(medium_hits[:2]))
    if low_hits:
        score += weight * 0.1

    if len(text) >= 80:
        score += weight * 0.15
    elif len(text) < 20:
        score -= weight * 0.1

    score = max(0, min(weight, round(score)))

    if lang == "en":
        if score >= weight * 0.8:
            comment = "Great answer, accurate concepts and thorough explanation."
        elif score >= weight * 0.5:
            comment = "Basically correct, could go deeper."
        else:
            comment = "Answer is brief. Add more details and examples."
        if reasons:
            comment += " (" + "; ".join(reasons) + ")"
    else:
        if score >= weight * 0.8:
            comment = "回答很好，概念准确、表述充分。"
        elif score >= weight * 0.5:
            comment = "基本正确，可以再深入一些。"
        else:
            comment = "回答偏简略，建议补充更多细节和例子。"
        if reasons:
            comment += "（" + "、".join(reasons) + "）"

    return score, comment


def generate_reference_answer(question, dimension, lang="zh"):
    dim_name = dimension if isinstance(dimension, str) else dimension.get("name", "")
    if lang == "en":
        prompt = (
            f"Dimension: {dim_name}\n"
            f"Question: {question}\n\n"
            f"Provide a concise, accurate reference answer (2-4 sentences).\n"
            f"Focus on key concepts and practical examples. Reply in English."
        )
        sys_msg = "You are an AI literacy expert. Provide clear, accurate reference answers. Reply in English."
    else:
        prompt = (
            f"维度：{dim_name}\n"
            f"问题：{question}\n\n"
            f"请给出一个简洁准确的参考答案（2-4句话）。\n"
            f"重点阐述核心概念，可举例说明。用中文回复。"
        )
        sys_msg = "你是AI素养专家，给出清晰准确的参考答案，用中文回复。"
    result = _call_spark(sys_msg, prompt, max_tokens=256, temperature=0.3)
    if result:
        return result.strip()
    if lang == "en":
        return f"This question about {dim_name} requires understanding of core concepts and practical application."
    return f"本题涉及{dim_name}的核心概念与实际应用，需结合具体场景作答。"


def generate_reply(dimension_key, user_answer, lang="zh"):
    dim = next((d for d in DIMENSIONS if d["key"] == dimension_key), DIMENSIONS[0])
    question = generate_question(dimension_key, lang=lang)
    dim_name = dim.get("name_en", dim["name"]) if lang == "en" else dim["name"]

    if lang == "en":
        prompt = (
            f"Dimension: {dim_name}\n"
            f"Question: {question}\n"
            f"Student answer: {user_answer}\n\n"
            f"First review the student's answer (strengths and weaknesses), then ask a follow-up question to encourage deeper thinking.\n"
            f"Format:\n[Review]...\n[Follow-up]..."
        )
        sys_msg = "You are a patient AI literacy assessment teacher. Reviews are constructive and follow-ups inspire thinking. Reply in English."
        review_tag = "[Review]"
    else:
        prompt = (
            f"维度：{dim['name']}\n"
            f"问题：{question}\n"
            f"学生回答：{user_answer}\n\n"
            f"请先对学生的回答进行点评（指出优点和不足），然后提出一个追问引导学生深入思考。\n"
            f"格式：\n【点评】...\n【追问】..."
        )
        sys_msg = "你是一位耐心的AI素养评估老师，点评具体有建设性，追问能启发思考。"
        review_tag = "【点评】"
    result = _call_spark(sys_msg, prompt, max_tokens=384)
    if result and review_tag in result:
        return result

    score, comment = score_answer(dim, user_answer, lang=lang)
    if lang == "en":
        follow_ups = {
            "basic":   "Can you give another example of AI in education?",
            "tools":   "If you had to recommend one AI tool to a classmate, which would it be and why?",
            "prompt":  "Try writing your idea as a complete prompt.",
            "evaluate": "What methods would you use to verify an AI-generated answer?",
            "ethics":  "What rules should schools set for AI usage?",
            "collab":  "In your view, what is the optimal division of labor between humans and AI?",
        }
        follow_label = "[Follow-up]"
    else:
        follow_ups = {
            "basic":   "你能再举一个 AI 在教育中的应用例子吗？",
            "tools":   "如果让你推荐一个 AI 工具给同学，你会推荐哪个？为什么？",
            "prompt":  "试着把你刚才的想法写成一段完整的提示词。",
            "evaluate": "你会用什么方法来验证 AI 给出的答案？",
            "ethics":  "你觉得学校在使用 AI 时应该制定什么规则？",
            "collab":  "在你看来，人和 AI 的最佳分工方式是什么？",
        }
        follow_label = "【追问】"
    return comment + "\n\n" + follow_label + " " + follow_ups.get(dimension_key, ("Please continue sharing your thoughts." if lang == "en" else "请继续分享你的想法。"))


def generate_report(records, lang="zh"):
    if not records:
        return {
            "comment": ("No records for this session." if lang == "en" else "本次练习没有记录。"),
            "highlights": [],
            "suggestions": [("Remember to write something each round next time." if lang == "en" else "下次记得每轮都写一点内容。")],
            "scores": [],
            "total_score": 0,
            "max_score": 100,
        }

    total_score = sum(r.get("score", 0) for r in records)
    max_score = sum(r.get("weight", 0) for r in records)

    summary_lines = []
    for r in records:
        dim_name = r.get("dimension_en", r.get("dimension", "")) if lang == "en" else r.get("dimension", "")
        summary_lines.append(f"- {dim_name}: {r.get('score', 0)}/{r.get('weight', 0)}")

    if lang == "en":
        prompt = (
            f"Total score: {total_score}/{max_score}\n"
            f"Dimension scores:\n" + "\n".join(summary_lines) + "\n\n"
            f"Generate an assessment report with: overall comment, 2 highlights, 2 suggestions.\n"
            f"Strictly reply in JSON format:\n"
            f'{{"comment": "...", "highlights": ["..."], "suggestions": ["..."]}}'
        )
        sys_msg = "You are an AI literacy assessment expert. Generate concise, targeted reports. Reply only in JSON, in English."
    else:
        prompt = (
            f"总分：{total_score}/{max_score}\n"
            f"各维度得分：\n" + "\n".join(summary_lines) + "\n\n"
            f"请生成评估报告，包含：总体评价、2个亮点、2条建议。\n"
            f"严格按 JSON 格式回复：\n"
            f'{{"comment": "...", "highlights": ["..."], "suggestions": ["..."]}}'
        )
        sys_msg = "你是AI素养评估专家，生成简洁有针对性的评估报告。只回复JSON。"
    result = _call_spark(sys_msg, prompt, max_tokens=384, temperature=0.3)
    if result:
        try:
            clean = result.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[-1].rsplit("```", 1)[0]
            clean = clean.strip()
            if clean.startswith("json"):
                clean = clean[4:].strip()
            report_data = json.loads(clean)
            scores = []
            for r in records:
                dim_name = r.get("dimension_en", r.get("dimension", "")) if lang == "en" else r.get("dimension", "")
                scores.append({"dimension": dim_name, "score": r.get("score", 0), "weight": r.get("weight", 0)})
            return {
                "comment": report_data.get("comment", ""),
                "highlights": report_data.get("highlights", []),
                "suggestions": report_data.get("suggestions", []),
                "scores": scores,
                "total_score": total_score,
                "max_score": max_score,
            }
        except (json.JSONDecodeError, KeyError):
            pass

    ratio = total_score / max_score if max_score else 0
    if lang == "en":
        if ratio >= 0.8:
            comment = "Excellent! You have a solid understanding across all AI literacy dimensions. Keep it up!"
        elif ratio >= 0.6:
            comment = "Good performance. Most dimensions are well grasped; a few could use more depth."
        elif ratio >= 0.4:
            comment = "Fair completion. Try using more real examples to deepen understanding."
        else:
            comment = "Needs improvement. Start from basic concepts and build up gradually."
    else:
        if ratio >= 0.8:
            comment = "表现优秀！你对 AI 素养的各个方面都有较好的理解，继续保持。"
        elif ratio >= 0.6:
            comment = "表现良好。多数维度掌握不错，个别维度可以再深入。"
        elif ratio >= 0.4:
            comment = "完成度一般。建议多结合实际例子来加深理解。"
        else:
            comment = "还需要加强。建议从基础概念开始，逐步积累。"

    sorted_records = sorted(
        records,
        key=lambda r: r.get("score", 0) / (r.get("weight", 1) or 1),
        reverse=True,
    )

    highlights = []
    for r in sorted_records[:2]:
        dim_name = r.get("dimension_en", r.get("dimension", "")) if lang == "en" else r.get("dimension", "")
        if lang == "en":
            highlights.append(f"'{dim_name}' performed well, score {r.get('score', 0)} / {r.get('weight', 0)}")
        else:
            highlights.append(f"\u300c{dim_name}\u300d表现较好，得分 {r.get('score', 0)} / {r.get('weight', 0)}")

    suggestions = []
    for r in sorted_records[-2:]:
        dim_name = r.get("dimension_en", r.get("dimension", "")) if lang == "en" else r.get("dimension", "")
        if lang == "en":
            suggestions.append(f"'{dim_name}' could be strengthened; practice more related questions")
        else:
            suggestions.append(f"\u300c{dim_name}\u300d还可加强，建议多练习相关题目")
    if lang == "en":
        suggestions.append("When using AI daily, consciously practice prompts and result verification")
    else:
        suggestions.append("日常使用 AI 时，有意识地练习提示词和结果验证")

    scores = []
    for r in records:
        dim_name = r.get("dimension_en", r.get("dimension", "")) if lang == "en" else r.get("dimension", "")
        scores.append({"dimension": dim_name, "score": r.get("score", 0), "weight": r.get("weight", 0)})

    return {
        "comment": comment,
        "highlights": highlights,
        "suggestions": suggestions,
        "scores": scores,
        "total_score": total_score,
        "max_score": max_score,
    }


# ================================================================
# 实操式练习
# ================================================================






PRACTICE_STEPS = [
    {
        "step": 1,
        "dimension_key": "basic",
        "dimension": "AI基础认知",
        "dimension_en": "AI Fundamentals",
        "weight": 20,
        "question": "第 1 步：请先梳理这个任务的目标。用 3–5 句话说明：你打算解决什么问题、面向谁、希望达到什么效果。",
        "question_en": "Step 1: Clarify the task goal. In 3-5 sentences, explain: what problem to solve, who is the audience, and what effect you want.",
        "keywords": ["目标", "对象", "效果", "问题", "任务"],
    },
    {
        "step": 2,
        "dimension_key": "tools",
        "dimension": "AI工具使用",
        "dimension_en": "AI Tools",
        "weight": 20,
        "question": "第 2 步：针对这个任务，你打算用哪些 AI 工具？请列出 2–3 个，并说明它们各自能帮上什么忙。",
        "question_en": "Step 2: Which AI tools will you use for this task? List 2-3 and explain how each helps.",
        "keywords": ["工具", "通义", "ChatGPT", "Copilot", "插件", "数据分析"],
    },
    {
        "step": 3,
        "dimension_key": "prompt",
        "dimension": "提示词工程",
        "dimension_en": "Prompt Engineering",
        "weight": 20,
        "question": "第 3 步：请写出你会给 AI 的完整提示词，要求包含：角色、任务、输出格式。",
        "question_en": "Step 3: Write a complete prompt for AI, including: role, task, and output format.",
        "keywords": ["角色", "任务", "格式", "提示词", "步骤"],
    },
    {
        "step": 4,
        "dimension_key": "evaluate",
        "dimension": "AI结果评估与优化",
        "dimension_en": "AI Evaluation",
        "weight": 20,
        "question": "第 4 步：假设 AI 已经给了你一份初步结果。你会怎么核实它？请说出你的步骤，并指出可能出现的问题。",
        "question_en": "Step 4: Suppose AI gave you a draft result. How would you verify it? Describe your steps and potential issues.",
        "keywords": ["核实", "验证", "来源", "幻觉", "偏见", "改进"],
    },
    {
        "step": 5,
        "dimension_key": "collab",
        "dimension": "人机协同解决问题",
        "dimension_en": "Human-AI Collaboration",
        "weight": 20,
        "question": "第 5 步：写出你最终的成果（可以是简报、方案或一段说明）。同时说明：哪些是 AI 做的，哪些是你做的，为什么这样分工。",
        "question_en": "Step 5: Write your final output. Also explain: what did AI do, what did you do, and why this division of labor.",
        "keywords": ["分工", "我负责", "AI负责", "步骤", "协同", "总结"],
    },
]

PRACTICE_TASKS = [
    {
        "task_title": "帮班级做一份 AI 使用情况小调查",
        "task_title_en": "Conduct a mini AI usage survey for your class",
        "task_desc": "你需要设计并完成一次关于班级 AI 使用情况的小调查，最后形成一份简短说明。",
        "task_desc_en": "Design and complete a mini survey about AI usage in your class, and produce a brief summary.",
    },
    {
        "task_title": "用 AI 辅助完成一次文献速览",
        "task_title_en": "Use AI to quickly review literature",
        "task_desc": "围绕一个你感兴趣的主题，借助 AI 快速浏览 2–3 篇资料，并整理成一段要点。",
        "task_desc_en": "Pick a topic of interest, use AI to quickly review 2-3 sources, and summarize key points.",
    },
    {
        "task_title": "设计一份 AI 辅助的学习计划",
        "task_title_en": "Design an AI-assisted study plan",
        "task_desc": "为一门你正在学的课，借助 AI 制定一份 2 周的学习计划，并说明执行方式。",
        "task_desc_en": "For a course you're taking, use AI to create a 2-week study plan and explain how to execute it.",
    },
    {
        "task_title": "设计自适应测评策略",
        "task_title_en": "Design an adaptive testing strategy",
        "task_desc": "你的团队正在开发AI能力测评智能体，需要根据学生答题情况动态调整题目难度。请设计一个简单的自适应策略，包含动态调整机制和多个评价指标。",
        "task_desc_en": "Your team is building an AI assessment agent. Design a simple adaptive strategy with dynamic difficulty adjustment and multiple evaluation metrics.",
    },
    {
        "task_title": "设计AI能力测评报告",
        "task_title_en": "Design an AI capability assessment report",
        "task_desc": "设计一份AI能力测评报告，至少包含AI能力等级、六维能力评分、优势分析、薄弱能力、推荐学习路径。",
        "task_desc_en": "Design an AI capability report including: AI level, 6-dimension scores, strengths, weaknesses, and recommended learning paths.",
    },
]


def generate_practice_task():
    return random.choice(PRACTICE_TASKS)


def get_practice_step(index):
    if 0 <= index < len(PRACTICE_STEPS):
        return PRACTICE_STEPS[index]
    return None


def score_practice_step(step, user_answer, lang="zh"):
    text = (user_answer or "").strip()
    weight = step["weight"]

    if not text:
        return 0, ("No answer provided." if lang == "en" else "没有作答。")

    score = 0.0
    reasons = []

    example_words_zh = ["比如", "例如", "举个例子", "举例", "譬如"]
    example_words_en = ["for example", "e.g.", "such as", "like", "instance"]
    example_words = example_words_en if lang == "en" else example_words_zh
    if any(w in text.lower() for w in example_words):
        score += weight * 0.3
        reasons.append(("Has concrete examples" if lang == "en" else "有具体例子"))

    reason_words_zh = ["因为", "所以", "理由", "因此", "由于"]
    reason_words_en = ["because", "therefore", "reason", "thus", "since"]
    reason_words = reason_words_en if lang == "en" else reason_words_zh
    if any(w in text.lower() for w in reason_words):
        score += weight * 0.25
        reasons.append(("Has reasoning" if lang == "en" else "有理由推导"))

    hit = [k for k in step.get("keywords", []) if k in text]
    if hit:
        score += weight * 0.35
        if lang == "en":
            reasons.append("Keywords: " + ", ".join(hit[:3]))
        else:
            reasons.append("涉及关键词：" + "、".join(hit[:3]))

    if len(text) >= 100:
        score += weight * 0.1
    elif len(text) < 25:
        score -= weight * 0.15

    score = max(0, min(weight, round(score)))

    if lang == "en":
        if score >= weight * 0.8:
            comment = "Well done on this step, content is specific and well-supported."
        elif score >= weight * 0.5:
            comment = "Meets basic requirements, could add more details."
        else:
            comment = "This step needs more development. Add specific methods or examples."
        if reasons:
            comment += " (" + "; ".join(reasons) + ")"
    else:
        if score >= weight * 0.8:
            comment = "这一步完成得很好，内容具体、有支撑。"
        elif score >= weight * 0.5:
            comment = "基本达到要求，可以再补充一些细节。"
        else:
            comment = "这一步还需要展开，建议补充具体做法或例子。"
        if reasons:
            comment += "（" + "、".join(reasons) + "）"

    return score, comment


def generate_practice_feedback(step, user_answer, lang="zh"):
    dim_name = step.get("dimension_en", step["dimension"]) if lang == "en" else step["dimension"]
    question = step.get("question_en", step["question"]) if lang == "en" else step["question"]

    if lang == "en":
        prompt = (
            f"Step: {dim_name}\n"
            f"Question: {question}\n"
            f"Student answer: {user_answer}\n\n"
            f"Provide: 1) Feedback on this step (strengths and improvements); 2) An inspiring follow-up question.\n"
            f"Format:\n[{dim_name} · Feedback]\n...\n\n[Think About It]\n..."
        )
        sys_msg = "You are an AI practice guide teacher. Feedback is constructive and follow-ups inspire deeper thinking. Reply in English."
        fb_tag = "Feedback"
    else:
        prompt = (
            f"步骤：{step['dimension']}\n"
            f"问题：{step['question']}\n"
            f"学生回答：{user_answer}\n\n"
            f"请给出：1）对这一步的反馈（做得好的和可改进的）；2）一个启发式追问。\n"
            f"格式：\n【{step['dimension']} · 反馈】\n...\n\n【想一想】\n..."
        )
        sys_msg = "你是AI实操指导老师，反馈具体有建设性，追问能启发深入思考。"
        fb_tag = "反馈"
    result = _call_spark(sys_msg, prompt, max_tokens=384)
    if result and fb_tag in result:
        return result

    score, comment = score_practice_step(step, user_answer, lang=lang)
    if lang == "en":
        tips = [
            "Would your approach change in a different scenario?",
            "What's the most likely point of failure in this step?",
            "If you could keep only one sentence, which would it be?",
            "Is there a better way to express your idea?",
            "Is there a simpler way to achieve the same effect?",
        ]
        return (
            "[" + dim_name + " · Feedback]\n"
            + comment + "\n\n"
            + "[Think About It]\n" + random.choice(tips)
        )
    else:
        tips = [
            "如果换一个场景，你的做法会变吗？",
            "这一步里，你觉得最容易出问题的地方在哪？",
            "如果只能保留一句话，你会留下哪一句？",
            "有没有更好的方式来表达你的想法？",
            "有没有更简单的方式达到同样的效果？",
        ]
        return (
            "【" + step["dimension"] + " · 反馈】\n"
            + comment + "\n\n"
            + "【想一想】\n" + random.choice(tips)
        )


def generate_practice_report(records, lang="zh"):
    if not records:
        return {
            "comment": ("No records for this session." if lang == "en" else "本次练习没有记录。"),
            "highlights": [],
            "suggestions": [("Remember to write something each step next time." if lang == "en" else "下次记得每步都写一点内容。")],
            "scores": [],
            "total_score": 0,
            "max_score": 100,
        }

    total_score = sum(r.get("score", 0) for r in records)
    max_score = sum(r.get("weight", 0) for r in records)

    summary_lines = []
    for r in records:
        dim_name = r.get("dimension_en", r.get("dimension", "")) if lang == "en" else r.get("dimension", "")
        summary_lines.append(f"- {dim_name}: {r.get('score', 0)}/{r.get('weight', 0)}")

    if lang == "en":
        prompt = (
            f"Practice total score: {total_score}/{max_score}\n"
            f"Step scores:\n" + "\n".join(summary_lines) + "\n\n"
            f"Generate a practice assessment report with: overall comment, 2 highlights, 2 suggestions.\n"
            f"Strictly reply in JSON format:\n"
            f'{{"comment": "...", "highlights": ["..."], "suggestions": ["..."]}}'
        )
        sys_msg = "You are an AI practice assessment expert. Generate concise, targeted reports. Reply only in JSON, in English."
    else:
        prompt = (
            f"实操练习总分：{total_score}/{max_score}\n"
            f"各步骤得分：\n" + "\n".join(summary_lines) + "\n\n"
            f"请生成实操评估报告，包含：总体评价、2个亮点、2条建议。\n"
            f"严格按 JSON 格式回复：\n"
            f'{{"comment": "...", "highlights": ["..."], "suggestions": ["..."]}}'
        )
        sys_msg = "你是AI实操评估专家，生成简洁有针对性的报告。只回复JSON。"
    result = _call_spark(sys_msg, prompt, max_tokens=384, temperature=0.3)
    if result:
        try:
            clean = result.strip()
            if clean.startswith("```"):
                clean = clean.split("\n", 1)[-1].rsplit("```", 1)[0]
            clean = clean.strip()
            if clean.startswith("json"):
                clean = clean[4:].strip()
            report_data = json.loads(clean)
            scores = []
            for r in records:
                dim_name = r.get("dimension_en", r.get("dimension", "")) if lang == "en" else r.get("dimension", "")
                scores.append({"dimension": dim_name, "score": r.get("score", 0), "weight": r.get("weight", 0)})
            return {
                "comment": report_data.get("comment", ""),
                "highlights": report_data.get("highlights", []),
                "suggestions": report_data.get("suggestions", []),
                "scores": scores,
                "total_score": total_score,
                "max_score": max_score,
            }
        except (json.JSONDecodeError, KeyError):
            pass

    ratio = total_score / max_score if max_score else 0
    if lang == "en":
        if ratio >= 0.8:
            comment = "Excellent practice performance. You provided specific methods at each step with clear goals, tools, and verification awareness."
        elif ratio >= 0.6:
            comment = "Good practice performance. Most steps completed as required; a few could be more detailed."
        elif ratio >= 0.4:
            comment = "Fair completion. Add more specific operational details at each step to make the plan more concrete."
        else:
            comment = "Low completion. Start by clarifying the task goal, then build up tools, prompts, and verification methods."
    else:
        if ratio >= 0.8:
            comment = "本次实操练习表现优秀。你在各步骤都能给出具体做法，有目标、有工具、有验证意识，整体完成度很高。"
        elif ratio >= 0.6:
            comment = "本次实操练习表现良好。多数步骤都能按要求完成，个别步骤可以再细化。"
        elif ratio >= 0.4:
            comment = "本次实操练习完成度一般。建议在每一步都补充具体操作细节，让方案更落地。"
        else:
            comment = "本次实操练习完成度偏低。建议先从明确任务目标开始，再逐步补齐工具、提示词和验证方法。"

    sorted_records = sorted(
        records,
        key=lambda r: r.get("score", 0) / (r.get("weight", 1) or 1),
        reverse=True,
    )

    highlights = []
    for r in sorted_records[:2]:
        dim_name = r.get("dimension_en", r.get("dimension", "")) if lang == "en" else r.get("dimension", "")
        if lang == "en":
            highlights.append(f"'{dim_name}' performed well, score {r.get('score', 0)} / {r.get('weight', 0)}")
        else:
            highlights.append(f"「{dim_name}」表现较好，得分 {r.get('score', 0)} / {r.get('weight', 0)}")
    if lang == "en":
        highlights.append("Completed all 5 practice steps")
    else:
        highlights.append("完整走完了 5 步实操流程")

    suggestions = []
    for r in sorted_records[-2:]:
        dim_name = r.get("dimension_en", r.get("dimension", "")) if lang == "en" else r.get("dimension", "")
        if lang == "en":
            suggestions.append(f"'{dim_name}' could be strengthened; add more specific operational details")
        else:
            suggestions.append(f"「{dim_name}」还可加强，建议补充具体操作细节")
    if lang == "en":
        suggestions.append("For complex tasks: define goals first, then choose tools, then plan verification")
    else:
        suggestions.append("执行复杂任务时，先写目标，再配工具，最后想验证方法")

    scores = []
    for r in records:
        dim_name = r.get("dimension_en", r.get("dimension", "")) if lang == "en" else r.get("dimension", "")
        scores.append({"dimension": dim_name, "score": r.get("score", 0), "weight": r.get("weight", 0)})

    return {
        "comment": comment,
        "highlights": highlights,
        "suggestions": suggestions,
        "scores": scores,
        "total_score": total_score,
        "max_score": max_score,
    }