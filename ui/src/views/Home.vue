<template>
  <div class="home-nm">
    <!-- ── 顶部英雄区 ─────────────────────────────────── -->
    <div class="hero-section">
      <div class="hero-inner">
        <!-- 左侧文字 -->
        <div class="hero-text">
          <div class="hero-badge nm-pill">
            <span class="badge-dot" />
            多智能体协同 · RAG增强 · 多模态望诊
          </div>
          <h1 class="hero-title">中医智能问诊系统</h1>
          <p class="hero-subtitle">
            基于大语言模型与多智能体架构，模拟中医"望闻问切"全流程，<br />
            提供可解释、可追溯的辨证分析与个性化调理建议
          </p>
          <div class="hero-cta">
            <button class="nm-btn-primary" @click="router.push('/consult')">
              <span class="btn-icon">🩺</span>
              立即开始问诊
            </button>
            <button class="nm-btn-secondary" @click="router.push('/wellness')">
              <span class="btn-icon">🌿</span>
              查看养生计划
            </button>
          </div>
          <div class="disclaimer-pill">
            ⚠️ 本系统仅提供健康参考，不构成医疗诊断，如有急重症状请立即就医
          </div>
        </div>

        <!-- 右侧四象仪 -->
        <div class="hero-visual">
          <div class="wq-ring nm-ring">
            <div class="wq-center">
              <img src="@/assets/assistant-avatar.png" alt="AI助手" class="hero-avatar" />
            </div>
            <div
              v-for="(item, i) in wqItems"
              :key="item.char"
              class="wq-orbit"
              :style="orbitStyle(i)"
            >
              <div class="wq-dot nm-dot" :style="{ '--dot-color': item.color }">
                <span class="wq-char">{{ item.char }}</span>
                <span class="wq-label">{{ item.label }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ── 核心功能卡片 ─────────────────────────────── -->
    <div class="section">
      <div class="section-header">
        <h2 class="section-title">核心功能</h2>
        <p class="section-sub">七大智能体协同工作，覆盖完整问诊流程</p>
      </div>
      <div class="card-grid">
        <div
          v-for="feat in features"
          :key="feat.title"
          class="nm-card feature-card"
          :class="{ clickable: !!feat.route }"
          @click="feat.route && router.push(feat.route)"
        >
          <div class="feat-emoji" :style="{ '--c': feat.color }">{{ feat.emoji }}</div>
          <div class="feat-text">
            <h4>{{ feat.title }}</h4>
            <p>{{ feat.desc }}</p>
          </div>
          <div v-if="feat.route" class="feat-arrow">›</div>
        </div>
      </div>
    </div>

    <!-- ── 多智能体流程 ─────────────────────────────── -->
    <div class="section arch-section">
      <div class="section-header">
        <h2 class="section-title">多智能体架构</h2>
        <p class="section-sub">各 Agent 职责明确，通过统一状态机传递上下文</p>
      </div>
      <div class="arch-flow">
        <div
          v-for="(agent, i) in agents"
          :key="agent.name"
          class="arch-step"
        >
          <div class="nm-node" :style="{ '--nc': agent.color }">
            <div class="node-emoji">{{ agent.emoji }}</div>
            <div class="node-name">{{ agent.name }}</div>
            <div class="node-desc">{{ agent.desc }}</div>
          </div>
          <div v-if="i < agents.length - 1" class="arch-arrow">→</div>
        </div>
      </div>
    </div>

    <!-- ── 技术亮点 ──────────────────────────────────── -->
    <div class="section">
      <div class="section-header">
        <h2 class="section-title">技术亮点</h2>
        <p class="section-sub">工程化、可观测、可扩展的多智能体中医问诊实现</p>
      </div>
      <div class="tech-grid">
        <div
          v-for="tech in techPoints"
          :key="tech.title"
          class="nm-card tech-card"
        >
          <div class="tech-icon">{{ tech.emoji }}</div>
          <h4>{{ tech.title }}</h4>
          <p>{{ tech.desc }}</p>
          <div class="tech-tags">
            <span v-for="t in tech.tags" :key="t" class="nm-tag">{{ t }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- ── 快速入口 ──────────────────────────────────── -->
    <div class="section">
      <div class="section-header">
        <h2 class="section-title">快速入口</h2>
      </div>
      <div class="quick-grid">
        <div
          v-for="nav in quickNav"
          :key="nav.label"
          class="nm-quick-btn"
          @click="router.push(nav.path)"
        >
          <div class="qbtn-emoji">{{ nav.emoji }}</div>
          <span>{{ nav.label }}</span>
        </div>
      </div>
    </div>

    <!-- ── 页脚 ─────────────────────────────────────── -->
    <div class="footer">
      <p class="footer-title">中医智能问诊系统 · 基于大语言模型的多智能体协同架构</p>
      <p class="footer-disclaimer">
        ⚠️ 重要提示：本系统输出内容仅为健康建议与中医辨证参考，不构成任何医疗诊断，不能替代执业医师的专业诊疗。
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

/* 望闻问切四象 */
const wqItems = [
  { char: '望', label: '望诊', color: '#007AFF' },
  { char: '闻', label: '闻诊', color: '#FF9500' },
  { char: '问', label: '问诊', color: '#34C759' },
  { char: '切', label: '切诊', color: '#AF52DE' },
]

const orbitStyle = (i: number) => {
  const angle = (i / wqItems.length) * 360 - 90
  const rad = (angle * Math.PI) / 180
  const r = 110
  return {
    left: `calc(50% + ${Math.cos(rad) * r}px - 32px)`,
    top: `calc(50% + ${Math.sin(rad) * r}px - 32px)`,
  }
}

const features = [
  {
    emoji: '🩺',
    title: '多智能体协同问诊',
    desc: '七大专业 Agent 流水线协作，覆盖接诊→追问→望诊→辨证→建议→安全→报告全流程',
    color: '#007AFF',
    route: '/consult',
  },
  {
    emoji: '👅',
    title: '舌象图像分析',
    desc: '上传舌象图片，ObservationAgent 自动提取舌色、苔色、苔厚薄等视觉诊断特征',
    color: '#FF9500',
    route: '/consult/tongue',
  },
  {
    emoji: '��',
    title: '辨证分型推理',
    desc: 'SyndromeAgent 综合所有信息，输出候选证型、置信度及关键证据链',
    color: '#34C759',
    route: null,
  },
  {
    emoji: '🌿',
    title: '个性化养生管理',
    desc: '根据体质生成作息、饮食、情志、穴位周期计划，支持打卡与反馈迭代',
    color: '#AF52DE',
    route: '/wellness',
  },
  {
    emoji: '📚',
    title: 'RAG知识增强',
    desc: '混合检索中医教材与证候知识库，输出附带参考依据片段，结论可溯源',
    color: '#FF2D55',
    route: null,
  },
  {
    emoji: '🛡️',
    title: '安全合规审查',
    desc: 'SafetyGuardAgent 识别高危症状并拦截不当建议，禁止输出明确处方剂量',
    color: '#5AC8FA',
    route: null,
  },
  {
    emoji: '📝',
    title: '结构化报告生成',
    desc: 'ReportAgent 生成可导出的 JSON+可读版问诊报告，包含完整推理轨迹',
    color: '#FFCC00',
    route: '/consult/report',
  },
]

const agents = [
  { emoji: '📋', name: 'Intake',         desc: '接诊分诊',  color: '#007AFF' },
  { emoji: '❓', name: 'Inquiry',        desc: '追问引导',  color: '#FF9500' },
  { emoji: '👁',  name: 'Observation',   desc: '望诊融合',  color: '#34C759' },
  { emoji: '🔬', name: 'Syndrome',       desc: '辨证分型',  color: '#AF52DE' },
  { emoji: '💊', name: 'Recommendation', desc: '调理建议',  color: '#FF2D55' },
  { emoji: '🛡',  name: 'SafetyGuard',   desc: '安全审查',  color: '#5AC8FA' },
  { emoji: '📝', name: 'Report',         desc: '报告生成',  color: '#FFCC00' },
]

const techPoints = [
  {
    emoji: '🤖',
    title: '多智能体编排',
    desc: '基于状态机的 Agent 协调调度，支持失败重试与降级策略，任意 Agent 失败时给出保守输出',
    tags: ['状态机', 'Orchestrator', '重试降级'],
  },
  {
    emoji: '🔍',
    title: '混合检索 RAG',
    desc: '向量检索（Embedding）+ BM25 关键词检索的 RRF 融合策略，附 Query 重写与 Rerank',
    tags: ['向量检索', 'BM25', 'RRF融合', 'Rerank'],
  },
  {
    emoji: '🎨',
    title: '多模态望诊',
    desc: '支持上传舌象/面色图片，提取视觉特征后作为结构化输入融合进辨证推理流程',
    tags: ['图像上传', '特征提取', '望诊融合'],
  },
  {
    emoji: '🔒',
    title: '安全与合规',
    desc: '双层安全检查（快速预检 + 完整审查）、高危关键词库、特殊人群保守策略、禁止处方剂量输出',
    tags: ['高危拦截', '安全约束', '合规输出'],
  },
]

const quickNav = [
  { emoji: '🩺', label: '智能问诊', path: '/consult' },
  { emoji: '👅', label: '舌象分析', path: '/consult/tongue' },
  { emoji: '🌿', label: '养生管理', path: '/wellness' },
  { emoji: '📚', label: '知识库', path: '/knowledge' },
]
</script>

<style scoped>
/* ── CSS 变量 & 基础 ───────────────────────────────── */
.home-nm {
  --bg: #f0f0f0;
  --bg-card: #f0f0f0;
  --shadow-out-dark: rgba(163, 177, 198, 0.7);
  --shadow-out-light: rgba(255, 255, 255, 0.9);
  --shadow-in-dark: rgba(163, 177, 198, 0.5);
  --shadow-in-light: rgba(255, 255, 255, 0.8);
  --text-primary: #2c3e50;
  --text-secondary: #6b7c93;
  --accent-blue: #007AFF;
  --accent-orange: #FF9500;

  background: var(--bg);
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
  color: var(--text-primary);
}

/* ── 拟态基础 mixin ─────────────────────────────────── */
.nm-card {
  background: var(--bg-card);
  border-radius: 18px;
  box-shadow:
    6px 6px 12px var(--shadow-out-dark),
    -6px -6px 12px var(--shadow-out-light);
  transition: box-shadow 0.25s ease, transform 0.25s ease;
}

.nm-card:hover {
  box-shadow:
    8px 8px 16px var(--shadow-out-dark),
    -8px -8px 16px var(--shadow-out-light);
}

.nm-card.clickable {
  cursor: pointer;
}

.nm-card.clickable:active {
  box-shadow:
    inset 4px 4px 8px var(--shadow-in-dark),
    inset -4px -4px 8px var(--shadow-in-light);
  transform: scale(0.98);
}

/* ── 英雄区 ──────────────────────────────────────────── */
.hero-section {
  background: linear-gradient(145deg, #f7f7f7 0%, #e8e8e8 100%);
  padding: 60px 40px 48px;
}

.hero-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 60px;
}

.hero-text { flex: 1; }

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--accent-blue);
  font-weight: 600;
  margin-bottom: 20px;
}

.nm-pill {
  background: var(--bg);
  padding: 6px 16px;
  border-radius: 99px;
  box-shadow:
    3px 3px 7px var(--shadow-out-dark),
    -3px -3px 7px var(--shadow-out-light);
}

.badge-dot {
  width: 8px;
  height: 8px;
  background: #34C759;
  border-radius: 50%;
  animation: pulse-dot 2s infinite;
}

@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0.6; transform: scale(1.3); }
}

.hero-title {
  font-size: 44px;
  font-weight: 700;
  letter-spacing: -1px;
  background: linear-gradient(135deg, #1a1a2e 0%, #007AFF 80%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0 0 16px;
  line-height: 1.15;
}

.hero-subtitle {
  font-size: 16px;
  color: var(--text-secondary);
  line-height: 1.7;
  margin: 0 0 32px;
}

.hero-cta {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.nm-btn-primary, .nm-btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  padding: 14px 28px;
  border: none;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
  outline: none;
  letter-spacing: 0.3px;
}

.nm-btn-primary {
  background: var(--accent-blue);
  color: #fff;
  box-shadow:
    4px 4px 10px rgba(0, 122, 255, 0.4),
    -2px -2px 6px rgba(255,255,255,0.6);
}

.nm-btn-primary:hover {
  box-shadow:
    6px 6px 14px rgba(0, 122, 255, 0.5),
    -2px -2px 8px rgba(255,255,255,0.7);
  transform: translateY(-2px);
}

.nm-btn-primary:active {
  box-shadow:
    inset 3px 3px 6px rgba(0, 0, 0, 0.25),
    inset -1px -1px 4px rgba(255,255,255,0.4);
  transform: translateY(0) scale(0.97);
}

.nm-btn-secondary {
  background: var(--bg);
  color: var(--text-primary);
  box-shadow:
    5px 5px 10px var(--shadow-out-dark),
    -5px -5px 10px var(--shadow-out-light);
}

.nm-btn-secondary:hover {
  box-shadow:
    7px 7px 14px var(--shadow-out-dark),
    -7px -7px 14px var(--shadow-out-light);
  transform: translateY(-2px);
}

.nm-btn-secondary:active {
  box-shadow:
    inset 4px 4px 8px var(--shadow-in-dark),
    inset -2px -2px 6px var(--shadow-in-light);
  transform: scale(0.97);
}

.btn-icon { font-size: 17px; }

.disclaimer-pill {
  display: inline-block;
  font-size: 12px;
  color: #e07a00;
  background: #fff8ed;
  border: 1px solid #ffe0a0;
  border-radius: 8px;
  padding: 8px 14px;
  box-shadow: inset 2px 2px 4px rgba(163,177,198,0.15);
}

/* ── 四象仪 ─────────────────────────────────────────── */
.hero-visual {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.wq-ring {
  position: relative;
  width: 280px;
  height: 280px;
  border-radius: 50%;
}

.nm-ring {
  background: var(--bg);
  box-shadow:
    10px 10px 20px var(--shadow-out-dark),
    -10px -10px 20px var(--shadow-out-light),
    inset 2px 2px 5px var(--shadow-in-light),
    inset -2px -2px 5px var(--shadow-in-dark);
}

.wq-center {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 90px;
  height: 90px;
  border-radius: 50%;
  background: linear-gradient(145deg, #ffffff, #e6e6e6);
  box-shadow:
    6px 6px 12px var(--shadow-out-dark),
    -6px -6px 12px var(--shadow-out-light);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.hero-avatar {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 50%;
}

.wq-orbit {
  position: absolute;
  width: 64px;
  height: 64px;
}

.nm-dot {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--bg);
  box-shadow:
    4px 4px 8px var(--shadow-out-dark),
    -4px -4px 8px var(--shadow-out-light);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  animation: orbit-float 3s ease-in-out infinite;
}

.nm-dot:nth-child(2) { animation-delay: 0.75s; }
.nm-dot:nth-child(3) { animation-delay: 1.5s; }
.nm-dot:nth-child(4) { animation-delay: 2.25s; }

@keyframes orbit-float {
  0%, 100% { transform: translateY(0); }
  50%       { transform: translateY(-4px); }
}

.wq-char {
  font-size: 18px;
  font-weight: 700;
  color: var(--dot-color);
}

.wq-label {
  font-size: 9px;
  color: var(--text-secondary);
}

/* ── 通用 Section ────────────────────────────────────── */
.section {
  max-width: 1200px;
  margin: 0 auto;
  padding: 48px 40px;
}

.section-header {
  text-align: center;
  margin-bottom: 36px;
}

.section-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 8px;
}

.section-sub {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0;
}

/* ── 功能卡片网格 ────────────────────────────────────── */
.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
}

.feature-card {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 22px 20px;
}

.feat-emoji {
  font-size: 32px;
  flex-shrink: 0;
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: linear-gradient(145deg, #f7f7f7, #e4e4e4);
  box-shadow:
    4px 4px 8px var(--shadow-out-dark),
    -4px -4px 8px var(--shadow-out-light),
    inset 1px 1px 3px var(--shadow-in-light);
  display: flex;
  align-items: center;
  justify-content: center;
}

.feat-text { flex: 1; }
.feat-text h4 {
  margin: 0 0 6px;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}
.feat-text p {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}

.feat-arrow {
  font-size: 20px;
  color: var(--accent-blue);
  flex-shrink: 0;
  align-self: center;
}

/* ── Agent 架构流 ────────────────────────────────────── */
.arch-section {
  background: linear-gradient(145deg, #eef1f5, #e8ebf0);
  max-width: 100%;
  padding: 48px 40px;
}

.arch-flow {
  display: flex;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 0;
  justify-content: center;
  max-width: 1200px;
  margin: 0 auto;
}

.arch-step {
  display: flex;
  align-items: center;
}

.nm-node {
  background: var(--bg);
  border-radius: 16px;
  padding: 20px 16px;
  text-align: center;
  width: 110px;
  box-shadow:
    5px 5px 10px var(--shadow-out-dark),
    -5px -5px 10px var(--shadow-out-light);
  transition: box-shadow 0.2s, transform 0.2s;
  border-top: 3px solid var(--nc);
}

.nm-node:hover {
  box-shadow:
    7px 7px 14px var(--shadow-out-dark),
    -7px -7px 14px var(--shadow-out-light);
  transform: translateY(-3px);
}

.node-emoji { font-size: 28px; margin-bottom: 6px; }
.node-name  { font-size: 12px; font-weight: 700; color: var(--nc); margin-bottom: 4px; }
.node-desc  { font-size: 11px; color: var(--text-secondary); line-height: 1.4; }

.arch-arrow {
  font-size: 22px;
  color: var(--text-secondary);
  padding: 0 8px;
  flex-shrink: 0;
  align-self: center;
  margin-top: 0;
}

/* ── 技术亮点 ────────────────────────────────────────── */
.tech-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 20px;
}

.tech-card {
  padding: 24px 20px;
}

.tech-icon {
  font-size: 36px;
  margin-bottom: 12px;
}

.tech-card h4 {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 8px;
  color: var(--text-primary);
}

.tech-card p {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.65;
  margin: 0 0 12px;
}

.tech-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.nm-tag {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 99px;
  background: var(--bg);
  color: var(--accent-blue);
  box-shadow:
    2px 2px 4px var(--shadow-out-dark),
    -2px -2px 4px var(--shadow-out-light);
}

/* ── 快速入口 ────────────────────────────────────────── */
.quick-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.nm-quick-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 28px 16px;
  background: var(--bg);
  border-radius: 18px;
  cursor: pointer;
  box-shadow:
    6px 6px 12px var(--shadow-out-dark),
    -6px -6px 12px var(--shadow-out-light);
  transition: all 0.2s ease;
  user-select: none;
}

.nm-quick-btn:hover {
  box-shadow:
    8px 8px 16px var(--shadow-out-dark),
    -8px -8px 16px var(--shadow-out-light);
  transform: translateY(-3px);
}

.nm-quick-btn:active {
  box-shadow:
    inset 4px 4px 8px var(--shadow-in-dark),
    inset -4px -4px 8px var(--shadow-in-light);
  transform: scale(0.96);
}

.qbtn-emoji {
  font-size: 36px;
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background: linear-gradient(145deg, #f7f7f7, #e4e4e4);
  box-shadow:
    3px 3px 6px var(--shadow-out-dark),
    -3px -3px 6px var(--shadow-out-light);
  display: flex;
  align-items: center;
  justify-content: center;
}

.nm-quick-btn span {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

/* ── 页脚 ─────────────────────────────────────────────── */
.footer {
  text-align: center;
  padding: 32px 20px 40px;
  background: linear-gradient(145deg, #e8e8e8, #f0f0f0);
  border-top: 1px solid rgba(163,177,198,0.3);
}

.footer-title {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 0 8px;
  font-weight: 600;
}

.footer-disclaimer {
  font-size: 12px;
  color: #999;
  margin: 0;
}

/* ── 响应式 ───────────────────────────────────────────── */
@media (max-width: 900px) {
  .hero-inner { flex-direction: column; gap: 36px; }
  .hero-title { font-size: 32px; }
  .hero-visual { display: none; }
  .section { padding: 36px 20px; }
  .arch-section { padding: 36px 20px; }
  .card-grid { grid-template-columns: 1fr; }
  .quick-grid { grid-template-columns: repeat(2, 1fr); }
  .arch-flow { gap: 4px; }
}
</style>
