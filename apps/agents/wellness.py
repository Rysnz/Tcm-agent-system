"""
个性化养生管理模块

基于九种中医体质生成个性化养生计划，支持用户反馈微调。

功能：
1. 基于体质类型生成周期养生计划（7天/14天）
2. 包含：作息、饮食禁忌、运动强度、情志调节、穴位保健
3. 支持用户打卡记录
4. 基于反馈规则引擎微调下一周期计划

体质类型（中医九种体质）：
平和质、气虚质、阳虚质、阴虚质、痰湿质、湿热质、血瘀质、气郁质、特禀质
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

# 导入统一的枚举定义，避免重复
from apps.agents.session_state import ConstitutionType

logger = logging.getLogger("apps.agents")


@dataclass
class DailyPlan:
    """单日养生计划"""
    date: str  # ISO 格式日期字符串
    sleep_advice: str
    morning_routine: str
    diet_breakfast: str
    diet_lunch: str
    diet_dinner: str
    exercise: str
    emotion_adjustment: str
    acupoint_care: Optional[str] = None
    tea_recommendation: Optional[str] = None
    checklist: List[str] = field(default_factory=list)


@dataclass
class WeeklyWellnessPlan:
    """一周养生计划"""
    constitution: str
    start_date: str
    end_date: str
    theme: str
    key_principles: List[str]
    daily_plans: List[DailyPlan]
    weekly_notes: str
    generated_by: str = "TCM-Agent"


@dataclass
class CheckInRecord:
    """打卡记录"""
    date: str
    completed_items: List[str]
    skipped_items: List[str]
    energy_level: int  # 1-5
    sleep_quality: int  # 1-5
    mood_score: int  # 1-5
    notes: str = ""


# ---------------------------------------------------------------------------
# 九种体质基础养生方案库
# ---------------------------------------------------------------------------

CONSTITUTION_PLANS: Dict[str, Dict] = {
    "平和质": {
        "theme": "维护阴阳平衡，保持身心和谐",
        "principles": [
            "饮食有节，不偏食偏嗜",
            "起居有常，不妄劳作",
            "精神内守，乐观豁达",
        ],
        "sleep": "22:30前入睡，7点左右起床，保证7~8小时睡眠",
        "morning": "起床后做5分钟伸展，饮温水一杯",
        "exercise": "每日30分钟中等强度运动（散步、太极拳、八段锦）",
        "emotion": "保持平和心态，适当社交，培养兴趣爱好",
        "diet_principles": "五谷为养，五果为助，五畜为益，五菜为充",
        "forbidden_foods": ["暴饮暴食", "长期偏食"],
        "recommended_teas": ["绿茶", "菊花茶"],
        "acupoints": ["足三里（健脾胃）", "合谷（调气血）"],
    },
    "气虚质": {
        "theme": "补气健脾，固表养正",
        "principles": [
            "避免过度劳累，注意休息",
            "多食益气健脾食物",
            "适当运动，不宜大汗",
        ],
        "sleep": "21:30~22:00前入睡，保证充足睡眠，可午休30分钟",
        "morning": "缓慢起床，先静坐3分钟再站立，防止头晕",
        "exercise": "以柔和运动为主：散步、八段锦，每次20~30分钟，避免大量出汗",
        "emotion": "保持乐观心态，避免过思过虑，避免紧张焦虑",
        "diet_principles": "多食益气健脾食物：山药、红枣、南瓜、鸡肉、扁豆",
        "forbidden_foods": ["生冷食物", "肥腻厚味", "耗气伤正食物（如生萝卜）"],
        "recommended_teas": ["黄芪红枣茶", "党参枸杞茶"],
        "acupoints": ["足三里（补气健脾）", "气海（益气固本）", "太白（健脾益气）"],
    },
    "阳虚质": {
        "theme": "温阳散寒，培补命门",
        "principles": [
            "注意保暖，尤其腰腹部",
            "多食温阳食物",
            "不宜在寒冷环境中长时间停留",
        ],
        "sleep": "21:00~22:00前入睡，早起晒太阳",
        "morning": "晨起后做热身活动，先暖身再外出",
        "exercise": "以温阳运动为主：慢跑、骑行，在温暖时段运动，注意保暖",
        "emotion": "培养阳光心态，多晒太阳，避免悲忧过度",
        "diet_principles": "多食温热食物：生姜、韭菜、羊肉、核桃、荔枝",
        "forbidden_foods": ["生冷食物", "冰镇饮品", "寒凉水果（如西瓜、梨）"],
        "recommended_teas": ["生姜红枣茶", "肉桂茶"],
        "acupoints": ["命门（温阳固本）", "肾俞（补肾阳）", "足三里（健脾温中）"],
    },
    "阴虚质": {
        "theme": "滋阴降火，保津护液",
        "principles": [
            "避免熬夜，保证睡眠",
            "多食养阴生津食物",
            "避免辛辣燥热食物",
        ],
        "sleep": "22:00前入睡，不熬夜，可午休30分钟",
        "morning": "起床后用温水洗漱，避免热水",
        "exercise": "以舒缓运动为主：游泳、太极拳，避免大量出汗",
        "emotion": "保持平静心态，避免急躁易怒，冥想练习有助于静心",
        "diet_principles": "多食滋阴食物：百合、银耳、梨、枸杞、鸭肉、海参",
        "forbidden_foods": ["辛辣食物", "煎炸烧烤", "浓茶咖啡", "酒类"],
        "recommended_teas": ["百合枸杞茶", "石斛麦冬茶"],
        "acupoints": ["三阴交（滋阴）", "太溪（滋肾阴）", "涌泉（引火归元）"],
    },
    "痰湿质": {
        "theme": "健脾化湿，行气利水",
        "principles": [
            "控制体重，避免久坐",
            "少食甜腻油腻食物",
            "加强有氧运动",
        ],
        "sleep": "22:30~23:00前入睡，避免睡前进食",
        "morning": "起床后做20分钟有氧活动",
        "exercise": "加强有氧运动：快走、游泳、骑行，每日不少于45分钟，促进水湿代谢",
        "emotion": "保持积极心态，避免过度思虑（思伤脾），多参与社交活动",
        "diet_principles": "多食健脾化湿食物：薏苡仁、赤小豆、扁豆、冬瓜、荷叶",
        "forbidden_foods": ["甜腻食物", "油炸食物", "奶油制品", "过咸食物"],
        "recommended_teas": ["荷叶薏苡仁茶", "陈皮普洱茶"],
        "acupoints": ["丰隆（化痰祛湿）", "脾俞（健脾化湿）", "阴陵泉（利水渗湿）"],
    },
    "湿热质": {
        "theme": "清热利湿，疏肝健脾",
        "principles": [
            "清淡饮食，忌酒忌辛辣",
            "保持大便通畅",
            "避免潮湿环境",
        ],
        "sleep": "22:30前入睡，保证睡眠规律",
        "morning": "晨起饮用温开水，促进排便",
        "exercise": "适量有氧运动：慢跑、游泳，避免在高温潮湿环境中锻炼",
        "emotion": "保持心情舒畅，避免烦躁易怒",
        "diet_principles": "清淡饮食，多食清热利湿食物：绿豆、苦瓜、黄瓜、芹菜、莲藕",
        "forbidden_foods": ["酒类", "辛辣食物", "油腻食物", "甜腻食物"],
        "recommended_teas": ["绿茶", "薏苡仁绿豆茶"],
        "acupoints": ["曲池（清热）", "阴陵泉（利湿）", "三阴交（健脾利湿）"],
    },
    "血瘀质": {
        "theme": "活血化瘀，疏通经络",
        "principles": [
            "避免久坐久卧",
            "多食活血化瘀食物",
            "保持情绪舒畅",
        ],
        "sleep": "22:30前入睡，不宜过度劳累",
        "morning": "晨起做关节活动操，促进血液循环",
        "exercise": "坚持有氧运动：慢跑、骑行、瑜伽，每日30~45分钟，促进血液循环",
        "emotion": "保持心情舒畅，通过书法、音乐等舒缓情绪，避免郁闷",
        "diet_principles": "多食活血化瘀食物：山楂、黑木耳、洋葱、玫瑰花（遵医嘱）",
        "forbidden_foods": ["冷饮冷食", "收涩食物"],
        "recommended_teas": ["玫瑰山楂茶", "三七花茶（遵医嘱）"],
        "acupoints": ["血海（活血化瘀）", "膈俞（活血止痛）", "太冲（疏肝理气）"],
    },
    "气郁质": {
        "theme": "疏肝理气，调畅情志",
        "principles": [
            "培养乐观心态",
            "多参与社交活动",
            "多食疏肝理气食物",
        ],
        "sleep": "22:00~22:30前入睡，睡前可做放松练习",
        "morning": "晨起后做10分钟舒展运动，保持好心情",
        "exercise": "以舒展类运动为主：太极拳、瑜伽，有助于疏肝解郁",
        "emotion": "积极参加社交活动，培养兴趣爱好，必要时进行心理疏导",
        "diet_principles": "多食疏肝理气食物：玫瑰花、佛手、柑橘、陈皮、薄荷",
        "forbidden_foods": ["过食酸涩食物", "含咖啡因饮品（易加重焦虑）"],
        "recommended_teas": ["玫瑰花茶", "薄荷柠檬茶"],
        "acupoints": ["太冲（疏肝解郁）", "期门（疏肝理气）", "内关（宁心安神）"],
    },
    "特禀质": {
        "theme": "固表益气，防御外邪",
        "principles": [
            "避免接触已知过敏原",
            "增强免疫力",
            "居住环境保持清洁",
        ],
        "sleep": "22:00~22:30前入睡，保证充足睡眠，增强免疫力",
        "morning": "注意天气变化，及时增减衣物",
        "exercise": "根据自身情况适量运动，避免在花粉高峰期户外运动，佩戴口罩",
        "emotion": "保持平和心态，避免因过敏困扰产生焦虑",
        "diet_principles": "清淡饮食，避免已知过敏食物，适当食用益气固表食物",
        "forbidden_foods": ["海鲜类", "芒果、菠萝等热带水果（易致敏）", "花粉类食物"],
        "recommended_teas": ["绿茶（少量）", "灵芝茶（增强免疫）"],
        "acupoints": ["足三里（增强免疫）", "风池（固表防风）"],
    },
}

# 节气与体质调养建议（24节气简化版）
SOLAR_TERMS_ADVICE = {
    "春季": {
        "general": "春季肝气旺盛，宜疏肝理气，忌抑郁",
        "气郁质": "春季最需疏肝，多户外活动，赏花踏青",
        "阳虚质": "春季阳气渐升，可适当补阳",
    },
    "夏季": {
        "general": "夏季心火旺，宜清心养心，忌贪凉",
        "湿热质": "夏季湿热最难受，需特别注意清热利湿",
        "阴虚质": "夏季耗阴，需特别注意滋阴",
    },
    "秋季": {
        "general": "秋季肺气旺，宜养肺润燥，防悲秋",
        "阴虚质": "秋燥伤阴，需特别滋阴润燥",
        "气郁质": "秋季易悲秋，需调畅情志",
    },
    "冬季": {
        "general": "冬季肾气主令，宜藏精养肾，保暖防寒",
        "阳虚质": "冬季最需温补，可适当进补",
        "血瘀质": "冬季寒凝血瘀，需特别注意活血保暖",
    },
}


class WellnessPlanGenerator:
    """
    个性化养生计划生成器

    基于体质类型和当前日期生成7天养生计划，
    并支持基于用户反馈的下一周期微调。
    """

    def generate_weekly_plan(
        self,
        constitution: str,
        start_date: Optional[date] = None,
        cycle_days: int = 7,
        previous_feedback: Optional[List[CheckInRecord]] = None,
    ) -> WeeklyWellnessPlan:
        """
        生成周期养生计划

        Parameters
        ----------
        constitution : str
            体质类型（如"气虚质"）
        start_date : date, optional
            计划开始日期，默认为今天
        cycle_days : int
            计划天数，默认7天
        previous_feedback : List[CheckInRecord], optional
            上一周期的打卡反馈，用于微调本期计划
        """
        if start_date is None:
            start_date = date.today()

        plan_data = CONSTITUTION_PLANS.get(constitution, CONSTITUTION_PLANS["平和质"])

        # 基于反馈微调计划
        adjustments = self._compute_adjustments(previous_feedback)

        # 生成每日计划
        daily_plans = []
        for day_offset in range(cycle_days):
            current_date = start_date + timedelta(days=day_offset)
            daily = self._generate_daily_plan(
                plan_data, current_date, day_offset, adjustments
            )
            daily_plans.append(daily)

        end_date = start_date + timedelta(days=cycle_days - 1)

        return WeeklyWellnessPlan(
            constitution=constitution,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            theme=plan_data["theme"],
            key_principles=plan_data["principles"],
            daily_plans=daily_plans,
            weekly_notes=self._build_weekly_notes(plan_data, adjustments),
        )

    def _generate_daily_plan(
        self,
        plan_data: Dict,
        current_date: date,
        day_index: int,
        adjustments: Dict,
    ) -> DailyPlan:
        """生成单日计划"""
        # 一周饮食轮换（避免每天相同）
        diet_options = self._get_diet_options(plan_data, day_index)

        # 构建打卡清单
        checklist = [
            f"☑ 按时入睡（{plan_data['sleep'][:10]}）",
            f"☑ {plan_data['exercise'][:20]}",
            "☑ 饮温水 ≥ 1500ml",
            f"☑ {plan_data['emotion'][:20]}",
        ]
        if plan_data.get("acupoints"):
            checklist.append(f"☑ 穴位保健：{plan_data['acupoints'][0]}")

        # 如果上期有大量跳过，降低运动强度
        if adjustments.get("reduce_exercise_intensity"):
            exercise = plan_data["exercise"].replace("不少于45分钟", "20~30分钟")
        else:
            exercise = plan_data["exercise"]

        return DailyPlan(
            date=current_date.isoformat(),
            sleep_advice=plan_data["sleep"],
            morning_routine=plan_data["morning"],
            diet_breakfast=diet_options["breakfast"],
            diet_lunch=diet_options["lunch"],
            diet_dinner=diet_options["dinner"],
            exercise=exercise,
            emotion_adjustment=plan_data["emotion"],
            acupoint_care=(
                plan_data["acupoints"][day_index % len(plan_data["acupoints"])]
                if plan_data.get("acupoints") else None
            ),
            tea_recommendation=(
                plan_data["recommended_teas"][day_index % len(plan_data["recommended_teas"])]
                if plan_data.get("recommended_teas") else None
            ),
            checklist=checklist,
        )

    def _get_diet_options(self, plan_data: Dict, day_index: int) -> Dict[str, str]:
        """生成轮换饮食建议（增强版）"""
        constitution = plan_data.get("diet_principles", "均衡饮食")
        forbidden = "、".join(plan_data.get("forbidden_foods", [])[:2])
        
        # 更丰富的饮食轮换选项（7天一个周期）
        diet_cycle = [
            # 第1天
            {
                "breakfast": f"温热粥（如山药粥、红枣粥）+ 适量坚果，忌{forbidden}",
                "lunch": f"五谷饭 + 蔬菜 + 蛋白质适量（{constitution[:15]}）",
                "dinner": "清淡为主，七分饱，不宜过晚进食",
            },
            # 第2天
            {
                "breakfast": "温热豆浆或牛奶 + 全麦面包，忌生冷",
                "lunch": f"杂粮饭 + 深色蔬菜 + 适量优质蛋白（{constitution[:15]}）",
                "dinner": "蒸煮为主，少油少盐，忌暴饮暴食",
            },
            # 第3天
            {
                "breakfast": f"小米粥 + 蒸蛋 + 小菜，忌{forbidden}",
                "lunch": f"糙米饭 + 时令蔬菜 + 瘦肉（{constitution[:15]}）",
                "dinner": "粥类为主，易消化，七分饱",
            },
            # 第4天
            {
                "breakfast": "燕麦粥 + 水果 + 坚果，忌生冷",
                "lunch": f"米饭 + 豆制品 + 绿叶菜（{constitution[:15]}）",
                "dinner": "面条或馄饨，温热食用",
            },
            # 第5天
            {
                "breakfast": f"南瓜粥 + 鸡蛋 + 小菜，忌{forbidden}",
                "lunch": f"杂粮饭 + 菌菇类 + 蛋白质（{constitution[:15]}）",
                "dinner": "清淡粥品，配少量蔬菜",
            },
            # 第6天
            {
                "breakfast": "黑芝麻糊 + 全麦馒头，忌生冷",
                "lunch": f"米饭 + 清蒸鱼 + 时蔬（{constitution[:15]}）",
                "dinner": "汤面或米粉，温热食用",
            },
            # 第7天
            {
                "breakfast": f"八宝粥 + 鸡蛋，忌{forbidden}",
                "lunch": f"五谷饭 + 蔬菜 + 豆制品（{constitution[:15]}）",
                "dinner": "清淡为主，可适当增加汤品",
            },
        ]
        
        # 使用day_index模7来选择对应天的饮食
        day_of_week = day_index % 7
        return diet_cycle[day_of_week]

    def _compute_adjustments(
        self, feedbacks: Optional[List[CheckInRecord]]
    ) -> Dict[str, Any]:
        """基于反馈计算下一周期调整策略（规则引擎）"""
        if not feedbacks:
            return {}

        adjustments: Dict[str, Any] = {}

        # 统计上期完成率
        total_items = sum(
            len(r.completed_items) + len(r.skipped_items)
            for r in feedbacks
        )
        completed_items = sum(len(r.completed_items) for r in feedbacks)
        completion_rate = completed_items / total_items if total_items > 0 else 0

        # 平均精力值
        avg_energy = sum(r.energy_level for r in feedbacks) / len(feedbacks)
        avg_sleep = sum(r.sleep_quality for r in feedbacks) / len(feedbacks)

        # 规则 1：运动完成率低，适当降低强度
        exercise_skipped = sum(
            1 for r in feedbacks
            if any("运动" in item for item in r.skipped_items)
        )
        if exercise_skipped > len(feedbacks) * 0.5:
            adjustments["reduce_exercise_intensity"] = True
            adjustments["exercise_note"] = "本周适当调低运动强度，以坚持为主"

        # 规则 2：睡眠质量差，强化睡眠建议
        if avg_sleep < 3:
            adjustments["enhance_sleep_focus"] = True
            adjustments["sleep_note"] = "本周重点改善睡眠：睡前1小时放下手机，泡脚助眠"

        # 规则 3：精力普遍低落，提醒注意劳逸结合
        if avg_energy < 2.5:
            adjustments["low_energy_mode"] = True
            adjustments["energy_note"] = "本周以恢复体力为主，减少消耗，多休息"

        adjustments["completion_rate"] = completion_rate
        return adjustments

    def _build_weekly_notes(
        self, plan_data: Dict, adjustments: Dict
    ) -> str:
        """生成本周注意事项"""
        notes = [f"本周主题：{plan_data['theme']}"]

        if adjustments.get("exercise_note"):
            notes.append(f"⚠️ {adjustments['exercise_note']}")
        if adjustments.get("sleep_note"):
            notes.append(f"💤 {adjustments['sleep_note']}")
        if adjustments.get("energy_note"):
            notes.append(f"⚡ {adjustments['energy_note']}")

        completion = adjustments.get("completion_rate")
        if completion is not None:
            notes.append(f"上周完成率：{completion:.0%}，继续加油！")

        return "\n".join(notes)

    def generate_summary_text(self, plan: WeeklyWellnessPlan) -> str:
        """生成可读的计划摘要"""
        lines = [
            f"🌿 {plan.constitution} 养生计划",
            f"📅 {plan.start_date} ~ {plan.end_date}",
            f"主题：{plan.theme}",
            "",
            "核心原则：",
        ]
        for p in plan.key_principles:
            lines.append(f"  • {p}")

        lines.extend([
            "",
            f"作息建议：{plan.daily_plans[0].sleep_advice}",
            f"运动方案：{plan.daily_plans[0].exercise}",
            f"情志调节：{plan.daily_plans[0].emotion_adjustment}",
        ])

        if plan.daily_plans[0].acupoint_care:
            lines.append(f"穴位保健：{plan.daily_plans[0].acupoint_care}")
        if plan.daily_plans[0].tea_recommendation:
            lines.append(f"代茶饮：{plan.daily_plans[0].tea_recommendation}")

        lines.extend([
            "",
            "⚠️ 温馨提示：以上建议为通用养生参考，如有不适请及时就医。",
        ])

        return "\n".join(lines)
