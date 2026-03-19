<template>
  <div class="home-page">
    <!-- 英雄区 -->
    <div class="hero">
      <div class="hero-content">
        <div class="hero-badge">
          <el-tag type="primary" effect="light" size="large">🌿 多智能体协同 · RAG增强</el-tag>
        </div>
        <h1 class="hero-title">中医智能问诊系统</h1>
        <p class="hero-subtitle">
          基于大语言模型与多智能体架构，模拟中医"望闻问切"全流程，<br />
          提供可解释、可追溯的辨证分析与个性化调理建议
        </p>
        <div class="hero-actions">
          <el-button type="primary" size="large" @click="$router.push('/consult')" class="primary-cta">
            <el-icon><ChatDotRound /></el-icon>
            立即开始问诊
          </el-button>
          <el-button size="large" @click="$router.push('/wellness')" class="secondary-cta" plain>
            <el-icon><Sunny /></el-icon>
            查看养生计划
          </el-button>
        </div>
        <div class="disclaimer-bar">
          ⚠️ 本系统仅提供健康参考，不构成医疗诊断，如有急重症状请立即就医
        </div>
      </div>
      <div class="hero-visual">
        <div class="visual-circle">
          <div class="circle-inner">
            <img src="@/assets/assistant-avatar.png" alt="AI助手" class="hero-avatar" />
          </div>
          <div class="orbit orbit-1">
            <div class="orbit-dot">望</div>
          </div>
          <div class="orbit orbit-2">
            <div class="orbit-dot">闻</div>
          </div>
          <div class="orbit orbit-3">
            <div class="orbit-dot">问</div>
          </div>
          <div class="orbit orbit-4">
            <div class="orbit-dot">切</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 核心功能 -->
    <div class="features-section section">
      <div class="section-title-wrap">
        <h2 class="section-title">核心功能</h2>
        <p class="section-sub">七大智能体协同工作，覆盖完整问诊流程</p>
      </div>
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" :md="8" v-for="feat in features" :key="feat.title">
          <div class="feature-card" @click="feat.route && $router.push(feat.route)">
            <div class="feat-icon" :style="{ background: feat.color }">{{ feat.emoji }}</div>
            <div class="feat-body">
              <h4>{{ feat.title }}</h4>
              <p>{{ feat.desc }}</p>
            </div>
            <el-icon v-if="feat.route" class="feat-arrow"><ArrowRight /></el-icon>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 智能体架构 -->
    <div class="architecture-section section">
      <div class="section-title-wrap">
        <h2 class="section-title">多智能体架构</h2>
        <p class="section-sub">各 Agent 职责明确，通过统一状态机传递上下文</p>
      </div>
      <div class="arch-flow">
        <div
          v-for="(agent, i) in agents"
          :key="agent.name"
          class="arch-node"
        >
          <div class="node-icon" :style="{ borderColor: agent.color }">{{ agent.emoji }}</div>
          <div class="node-name">{{ agent.name }}</div>
          <div class="node-desc">{{ agent.desc }}</div>
          <div v-if="i < agents.length - 1" class="node-arrow">→</div>
        </div>
      </div>
    </div>

    <!-- 技术亮点 -->
    <div class="tech-section section">
      <div class="section-title-wrap">
        <h2 class="section-title">技术亮点</h2>
      </div>
      <el-row :gutter="20">
        <el-col :xs="24" :sm="12" v-for="tech in techPoints" :key="tech.title">
          <el-card class="tech-card" shadow="hover">
            <div class="tech-header">
              <div class="tech-icon">{{ tech.emoji }}</div>
              <h4>{{ tech.title }}</h4>
            </div>
            <p>{{ tech.desc }}</p>
            <div class="tech-tags">
              <el-tag v-for="t in tech.tags" :key="t" size="small" type="info" effect="plain">{{ t }}</el-tag>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 快速入口 -->
    <div class="quick-nav section">
      <div class="section-title-wrap">
        <h2 class="section-title">快速入口</h2>
      </div>
      <el-row :gutter="16">
        <el-col :xs="12" :sm="6" v-for="nav in quickNavItems" :key="nav.label">
          <div class="nav-card" @click="$router.push(nav.path)">
            <div class="nav-icon">{{ nav.emoji }}</div>
            <span>{{ nav.label }}</span>
          </div>
        </el-col>
      </el-row>
    </div>

    <!-- 页脚 -->
    <div class="footer">
      <p>中医智能问诊系统 · 毕业设计项目 · 基于大语言模型的多智能体协同架构</p>
      <p class="footer-disclaimer">
        ⚠️ 重要提示：本系统输出内容仅为健康建议与中医辨证参考，不构成任何医疗诊断，不能替代执业医师的专业诊疗。
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ChatDotRound, Sunny, ArrowRight } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const features = [
  {
    emoji: '🩺',
    title: '多智能体协同问诊',
    desc: '七大专业 Agent 流水线协作，覆盖接诊、追问、望诊、辨证、建议、安全、报告全流程',
    color: 'linear-gradient(135deg,#667eea,#764ba2)',
    route: '/consult',
  },
  {
    emoji: '👅',
    title: '舌象智能分析（望诊）',
    desc: '上传舌象图片，自动提取舌色、苔色、苔质等特征，融合多模态信息辅助辨证',
    color: 'linear-gradient(135deg,#f093fb,#f5576c)',
    route: '/consult/tongue',
  },
  {
    emoji: '📋',
    title: '辨证分型推理',
    desc: '基于 RAG 检索增强，输出候选证型与置信度，每条结论均有症状依据和知识来源',
    color: 'linear-gradient(135deg,#4facfe,#00f2fe)',
    route: null,
  },
  {
    emoji: '🌿',
    title: '个性化养生管理',
    desc: '根据九种体质生成周期养生计划，含作息、饮食、运动、情志、穴位保健',
    color: 'linear-gradient(135deg,#43e97b,#38f9d7)',
    route: '/wellness',
  },
  {
    emoji: '🛡️',
    title: '安全审查机制',
    desc: '高危关键词库实时监控，特殊人群保护策略，禁止输出处方剂量，始终附免责声明',
    color: 'linear-gradient(135deg,#fa709a,#fee140)',
    route: null,
  },
  {
    emoji: '📊',
    title: '可解释性报告',
    desc: '生成结构化问诊报告（JSON + 可读版），附参考文献链路，支持打印/导出',
    color: 'linear-gradient(135deg,#a18cd1,#fbc2eb)',
    route: null,
  },
]

const agents = [
  { emoji: '🏥', name: 'IntakeAgent', desc: '接诊分诊', color: '#667eea' },
  { emoji: '❓', name: 'InquiryAgent', desc: '十问追问', color: '#f5576c' },
  { emoji: '👁️', name: 'ObservationAgent', desc: '望诊融合', color: '#4facfe' },
  { emoji: '🧬', name: 'SyndromeAgent', desc: '辨证分型', color: '#43e97b' },
  { emoji: '💊', name: 'RecommendAgent', desc: '调理建议', color: '#fa709a' },
  { emoji: '🔒', name: 'SafetyAgent', desc: '安全审查', color: '#fee140' },
  { emoji: '📄', name: 'ReportAgent', desc: '报告生成', color: '#a18cd1' },
]

const techPoints = [
  {
    emoji: '🤖',
    title: 'LLM 可配置接入',
    desc: '支持 Qwen、ChatGLM、OpenAI 兼容接口，可在管理后台配置模型提供商，无需改动代码',
    tags: ['Qwen', 'ChatGLM', 'OpenAI API', '可配置'],
  },
  {
    emoji: '🔍',
    title: 'RAG 混合检索',
    desc: '中医知识库支持向量检索 + BM25 关键词检索混合策略，结合 RRF 融合，提升知识召回准确率',
    tags: ['向量检索', 'BM25', 'RRF融合', '知识库'],
  },
  {
    emoji: '🔄',
    title: '会话状态机',
    desc: '使用 Pydantic 强类型 SessionState 在各 Agent 间传递，支持序列化持久化与链路追踪',
    tags: ['Pydantic', 'SessionState', '链路追踪'],
  },
  {
    emoji: '🛡️',
    title: '安全合规设计',
    desc: '关键词级快速预检 + LLM 语义级安全审查双重保障，特殊人群（孕妇、未成年）差异化策略',
    tags: ['关键词检测', '特殊人群', '免责声明', '安全拦截'],
  },
]

const quickNavItems = [
  { emoji: '🩺', label: '开始问诊', path: '/consult' },
  { emoji: '👅', label: '舌象分析', path: '/consult/tongue' },
  { emoji: '🌿', label: '养生计划', path: '/wellness' },
  { emoji: '📚', label: '知识库', path: '/knowledge' },
]
</script>

<style scoped lang="scss">
$primary: #1677ff;
$border: #e8eaf0;

.home-page {
  min-height: 100vh;
  background: #f5f7fb;
}

/* ─── Section layout ──────────────────────────────── */
.section {
  max-width: 1140px;
  margin: 0 auto 48px;
  padding: 0 24px;
}

.section-title-wrap {
  text-align: center;
  margin-bottom: 32px;

  .section-title {
    font-size: 28px;
    font-weight: 700;
    color: #1a1a2e;
    margin: 0 0 8px;
  }

  .section-sub { font-size: 15px; color: #666; margin: 0; }
}

/* ─── Hero ────────────────────────────────────────── */
.hero {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
  color: #fff;
  padding: 60px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 32px;
  margin-bottom: 60px;

  .hero-content {
    flex: 1;
    max-width: 580px;
    margin: 0 auto;

    .hero-badge { margin-bottom: 16px; }

    .hero-title {
      font-size: 42px;
      font-weight: 800;
      margin: 0 0 16px;
      background: linear-gradient(135deg, #fff 0%, #a8c8ff 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      background-clip: text;
    }

    .hero-subtitle {
      font-size: 16px;
      color: rgba(255, 255, 255, 0.75);
      line-height: 1.7;
      margin: 0 0 28px;
    }

    .hero-actions {
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-bottom: 20px;

      .primary-cta {
        padding: 12px 32px;
        font-size: 16px;
        height: auto;
      }

      .secondary-cta {
        padding: 12px 28px;
        font-size: 16px;
        height: auto;
        color: #fff;
        border-color: rgba(255,255,255,0.4);

        &:hover { background: rgba(255,255,255,0.1); }
      }
    }

    .disclaimer-bar {
      font-size: 12px;
      color: rgba(255, 200, 0, 0.8);
    }
  }

  .hero-visual {
    flex-shrink: 0;
    display: flex;
    justify-content: center;

    .visual-circle {
      position: relative;
      width: 240px;
      height: 240px;

      .circle-inner {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        width: 90px;
        height: 90px;
        background: rgba(255,255,255,0.1);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        border: 2px solid rgba(255,255,255,0.2);

        .hero-avatar {
          width: 70px;
          height: 70px;
          border-radius: 50%;
        }
      }

      .orbit {
        position: absolute;
        top: 50%;
        left: 50%;
        transform-origin: center;
        animation: rotate 8s linear infinite;

        .orbit-dot {
          width: 40px;
          height: 40px;
          background: rgba(255,255,255,0.15);
          border: 1px solid rgba(255,255,255,0.3);
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 14px;
          font-weight: 600;
          backdrop-filter: blur(4px);
        }

        &.orbit-1 { margin-left: 90px; margin-top: -20px; animation-delay: 0s; }
        &.orbit-2 { margin-left: -20px; margin-top: 90px; animation-delay: 2s; }
        &.orbit-3 { margin-left: -130px; margin-top: -20px; animation-delay: 4s; }
        &.orbit-4 { margin-left: -20px; margin-top: -130px; animation-delay: 6s; }
      }
    }
  }
}

@keyframes rotate {
  0% { transform: rotate(0deg) translateX(0) rotate(0deg); }
}

/* ─── Feature cards ───────────────────────────────── */
.feature-card {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 20px;
  background: #fff;
  border-radius: 12px;
  border: 1px solid $border;
  margin-bottom: 20px;
  cursor: pointer;
  transition: all 0.25s;

  &:hover {
    border-color: $primary;
    box-shadow: 0 4px 20px rgba(22, 119, 255, 0.12);
    transform: translateY(-2px);
  }

  .feat-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    flex-shrink: 0;
  }

  .feat-body {
    flex: 1;
    h4 { margin: 0 0 6px; font-size: 15px; }
    p { margin: 0; font-size: 13px; color: #666; line-height: 1.6; }
  }

  .feat-arrow { color: #bbb; flex-shrink: 0; margin-top: 4px; }
}

/* ─── Architecture flow ───────────────────────────── */
.arch-flow {
  display: flex;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 0;
  justify-content: center;
  padding: 32px;
  background: #fff;
  border-radius: 16px;
  border: 1px solid $border;

  .arch-node {
    display: flex;
    align-items: center;
    gap: 8px;

    .node-icon {
      width: 56px;
      height: 56px;
      border-radius: 50%;
      border: 2px solid #667eea;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 22px;
      background: #f0f4ff;
      flex-shrink: 0;
    }

    .node-name {
      font-size: 12px;
      font-weight: 600;
      text-align: center;
      display: none;
    }

    .node-arrow {
      font-size: 20px;
      color: #bbb;
      margin: 0 4px;
    }
  }
}

/* Override to show name below */
.arch-flow {
  .arch-node {
    flex-direction: column;
    text-align: center;
    gap: 6px;
    position: relative;

    .node-icon { margin-bottom: 2px; }
    .node-name { display: block; }
    .node-desc { font-size: 11px; color: #888; }
    .node-arrow {
      position: absolute;
      right: -24px;
      top: 20px;
      font-size: 16px;
    }

    &:last-child .node-arrow { display: none; }
  }
}

/* ─── Tech cards ──────────────────────────────────── */
.tech-card {
  border-radius: 12px;
  margin-bottom: 20px;
  height: 100%;

  .tech-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 10px;

    .tech-icon { font-size: 28px; }
    h4 { margin: 0; font-size: 16px; }
  }

  p { font-size: 13px; color: #666; line-height: 1.6; margin: 0 0 12px; }

  .tech-tags { display: flex; flex-wrap: wrap; gap: 6px; }
}

/* ─── Quick nav ───────────────────────────────────── */
.nav-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 24px 16px;
  background: #fff;
  border-radius: 12px;
  border: 1px solid $border;
  cursor: pointer;
  transition: all 0.25s;
  margin-bottom: 16px;
  text-align: center;

  &:hover {
    border-color: $primary;
    box-shadow: 0 4px 12px rgba(22,119,255,0.12);
    transform: translateY(-2px);
  }

  .nav-icon { font-size: 32px; }
  span { font-size: 14px; font-weight: 500; }
}

/* ─── Footer ──────────────────────────────────────── */
.footer {
  text-align: center;
  padding: 32px 24px;
  background: #1a1a2e;
  color: rgba(255,255,255,0.6);
  font-size: 13px;

  p { margin: 0 0 6px; }
  .footer-disclaimer { color: rgba(255,200,0,0.7); font-size: 12px; }
}

/* ─── Responsive ──────────────────────────────────── */
@media (max-width: 768px) {
  .hero {
    flex-direction: column;
    padding: 40px 20px;
    text-align: center;

    .hero-content .hero-title { font-size: 28px; }
    .hero-visual { display: none; }
    .hero-actions { justify-content: center; }
  }

  .arch-flow {
    .arch-node .node-arrow { display: none; }
    gap: 16px;
  }
}
</style>
